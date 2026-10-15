#!/usr/bin/env python3
"""Explain explicit HTTP cache freshness from a saved Endpoint/Deadline Sentry report."""
import argparse
import datetime as dt
import email.utils
import json
from pathlib import Path
import re
import sys

LIMIT = 1048576
TOKEN = re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+\Z")


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError('timestamp must be a timezone-aware ISO string')
    parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.utcoffset() is None:
        raise ValueError('timestamp must include a timezone')
    return parsed


def directives(values):
    """Split comma lists without treating quoted commas as separators."""
    result = {}
    for value in values:
        parts, current, quoted, escaped = [], '', False, False
        for char in value:
            if escaped:
                current += char
                escaped = False
                continue
            if quoted and char == '\\':
                current += char
                escaped = True
                continue
            if char == '"':
                quoted = not quoted
            if char == ',' and not quoted:
                parts.append(current)
                current = ''
            else:
                current += char
        if quoted or escaped:
            raise ValueError('unterminated Cache-Control quoted string')
        parts.append(current)
        for part in parts:
            if not part.strip():
                continue
            name, separator, argument = part.strip().partition('=')
            name = name.strip().lower()
            if not TOKEN.fullmatch(name):
                raise ValueError('invalid Cache-Control directive name')
            argument = argument.strip() if separator else None
            if argument is not None:
                if argument.startswith('"') and argument.endswith('"'):
                    raw = argument[1:-1]
                    if re.search(r'(?<!\\)"', raw):
                        raise ValueError('invalid quoted directive')
                    argument = re.sub(r'\\(.)', r'\1', raw)
                elif not TOKEN.fullmatch(argument):
                    raise ValueError('invalid Cache-Control directive value')
            result.setdefault(name, []).append(argument)
    return result


