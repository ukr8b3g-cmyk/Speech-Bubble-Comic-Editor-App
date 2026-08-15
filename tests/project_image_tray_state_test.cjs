const assert = require("node:assert/strict");

require("../web/project-image-tray.js");
const tray = globalThis.SpeechBubbleProjectImageTray;
assert.ok(tray, "Page Images module must register itself");
assert.deepEqual(tray.WORKSPACES, ["single", "comic", "comic_layout"]);

const fresh = tray.normalizeState(null, ["a", "b"]);
assert.equal(fresh.mode, "shared");
assert.deepEqual(fresh.shared, ["a", "b"]);
assert.deepEqual(fresh.workspaces, { single: [], comic: [], comic_layout: [] });

const separate = tray.normalizeState({
  mode: "separate",
  shared: ["missing"],
  workspaces: {
    single: ["a", "a", "missing"],
    comic: ["b"],
    comic_layout: ["a", "b"],
  },
}, ["a", "b"]);
assert.equal(separate.mode, "separate");
assert.deepEqual(separate.shared, []);
assert.deepEqual(separate.workspaces.single, ["a"]);
assert.deepEqual(separate.workspaces.comic, ["b"]);
assert.deepEqual(separate.workspaces.comic_layout, ["a", "b"]);

const shared = tray.normalizeState({ mode: "other", shared: ["b", "a", "b"] }, ["a", "b"]);
assert.equal(shared.mode, "shared");
assert.deepEqual(shared.shared, ["b", "a"]);

console.log("project_image_tray_state_test: OK");
