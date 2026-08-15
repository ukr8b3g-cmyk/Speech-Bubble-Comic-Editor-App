const fs = require('fs');
const path = require('path');
const assert = require('assert');
const root = path.resolve(__dirname, '..');
const comicCore = require(path.join(root, 'web', 'comic-panels.js'));
const generalCore = require(path.join(root, 'web', 'general-comic-core.js'));
const imageRotation = require(path.join(root, 'web', 'image-layer-rotation.js'));
const html = fs.readFileSync(path.join(root, 'web', 'speech-bubble-editor.html'), 'utf8');
const comicEditor = fs.readFileSync(path.join(root, 'web', 'comic-editor.js'), 'utf8');
const generalEditor = fs.readFileSync(path.join(root, 'web', 'general-comic-editor.js'), 'utf8');
const cropDialog = fs.readFileSync(path.join(root, 'web', 'image-crop-dialog.js'), 'utf8');

for (const id of ['imageCropToolbar','editImageCrop','resetImageCrop','multiAlignPanel','alignmentReference','groupRotationRange','groupRotation','backgroundRotationRange']) {
  assert(html.includes(`id="${id}"`), `missing #${id}`);
}
for (const action of ['left','hcenter','right','hdistribute','top','vcenter','bottom','vdistribute']) {
  assert(html.includes(`data-align-action="${action}"`), `missing alignment action ${action}`);
}
for (const value of ['selection','panel','page']) assert(html.includes(`<option value="${value}"`), `missing alignment reference ${value}`);
for (const fn of ['normalizedImageCrop','drawSingleImageLayer','startImageCropEdit','confirmImageCropEdit','cancelImageCropEdit','resetImageCrop','drawImageCropOverlay','alignSelectedObjects','distributeSelectedObjects','beginGroupRotationEdit','commitGroupRotationEdit','replaceSingleImageLayerFromBlob','shouldResizeSingleCanvasForImage']) {
  assert(html.includes(`function ${fn}`), `missing function ${fn}`);
}
assert(html.includes('canvas.addEventListener("dblclick"'), 'missing double-click crop entry');
assert(html.includes('structuralEditor?.startImageCrop?.()'), 'structural C-key crop routing missing');
assert(html.includes('structuralEditor?.startImageCropAt?.(point)'), 'structural double-click crop routing missing');
assert(html.includes('imageCropEdit&&!editing&&modifier&&(key==="z"||key==="y")'), 'crop history shortcut guard missing');
assert(html.includes('item.crop={x:0,y:0,w:1,h:1}'), 'single-image crop reset on replace/fit missing');
assert(!html.includes('item.rotation=0;syncProperties();render();}\n    function fitSelectedImage'), 'reset position must preserve rotation');
assert(html.includes('./image-crop-dialog.js?v=phase3-crop-align-1'), 'crop dialog script not loaded');
assert(html.includes('./image-layer-rotation.js?v=phase3-crop-align-1'), 'rotation helper script not loaded');

assert.deepStrictEqual(comicCore.normalizeImageCrop({x:.2,y:.1,w:.5,h:.6}), {x:.2,y:.1,w:.5,h:.6});
assert.deepStrictEqual(comicCore.panelNode(()=>'a', {image_crop:{x:.2,y:.1,w:.5,h:.6}}).image_crop, {x:.2,y:.1,w:.5,h:.6});
assert.deepStrictEqual(generalCore.panelNode(()=>'b', {image_crop:{x:.15,y:.2,w:.7,h:.5}}).image_crop, {x:.15,y:.2,w:.7,h:.5});
assert.strictEqual(comicCore.panelNode(()=>'c', {}).image_rotation, 0);
assert.strictEqual(generalCore.panelNode(()=>'d', {}).image_rotation, 0);
assert.strictEqual(comicCore.panelNode(()=>'e', {image_rotation:181}).image_rotation, 180);
assert.strictEqual(generalCore.panelNode(()=>'f', {image_rotation:-181}).image_rotation, -180);

let comicId = 0;
const comicState = comicCore.defaultState(720, 2200, ()=>`persist-${++comicId}`);
const comicPanel = comicCore.collectPanels(comicState.tree)[0];
comicPanel.image_crop = {x:.12,y:.18,w:.66,h:.55};
comicPanel.image_rotation = 37;
let normalizedComicId = 0;
const normalizedComicState = comicCore.normalizeState(comicState, {width:720,height:2200,makeId:()=> `persist-normalized-${++normalizedComicId}`});
const normalizedComicPanel = comicCore.collectPanels(normalizedComicState.tree)[0];
assert.deepStrictEqual(normalizedComicPanel.image_crop, {x:.12,y:.18,w:.66,h:.55});
assert.strictEqual(normalizedComicPanel.image_rotation, 37);

let generalId = 0;
const generalState = generalCore.defaultState(2480, 3508, ()=>`persist-general-${++generalId}`);
const generalPanel = generalCore.collectPanels(generalState.tree)[0];
generalPanel.image_crop = {x:.08,y:.14,w:.72,h:.63};
generalPanel.image_rotation = -42;
let normalizedGeneralId = 0;
const normalizedGeneralState = generalCore.normalizeState(generalState, {width:2480,height:3508,makeId:()=> `persist-general-normalized-${++normalizedGeneralId}`});
const normalizedGeneralPanel = generalCore.collectPanels(normalizedGeneralState.tree)[0];
assert.deepStrictEqual(normalizedGeneralPanel.image_crop, {x:.08,y:.14,w:.72,h:.63});
assert.strictEqual(normalizedGeneralPanel.image_rotation, -42);

for (const source of [comicEditor, generalEditor]) {
  assert(source.includes('edit-image-crop'), 'panel crop edit button missing');
  assert(source.includes('reset-image-crop'), 'panel crop reset button missing');
  assert(source.includes('image_crop'), 'panel crop state missing');
  assert(source.includes('startImageCropAt'), 'panel double-click crop API missing');
  assert(source.includes('startImageCrop:'), 'panel C-key crop API missing');
  assert(source.includes('image_rotation'), 'panel rotation state missing');
  assert(source.includes('imageLayerRotation.drawCroppedImage'), 'shared rotated crop draw path missing');
}
assert(cropDialog.includes('sb-image-crop-handle'), 'interactive crop handles missing');
assert(cropDialog.includes('data-crop-confirm'), 'crop confirm button missing');
assert(cropDialog.includes('data-crop-cancel'), 'crop cancel button missing');

const calls = [];
const target = {
  globalAlpha: 1,
  save: () => calls.push(['save']), restore: () => calls.push(['restore']),
  translate: (...args) => calls.push(['translate', ...args]), rotate: (...args) => calls.push(['rotate', ...args]),
  scale: (...args) => calls.push(['scale', ...args]), drawImage: (...args) => calls.push(['drawImage', ...args]),
};
imageRotation.drawCroppedImage(target, {naturalWidth:400,naturalHeight:300}, {x:10,y:20,w:100,h:60,sourceX:5,sourceY:6,sourceW:200,sourceH:150}, 90);
assert.deepStrictEqual(calls.find((entry) => entry[0] === 'translate'), ['translate',60,50]);
assert.strictEqual(calls.find((entry) => entry[0] === 'rotate')[1], Math.PI / 2);
assert.deepStrictEqual(calls.find((entry) => entry[0] === 'drawImage').slice(-4), [-50,-30,100,60]);

console.log('phase3_crop_align_test: OK');
