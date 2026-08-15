const assert = require("node:assert/strict");
const fs = require("node:fs");

const html = fs.readFileSync("web/speech-bubble-editor.html", "utf8");

assert.match(html, /function createSingleImageLayer\(asset,\{[^}]*locked=false/);
assert.match(html, /function primarySingleCanvasImageLayer\(\)/);
assert.match(html, /function shouldResizeSingleCanvasForImage\(asset,item\)/);
assert.match(html, /const otherEditable=state\.elements\.some\(layer=>layer\.id!==item\.id&&layer\.visible!==false\)/);
assert.match(html, /Resize the canvas to the new image\?/);
assert.match(html, /async function replaceSingleImageLayerFromBlob\(item,blob,name/);
assert.match(html, /item\.rotation=0/);
assert.match(html, /scaleStateToImageSize\(Math\.max\(1,asset\.width\),Math\.max\(1,asset\.height\)\)/);
assert.match(html, /fitImageLayerGeometry\(asset,"contain"\)/);
assert.match(html, /async function requestBackgroundFile\(file\)\{if\(!file\)return;const primary=primarySingleCanvasImageLayer\(\);if\(primary\)\{await replaceSingleImageLayerFromBlob/);
assert.match(html, /target==="__add__"\)\{await addSingleImageLayerFromBlob\(file,file\.name,\{role:"image",locked:false\}\)/);
assert.match(html, /if\(item\)\{await replaceSingleImageLayerFromBlob\(item,file,file\.name\);return;\}/);

console.log("single_image_replacement_test: OK");
