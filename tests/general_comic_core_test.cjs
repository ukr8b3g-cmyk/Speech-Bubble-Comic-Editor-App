const assert = require("node:assert/strict");
const core = require("../web/general-comic-core.js");

let nextId = 0;
const makeId = () => String(++nextId);

function layoutFor(templateId, width = 1200, height = 1600, gutter = 24) {
  nextId = 0;
  return core.computeLayout(core.createTemplate(templateId, makeId), { x: 0, y: 0, w: width, h: height }, gutter);
}

for (const [templateId, expected] of [
  ["standard_five", 5],
  ["equal_six", 6],
  ["main_focus", 4],
]) {
  const layout = layoutFor(templateId);
  assert.equal(layout.panels.length, expected, `${templateId} panel count`);
  assert.equal(layout.dividers.length, expected - 1, `${templateId} divider count`);
  assert.equal(new Set(layout.panels.map((item) => item.id)).size, expected);
  for (const panel of layout.panels) {
    assert.ok(panel.rect.w >= core.MIN_PANEL_SIZE - 1e-6);
    assert.ok(panel.rect.h >= core.MIN_PANEL_SIZE - 1e-6);
  }
}

const page = core.defaultPage(2480, 3508);
assert.equal(page.gutter, 60);
assert.equal(page.border_width, 4.5);
assert.equal(page.print_guides_visible, false);
assert.deepEqual(core.pageContentRect(page), { x: 96, y: 96, w: 2288, h: 3316 });

const patterned = core.panelNode(makeId, { background: "#123456", background_pattern: { type: "checker", color: "#123456", patternColor: "#ffffff", scale: 40 } });
assert.equal(patterned.background_pattern.type, "checker");
const patternedSplit = core.splitPanel(patterned, patterned.id, "x", makeId);
assert.equal(patternedSplit.tree.second.background_pattern.type, "checker");

nextId = 0;
let tree = core.panelNode(makeId);
const originalPanelId = tree.id;
let splitResult = core.splitPanel(tree, originalPanelId, "x", makeId);
assert.equal(splitResult.changed, true);
tree = splitResult.tree;
let layout = core.computeLayout(tree, { x: 0, y: 0, w: 1000, h: 1000 }, 20);
assert.equal(layout.panels.length, 2);
assert.equal(layout.dividers.length, 1);
assert.equal(layout.dividers[0].hitRect.w, 20);
assert.equal(layout.panels[1].rect.x - (layout.panels[0].rect.x + layout.panels[0].rect.w), 20);

const ratioResult = core.setSplitRatio(tree, splitResult.splitId, 0.3);
assert.equal(ratioResult.changed, true);
tree = ratioResult.tree;
layout = core.computeLayout(tree, { x: 0, y: 0, w: 1000, h: 1000 }, 20);
assert.ok(Math.abs(layout.panels[0].rect.w - 294) < 1e-6);
assert.ok(Math.abs(layout.panels[1].rect.w - 686) < 1e-6);

const diagonalResult = core.setSplitRatios(tree, splitResult.splitId, 0.35, 0.65);
assert.equal(diagonalResult.changed, true);
const diagonalLayout = core.computeLayout(diagonalResult.tree, { x: 0, y: 0, w: 1000, h: 1000 }, 40);
assert.deepEqual(diagonalLayout.dividers[0].line, { x1: 356, y1: 0, x2: 644, y2: 1000 });
assert.equal(diagonalLayout.panels.every((item) => item.polygon.length >= 3), true);
assert.equal(core.pointInPolygon({ x: 100, y: 500 }, diagonalLayout.panels[0].polygon), true);
assert.equal(core.pointInPolygon({ x: 900, y: 500 }, diagonalLayout.panels[1].polygon), true);
const diagonalSplit = core.splitPolygon(core.rectPolygon({ x: 0, y: 0, w: 1000, h: 1000 }), { x: 0, y: 0, w: 1000, h: 1000 }, "y", 0.4, 0.6, 40);
assert.ok(Math.abs(core.lineDistance(diagonalSplit.first.at(-1), diagonalSplit.line) - 20) < 1e-6, "first gutter edge stays half the configured width from the center line");
assert.ok(Math.abs(core.lineDistance(diagonalSplit.second[0], diagonalSplit.line) - 20) < 1e-6, "second gutter edge stays half the configured width from the center line");
assert.equal(core.dividerHandleAtPoint(diagonalLayout, { x: 356, y: 0 }, 10)?.endpoint, "start");
assert.equal(core.dividerStraightDistancePx({ ...diagonalLayout.dividers[0], startRatio: .5, endRatio: .504 }, 1, 40) < 5, true);
const verticalSnap = core.snapDividerEndpointToAngle({ ...diagonalLayout.dividers[0], axis: "x", startRatio: .5, endRatio: .51 }, "end", .51, 40, 15);
assert.equal(verticalSnap.angle, 90);
assert.ok(Math.abs(verticalSnap.ratio - .5) < 1e-9);

