const assert = require("node:assert/strict");
const fs = require("node:fs");
const comic = fs.readFileSync("web/comic-editor.js", "utf8");
const editor = fs.readFileSync("web/speech-bubble-editor.html", "utf8");
assert.match(comic, /function panelEditable\(panel\) \{\s*return panel\?\.kind === "panel" && panel\.locked !== true && panel\.collapsed !== true;\s*\}/);
assert.match(comic, /const target = dropped \|\| \(control\.assignToSelectedPanel \? selectedPanel\(\) : null\);\s*if \(target && panelEditable\(target\)\)/);
assert.match(editor, /projectImageTray\.place\(projectImageId,\{point\}\)/);
assert.match(editor, /comicEditor\?\.importExternalImage\?\.\(file,asset,\{assignToSelectedPanel:true,point:control\.point\}\)/);
console.log("page_images_4panel_placement_test: OK");