def inspect(report, shared=False, at=None):
    if not isinstance(report, dict):
        raise ValueError('report must be an object')
    if report.get('schema') == 'deadline-sentry/v1':
        report = report.get('probe')
    if not isinstance(report, dict) or report.get('schema') != 'endpoint-sentry/v1':
        raise ValueError('need a completed endpoint-sentry/v1 report (or Deadline wrapper)')
    if report.get('error') or not report.get('final_url') or not report.get('hops'):
        raise ValueError('probe did not complete an HTTP response')
    hop = report['hops'][-1]
    if not isinstance(hop, dict) or type(hop.get('status')) is not int:
        raise ValueError('invalid final hop')
    pairs = hop.get('cache_headers')
    if not isinstance(pairs, list) or len(pairs) > 256:
        raise ValueError('cache headers absent or too numerous; capture with updated Endpoint Sentry')
    headers = {}
    for pair in pairs:
        if (not isinstance(pair, list) or len(pair) != 2 or
                not all(isinstance(x, str) for x in pair) or
                not TOKEN.fullmatch(pair[0]) or
                any(ord(c) < 32 or ord(c) == 127 for c in pair[1])):
            raise ValueError('invalid cache header pair')
        headers.setdefault(pair[0].lower(), []).append(pair[1])
    sent = timestamp(hop.get('request_sent_at'))
    received = timestamp(hop.get('headers_received_at'))
    now = timestamp(at) if at is not None else received
    if received < sent or now < received:
        raise ValueError('timestamps must satisfy request <= headers <= evaluation')
    cc = directives(headers.get('cache-control', []))
    warnings = []

    def singleton(name):
        values = headers.get(name, [])
        if len(values) > 1:
            warnings.append('duplicate ' + name)
            return None
        return values[0] if values else None

    def http_date(name):
        text = singleton(name)
        if text is None:
            return None
        try:
            value = email.utils.parsedate_to_datetime(text)
            if value.utcoffset() is None:
                raise ValueError('missing timezone')
            return value
        except (ValueError, TypeError, OverflowError):
            warnings.append('invalid ' + name)
            return None

    def delta(name, values):
        if not values:
            return None
        if len(values) != 1 or values[0] is None or not re.fullmatch(r'[0-9]{1,15}', values[0]):
            warnings.append('invalid or duplicate ' + name)
            return None
        return int(values[0])

    date = http_date('date')
    age = delta('age', headers.get('age', []))
    if 'age' not in headers:
        age = 0
    current_age = None
    if date is None:
        warnings.append('Date missing or unusable; age cannot be established')
    elif age is not None:
        apparent_age = max(0, (received - date).total_seconds())
        response_delay = (received - sent).total_seconds()
        current_age = max(apparent_age, age + response_delay) + (now - received).total_seconds()
    # Invalid higher-priority directives cannot silently fall back to a lower one.
    source = ('s-maxage' if shared and 's-maxage' in cc else
              'max-age' if 'max-age' in cc else None)
    lifetime = delta(source, cc[source]) if source else None
    if source is None and 'expires' in headers:
        source = 'expires'
        expires = http_date('expires')
        if expires is not None and date is not None:
            lifetime = max(0, (expires - date).total_seconds())
    for key in ('no-store', 'no-cache', 'private', 'public', 'must-revalidate', 'proxy-revalidate'):
        if len(cc.get(key, [])) > 1:
            warnings.append('duplicate ' + key)
    vary_star = any('*' in [v.strip() for v in line.split(',')]
                    for line in headers.get('vary', []))
    if 'no-store' in cc:
        verdict = 'storage_forbidden'
    elif shared and 'private' in cc:
        verdict = 'shared_storage_forbidden'
    elif 'no-cache' in cc or vary_star:
        verdict = 'revalidation_required'
    elif hop['status'] != 200:
        verdict = 'unsupported_status'
    elif warnings or current_age is None or lifetime is None:
        verdict = 'freshness_unknown'
    elif current_age >= lifetime:
        verdict = 'stale'
    else:
        verdict = 'within_freshness_lifetime'
    return {'schema': 'cache-lens/v1', 'cache_type': 'shared' if shared else 'private',
            'evaluated_at': now.isoformat(), 'verdict': verdict,
            'freshness_lifetime_seconds': lifetime, 'lifetime_source': source,
            'current_age_seconds': round(current_age, 6) if current_age is not None else None,
            'remaining_seconds': round(max(0, lifetime - current_age), 6)
                if lifetime is not None and current_age is not None else None,
            'validators_present': {'etag': bool(headers.get('etag')),
                                   'last_modified': bool(headers.get('last-modified'))},
            'stale_reuse_requires_validation': bool('must-revalidate' in cc or
                shared and ('proxy-revalidate' in cc or 's-maxage' in cc)),
            'warnings': warnings,
            'scope': 'Freshness metadata only; not permission to store or reuse a response. '
                     'Request directives, Vary matching, authorization, cache keys and stale '
                     'extensions are not evaluated. No conditional request is sent.'}


def workspace_file(value):
    root = Path.cwd().resolve()
    path = Path(value).resolve()
    if not path.is_relative_to(root):
        raise ValueError('input must be inside the current workspace')
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('report', help='saved report inside current workspace, or - for stdin')
    parser.add_argument('--shared', action='store_true', help='use s-maxage and private restrictions')
    parser.add_argument('--at', help='timezone-aware ISO evaluation time; default: header receipt time')
    args = parser.parse_args(argv)
    try:
        if args.report == '-':
            data = sys.stdin.buffer.read(LIMIT + 1)
        else:
            with workspace_file(args.report).open('rb') as stream:
                data = stream.read(LIMIT + 1)
        if len(data) > LIMIT:
            raise ValueError('report exceeds 1 MiB input limit')
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError('duplicate JSON key: ' + key)
                result[key] = value
            return result
        def invalid(value):
            raise ValueError('non-finite JSON constant: ' + value)
        report = json.loads(data, object_pairs_hook=unique, parse_constant=invalid)
        result = inspect(report, args.shared, args.at)
    except (OSError, ValueError, TypeError, KeyError, IndexError, OverflowError,
            RecursionError) as error:
        print(json.dumps({'schema': 'cache-lens/v1', 'error': str(error)}))
        return 2
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