const nestedTree = core.splitNode("y", .5,
  core.splitNode("x", .5, core.panelNode(makeId), core.panelNode(makeId), makeId, { divider_start_ratio: .35, divider_end_ratio: .65 }),
  core.panelNode(makeId), makeId, { divider_start_ratio: .35, divider_end_ratio: .65 });
const nestedLayout = core.computeLayout(nestedTree, { x: 0, y: 0, w: 1200, h: 1600 }, 40);
assert.equal(nestedLayout.panels.length, 3);
assert.equal(nestedLayout.panels.every((item) => item.polygon.length >= 3 && item.polygon.every((point) => point.x >= -1e-6 && point.x <= 1200 + 1e-6 && point.y >= -1e-6 && point.y <= 1600 + 1e-6)), true, "nested diagonal panels remain clipped to their polygon ancestor");

const hiddenPanel = core.findNode(tree, originalPanelId);
hiddenPanel.visible = false;
layout = core.computeLayout(tree, { x: 0, y: 0, w: 1000, h: 1000 }, 20);
assert.equal(layout.panels.length, 1, "hidden panels must be removed from the canvas layout");
assert.equal(layout.panels[0].rect.w, 1000, "the remaining panel must fill the available layout");
assert.equal(core.collectPanels(tree).length, 2, "hidden panel data must remain available to Layers and restore");
assert.notEqual(core.panelAtPoint(layout, { x: 10, y: 10 }), null, "the remaining panel must become the canvas target");
hiddenPanel.visible = true;

const mergeResult = core.mergeDivider(tree, splitResult.splitId, "first");
assert.equal(mergeResult.changed, true);
assert.equal(mergeResult.keptPanelId, originalPanelId);
assert.equal(mergeResult.removedPanelIds.length, 1);
assert.equal(core.collectPanels(mergeResult.tree).length, 1);

const normalized = core.normalizeState({
  version: 1,
  enabled: true,
  created: true,
  template_id: "equal_six",
  page: { width: 2000, height: 3000, gutter: 30, border_width: 5, print_guides_visible: true },
  tree: core.createTemplate("equal_six", makeId),
  images: [
    { id: "general-comic-image:1", name: "a.png", mime: "image/png", width: 10, height: 20 },
    { id: "general-comic-image:1", name: "duplicate.png" },
  ],
}, { makeId });
assert.equal(normalized.enabled, true);
assert.equal(normalized.created, true);
assert.equal(normalized.page.gutter, 30);
assert.equal(normalized.images.length, 1);
assert.throws(() => core.normalizeState({ version: 2 }, { makeId }), /Unsupported general comic state version/);

const normalizedDiagonal = core.normalizeState({ version: 1, tree: diagonalResult.tree }, { makeId });
const restoredDivider = core.computeLayout(normalizedDiagonal.tree, { x: 0, y: 0, w: 1000, h: 1000 }, 40).dividers[0];
assert.equal(restoredDivider.startRatio, .35);
assert.equal(restoredDivider.endRatio, .65);

const duplicateTree = core.normalizeTree({
  kind: "split",
  id: "duplicate",
  axis: "x",
  ratio: 0.5,
  first: { kind: "panel", id: "duplicate" },
  second: { kind: "panel", id: "duplicate" },
}, makeId);
const duplicateIds = [duplicateTree.id, ...core.collectPanels(duplicateTree).map((item) => item.id)];
assert.equal(new Set(duplicateIds).size, duplicateIds.length);

const orderLayout = {
  panels: [
    { id: "left-top", rect: { x: 0, y: 0, w: 100, h: 100 } },
    { id: "right-top", rect: { x: 120, y: 0, w: 100, h: 100 } },
    { id: "bottom", rect: { x: 0, y: 140, w: 220, h: 100 } },
  ],
};
assert.deepEqual(core.readingOrder(orderLayout).map((item) => item.id), ["right-top", "left-top", "bottom"]);

const source = core.defaultState(2480, 3508, makeId, "standard_five");
const serialized = JSON.stringify(source);
core.computeLayout(source.tree, core.pageContentRect(source.page), source.page.gutter);
assert.equal(JSON.stringify(source), serialized, "layout computation must not mutate state");

console.log("general_comic_core_test: OK");
