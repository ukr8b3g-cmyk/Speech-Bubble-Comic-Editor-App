const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const html = fs.readFileSync(path.join(root, "web", "speech-bubble-editor.html"), "utf8");
for (const match of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi)) {
  if (match[1].trim()) assert.doesNotThrow(() => new Function(match[1]), "inline editor script must parse");
}

const expected = [
  ["corner-kawaii-ribbon-lace", "corner_kawaii_ribbon_lace.png"],
  ["corner-kawaii-heart-lace", "corner_kawaii_heart_lace.png"],
  ["corner-kawaii-flower-vine", "corner_kawaii_flower_vine.png"],
  ["corner-kawaii-star-vine", "corner_kawaii_star_vine.png"],
  ["corner-kawaii-clover-vine", "corner_kawaii_clover_vine.png"],
  ["corner-kawaii-frill", "corner_kawaii_frill.png"],
  ["corner-shoujo-rose-vine", "corner_shoujo_rose_vine.png"],
  ["corner-shoujo-lace-pearl", "corner_shoujo_lace_pearl.png"],
  ["corner-shoujo-feather", "corner_shoujo_feather.png"],
  ["corner-shoujo-lily", "corner_shoujo_lily.png"],
  ["corner-shoujo-gem-chain", "corner_shoujo_gem_chain.png"],
  ["corner-shoujo-monochrome-rose", "corner_shoujo_monochrome_rose.png"],
  ["corner-standard-geometric", "corner_standard_geometric.png"],
  ["corner-standard-laurel", "corner_standard_laurel.png"],
  ["corner-standard-art-deco", "corner_standard_art_deco.png"],
  ["corner-standard-japanese-wave", "corner_standard_japanese_wave.png"],
  ["corner-standard-classic-leaf", "corner_standard_classic_leaf.png"],
  ["corner-standard-monochrome", "corner_standard_monochrome.png"],
];

assert.match(html, /\["symbols","effects","kawaii","corners"\]/, "corners must be treated as comic stamps");
assert.match(html, /<option value="corners">\$\{uiText\("コーナー装飾","Corner Decorations"\)\}<\/option>/, "the bilingual corner category option is missing");

for (const [id, filename] of expected) {
  const assetPath = path.join(root, "web", "assets", "stamps", "corners", filename);
  assert.ok(fs.existsSync(assetPath), `missing asset: ${filename}`);
  const png = fs.readFileSync(assetPath);
  assert.deepEqual([...png.subarray(0, 8)], [137, 80, 78, 71, 13, 10, 26, 10], `${filename} is not PNG`);
  const width = png.readUInt32BE(16);
  const height = png.readUInt32BE(20);
  assert.ok(width > 0 && height > 0 && width <= 400 && height <= 400, `${filename} has invalid dimensions ${width}x${height}`);
  assert.equal(png[24], 8, `${filename} must use 8-bit channels`);
  assert.equal(png[25], 6, `${filename} must be RGBA PNG`);
  const escapedFilename = filename.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const definition = new RegExp(`id:"${id}"[^\\n]+category:"corners"[^\\n]+src:"\\./assets/stamps/corners/${escapedFilename}"[^\\n]+mask:false[^\\n]+w:${width},h:${height}`);
  assert.match(html, definition, `invalid built-in definition for ${id}`);
}

assert.equal((html.match(/id:"corner-[^"]+"/g) || []).length, expected.length, "unexpected corner built-in count");
console.log(`corner stamp assets OK: ${expected.length}`);
