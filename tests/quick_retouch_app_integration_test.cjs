"use strict";
const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm");
const editor=fs.readFileSync("web/speech-bubble-editor.html","utf8"),js=fs.readFileSync("web/quick-retouch.js","utf8"),core=fs.readFileSync("web/quick-retouch-core.js","utf8"),css=fs.readFileSync("web/quick-retouch.css","utf8");
new vm.Script(js,{filename:"quick-retouch.js"});new vm.Script(core,{filename:"quick-retouch-core.js"});
assert.match(editor,/quick-retouch\.css\?v=phase4-quick-retouch-0710-1/);assert.match(editor,/quick-retouch-core\.js\?v=phase4-quick-retouch-0710-1/);assert.match(editor,/quick-retouch\.js\?v=phase4-quick-retouch-0710-1/);
assert.match(editor,/data-quick-retouch-open/);assert.match(editor,/processLayerQuickRetouch/);assert.match(editor,/function initializeQuickRetouch\(\)/);assert.match(editor,/getSingleSource:selectedSingleImageSource/);assert.match(editor,/getComicSources:\(\)=>generalComicEditor/);assert.match(editor,/addPageImage:\(blob,name\)=>generalComicEditor/);assert.match(editor,/"quick-retouch",source/);assert.match(editor,/sourceContext\?\.layer_id\|\|lastSingleProcessingLayerId/);assert.match(editor,/quickRetouch\?\.close\?\.\(\)/);assert.match(js,/BUILD_VERSION = "0\.7\.10"/);assert.match(css,/quick-retouch-dialog/);
console.log("quick_retouch_app_integration_test: OK");
