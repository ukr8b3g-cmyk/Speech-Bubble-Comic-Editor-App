"use strict";

const assert = require("node:assert/strict");
const { selectContiguousRgba } = require("../web/background-removal-selection.js");

function rgba(colors) {
  return new Uint8ClampedArray(colors.flat());
}

// Exact selection only includes the connected matching color.
{
  const pixels = rgba([
    [255, 255, 255, 255],
    [0, 0, 0, 255],
    [255, 255, 255, 255],
  ]);
  assert.deepEqual([...selectContiguousRgba(pixels, 3, 1, 0, 0, 0).indices], [0]);
}

// Disconnected regions with the same color remain untouched.
{
  const pixels = rgba([
    [255, 255, 255, 255],
    [0, 0, 0, 255],
    [255, 255, 255, 255],
  ]);
  assert.deepEqual([...selectContiguousRgba(pixels, 3, 1, 2, 0, 0).indices], [2]);
}

// Tolerance is always measured from the initial seed, not the prior neighbor.
{
  const pixels = rgba([
    [0, 0, 0, 255],
    [10, 10, 10, 255],
    [20, 20, 20, 255],
  ]);
  assert.deepEqual([...selectContiguousRgba(pixels, 3, 1, 0, 0, 10).indices], [0, 1]);
}

// Four-way connectivity excludes diagonal-only pixels.
{
  const pixels = rgba([
    [100, 100, 100, 255], [0, 0, 0, 255],
    [0, 0, 0, 255], [100, 100, 100, 255],
  ]);
  assert.deepEqual([...selectContiguousRgba(pixels, 2, 2, 0, 0, 0).indices], [0]);
}

// Alpha is part of the comparison, so opaque and transparent pixels do not join.
{
  const pixels = rgba([
    [100, 100, 100, 255],
    [100, 100, 100, 0],
  ]);
  assert.deepEqual([...selectContiguousRgba(pixels, 2, 1, 0, 0, 16).indices], [0]);
}

// Out-of-bounds selection safely returns an empty result.
{
  const result = selectContiguousRgba(rgba([[0, 0, 0, 255]]), 1, 1, -1, 0, 16);
  assert.equal(result.count, 0);
}

assert.throws(
  () => selectContiguousRgba(new Uint8ClampedArray(3), 1, 1, 0, 0, 16),
  /RGBA pixel data is missing or too short/,
);

console.log("background_removal_selection_test: OK");
