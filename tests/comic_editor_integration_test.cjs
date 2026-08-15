const assert = require("node:assert/strict");
const fs = require("node:fs");

const html = fs.readFileSync("web/speech-bubble-editor.html", "utf8");
const editor = fs.readFileSync("web/comic-editor.js", "utf8");
const converter = fs.readFileSync("web/comic-converter.js", "utf8");
const css = fs.readFileSync("web/comic-editor.css", "utf8");
const desktopShell = fs.readFileSync("web/desktop/desktop-shell.js", "utf8");
const desktopCss = fs.readFileSync("web/desktop/desktop.css", "utf8");
const canvasBackgroundPatterns = fs.readFileSync("web/canvas-background-patterns.js", "utf8");
const projectSchema = fs.readFileSync("web/project-schema.js", "utf8");
const modeController = fs.readFileSync("web/editor-mode-controller.js", "utf8");
const generalComicCore = fs.readFileSync("web/general-comic-core.js", "utf8");
const generalComicEditor = fs.readFileSync("web/general-comic-editor.js", "utf8");
const generalComicCss = fs.readFileSync("web/general-comic-editor.css", "utf8");
const desktopMain = fs.readFileSync("desktop_app/main.py", "utf8");
const renderer = fs.readFileSync("speech_bubble_editor/renderer.py", "utf8");
const readme = fs.readFileSync("README.md", "utf8");
const shapeManifest = JSON.parse(fs.readFileSync("web/assets/shapes/manifest.json", "utf8"));
const correctedSfxManifestPath = "web/assets/sfx/sfx-png-corrected-list-v2/manifest.json";
const correctedSfxManifest = JSON.parse(fs.readFileSync(correctedSfxManifestPath, "utf8"));
for (const match of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi)) {
  if (match[1].trim()) assert.doesNotThrow(() => new Function(match[1]), "Inline Editor script must parse");
}

for (const asset of ["comic-editor.css", "comic-panels.js", "comic-editor.js", "general-comic-editor.css", "editor-mode-controller.js", "project-image-tray.js", "general-comic-core.js", "general-comic-editor.js"]) {
  assert.ok(html.includes(`./${asset}?v=`), `${asset} must be loaded by the Editor with cache busting`);
}

assert.match(html, /comicEditor=window\.SpeechBubbleComicEditor\.create/);
assert.match(html, /generalComicEditor=window\.SpeechBubbleGeneralComicEditor\.create/);
const newBuiltInSfx = correctedSfxManifest.items.filter((item) => item.id.startsWith("sfx-builtin-"));
assert.equal(newBuiltInSfx.length, 15, "15 source crops must be built-in SFX, not user presets");
for (const item of newBuiltInSfx) {
  assert.ok(item.mask, `${item.id} must remain a recolorable alpha mask`);
  assert.ok(item.w > 0 && item.w <= 512 && item.h > 0 && item.h <= 512, `${item.id} must retain bounded geometry`);
  assert.ok(Number.isFinite(item.sortGroup) && Number.isFinite(item.sortRank), `${item.id} must have recommended-order placement`);
  assert.deepEqual(item.defaults, { fillColor: "#EC407A", outlineColor: "#111111", outlineWidth: 3 }, `${item.id} must use the requested pink and black style`);
  assert.ok(fs.existsSync(`web/assets/sfx/sfx-png-corrected-list-v2/${item.asset}`), `${item.id} asset must exist`);
}

