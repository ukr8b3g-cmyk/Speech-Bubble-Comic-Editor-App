const assert = require("node:assert/strict");
const fs = require("node:fs");

const html = fs.readFileSync("web/speech-bubble-editor.html", "utf8");

assert.match(html, /const file=blob instanceof File\?blob:new File\(\[blob\],asset\.name\|\|"page-image"/);
assert.match(html, /generalComicEditor\?\.isActive\(\)\|\|activeWorkspace==="comic_layout"/);
assert.match(html, /comicEditor\?\.isActive\(\)\|\|activeWorkspace==="comic"/);
assert.match(html, /comicEditor\?\.defaultPanelInsertionTarget\?\.\(\)/);
assert.match(html, /comicEditor\?\.selectPanel\?\.\(fallback\.panelId\)/);
assert.match(html, /comicEditor\?\.importExternalImage\?\.\(file,asset,\{assignToSelectedPanel:true,point:control\.point\}\)/);
assert.match(html, /projectImageTray\.place\(projectImageId,\{point\}\)/);

console.log("page_image_4panel_place_test: OK");
