const assert = require("node:assert/strict");
const core = require("../web/comic-panels.js");

let nextId = 0;
const makeId = () => String(++nextId);
const page = { x: 0, y: 0, w: 1200, h: 1600 };

function verifyTemplate(id, expectedPanels) {
  nextId = 0;
  const tree = core.createTemplate(id, makeId);
  const layout = core.computeLayout(tree, page, 16);
  assert.equal(layout.panels.length, expectedPanels);
  assert.equal(layout.dividers.length, expectedPanels - 1);
  for (const panel of layout.panels) {
    assert.ok(panel.rect.w >= core.MIN_PANEL_SIZE);
    assert.ok(panel.rect.h >= core.MIN_PANEL_SIZE);
    assert.ok(panel.rect.x >= 0 && panel.rect.y >= 0);
    assert.ok(panel.rect.x + panel.rect.w <= page.w + 1e-6);
    assert.ok(panel.rect.y + panel.rect.h <= page.h + 1e-6);
  }
}

verifyTemplate("vertical_four", 4);
verifyTemplate("two_column", 8);
verifyTemplate("two_column_sample", 8);
verifyTemplate("blank", 4);
assert.deepEqual([...core.PUBLIC_TEMPLATE_IDS], ["vertical_four"]);
assert.equal(core.CURRENT_STATE_VERSION, 1);
assert.equal(core.normalizeState({ enabled: true }, { makeId }).version, 1);
assert.equal(core.normalizeState({ version: 1, enabled: true }, { makeId }).version, 1);
assert.throws(
  () => core.normalizeState({ version: 2, enabled: true }, { makeId }),
  /Unsupported comic state version/i,
);

nextId = 0;
const verticalFour = core.createTemplate("vertical_four", makeId);
const panelIdsBeforeReset = core.computeLayout(verticalFour, page, 16).panels.map((panel) => panel.id);
verticalFour.ratio = 0.4;
verticalFour.second.ratio = 0.6;
verticalFour.second.second.ratio = 0.7;
assert.equal(core.resetVerticalFourRatios(verticalFour), true);
assert.deepEqual([verticalFour.ratio, verticalFour.second.ratio, verticalFour.second.second.ratio], [0.25, 1 / 3, 0.5]);
assert.deepEqual(core.computeLayout(verticalFour, page, 16).panels.map((panel) => panel.id), panelIdsBeforeReset);
assert.equal(core.resetVerticalFourRatios(verticalFour), false);

nextId = 0;
const collapsible = core.createTemplate("vertical_four", makeId);
const allCollapsiblePanels = core.collectPanels(collapsible);
const savedRatios = [collapsible.ratio, collapsible.second.ratio, collapsible.second.second.ratio];
assert.equal(core.countExpandedPanels(collapsible), 4);
allCollapsiblePanels[1].collapsed = true;
let collapsedLayout = core.computeLayout(collapsible, page, 16);
assert.equal(collapsedLayout.panels.length, 3);
assert.equal(collapsedLayout.dividers.length, 2);
assert.equal(collapsedLayout.panels.some((panel) => panel.id === allCollapsiblePanels[1].id), false);
assert.deepEqual([collapsible.ratio, collapsible.second.ratio, collapsible.second.second.ratio], savedRatios);
allCollapsiblePanels[2].collapsed = true;
collapsedLayout = core.computeLayout(collapsible, page, 16);
assert.equal(collapsedLayout.panels.length, 2);
assert.equal(collapsedLayout.dividers.length, 1);
allCollapsiblePanels[1].collapsed = false;
allCollapsiblePanels[2].collapsed = false;
const restoredLayout = core.computeLayout(collapsible, page, 16);
assert.deepEqual(restoredLayout.panels.map((panel) => panel.id), allCollapsiblePanels.map((panel) => panel.id));
assert.equal(restoredLayout.dividers.length, 3);

const collapsedFirst = core.createTemplate("vertical_four", makeId);
core.collectPanels(collapsedFirst)[0].collapsed = true;
const collapsedFirstLayout = core.computeLayout(collapsedFirst, page, 16);
assert.equal(collapsedFirstLayout.panels[0].rect.y, page.y, "collapsing the first panel must not add space above the reflowed panels");

nextId = 0;
let tree = core.panelNode(makeId);
const originalId = tree.id;
let result = core.splitPanel(tree, originalId, "x", makeId);
assert.equal(result.changed, true);
tree = result.tree;
assert.equal(core.computeLayout(tree, page, 16).panels.length, 2);
result = core.mergeSibling(tree, result.panelId, result.panelId, makeId);
assert.equal(result.changed, true);
tree = result.tree;
assert.equal(core.computeLayout(tree, page, 16).panels.length, 1);

