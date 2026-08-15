const assert = require("node:assert/strict");
const fs = require("node:fs");

const html = fs.readFileSync("web/speech-bubble-editor.html", "utf8");
const comic = fs.readFileSync("web/comic-editor.js", "utf8");
const general = fs.readFileSync("web/general-comic-editor.js", "utf8");

assert.match(html, /<main class="canvas-panel">\s*<div class="canvas-workspace">/);
assert.match(comic, /footer\.parentElement\?\.insertBefore\(tray, footer\)/);
assert.match(general, /footer\.parentElement\?\.insertBefore\(tray, footer\)/);
assert.doesNotMatch(comic, /canvasPanel\.insertBefore\(tray, footer\)/);
assert.doesNotMatch(general, /canvasPanel\.insertBefore\(tray, footer\)/);
assert.match(html, /\.canvas-workspace > \.comic-image-tray,\.canvas-workspace > \.general-comic-image-tray \{ display:none !important; \}/);

console.log("phase2_canvas_wrapper_regression_test: OK");
