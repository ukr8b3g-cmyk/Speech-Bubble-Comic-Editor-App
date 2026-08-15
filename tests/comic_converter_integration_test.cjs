const assert = require("node:assert/strict");
const fs = require("node:fs");

const html = fs.readFileSync("web/speech-bubble-editor.html", "utf8");
const converter = fs.readFileSync("web/comic-converter.js", "utf8");
const converterCss = fs.readFileSync("web/comic-converter.css", "utf8");
const comicEditor = fs.readFileSync("web/comic-editor.js", "utf8");
const desktopShell = fs.readFileSync("web/desktop/desktop-shell.js", "utf8");
const readme = fs.readFileSync("README.md", "utf8");

for (const asset of ["comic-converter.css", "comic-converter.js"]) {
  assert.ok(html.includes(`./${asset}?v=`), `${asset} must be cache-busted and loaded`);
}

for (const feature of [
  "data-comic-converter-open",
  "initializeComicConverter",
  "getSingleSource",
  "getComicSources",
  "addPageImage",
  "applySingleImage",
  "clearConversionHistory",
  "cleanupUnusedComicImages",
]) {
  assert.ok(html.includes(feature), `Editor integration must include ${feature}`);
}

for (const value of [
  "PREVIEW_LONG_EDGE = 768",
  "HISTORY_MAX_PER_DOCUMENT = 5",
  "HISTORY_MAX_BYTES = 512 * 1024 * 1024",
  "HISTORY_MAX_AGE = 30 * 24 * 60 * 60 * 1000",
  "brightness: 0",
  "contrast: 1.04",
  "smoothRadius: 2",
  "posterLevels: 5",
  "edgeThreshold: 0.055",
  "edgeStrength: 0.3",
  "colorEdgeWeight: 1.25",
  "lineCleanup: 0.04",
  "sigma: 0.8",
  "epsilon: -0.005",
  "phi: 45",
  "lineStrength: 0.95",
  "k: 1.6",
  "tau: 0.995",
]) {
  assert.ok(converter.includes(value), `Converter must preserve approved default: ${value}`);
}

assert.match(converter, /new Worker/);
assert.match(converter, /mode: "grayscale"/);
assert.match(converter, /let currentPreset = "grayscale"/);
assert.ok(
  converter.indexOf('<option value="grayscale">') < converter.indexOf('<option value="comic">'),
  "Simple Grayscale must be the first conversion preset",
);
assert.match(converter, /edgePreservingSmooth/);
assert.match(converter, /comicRender/);
assert.match(converter, /full\.width = source\.width/);
assert.match(converter, /full\.height = source\.height/);
assert.match(converter, /full\.toBlob/);
assert.match(converter, /storeHistory\(options\.getDocumentId/);
assert.match(converter, /temporary_preview_files: 0/);
for (const preset of [
  '<option value="comic">白黒コミック</option>',
  '<option value="grayscale">単純グレースケール</option>',
  '<option value="monochrome">単純モノクロ</option>',
  '<option value="xdog100">XDoG 100</option>',
]) {
  assert.ok(converter.includes(preset), `Converter dialog must include ${preset}`);
}
assert.match(converter, /params\.mode === "grayscale"/);
assert.match(converter, /params\.mode === "monochrome"/);
assert.match(converter, /params\.mode === "xdog"/);
assert.doesNotMatch(html, /data-comic-converter-preset/);
assert.doesNotMatch(converter, /localStorage.*data:image/);
assert.doesNotMatch(converter, /showSaveFilePicker/);

for (const feature of [
  "getConversionSources",
  "addConvertedImage",
  "storageStatus",
  "cleanupUnusedImages",
]) {
  assert.ok(comicEditor.includes(feature), `Comic image tray API must include ${feature}`);
}

assert.match(converterCss, /resize: both/);
assert.match(converterCss, /\.comic-converter-dialog\.maximized/);
assert.match(converterCss, /grid-template-rows:\s*42px auto auto minmax\(0,\s*1fr\) 52px/);
assert.match(converter, /rgba\[i \+ 3\] = image\.data\[i \+ 3\]/);
assert.match(converter, /y = y \* alpha \+ \(1 - alpha\)/);
assert.match(converter, /forceOpen \? false : !picker\.hidden/);
assert.match(converterCss, /grid-template-columns: 1fr 1fr/);
assert.match(converterCss, /\.comic-converter-source-picker[\s\S]*grid-template-columns: minmax\(0, 1fr\) 250px/);
assert.match(converterCss, /\.comic-converter-source-picker\[hidden\]/);
assert.match(converterCss, /min-width: min\(720px, calc\(100vw - 16px\)\)/);
assert.match(converterCss, /@media \(max-width: 680px\)/);
assert.match(converterCss, /grid-template-rows: minmax\(180px, 1fr\) minmax\(150px, 42%\)/);
assert.match(converterCss, /@media \(max-height: 620px\)/);
assert.match(converter, /class="comic-converter-footer-actions"/);
assert.match(converterCss, /\.comic-converter-footer\s*\{[\s\S]*grid-template-columns: minmax\(0, 1fr\) auto/);
assert.match(converterCss, /\.comic-converter-footer-actions\s*\{[\s\S]*justify-content: flex-end/);

for (const feature of [
  "ページ画像・変換履歴",
  "data-desktop-image-storage-status",
  "未使用画像を整理",
  "変換履歴を削除",
  "refreshImageStorageStatus",
]) {
  assert.ok(desktopShell.includes(feature), `Desktop Settings must include ${feature}`);
}

assert.match(readme, /## コミック変換/);
assert.match(readme, /長辺768px/);
assert.match(readme, /文書ごとに最大5件、全体512MB、30日/);
assert.match(readme, /単純グレースケール（初期値）、白黒コミック、単純モノクロ、XDoG 100/);

console.log("comic converter integration tests passed");
