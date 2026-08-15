const assert = require("node:assert/strict");

const schema = require("../web/project-schema.js");

function currentLayout(activeWorkspace = "single") {
  const canvases = {
    single: { width: 1024, height: 1024 },
    comic: { width: 720, height: 2200 },
    comic_layout: { width: 2480, height: 3508 },
  };
  const elements = {
    single: [{ id: "single-1", type: "image" }],
    comic: [{ id: "comic-1", type: "text" }],
    comic_layout: [{ id: "general-1", type: "text", general_comic_scope: "page" }],
  };
  return {
    format: "speech-bubble-editor-layout",
    version: 5,
    active_workspace: activeWorkspace,
    canvas: canvases[activeWorkspace],
    background_visible: true,
    elements: elements[activeWorkspace],
    workspaces: {
      single: {
        canvas: { width: 1024, height: 1024 },
        background_visible: true,
        canvas_background: { color: "#ffffff", transparent: false },
        elements: [{ id: "single-1", type: "image" }],
        view: { zoom: 1, panX: 0, panY: 0 },
      },
      comic: {
        canvas: { width: 720, height: 2200 },
        background_visible: true,
        elements: [{ id: "comic-1", type: "text" }],
        view: { zoom: 1, panX: 0, panY: 0 },
      },
      comic_layout: {
        canvas: { width: 2480, height: 3508 },
        background_visible: true,
        elements: [{ id: "general-1", type: "text", general_comic_scope: "page" }],
        view: { zoom: 1, panX: 0, panY: 0 },
      },
    },
    comic: { version: 1, enabled: true },
    general_comic: { version: 1, enabled: activeWorkspace === "comic_layout", created: true },
  };
}

const source = currentLayout();
const sourceJson = JSON.stringify(source);
const normalized = schema.normalize(source);
assert.equal(normalized.version, 5);
assert.equal(normalized.workspaces.single.elements[0].id, "single-1");
assert.equal(normalized.workspaces.comic.elements[0].id, "comic-1");
assert.equal(normalized.workspaces.comic_layout.elements[0].id, "general-1");
assert.equal(JSON.stringify(source), sourceJson, "normalize must not mutate input");

const built = schema.build({
  activeWorkspace: "comic",
  workspaces: {
    single: {
      width: 1024,
      height: 1024,
      backgroundVisible: true,
      canvasBackground: { color: "#ffffff", transparent: false },
      elements: [{ id: "single-1", type: "image" }],
      view: { zoom: 1, panX: 0, panY: 0 },
    },
    comic: {
      width: 720,
      height: 2200,
      backgroundVisible: true,
      elements: [{ id: "comic-1", type: "text" }],
      view: { zoom: 1, panX: 0, panY: 0 },
    },
    comic_layout: {
      width: 2480,
      height: 3508,
      backgroundVisible: true,
      elements: [{ id: "general-1", type: "text", general_comic_scope: "panel", general_comic_panel_id: "panel-1" }],
      view: { zoom: 1, panX: 0, panY: 0 },
    },
  },
  comic: { version: 1, enabled: true },
  generalComic: { version: 1, enabled: false, created: true },
});
const rebuilt = schema.normalize(built);
assert.equal(rebuilt.active_workspace, "comic");
assert.equal(rebuilt.workspaces.single.elements[0].id, "single-1");
assert.equal(rebuilt.workspaces.comic.elements[0].id, "comic-1");
assert.equal(rebuilt.workspaces.comic_layout.elements[0].id, "general-1");
assert.notEqual(rebuilt.workspaces.single.elements, rebuilt.workspaces.comic.elements);
assert.notEqual(rebuilt.workspaces.comic.elements, rebuilt.workspaces.comic_layout.elements);

const legacy = schema.normalize({
  canvas: { width: 640, height: 900 },
  background_visible: false,
  elements: [{ id: "legacy-layer", type: "text" }],
});
assert.equal(legacy.version, 5);
assert.equal(legacy.active_workspace, "single");
assert.equal(legacy.workspaces.single.canvas.width, 640);
assert.equal(legacy.workspaces.single.elements[0].id, "legacy-layer");
assert.deepEqual(legacy.workspaces.comic.elements, []);
assert.deepEqual(legacy.workspaces.comic_layout.elements, []);

const legacyV4 = currentLayout("comic");
legacyV4.version = 4;
delete legacyV4.workspaces.comic_layout;
delete legacyV4.general_comic;
const migratedV4 = schema.normalize(legacyV4);
assert.equal(migratedV4.version, 5);
assert.equal(migratedV4.active_workspace, "comic");
assert.equal(migratedV4.workspaces.single.elements[0].id, "single-1");
assert.equal(migratedV4.workspaces.comic.elements[0].id, "comic-1");
assert.equal(migratedV4.workspaces.comic_layout.canvas.width, 2480);
assert.deepEqual(migratedV4.workspaces.comic_layout.elements, []);

assert.throws(
  () => schema.normalize({ version: 999 }),
  (error) => error?.code === "UNSUPPORTED_LAYOUT_VERSION",
);
assert.throws(
  () => schema.normalize({ ...currentLayout(), comic: { version: 999 } }),
  (error) => error?.code === "UNSUPPORTED_COMIC_VERSION",
);
assert.throws(
  () => schema.normalize({ ...currentLayout(), general_comic: { version: 999 } }),
  (error) => error?.code === "UNSUPPORTED_GENERAL_COMIC_VERSION",
);
assert.throws(
  () => schema.normalize({ ...currentLayout(), workspaces: { ...currentLayout().workspaces, single: { ...currentLayout().workspaces.single, canvas: { width: 0, height: 100 } } } }),
  (error) => error?.code === "INVALID_WORKSPACE",
);

const preflight = schema.preflightPayload({
  layout: currentLayout("comic_layout"),
  images: [
    { id: "single-image:1", name: "single.png", mime: "image/png", data_url: "data:image/png;base64,AA==" },
    { id: "comic-image:1", name: "four.png", mime: "image/png", data_url: "data:image/png;base64,AA==" },
    { id: "general-comic-image:1", name: "general.png", mime: "image/png", data_url: "data:image/png;base64,AA==" },
  ],
});
assert.deepEqual(preflight.singleRecords.map((item) => item.id), ["single-image:1"]);
assert.deepEqual(preflight.comicRecords.map((item) => item.id), ["comic-image:1"]);
assert.deepEqual(preflight.generalRecords.map((item) => item.id), ["general-comic-image:1"]);
assert.throws(
  () => schema.normalize({ ...currentLayout(), workspaces: { ...currentLayout().workspaces, single: { ...currentLayout().workspaces.single, elements: [{ id: "duplicate" }, { id: "duplicate" }] } } }),
  (error) => error?.code === "DUPLICATE_ELEMENT_ID",
);
assert.throws(
  () => schema.preflightPayload({
    layout: currentLayout(),
    images: [
      { id: "single-image:1", name: "one.png", mime: "image/png", data_url: "data:image/png;base64,AA==" },
      { id: "single-image:1", name: "two.png", mime: "image/png", data_url: "data:image/png;base64,AA==" },
    ],
  }),
  (error) => error?.code === "DUPLICATE_IMAGE_ID",
);

console.log("project_schema_core_test: OK");
