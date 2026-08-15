"use strict";
const assert=require("node:assert/strict"),fs=require("node:fs");
const editor=fs.readFileSync("web/speech-bubble-editor.html","utf8"),comic=fs.readFileSync("web/comic-editor.js","utf8"),general=fs.readFileSync("web/general-comic-editor.js","utf8"),tray=fs.readFileSync("web/project-image-tray.js","utf8");
assert.match(tray,/if \(!current\.includes\(id\)\) current\.push\(id\)/);
assert.match(editor,/importExternalImage\?\.\(file,asset,/);
for(const source of [comic,general]){assert.match(source,/id: String\(asset\.id\)/);assert.match(source,/comic\.images\.find\(\(item\) => item\.id === metadata\.id\)/);}
console.log("page_images_id_reuse_test: OK");
