const assert = require("node:assert/strict");
const fs = require("node:fs");

const html = fs.readFileSync("web/speech-bubble-editor.html", "utf8");
const modeController = fs.readFileSync("web/editor-mode-controller.js", "utf8");
const fourPanelEditor = fs.readFileSync("web/comic-editor.js", "utf8");
const generalCore = fs.readFileSync("web/general-comic-core.js", "utf8");
const generalEditor = fs.readFileSync("web/general-comic-editor.js", "utf8");
const generalCss = fs.readFileSync("web/general-comic-editor.css", "utf8");
const schema = fs.readFileSync("web/project-schema.js", "utf8");
const pythonSchema = fs.readFileSync("desktop_app/project_schema.py", "utf8");

assert.match(modeController, /MODES = Object\.freeze\(\["single", "comic", "comic_layout"\]\)/);
for (const label of ["一枚画像", "4コマ漫画", "コミック", "Single Image", "4-Panel Manga", "Comic"]) {
  assert.ok(modeController.includes(label), `mode label missing: ${label}`);
}
assert.match(fourPanelEditor, /requested === "comic"/);
assert.doesNotMatch(fourPanelEditor, /requested !== "single"/);
assert.match(html, /modeController\.register\("single"/);
assert.match(html, /modeController\.register\("comic"/);
assert.match(html, /modeController\.register\("comic_layout"/);
assert.match(html, /function initializeModeController\(\)\{[\s\S]*?\["desktop","desktop-file"\]\.includes\(hostMode\)/);
assert.match(html, /comicEditor\?\.setActive\(target==="comic"/);
assert.match(html, /generalComicEditor\?\.setActive\(target==="comic_layout"/);

assert.match(schema, /CURRENT_LAYOUT_VERSION = 5/);
assert.match(schema, /WORKSPACE_NAMES = Object\.freeze\(\["single", "comic", "comic_layout"\]\)/);
assert.match(schema, /CURRENT_GENERAL_COMIC_VERSION = 1/);
assert.match(pythonSchema, /LAYOUT_SCHEMA_VERSION = 5/);
assert.match(pythonSchema, /GENERAL_COMIC_SCHEMA_VERSION = 1/);
assert.match(html, /generalComic:generalComicEditor\?\.serialize\(\)/);
assert.match(html, /generalComicEditor\?\.restore\(data\.generalComic/);

for (const template of ["standard_five", "equal_six", "main_focus"]) {
  assert.ok(generalCore.includes(template), `general comic template missing: ${template}`);
  assert.ok(generalEditor.includes(template), `template dropdown option missing: ${template}`);
}
assert.doesNotMatch(generalEditor, /data-general-create-template/);
assert.doesNotMatch(generalEditor, /general-comic-create-overlay|data-general-create-page/);
assert.match(generalEditor, /active && !comic\.created[\s\S]*?createPage\(\{ width: 2480, height: 3508, templateId: "standard_five" \}, \{ recordUndo: false \}\)/);
assert.match(generalEditor, /"テンプレート","Template"/);
assert.match(generalEditor, /data-general-page-title-lock/);
assert.match(generalEditor, /comic-image-tray general-comic-image-tray collapsed/);
assert.match(generalEditor, /className = `comic-image-card/);
assert.match(generalEditor, /preview\.className = "comic-image-preview"/);
assert.match(generalEditor, /general-comic-tray-visible/);
assert.match(generalCss, /\.general-comic-title-lock\{[^}]*flex-direction:row/);
assert.match(fs.readFileSync("web/comic-editor.css", "utf8"), /\.comic-heading-title-toggle\s*\{[^}]*flex-direction:\s*row/s);
assert.match(generalEditor, /data-general-panel-pattern-select="type"/);
assert.match(generalEditor, /function rebuildPanelBackgroundProperties/);
assert.match(generalEditor, /backgroundPatterns\(\)\.draw/);
assert.match(generalEditor, /function getConversionSources/);
assert.match(generalEditor, /function addConvertedImage/);
assert.match(html, /generalComicEditor\?\.isActive\(\)\?generalComicEditor\.getConversionSources/);
assert.match(html, /generalComicEditor\?\.isActive\(\)\?generalComicEditor\.addConvertedImage/);
for (const kind of ["page", "panel", "image", "divider", "normal"]) {
  assert.ok(generalEditor.includes(`kind${kind === "normal" ? " !==" : " ==="} \"${kind}\"`) || generalEditor.includes(`\"${kind}\"`), `selection kind missing: ${kind}`);
}
assert.match(generalEditor, /speech-bubble-editor-general-comic-images/);
assert.match(generalEditor, /IMAGE_PREFIX = "general-comic-image:"/);
assert.match(generalEditor, /function splitSelected\(axis\)/);
assert.match(generalEditor, /function mergeSelectedDivider\(keep = "first"\)/);
assert.match(generalEditor, /function handlePointerDown\(point/);
assert.match(generalEditor, /function handlePointerMove\(point, event = \{\}\)/);
assert.match(generalEditor, /function handlePointerEnd\(event = \{\}\)/);
assert.match(generalEditor, /function selectPanelImage\(id, event = \{\}\)/);
assert.match(generalEditor, /data-general-properties="image"/);
assert.match(generalEditor, /data-general-image="image_scale"/);
assert.match(generalEditor, /data-general-selected-thumbnail/);
assert.match(generalEditor, /selectedImagePanels\(\)\.filter\(\(panel\) => panelEditable\(panel\) && !panel\.image_locked\)/);
assert.match(generalEditor, /const panelEditable = \(panel\) => panel\?\.kind === "panel" && panel\.locked !== true/);
assert.match(generalEditor, /const dividerEditable = \(divider\) => Boolean\(divider\?\.node\) && !comic\.page\.structure_locked && core\.collectPanels\(divider\.node\)\.every\(\(panel\) => panel\.locked !== true\)/);
assert.match(generalEditor, /Keep the Blob and runtime image until the document is closed so Undo can restore this image/);
assert.doesNotMatch(generalEditor, /removeTrayImage\(imageId\)[\s\S]*?await deleteImageBlob\(documentId\(\), imageId\)/);
assert.match(generalEditor, /key === "template_id"\) input\.disabled = comic\.page\.structure_locked/);
assert.match(generalEditor, /input\.disabled = !editable/);
assert.match(generalEditor, /button\.disabled = !editable \|\| !mergeAllowed/);
assert.match(generalEditor, /if \(dividerInput\) \{ const divider = selectedDivider\(\); if \(!dividerEditable\(divider\)\) return;/);
assert.match(generalEditor, /function applyTemplate\(templateId\) \{ if \(comic\.page\.structure_locked\) \{ syncUi\(\); return false; \}/);
assert.match(generalEditor, /selection\.kind !== "image"/);
assert.match(generalEditor, /data-general-action="toggle-panel-visibility"/);
assert.match(generalEditor, /"コマを非表示", "Hide Panel"/);
assert.doesNotMatch(generalEditor, /data-general-action="process-background-removal"|data-general-action="process-comic-conversion"|data-general-image-fit-label|data-general-panel="fit"|data-general-action="select-page"/);
assert.match(generalEditor, /phase === "all" \|\| phase === "base"/);
assert.match(generalEditor, /phase === "all" \|\| phase === "images"/);
assert.match(generalEditor, /phase === "all" \|\| phase === "borders"/);
assert.match(generalEditor, /const overlay = optionsValue\.overlay === true/);
assert.match(html, /generalComicEditor\.drawUnderlay\(ctx,\{overlay:comicOverlayExport,phase:"base"\}\)/);
assert.match(generalEditor, /target\.strokeRect\(inset, inset, Math\.max\(0, comic\.page\.width - comic\.page\.border_width\)/);
for (const guide of ["margin / 2", "margin", "margin * 2"]) assert.ok(generalEditor.includes(`guide(${guide},`));
assert.match(generalEditor, /general_comic_scope = "panel"/);
assert.match(generalEditor, /general_comic_panel_id = panelId/);
assert.match(generalEditor, /selection\.kind === "page"\) return pageTarget/);
assert.match(html, /function traceClipShape\(target,shape\)/);
assert.match(html, /function pointInClipShape\(point,shape\)/);
assert.match(html, /generalComicEditor\?\.isActive\(\)\?elementClipShape\(e\):null/);
assert.match(generalEditor, /const panelShape = \(id\).*kind: "polygon"/);
assert.match(html, /generalRecords=records\.filter\(record=>record\.id\.startsWith/);
assert.match(html, /generalComicEditor\?\.exportProjectImages/);
assert.match(html, /generalComicEditor\?\.importProjectImages/);
assert.match(html, /function insertFrame[\s\S]*?generalComicEditor\?\.isActive\(\)[\s\S]*?applyComicPanelTarget/);
assert.match(html, /id="comicLayerScopeLabel"/);
assert.match(html, /pageLayerRows=\[\.\.\.host\.querySelectorAll\('\[data-layer-id\]:not\(\[data-general-comic-panel-target\]\)'\)\]/);

assert.match(generalCore, /divider_start_ratio/);
assert.match(generalCore, /divider_end_ratio/);
assert.match(generalCore, /function splitPolygon\(/);
assert.match(generalCore, /function dividerHandleAtPoint\(/);
assert.match(generalEditor, /drag\.kind === "divider-endpoint"/);
assert.match(generalCore, /function snapDividerEndpointToAngle\(/);
assert.match(generalCore, /function dividerStraightDistancePx\(/);
assert.match(generalEditor, /snapDividerEndpointToAngle\(divider, drag\.endpoint, next, comic\.page\.gutter, 15\)/);
assert.match(generalEditor, /dividerStraightDistancePx\(divider, canvasState\(\)\.zoom \|\| 1, comic\.page\.gutter\) <= 5/);
assert.match(generalEditor, /!event\.altKey/);
assert.doesNotMatch(generalEditor, /data-general-page="print_guides_visible"/);
assert.match(generalCore, /print_guides_visible/);
assert.match(generalEditor, /const PRINT_GUIDES_ENABLED = false/);
assert.match(generalEditor, /PRINT_GUIDES_ENABLED && comic\.page\.print_guides_visible/);
assert.match(html, /generalComicEditor\.handlePointerEnd\(event\)/);

console.log("general_comic_editor_integration_test: OK");
