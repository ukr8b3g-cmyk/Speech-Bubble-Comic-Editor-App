const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const html = fs.readFileSync(path.join(root, "web", "speech-bubble-editor.html"), "utf8");
for (const match of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi)) {
  if (match[1].trim()) assert.doesNotThrow(() => new Function(match[1]), "inline editor script must parse");
}
const expected = [
  ["kawaii-shortcake", "kawaii_shortcake.png"],
  ["kawaii-cupcake", "kawaii_cupcake.png"],
  ["kawaii-macaron", "kawaii_macaron.png"],
  ["kawaii-donut", "kawaii_donut.png"],
  ["kawaii-candy", "kawaii_candy.png"],
  ["kawaii-strawberry", "kawaii_strawberry.png"],
  ["kawaii-cherries", "kawaii_cherries.png"],
  ["kawaii-gift", "kawaii_gift.png"],
  ["kawaii-teddy-bear", "kawaii_teddy_bear.png"],
  ["kawaii-rabbit", "kawaii_rabbit.png"],
  ["kawaii-cat", "kawaii_cat.png"],
  ["kawaii-chick", "kawaii_chick.png"],
  ["kawaii-paw", "kawaii_paw.png"],
  ["kawaii-fluffy-cloud", "kawaii_fluffy_cloud.png"],
  ["kawaii-soap-bubble", "kawaii_soap_bubble.png"],
  ["kawaii-small-flowers", "kawaii_small_flowers.png"],
  ["kawaii-butterfly", "kawaii_butterfly.png"],
  ["kawaii-feather", "kawaii_feather.png"],
  ["kawaii-manga-meat", "kawaii_manga_meat.png"],
  ["kawaii-temari", "kawaii_temari.png"],
  ["kawaii-maneki-neko", "kawaii_maneki_neko.png"],
  ["kawaii-crown", "kawaii_crown.png"],
  ["kawaii-magic-wand", "kawaii_magic_wand.png"],
  ["kawaii-perfume-bottle", "kawaii_perfume_bottle.png"],
  ["kawaii-teacup", "kawaii_teacup.png"],
  ["kawaii-origami-crane", "kawaii_origami_crane.png"],
  ["kawaii-wind-chime", "kawaii_wind_chime.png"],
];

assert.match(html, /\["symbols","effects","kawaii","corners"\]/, "kawaii must be treated as a comic stamp category");
assert.match(html, /<option value="kawaii">\$\{uiText\("かわいい装飾","Kawaii Decorations"\)\}<\/option>/, "the bilingual kawaii category option is missing");

for (const [id, filename] of expected) {
  const assetPath = path.join(root, "web", "assets", "stamps", "kawaii", filename);
  assert.ok(fs.existsSync(assetPath), `missing asset: ${filename}`);
  const png = fs.readFileSync(assetPath);
  assert.deepEqual([...png.subarray(0, 8)], [137, 80, 78, 71, 13, 10, 26, 10], `${filename} is not PNG`);
  const width = png.readUInt32BE(16);
  const height = png.readUInt32BE(20);
  const bitDepth = png[24];
  const colorType = png[25];
  assert.ok(width > 0 && height > 0 && width <= 400 && height <= 400, `${filename} has invalid dimensions ${width}x${height}`);
  assert.equal(bitDepth, 8, `${filename} must use 8-bit channels`);
  assert.equal(colorType, 6, `${filename} must be RGBA PNG`);
  const escapedFilename = filename.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const definition = new RegExp(`id:"${id}"[^\\n]+category:"kawaii"[^\\n]+src:"\\./assets/stamps/kawaii/${escapedFilename}"[^\\n]+mask:false[^\\n]+w:${width},h:${height}`);
  assert.match(html, definition, `invalid built-in definition for ${id}`);
}

assert.equal((html.match(/id:"kawaii-[^"]+"/g) || []).length, expected.length, "unexpected kawaii built-in count");
console.log(`kawaii stamp assets OK: ${expected.length}`);