nextId = 0;
tree = core.panelNode(makeId);
result = core.splitPanel(tree, tree.id, "y", makeId);
tree = result.tree;
const first = core.findNode(tree, result.panelId);
const second = core.findNode(tree, result.siblingId);
first.image_id = "first-image";
second.image_id = "second-image";
first.tone = core.defaultTone();
result = core.mergeSibling(tree, first.id, first.id, makeId);
assert.equal(result.changed, true);
assert.equal(result.tree.image_id, "first-image");
assert.equal(result.tree.tone.type, "halftone_dots");

const tone = core.normalizeTone({
  type: "halftone_dots",
  dot_size: 80,
  spacing: 10,
  opacity: 2,
});
assert.equal(tone.dot_size, 9.5);
assert.equal(tone.opacity, 1);

const cover = core.imageFit({ x: 0, y: 0, w: 100, h: 100 }, 200, 100, "cover", 1, 0, 0);
assert.equal(cover.w, 200);
assert.equal(cover.h, 100);
assert.equal(cover.x, -50);
const contain = core.imageFit({ x: 0, y: 0, w: 100, h: 100 }, 200, 100, "contain", 1, 0, 0);
assert.equal(contain.w, 100);
assert.equal(contain.h, 50);
assert.equal(contain.y, 25);

const malformed = core.normalizeState(
  {
    enabled: true,
    page: { gutter: 999, border_width: -3 },
    tree: { kind: "split", axis: "bad", ratio: Number.NaN, first: {}, second: {} },
  },
  { width: 800, height: 600, makeId },
);
assert.equal(malformed.enabled, true);
assert.equal(malformed.page.gutter, 999);
assert.equal(malformed.page.border_width, 0);
assert.equal(malformed.tree.axis, "x");
assert.equal(malformed.page.margin, 80);
assert.equal(malformed.page.visible, true);
  assert.equal(malformed.page.structure_locked, false);
  assert.equal(malformed.page.frame_style, "white");
  assert.equal(malformed.headings.length, 1);
assert.equal(malformed.headings[0].background, "#ffffff");
assert.equal(malformed.headings[0].border_color, "#111111");
assert.equal(malformed.headings[0].border_width, 5);
assert.equal(malformed.headings[0].follow_panel_width, true);
assert.equal("text" in malformed.headings[0], false);
assert.equal(core.panelNode(makeId).image_locked, false);
assert.equal(core.panelNode(makeId, { collapsed: true }).collapsed, true);
const patternedPanel = core.panelNode(makeId, {
  background: "#abcdef",
  background_pattern: { type: "cellular", preset: "cells", color: "#abcdef", patternColor: "#112233", scale: 90, seed: 510 },
});
assert.deepEqual(patternedPanel.background_pattern, {
  type: "cellular", preset: "cells", color: "#abcdef", patternColor: "#112233", scale: 90, seed: 510,
});
assert.equal(core.panelNode(makeId, { background_pattern: "invalid" }).background_pattern, null);
const standard = core.defaultState(undefined, undefined, makeId);
assert.equal(standard.page.width, 720);
assert.equal(standard.page.height, 2200);
assert.equal(standard.page.border_width, 5);
assert.equal(standard.page.gutter, 40);
assert.equal(standard.page.margin_top, 80);
assert.equal(standard.page.margin_right, 80);
assert.equal(standard.page.margin_bottom, 80);
assert.equal(standard.page.margin_left, 80);
assert.equal(standard.page.heading_gap, 30);
assert.equal(standard.page.canvas_ratio_locked, false);
assert.equal(standard.headings[0].x, 79);
assert.equal(standard.headings[0].y, 58);
assert.equal(standard.headings[0].width, 563);
assert.equal(standard.headings[0].height, 91);
assert.equal(standard.headings[0].border_width, 5);
assert.equal(standard.headings[0].follow_panel_width, true);
assert.equal(standard.page.structure_locked, false);

const legacy = core.normalizeState(
  {
    enabled: true,
    template_id: "two_column_sample",
    page: { visible: false, structure_locked: false, frame_style: "black", margin: 30 },
    tree: {
      kind: "panel",
      id: "legacy-panel",
      visible: false,
      image_visible: false,
    },
  },
  { width: 1200, height: 1600, makeId },
);
assert.equal(legacy.template_id, "vertical_four");
assert.equal(legacy.page.visible, false);
assert.equal(legacy.page.structure_locked, false);
assert.equal(legacy.page.frame_style, "black");
assert.equal(legacy.page.margin, 30);
assert.equal(core.computeLayout(legacy.tree, page, legacy.page.gutter).panels.length, 4);
assert.equal(legacy.headings.length, 1);

const collapsedProject = core.normalizeState(
  {
    enabled: true,
    tree: { kind: "panel", id: "collapsed-panel", collapsed: true },
  },
  { width: 800, height: 600, makeId },
);
assert.equal(collapsedProject.tree.collapsed, true);

console.log("comic_panels_core_test: OK");
