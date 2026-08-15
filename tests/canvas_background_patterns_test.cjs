const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

class FakeGradient {
  constructor(log) { this.log = log; }
  addColorStop(offset, color) { this.log.push(["stop", offset, color]); }
}
class FakeContext {
  constructor() { this.log = []; this.globalAlpha = 1; }
  save(){this.log.push(["save"]);} restore(){this.log.push(["restore"]);}
  translate(x,y){this.log.push(["translate",x,y]);} rotate(v){this.log.push(["rotate",v]);}
  fillRect(x,y,w,h){this.log.push(["fillRect",x,y,w,h,this.fillStyle,this.globalAlpha]);}
  strokeRect(x,y,w,h){this.log.push(["strokeRect",x,y,w,h]);}
  beginPath(){this.log.push(["begin"]);} closePath(){this.log.push(["close"]);}
  moveTo(x,y){this.log.push(["move",x,y]);} lineTo(x,y){this.log.push(["line",x,y]);}
  arc(x,y,r){this.log.push(["arc",x,y,r]);} fill(){this.log.push(["fill"]);} stroke(){this.log.push(["stroke"]);}
  createLinearGradient(...args){this.log.push(["linear",...args]);return new FakeGradient(this.log);}
  createRadialGradient(...args){this.log.push(["radial",...args]);return new FakeGradient(this.log);}
  createImageData(w,h){return{width:w,height:h,data:new Uint8ClampedArray(w*h*4)};}
  putImageData(image){this.imageChecksum=image.data.reduce((sum,value)=>(sum+value)>>>0,0);}
  drawImage(canvas,...args){this.log.push(["drawImage",canvas.width,canvas.height,canvas.context.imageChecksum||0,...args]);}
}
global.window = {};
global.document = {createElement(name){assert.equal(name,"canvas");const canvas={width:0,height:0};canvas.context=new FakeContext();canvas.getContext=()=>canvas.context;return canvas;}};
vm.runInThisContext(fs.readFileSync("web/canvas-background-patterns.js","utf8"));
const patterns = window.SpeechBubbleCanvasBackgroundPatterns;

assert.equal(patterns.TYPES.length,23);
assert.equal(new Set(patterns.TYPES.map(item=>item.id)).size,23);
assert.ok(patterns.TYPES.every(item=>item.ja&&item.en&&item.presets.length));
assert.deepEqual(patterns.normalize({color:"#ABCDEF",transparent:true}).type,"solid");
assert.equal(patterns.normalize({color:"#ABCDEF"}).color,"#abcdef");
assert.equal(patterns.normalize({type:"missing"}).type,"solid");

for(const type of patterns.TYPES){
  const context=new FakeContext();
  assert.doesNotThrow(()=>patterns.draw(context,{type:type.id,preset:type.presets[0].id},64,48),type.id);
  assert.ok(context.log.length||type.id==="solid",`${type.id} should draw`);
}
const transparent=new FakeContext();
patterns.draw(transparent,{type:"solid",transparent:true},64,48);
assert.equal(transparent.log.some(entry=>entry[0]==="fillRect"),false);
for(const type of ["clouds","marble","cellular","turbulence","fractal","wood","digital-camouflage"]){
  const first=new FakeContext(),second=new FakeContext(),settings={type,seed:4242};
  patterns.draw(first,settings,64,48);patterns.draw(second,settings,64,48);
  assert.deepEqual(first.log,second.log,`${type} must be deterministic for the same seed`);
}

console.log("canvas_background_patterns_test: OK");