assert.ok(html.includes("./project-schema.js?v="), "Project schema must be loaded by the Editor");
assert.ok(
  html.indexOf("./project-schema.js?v=") < html.indexOf("./comic-panels.js?v="),
  "Project schema must load before comic panels",
);
assert.match(projectSchema, /CURRENT_LAYOUT_VERSION = 5/);
assert.match(projectSchema, /CURRENT_COMIC_VERSION = 1/);
assert.match(projectSchema, /CURRENT_GENERAL_COMIC_VERSION = 1/);
assert.match(html, /projectSchema\.build\(\{activeWorkspace,workspaces,comic:comicEditor\?\.serialize\(\)\|\|null,generalComic:generalComicEditor\?\.serialize\(\)\|\|null\}\)/);
assert.match(html, /const prepared=projectSchema\.preflightPayload\(payload\)[\s\S]*?clearDocumentCanvas\(\)/);
assert.match(html, /loadState\(JSON\.stringify\(prepared\.layout\),\{strict:true\}\)/);
assert.match(html, /sortGroup:Number\.isFinite\(Number\(raw\.sortGroup\)\)/);
for (const [id, width, height] of [
  ["n-small-tsu-ellipsis-mask", 380, 181],
  ["dokun-small-tsu-mask", 115, 480],
  ["chuu-vertical-uniform-mask", 134, 500],
  ["nyuru-mask", 129, 340],
  ["boto-small-tsu-vertical-uniform-mask", 140, 500],
  ["dochu-exclamation-angular-vertical-mask", 143, 500],
  ["dokkunn-vertical-gpt-v1", 181, 560],
  ["kunekune-mask", 152, 360],
  ["uguuu-ellipsis-mask", 142, 480],
  ["dochu-vertical-uniform-mask", 152, 500],
  ["biku-hiragana-mask-original-01", 164, 300],
  ["giu-long-angular-vertical-mask", 158, 500],
]) {
  const escapedId = id.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  assert.match(html, new RegExp(`id:\"${escapedId}\"[^\\n]*w:${width},h:${height}`), `${id} must preserve its source aspect ratio`);
}
assert.match(desktopShell, /class="desktop-check desktop-empty-guide-check"[^>]*><input data-desktop-setting="show_empty_canvas_guide"/);
assert.match(desktopCss, /\.desktop-empty-guide-check\s*\{[^}]*width:\s*100%;[^}]*justify-content:\s*flex-start;[^}]*text-align:\s*left;/);
assert.match(html, /comicEditor\?\.restore\(comicLayout\)/);
assert.match(html, /projectSchema\.build\(\{activeWorkspace,workspaces,comic:comicEditor\?\.serialize\(\)\|\|null,generalComic:generalComicEditor\?\.serialize\(\)\|\|null\}\)/);
assert.match(html, /comic:comicEditor\?\.serialize\(\)/);
for (const phase of ["base", "images", "borders"]) {
  assert.match(html, new RegExp(`comicEditor\\.drawUnderlay\\(ctx,\\{overlay:comicOverlayExport,phase:"${phase}"\\}\\)`));
}
assert.match(editor, /data-comic-panel-pattern-select="type"/);
assert.match(editor, /data-comic-panel-pattern-fields/);
assert.match(editor, /function drawDividerGuide\(target, divider, hovered\)/);
assert.match(editor, /const railThickness = 8 \/ zoom/);
assert.match(editor, /target\.fillText\(horizontal \? "↕" : "↔", centerX, centerY \+ \.5 \/ zoom\)/);
assert.match(editor, /for \(const divider of comic\.page\.structure_locked \? \[\] : computed\.dividers\) \{\s*const hovered[\s\S]*?drawDividerGuide\(target, divider, hovered\);/);
assert.match(editor, /randomize-panel-pattern/);
assert.match(editor, /backgroundPatterns\(\)\?\.draw\(target, pattern, rect\.w, rect\.h\)/);
assert.match(html, /comic_stack==="below_image"/);
assert.match(html, /assignLayerComicTarget/);
assert.match(html, /id:"center",label:"Center",line_count:180,inner_x:\.5,inner_y:\.5/);
assert.match(html, /id:"wide",label:"Wide",line_count:210,inner_x:\.45,inner_y:\.45/);
assert.match(html, /id:"tall",label:"Tall",line_count:190,inner_x:\.45,inner_y:\.45/);
assert.match(html, /id:"side",label:"One Side",line_count:130,inner_x:\.45,inner_y:\.45/);
for (const preset of ["wide", "tall", "side"]) {
  assert.match(renderer, new RegExp(`"${preset}": \\{[\\s\\S]*?"inner_x": 0\\.45, "inner_y": 0\\.45`));
}
assert.match(html, /function refreshQuickEmphasisLines\(\)/);
assert.match(html, /favoriteAssets\("emphasis",EMPHASIS_PRESETS,\["center","wide"\]\)/);
assert.match(html, /id="openEmphasisDrawer"/);
assert.match(html, /id="emphasisDrawer"/);
assert.match(html, /renderEmphasisBrowser\(\)/);
assert.match(html, /comicEditor\?\.drawOverlay\(ctx\)/);
assert.match(html, /comicOverlayExport=true/);
assert.match(html, /exportTransport==="multipart_canvas_v1"\|\|activeStructuralEditor\(\)/);
assert.match(html, /comicEditor\?\.handlePointerDown/);
assert.match(html, /comicEditor\?\.handlePointerMove/);
assert.match(html, /comicEditor\?\.handlePointerEnd/);
assert.match(html, /comicEditor\?\.handleImageDrop/);
assert.match(html, /comicEditor\?\.handleContextMenu/);
assert.match(html, /comicEditor\.confirmExport/);
assert.match(editor, /data-comic-mode="comic"/);
assert.doesNotMatch(editor, /data-comic-mode="panels"/);
assert.match(html, /speech_bubble:open_settings/);
assert.match(html, /bubbleShapeAssetsReady/);
assert.match(html, /base-thought/);
assert.match(html, /base-heart/);
assert.match(html, /function hasEditableDocument\(\)/);
assert.match(html, /comicEditor\?\.isActive\(\)/);
assert.match(html, /hostMode==="desktop"/);
assert.match(html, /comic_scope/);
assert.match(html, /data-comic-target="emphasis"/);
assert.match(html, /data-comic-target="asset"/);
assert.match(html, /assignElementTarget/);
assert.match(html, /text:uiText\("こんにちは","Hello!"\)/);
assert.match(html, /installBubbleFallbackAssets/);
assert.match(html, /complete built-in fallback/);
assert.match(html, /start\.cmd から起動すると利用できます/);
assert.match(html, /システムフォントを読み込めませんでした/);
assert.match(html, /url\.searchParams\.set\("token",desktopLaunchToken\)/);
assert.match(html, /function authenticatedAssetUrl\(value\)/);

const shapeIds = new Set(shapeManifest.presets.map((preset) => preset.id));
for (const shapeId of [
  "base-thought",
  "base-heart",
  "comic_tall_panel_soft",
  "comic_tall_panel_irregular",
  "comic_vertical_oval_notched",
  "rpg-dialogue-box-no-marker",
  "classic-sticky-note",
]) {
  assert.equal(shapeIds.has(shapeId), true, `shape manifest must include ${shapeId}`);
}

for (const feature of [
  "vertical_four",
  "data-comic-heading",
  "heading-resize",
  "follow_panel_width",
  "fitHeadingToPanelWidth",
  "scaleInteger",
  "border_color",
  "border_width",
  "image_scale",
  "image_locked",
  "structure_locked",
  "frame_style",
  "comicLayerRow",
  "renderLayers",
  "ページ画像",
  "画像はコマ内へドロップしてください",
  "elementTargetOptions",
  "assignElementTarget",
  "effectTargetRect",
  "panelContentRect",
  "toggle-panel-collapse",
  "shouldSkipPanelScopedItem",
  "countExpandedPanels",
  "is-collapsed",
  "comic-panel-collapse-action",
]) {
  assert.ok(editor.includes(feature), `comic editor must include ${feature}`);
}

assert.match(editor, /tr\("コマを表示", "Show Panel"\)/);
assert.match(editor, /tr\("コマを非表示", "Hide Panel"\)/);
assert.doesNotMatch(editor, /コマを折りたたむ|コマを再表示|\(Collapsed\)/);

assert.doesNotMatch(editor, /<strong>Screen Tone<\/strong>/);
assert.doesNotMatch(editor, /data-comic-property="tone_enabled"/);
assert.doesNotMatch(editor, /data-comic-template="four_grid"/);
assert.doesNotMatch(editor, /data-comic-template="blank"/);
assert.doesNotMatch(editor, /data-comic-template="two_column"/);
assert.doesNotMatch(editor, /data-comic-action="canvas-swap"/);
assert.doesNotMatch(editor, /data-comic-property="fit"/);
assert.doesNotMatch(editor, /data-comic-context="split-/);
assert.doesNotMatch(editor, /data-comic-context="merge"/);
assert.doesNotMatch(editor, /placeSequentially/);
assert.doesNotMatch(editor, /空きコマへ順番に配置/);
assert.doesNotMatch(editor, /heading\.text/);
assert.match(editor, /青いドラッグバー（↕）を上下に動かして高さを変更できます/);
assert.doesNotMatch(editor, /data-comic-page="visible"/);
assert.doesNotMatch(editor, /data-comic-property="image_locked"/);
assert.match(editor, /target\.strokeRect\(\s*item\.rect\.x \+ inset/);
assert.match(editor, /Ctrl＋ホイールで拡大・縮小/);
assert.match(editor, /speech-bubble-editor-comic-images/);
assert.match(editor, /MAX_IMAGE_BYTES = 96 \* 1024 \* 1024/);
assert.match(editor, /MAX_IMAGES = 100/);
assert.match(editor, /source: "stored"/);
assert.match(editor, /function removeTrayImage\(imageId\)/);
assert.match(editor, /comic\.images\.splice\(index, 1\)/);
assert.match(editor, /options\.switchWorkspace\?\.\(enableComic \? "comic" : "single"\)/);
assert.match(css, /\.comic-image-tray/);
assert.match(css, /\.comic-context-menu/);
assert.match(css, /\.comic-layer-nested/);
assert.match(css, /\.comic-panel-collapse-action:not\(:disabled\)[\s\S]*background: #b96f24/);
assert.match(css, /\.comic-panel-collapse-action\.is-restoring:not\(:disabled\)[\s\S]*background: #2f8654/);
assert.match(html, /dataset\.comicPanelTarget/);
assert.match(html, /insertAdjacentElement\("afterend",row\)/);
for (const removedDockControl of ["propertiesDockFloat", "propertiesDockReturn", "layersDockFloat", "layersDockReturn", "layersDockToggle", "rightDockDivider"]) {
  assert.doesNotMatch(html, new RegExp(`id="${removedDockControl}"`));
}
assert.match(html, /function initializeRightDockFloating\(\)/);
assert.match(html, /speech_bubble:floating_panels:v4/);
assert.match(html, /delete next\.leftRatio;delete next\.topRatio;applyGeometry\(entry,next\)/);
assert.doesNotMatch(html, /const detachExternal=/);
assert.match(html, /class="properties-dock floating-panel"/);
assert.match(html, /class="layers-dock floating-panel"/);
assert.match(html, /propertiesLeft=layersLeft-gap-width/);
assert.match(html, /EXTERNAL_PALETTE_GEOMETRY_KEY/);
assert.match(editor, /if \(heading\) \{[\s\S]*if \(!comic\.page\.structure_locked\) \{/);
assert.match(html, /modeKey=\(\)=>/);
assert.match(html, /viewportWidth:innerWidth,viewportHeight:innerHeight/);
assert.match(html, /speech_bubble:workspace_views:v1/);
assert.match(html, /if\(firstApplicationView\)fitView\(false\);else restoreWorkspaceView/);
assert.match(html, /SpeechBubbleWorkspaceLayout/);
assert.match(html, /document\.getElementById\("emphasisDrawer"\)\.classList\.remove\("open"\)/);
assert.match(html, /\.properties-dock\.floating-panel,\.layers-dock\.floating-panel/);
assert.match(html, /\.font-browser \{ position:fixed; z-index:100000/);
assert.match(html, /FONT_BROWSER_GEOMETRY_KEY/);
assert.match(html, /function initializeFontBrowserDrag\(\)/);
assert.match(html, /function hasSavedFontIdentity\(item\)/);
assert.match(html, /matchingSavedFont\(item,catalog\)\|\|\(hasSavedFontIdentity\(item\)\?null:fallback\)/);
assert.doesNotMatch(html, /if\(!font\)font=fallback/);
assert.match(html, /const restoredFont=matchingSavedFont\(item\);if\(restoredFont\)\{applyResolvedFont\(item,restoredFont\);ensureFontLoaded\(restoredFont\)/);
assert.match(html, /propertiesDock\?\.classList\.contains\("floating-panel"\)/);
assert.ok(
  html.indexOf("selectedInteractionHit") < html.indexOf("!selectedInteractionHit&&comicEditor?.handlePointerDown"),
  "selected canvas handles must be tested before comic page/image hit testing",
);
assert.match(html, /findRotationHandle\(item,point\)\{const handle=rotationHandle\(item\),radius=20\/state\.zoom/);
assert.match(html, /findTailHandle\(item,point\).*radius=28\/state\.zoom/);
assert.match(editor, /const resizeHeading =[\s\S]*headingResizeHandleRect\(activeHeading\)/);
assert.match(editor, /data-comic-action="reset-heading"/);
assert.match(editor, /data-comic-action="reset-panel-heights"/);
assert.match(editor, /data-comic-action="fit-heading-to-panel-width"/);
assert.match(editor, /data-comic-page-title-lock/);
assert.match(editor, /data-comic-page="structure_locked" type="checkbox"/);
assert.match(css, /\.comic-properties-title \.comic-heading-title-toggle\s*\{[^}]*display:\s*inline-flex/);
assert.match(editor, /selectionKind\.hidden = target === "heading" \|\| target === "page"/);
assert.match(editor, /function snapHeadingToPanelEdges\(heading\)/);
assert.match(editor, /function pageResizeHandleRect\(\)/);
assert.match(editor, /function pointerCursorAt\(point\)/);
assert.match(editor, /data-comic-heading-title-toggle/);
assert.match(editor, /comic-heading-title-toggle[\s\S]*data-comic-heading="visible"/);
assert.doesNotMatch(editor, /data-comic-action="add-heading"/);
assert.equal((editor.match(/data-comic-heading="visible"/g) || []).length, 1);
assert.match(editor, /selectionKind\.hidden = target === "heading"/);
assert.match(editor, /data-comic-heading-edit-hint/);
assert.match(editor, /const trayImages = comic\.images\.filter\(\(metadata\) => metadata\.id !== "source"\)/);
assert.match(editor, /event\.dataTransfer\.setData\("text\/plain", metadata\.id\)/);
assert.match(editor, /event\.dataTransfer\.setDragImage\(ghost, 18, 18\)/);
assert.match(editor, /function createTrayDragGhost\(name\)/);
assert.doesNotMatch(editor, />画像を差し替え</);
assert.doesNotMatch(editor, /画像を選択／差し替え/);
assert.ok(
  html.indexOf('data-left-section="emphasis"') < html.indexOf('data-left-section="frames"'),
  "Emphasis Lines must appear before Frames",
);
assert.doesNotMatch(html, /id="propertiesDockToggle"/);
assert.match(html, /let autoSaveDelay = Math\.max\(5000, Math\.min\(3600000/);
assert.match(html, /if\(layoutDirty&&autoSaveEnabled\)persistDraftNow\(\);\s*clearTimeout\(autoSaveTimer\)/);
assert.match(css, /\.comic-tray-heading button[\s\S]*white-space: nowrap/);
assert.match(css, /\.comic-tray-heading \.comic-tray-toggle[\s\S]*flex: 1 1 auto/);
assert.match(editor, /comic-tray-toggle[\s\S]*data-comic-image-count/);
assert.match(html, /SpeechBubbleApplyRuntimeSettings/);
assert.match(desktopShell, /SpeechBubbleApplyRuntimeSettings/);
assert.match(html, /let showEmptyCanvasGuide = params\.get\("showEmptyCanvasGuide"\) !== "0"/);
assert.match(html, /emptyCanvasState"\)\.hidden=hasDocument\|\|activeWorkspace!=="single"\|\|!showEmptyCanvasGuide/);
assert.match(html, /showEmptyCanvasGuide=settings\?\.show_empty_canvas_guide!==false/);
assert.match(html, /nextSharedProjectImages=settings\?\.shared_project_images!==false/);
assert.match(html, /payload\.image_trays=projectImageTray\.serialize\(\)/);
assert.match(html, /initializeProjectImageTray\(\)/);
assert.match(html, /projectImageTray\?\.setWorkspace\(target\)/);
assert.match(html, /projectImageTray\.place\(projectImageId,\{point\}\)/);
assert.match(editor, /function importExternalImage\(blob, asset, control = \{\}\)/);
assert.match(editor, /function removeAssetUsage\(imageId, control = \{\}\)/);
assert.match(html, /id="fitTextBoxNow"/);
assert.match(html, /fitTextBox\(current,true,false\)/);
assert.match(html, /const preserveManualBox=!item\.auto_fit/);
assert.match(html, /persistDesktopRecovery\(true,true\)/);
assert.match(html, /async function persistDesktopRecovery\(checkpoint=false,force=false\)/);
assert.match(html, /const resolved=await Promise\.all\(loaders\)/);
assert.match(html, /applyResolvedFont\(result\.item,result\.font\)/);
assert.match(html, /if\(layerClipboard\?\.length\)\{event\.preventDefault\(\);pasteLayers\(\);return;\}/);
assert.match(html, /comicEditor\?\.handleWheel\(event,imagePoint\(event\)\)/);
assert.match(html, /const fontTask=loadSystemFonts\(\),assetTask=Promise\.all/);
assert.match(css, /\.canvas-panel\.comic-tray-visible #viewport/);
assert.match(css, /\.comic-page-checks/);
assert.match(css, /\.comic-color-swatches\s*\{[\s\S]*grid-template-columns:\s*repeat\(auto-fill,\s*16px\)/);
assert.match(css, /\.comic-color-swatches button\s*\{[\s\S]*width:\s*16px;[\s\S]*height:\s*16px;/);
assert.match(css, /\.comic-image-card\.selected/);
assert.match(css, /\.comic-image-card\.selected::before/);
assert.match(css, /content: "SELECTED"/);
assert.match(css, /\.comic-image-card\.used::after/);
assert.match(css, /content: "使用中"/);
assert.match(editor, /selectedTrayImageId/);
assert.match(editor, /function selectedInsertionTarget\(\)/);
assert.match(editor, /function panelInsertionTarget\(panelId\)/);
assert.match(editor, /function insertionTargetAt\(point\)/);
assert.match(editor, /function defaultPanelInsertionTarget\(\)/);
assert.match(editor, /data-comic-page="heading_gap" type="range"/);
assert.match(editor, /data-comic-page="heading_gap" type="number"/);
assert.doesNotMatch(editor, /emptyImageButtonRect/);
assert.doesNotMatch(editor, /fillText\(tr\("＋ 画像を入れる", "\+ Add Image"\)/);
assert.match(editor, /locked:\s*comic\.page\.structure_locked !== false/);
assert.match(editor, /event\.target\.closest\('\[data-comic-action="remove-image"\]'\)/);
assert.match(editor, /selectedTrayImageId = addedId/);
assert.match(converter, /applyButton\.textContent = tr\("追加処理中…", "Adding…"\)/);
assert.match(html, /function insertSfx[\s\S]*insertionTargetAt[\s\S]*applyComicPanelTarget/);
assert.match(html, /projectSchema\.build\(\{activeWorkspace,workspaces,comic:comicEditor\?\.serialize\(\)\|\|null,generalComic:generalComicEditor\?\.serialize\(\)\|\|null\}\)/);
assert.match(html, /for\(const name of \["single","comic","comic_layout"\]\)/);
assert.match(html, /id="comicInsertTargetStatus"/);
assert.match(html, /function visibleCanvasDocumentRect\(\)/);
assert.match(html, /function addTextLayer\(\)[\s\S]*bubbleIndex\+1/);
assert.match(html, /item\.comic_scope="panel";item\.comic_panel_id=target\.panelId;item\.comic_stack="above_image"/);
assert.ok(
  html.indexOf('data-left-section="bubbles"') < html.indexOf('id="addText"') &&
  html.indexOf('id="addText"') < html.indexOf('data-left-section="sfx"'),
  "Add Text must appear between Speech Bubbles and SFX",
);
assert.match(html, /grid-template-columns:clamp\(150px,20vw,224px\) minmax\(220px,1fr\)/);
assert.match(html, /\.right \{ position:fixed; inset:0;/);
assert.match(
  html,
  /\.layer\[data-comic-layer="page"\]\s*\{[^}]*border-left:4px solid #4fb7bd;[^}]*background:#19383d;/,
);
for (const setting of [
  "export_directory",
  "auto_export_to_directory",
  "output_format",
  "filename_format",
  "backup_enabled",
  "auto_save",
  "auto_save_interval_seconds",
  "startup_behavior",
  "show_empty_canvas_guide",
  "shared_project_images",
]) {
  assert.ok(desktopShell.includes(`data-desktop-setting="${setting}"`), `Desktop settings must include ${setting}`);
}
assert.match(desktopShell, /data-desktop-action="cache-clear"/);
assert.match(desktopShell, /data-desktop-action="user-preset-replace-image"/);
assert.match(desktopShell, /data-desktop-action="user-preset-organize"/);
assert.match(desktopShell, /function applyTheme/);
assert.match(desktopShell, /function applyLanguage/);
assert.match(desktopShell, /activeDesktopLanguage/);
assert.match(desktopMain, /SetProcessDpiAwarenessContext/);
assert.match(desktopMain, /normalized_window_geometry/);
assert.match(desktopMain, /maximized=geometry\["maximized"\]/);
assert.match(desktopMain, /_ACTIVATE_EVENT_NAME/);
assert.match(desktopMain, /SetEvent\(event\)/);
assert.match(desktopMain, /getattr\(events, "closing", None\)/);
assert.match(desktopMain, /native_close_ready/);
assert.match(desktopMain, /native_close_ready\(self, ok=True, message="", cancelled=False\)/);
assert.match(desktopMain, /save_window_state/);
assert.match(desktopShell, /\["＋ 画像を追加", "＋ Add Images"\]/);
assert.doesNotMatch(desktopMain, /self\.(?:window|palette_window|webview)\s*=/);
assert.match(desktopMain, /SizableToolWindow/);
assert.match(desktopMain, /palette=1/);
assert.doesNotMatch(desktopMain, /SystemEvents|Screen\.AllScreens|begin_palette_drag/);
assert.match(html, /isPaletteWindow/);
assert.match(html, /palette_ready/);
assert.match(html, /id="openExternalPalette"/);
assert.match(html, /function insertEmphasisLines[\s\S]*item\.comic_scope="panel"[\s\S]*item\.comic_panel_id=resolved\.panelId/);
assert.match(desktopShell, /async function saveRecovery\(checkpoint = false\)/);
assert.match(desktopShell, /markProjectSaved/);
assert.match(desktopShell, /saveRecoveryCheckpoint/);
assert.match(desktopShell, /async function loadRecovery\(\)/);
assert.match(html, /SpeechBubbleDesktopEditor\.loadRecovery\(recovery\)/);
assert.match(html, /prepareNativeClose/);
assert.match(html, /nativeClosePrepared\|\|autoSaveEnabled/);
assert.match(html, /createNewDesktopProject/);
assert.match(html, /BACKGROUND_LAYER_ID/);
assert.match(desktopShell, /data-desktop-action="project-new"/);
assert.match(desktopShell, /confirmUnsavedChanges/);
assert.match(desktopShell, /event\.key\.toLowerCase\(\) !== "n"/);
assert.match(html, /project_path:currentProjectPath/);
assert.match(html, /Project saved, but recovery cache sync failed/);
assert.match(editor, /Project image blob is missing/);
assert.match(html, /if\(standaloneResumePromise\)return standaloneResumePromise/);
assert.match(html, /startStandaloneDocument\(standaloneId,\{offerResume:!isDesktop,behavior:isDesktop\?"new":"ask"\}\)/);
assert.match(html, /event\.key==="Delete"\|\|event\.key==="Backspace"\)&&state\.selection\.length/);
assert.match(html, /Date\.now\(\)-lastRecoveryCheckpoint>=600000/);
assert.match(html, /DESKTOP_SINGLE_BACKGROUND_ID="__single_background__"/);
assert.match(html, /snapshot:desktopSnapshot/);
assert.match(desktopShell, /data-desktop-action="workspace-layout-reset"/);
assert.match(desktopShell, /speech-bubble:language-change/);
assert.match(desktopShell, /\["コマ", "Panel"\]/);
assert.match(desktopShell, /function authenticatedMediaUrl\(value\)/);
assert.match(desktopShell, /addEventListener\("input"/);
assert.match(
  desktopShell,
  /data-desktop-setting="startup_behavior"[\s\S]*desktop-autosave-row[\s\S]*data-desktop-setting="auto_save"[\s\S]*data-desktop-setting="auto_save_interval_seconds"/,
);
assert.match(editor, /if \(!selectedTarget && !selectedTrayImageId\) return false/);
assert.match(editor, /selectedTrayImageId = ""/);
assert.match(editor, /Keep the blob alive while this deletion is present in the editor/);

// Replacing a single-image background must not reset the independent comic workspace.
assert.match(html, /function preserveComicWorkspace\(\)\s*\{\s*captureActiveWorkspace\(\)/);
assert.match(html, /workspace: structuredClone\(workspaces\.comic\)/);
assert.match(html, /comic: structuredClone\(comicEditor\?\.serialize\(\)\)/);
assert.match(html, /workspaces\.comic = snapshot\.workspace/);
assert.match(html, /comicEditor\?\.restore\(snapshot\.comic, \{\s*hydrate: true,\s*keepMode: true/);
assert.match(html, /if \(activeWorkspace === "single"\) \{\s*state\.width = workspaces\.single\.width/);
assert.match(html, /mode === "standalone" &&\s*!resume &&\s*imageLoaded &&\s*activeWorkspace === "single"/);
assert.match(html, /const preservedComic = replacingStandaloneSingleImage\s*\? preserveComicWorkspace\(\)\s*: null/);
assert.match(html, /const preservedSingle = replacingStandaloneSingleImage\s*\? structuredClone\(workspaces\.single\)\s*: null/);
assert.match(html, /function restorePreservedSingleWorkspace\(snapshot\)/);
assert.match(html, /if \(!copiedLayout\) \{\s*restorePreservedSingleWorkspace\(preservedSingle\)/);
assert.match(html, /restorePreservedComicWorkspace\(preservedComic\)/);
assert.match(html, /const next=copiedLayout\|\|"\{\}";applyLayoutForCurrentImage\(next,\{dirty:false\}\)/);
assert.match(html, /layoutDirty = currentLayoutJson\(\) !== lastSavedLayout/);
assert.match(html, /replaceDiscard"\)\.onclick=async\(\)=>\{[\s\S]*applyLayoutForCurrentImage\(lastSavedLayout,\{dirty:false\}\)[\s\S]*performPendingReplacement\(\)/);

// Desktop follow-up UI: no duplicate Close button, slider-based background scale,
// and separate reusable bubble preset management.
assert.doesNotMatch(html, /<button id="closeEditor"/);
assert.match(html, /id="backgroundScaleRange" type="range" min="10" max="800"/);
assert.match(html, /id="backgroundScaleOutput">100%/);
assert.match(html, /id="saveUserPresetAs"[\s\S]*別名で保存/);
assert.match(html, /makeBubblePresetSection\("My Presets"/);
assert.match(html, /makeBubblePresetSection\("Built-in"/);
assert.match(html, /manageBubblePreset/);
assert.match(desktopShell, /SFX／スタンプ画像プリセット/);
assert.match(desktopShell, /吹き出しプリセット管理/);
assert.match(desktopShell, /data-desktop-action="bubble-presets-import"/);

// Single Image v0.1.4: canvas background plus non-destructive image layers.
for (const feature of [
  "canvasBackgroundColorSwatches",
  "initializeCanvasBackgroundSwatches",
  "addSingleImageLayerFromLayers",
  "createSingleImageLayer",
  "singleImageAssets",
  "selectedSingleImageSource",
  "applyProcessedSingleImage",
  "processImageBackgroundRemoval",
  "processImageComicConversion",
  "showOriginalImageLayer",
]) {
  assert.ok(html.includes(feature), `Single Image layer implementation must include ${feature}`);
}
assert.doesNotMatch(html, /id="singlePageSettings"/);
assert.doesNotMatch(html, /id="singleCanvasBackgroundColor"/);
assert.doesNotMatch(html, /id="singleCanvasTransparent"/);
assert.doesNotMatch(html, /id="addSingleImageLayer"/);
assert.match(html, /\.compact-check input\[type="checkbox"\][^{]*\{[^}]*width:16px;[^}]*height:16px/);
assert.match(html, /#allSfx \.sfx-library-empty,\.user-preset-section \.sfx-library-empty \{[^}]*grid-column:1 \/ -1;[^}]*width:100%/);
assert.match(html, /Register PNG \/ WebP files in Settings\./);
assert.match(html, /\.shape-card \{[^}]*aspect-ratio:1/);
assert.match(html, /#allSfx \.sfx-library-section > \.palette \{[^}]*grid-template-columns:repeat\(auto-fill,minmax\(82px,1fr\)\)/);
assert.match(html, /header \.comic-mode-toggle \{[^}]*align-items:center;[^}]*margin:0/);
assert.match(html, /state\.selected===BACKGROUND_LAYER_ID[\s\S]*transformDetails"\)\.hidden=true[\s\S]*shadowEffects"\)\.hidden=true/);
assert.match(html, /projectSchema\.build\(\{activeWorkspace,workspaces,comic:comicEditor\?\.serialize\(\)\|\|null,generalComic:generalComicEditor\?\.serialize\(\)\|\|null\}\)/);
assert.match(html, /SINGLE_IMAGE_ASSET_PREFIX="single-image:"/);
assert.match(html, /createSingleImageLayer\(asset,\{role:"original"/);
assert.match(html, /applyProcessedSingleImage\(blob,[^\n]+,"background-removal"\)/);
assert.match(html, /applyProcessedSingleImage\(blob,[^\n]+,"comic-conversion"\)/);
assert.match(html, /if\(hideSource&&inherit\)inherit\.visible=false/);
assert.match(html, /rotation:Number\(inherit\?\.rotation\)\|\|0/);
assert.match(html, /locked:inherit\?inherit\.locked===true:locked/);
assert.match(html, /candidates\.filter\(e=>e\.type!=="image"\),candidates\.filter\(e=>e\.type==="image"\)/);
assert.match(desktopShell, /\["キャンバス背景", "Canvas Background"\]/);
assert.match(readme, /複数の画像レイヤー/);
assert.match(readme, /新しい画像レイヤーとして追加/);
assert.match(readme, /第3の編集モード「コミック」/);
assert.match(readme, /general-comic-diagonal-divider\.png/);
assert.match(readme, /Shift.*15度刻み/);
assert.match(readme, /background-removal-edge-correction\.png/);
assert.match(desktopShell, /data-desktop-action="bubble-presets-export"/);
assert.match(desktopShell, /function refreshBubblePresetManager/);
assert.match(readme, /吹き出しユーザープリセット/);
assert.match(readme, /Built-inは読み取り専用で上書きされません/);

// Single Image procedural canvas backgrounds use one renderer for preview/export.
assert.match(html, /canvas-background-patterns\.js/);
assert.match(html, /canvasBackgroundPatterns\?\.draw\(ctx,state\.canvasBackground,state\.width,state\.height\)/);
assert.match(html, /id="canvasBackgroundType"/);
assert.match(html, /id="canvasBackgroundPreset"/);
assert.match(html, /id="canvasBackgroundFields"/);
assert.match(html, /state\.canvasBackground=normalizedCanvasBackground/);
assert.match(desktopShell, /\["背景の種類", "Background Type"\]/);
assert.match(desktopShell, /\["内蔵プリセット", "Built-in Preset"\]/);
for (const id of ["solid","linear-gradient","radial-gradient","halftone","parallel-lines","crosshatch","checker","flowers","pixel","tile","scanline","clouds","marble","cellular","turbulence","fractal","wood","wave3d","brick","weave","hexagon","focus-lines","digital-camouflage"]) {
  assert.ok(canvasBackgroundPatterns.includes(`type("${id}"`), `Missing procedural background: ${id}`);
}
assert.match(canvasBackgroundPatterns, /window\.SpeechBubbleCanvasBackgroundPatterns/);
assert.match(canvasBackgroundPatterns, /function draw\(ctx,input,width,height\)/);
assert.doesNotMatch(canvasBackgroundPatterns, /https?:\/\//);
assert.match(html, /function enableRealtimeSelectWheel\(control\)/);
assert.match(html, /control\.addEventListener\("wheel"[\s\S]*\{passive:false\}/);
assert.match(html, /control\.dispatchEvent\(new Event\("change",\{bubbles:true\}\)\)/);
assert.match(html, /enableRealtimeSelectWheel\(type\);enableRealtimeSelectWheel\(preset\)/);
assert.match(html, /realtimeSelectWheelCommitTimer=setTimeout\(commitPropertyEdit,300\)/);
assert.match(html, /recordSelectUndo=\(\)=>\{if\(!state\.propertyEditSnapshot\)pushUndo\(\);\}/);

// Layer multi-selection: Shift range, bulk visibility/lock, and locked-layer exclusion.
assert.match(html, /let layerSelectionAnchorId=""/);
assert.match(html, /function selectLayerRow\(item,event\)/);
assert.match(html, /event\.shiftKey&&displayedIds\.includes\(layerSelectionAnchorId\)/);
assert.match(html, /displayed\.slice\(Math\.min\(start,end\),Math\.max\(start,end\)\+1\)/);
assert.match(html, /row\.onclick=event=>\{if\(event\.altKey\)/);
assert.match(html, /state\.selection\.length>1&&state\.selection\.includes\(item\.id\)\?selectedItems\(\):\[item\]/);
assert.match(html, /targets\.forEach\(layer=>layer\.visible=visible\)/);
assert.match(html, /targets\.forEach\(layer=>layer\.locked=locked\)/);
assert.match(html, /editableItems=items\.filter\(canvasItemEditable\)/);
assert.match(html, /selectionBounds\(editableItems\)/);
assert.match(html, /locked layer\$\{lockedCount===1\?"":"s"\} excluded from transforms/);
assert.match(desktopShell, /Ctrl: toggle selection \/ Shift: range selection/);

// Comic panel images have an independent, ephemeral multi-selection.
assert.match(editor, /const selectedPanelImageIds = new Set\(\)/);
assert.match(editor, /function selectedImagePanels\(\)/);
assert.match(editor, /function setPanelImageSelection\(panelIds, primaryId = null\)/);
assert.match(editor, /function selectPanelImage\(panelId, event = \{\}\)/);
assert.match(editor, /event\.shiftKey && imageIds\.includes\(panelImageSelectionAnchorId\)/);
assert.match(editor, /imageIds\.slice\(Math\.min\(start, end\), Math\.max\(start, end\) \+ 1\)/);
assert.match(editor, /targets\.forEach\(\(targetPanel\) => targetPanel\.image_visible = !visible\)/);
assert.match(editor, /targets\.forEach\(\(targetPanel\) => targetPanel\.image_locked = !panel\.image_locked\)/);
assert.match(editor, /panels: movablePanels\.map\(\(panel\) => \(\{ panel, offsetX: panel\.image_offset_x, offsetY: panel\.image_offset_y \}\)\)/);
assert.match(editor, /for \(const entry of drag\.panels\)/);
assert.match(editor, /panels\.forEach\(\(panel\) => panel\.image_scale = core\.clamp\(panel\.image_scale \* factor/);
assert.match(editor, /panels\.forEach\(\(panel\) => panel\.image_id = null\)/);
assert.match(editor, /selectedPanelImageIds\.clear\(\);\s*panelImageSelectionAnchorId = null;\s*selectedTarget = selectedPanelId \? "panel" : "page"/);
assert.match(editor, /image_rotation/);
assert.match(editor, /image_crop/);
assert.match(editor, /imageLayerRotation\.drawCroppedImage/);

console.log("comic_editor_integration_test: OK");
