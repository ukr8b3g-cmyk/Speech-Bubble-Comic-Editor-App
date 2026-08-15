const assert = require("node:assert/strict");
const edge = require("../web/background-removal-edge.js");

function rgba(...pixels) {
  return new Uint8ClampedArray(pixels.flat());
}

function pixelAt(buffer, index) {
  const offset = index * 4;
  return [buffer[offset], buffer[offset + 1], buffer[offset + 2], buffer[offset + 3]];
}

assert.deepEqual(edge.defaultSettings(), {
  width: 1,
  defringe: false,
  decontaminateAmount: 0,
  matte: "none",
});

assert.deepEqual(edge.normalizeSettings({
  width: 99,
  defringe: 1,
  decontaminateAmount: 2,
  matte: "invalid",
}), {
  width: 10,
  defringe: false,
  decontaminateAmount: 1,
  matte: "none",
});

// With correction disabled, RGB stays unchanged and alpha comes from the final mask.
{
  const source = rgba([10, 20, 30, 255], [40, 50, 60, 255]);
  const alpha = new Uint8ClampedArray([255, 0]);
  const result = edge.applyEdgeCorrection(source, alpha, 2, 1, edge.defaultSettings());
  assert.deepEqual([...result], [10, 20, 30, 255, 40, 50, 60, 0]);
  assert.deepEqual([...source], [10, 20, 30, 255, 40, 50, 60, 255]);
}

// Defringe width 1 replaces the first foreground ring with an inward color.
{
  const pixels = [];
  const alpha = new Uint8ClampedArray(25);
  for (let y = 0; y < 5; y += 1) {
    for (let x = 0; x < 5; x += 1) {
      const index = y * 5 + x;
      const transparent = x === 0 || x === 4 || y === 0 || y === 4;
      const center = x === 2 && y === 2;
      alpha[index] = transparent ? 0 : 255;
      pixels.push(transparent ? [0, 0, 0, 255] : center ? [0, 0, 255, 255] : [255, 0, 0, 255]);
    }
  }
  const result = edge.applyEdgeCorrection(rgba(...pixels), alpha, 5, 5, { width: 1, defringe: true });
  assert.deepEqual(pixelAt(result, 6).slice(0, 3), [0, 0, 255]);
  assert.deepEqual(pixelAt(result, 12).slice(0, 3), [0, 0, 255]);
  assert.equal(pixelAt(result, 0)[3], 0);
}

// A thin component with no reliable interior donor remains unchanged.
{
  const source = rgba(
    [0, 0, 0, 255], [0, 0, 0, 255], [0, 0, 0, 255],
    [0, 0, 0, 255], [200, 0, 0, 255], [0, 0, 200, 255],
    [0, 0, 0, 255], [0, 0, 0, 255], [0, 0, 0, 255],
  );
  const alpha = new Uint8ClampedArray([0, 0, 0, 0, 255, 255, 0, 0, 0]);
  const result = edge.applyEdgeCorrection(source, alpha, 3, 3, { width: 1, decontaminateAmount: 0.5 });
  assert.deepEqual(pixelAt(result, 4).slice(0, 3), [200, 0, 0]);
}

// 50% decontamination blends an edge color toward its inward donor.
{
  const pixels = [];
  const alpha = new Uint8ClampedArray(35);
  for (let y = 0; y < 5; y += 1) {
    for (let x = 0; x < 7; x += 1) {
      const index = y * 7 + x;
      const visible = x >= 1 && x <= 5 && y >= 1 && y <= 3;
      const edgePixel = visible && (x === 1 || x === 5 || y === 1 || y === 3);
      alpha[index] = visible ? 255 : 0;
      pixels.push(visible ? (edgePixel ? [200, 0, 0, 255] : [0, 0, 200, 255]) : [0, 0, 0, 255]);
    }
  }
  const result = edge.applyEdgeCorrection(rgba(...pixels), alpha, 7, 5, { width: 1, decontaminateAmount: 0.5 });
  assert.deepEqual(pixelAt(result, 8).slice(0, 3), [100, 0, 100]);
  assert.deepEqual(pixelAt(result, 17).slice(0, 3), [0, 0, 200]);
}

// Separate foreground components never borrow colors through transparent space.
{
  const width = 9;
  const height = 5;
  const pixels = [];
  const alpha = new Uint8ClampedArray(width * height);
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const left = x >= 1 && x <= 3 && y >= 1 && y <= 3;
      const right = x >= 5 && x <= 7 && y >= 1 && y <= 3;
      alpha[y * width + x] = left || right ? 255 : 0;
      pixels.push(left ? [20, 200, 20, 255] : right ? [200, 20, 200, 255] : [0, 0, 0, 255]);
    }
  }
  const result = edge.applyEdgeCorrection(rgba(...pixels), alpha, width, height, { width: 1, defringe: true });
  assert.deepEqual(pixelAt(result, width + 1).slice(0, 3), [20, 200, 20]);
  assert.deepEqual(pixelAt(result, width + 7).slice(0, 3), [200, 20, 200]);
}

for (const matte of ["white", "black"]) {
  const alphaByte = 128;
  const normalizedAlpha = alphaByte / 255;
  const foreground = [100, 50, 24];
  const matteValue = matte === "white" ? 255 : 0;
  const observed = foreground.map((value) => Math.round(value * normalizedAlpha + matteValue * (1 - normalizedAlpha)));
  const result = edge.applyEdgeCorrection(rgba([...observed, 255]), new Uint8ClampedArray([alphaByte]), 1, 1, { matte });
  const recovered = pixelAt(result, 0);
  assert.ok(Math.abs(recovered[0] - foreground[0]) <= 1);
  assert.ok(Math.abs(recovered[1] - foreground[1]) <= 1);
  assert.ok(Math.abs(recovered[2] - foreground[2]) <= 1);
  assert.equal(recovered[3], alphaByte);
}

assert.throws(
  () => edge.applyEdgeCorrection(new Uint8ClampedArray(3), new Uint8ClampedArray(1), 1, 1),
  /RGBA buffer length/,
);

console.log("background_removal_edge_test: OK");
