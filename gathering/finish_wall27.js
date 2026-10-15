// Export the image tool's new charcoal motif onto the untouched ancestor rock.
// One-time command: node gathering/finish_wall27.js
// No network, configuration, environment, or inputs outside the workspace.
'use strict';
const fs = require('node:fs');
const zlib = require('node:zlib');
const crypto = require('node:crypto');
const {decode, thumbnail} = require('./thumbnail.js');
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const ancestor = '25b5b2d1876680f2656e3e15f9b9fb6c49b694145559cf06b51cc1dd23a4ac2c';
const oldBytes = fs.readFileSync('artifacts/gathering/wall.png');
if (hash(oldBytes) !== ancestor) throw new Error('requires unchanged round-26 ancestor');
const generated = fs.readFileSync('artifacts/gathering/wall-v7.png');
const old = decode(oldBytes), fresh = decode(generated);
if(old.width !== 1254 || old.height !== 1254 || old.channels !== 3 ||
   fresh.width !== 1024 || fresh.height !== 1024) throw new Error('unexpected input dimensions');
const out = Buffer.from(old.pixels);
// The model added its motif lower than requested. Transfer only that new mark;
// never transfer model-redrawn ancestors. Dark-pigment mask retains original rock.
const source = [476, 888, 536, 948], bounds = [755, 982, 835, 1062];
for(let y=bounds[1];y<=bounds[3];y++)for(let x=bounds[0];x<=bounds[2];x++){
  const sx=Math.round(source[0]+(x-bounds[0])/(bounds[2]-bounds[0])*(source[2]-source[0]));
  const sy=Math.round(source[1]+(y-bounds[1])/(bounds[3]-bounds[1])*(source[3]-source[1]));
  const p=(y*old.width+x)*3, q=(sy*fresh.width+sx)*fresh.channels;
  const darkness=Math.max(0,Math.min(1,(85-Math.max(...fresh.pixels.subarray(q,q+3)))/35));
  const feather=Math.min(1,Math.min(x-bounds[0],bounds[2]-x,y-bounds[1],bounds[3]-y)/5);
  const alpha=darkness*feather;
  for(let c=0;c<3;c++)out[p+c]=Math.round(old.pixels[p+c]*(1-alpha)+fresh.pixels[q+c]*alpha);
}
let changed=0,outside=0,box=[1254,1254,-1,-1];
for(let y=0;y<old.height;y++)for(let x=0;x<old.width;x++){
  const p=(y*old.width+x)*3;
  if(out[p]!==old.pixels[p]||out[p+1]!==old.pixels[p+1]||out[p+2]!==old.pixels[p+2]){
    changed++;box=[Math.min(box[0],x),Math.min(box[1],y),Math.max(box[2],x),Math.max(box[3],y)];
    if(x<bounds[0]||x>bounds[2]||y<bounds[1]||y>bounds[3])outside++;
  }
}
if(!changed||outside)throw new Error('preservation failure');
function crc32(bytes){let crc=0xffffffff;for(const v of bytes){crc^=v;for(let i=0;i<8;i++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}return(crc^0xffffffff)>>>0;}
function chunk(name,data){const kind=Buffer.from(name),len=Buffer.alloc(4),crc=Buffer.alloc(4);len.writeUInt32BE(data.length);crc.writeUInt32BE(crc32(Buffer.concat([kind,data])));return Buffer.concat([len,kind,data,crc]);}
const header=Buffer.alloc(13);header.writeUInt32BE(old.width);header.writeUInt32BE(old.height,4);header[8]=8;header[9]=2;
const stride=old.width*3,scan=Buffer.alloc(old.height*(stride+1));
for(let y=0;y<old.height;y++)out.copy(scan,y*(stride+1)+1,y*stride,(y+1)*stride);
const png=Buffer.concat([Buffer.from('89504e470d0a1a0a','hex'),chunk('IHDR',header),chunk('IDAT',zlib.deflateSync(scan,{level:9})),chunk('IEND',Buffer.alloc(0))]);
const jpeg=thumbnail(png,512,75);
if(jpeg.length>=100000)throw new Error('JPEG over budget');
fs.writeFileSync('artifacts/gathering/wall-v7.png',png);
fs.writeFileSync('artifacts/gathering/wall.png',png);
fs.writeFileSync('dist/gathering/27.jpg',jpeg);
const result={ancestor_sha256:ancestor,generated_sha256:hash(generated),
  png:{path:'artifacts/gathering/wall-v7.png',format:'PNG',mode:'RGB',dimensions:[1254,1254],bytes:png.length,sha256:hash(png)},
  jpeg:{path:'dist/gathering/27.jpg',format:'JPEG',dimensions:[512,512],bytes:jpeg.length},
  preservation:{source_rectangle:source,rectangle:bounds,changed_pixels:changed,changed_bounds:box,outside_rectangle_changed_pixels:outside},
  model:'black-forest-labs/flux-kontext-pro',visual_review_required:true,unmet_visual_requirements:[]};
fs.writeFileSync('gathering/image-checks27.json',JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
