'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync('web/speech-bubble-editor.html','utf8');
const shell = fs.readFileSync('web/desktop/desktop-shell.js','utf8');
function part(source, first, next) {
  const start=source.indexOf(first),end=source.indexOf(next,start+first.length);
  assert.ok(start>=0&&end>start,`source boundary: ${first}`);
  return source.slice(start,end);
}
const saveCode=part(html,'    async function markProjectSaved(', '    function persistDraftNow(')+
  part(html,'    async function saveLayoutExplicit(', '    function discardChanges(')+
  part(html,'    function hasUnsavedDocumentChanges(', '    let sfxBrowseMode=');
let scenarios=0;
function makeSave() {
  let resolve,reject;const pending=new Promise((ok,no)=>{resolve=ok;reject=no;});
  const stored=new Map();
  const ctx={console,documentId:'one',current:'A',lastSavedLayout:'A',lastSavedProjectLayout:'A',currentProjectPath:'one.sbeproj',
    recoveryNeedsSave:false,layoutDirty:false,hasExplicitSavedLayout:true,layoutSaveInFlight:false,documentLoadInFlight:false,
    documentMode:'standalone',sourceName:'name',imageHash:'hash',forgeApiBase:'/api',jsonKey:'json',LAST_STANDALONE_ID_KEY:'last',
    dirtyTrackingEnabled:true,auto:0,removed:0,posts:[],button:{textContent:'Save',disabled:false},
    window:{SpeechBubbleDesktopShell:{isDocumentBusy:()=>false}},
    safeStoredLayout:x=>x,uiText:(ja,en)=>en,hasEditableDocument:()=>true,setSaveState:()=>{},updateActionState:()=>{},
    localStorage:{setItem:(k,v)=>stored.set(k,v)},savedLayoutKey:()=>`saved:${ctx.documentId}`,
    currentLayoutJson:()=>ctx.current,removeDraftCache:()=>ctx.removed++,scheduleAutoSave:()=>ctx.auto++,
    refreshDirtyState:()=>{ctx.layoutDirty=ctx.recoveryNeedsSave||ctx.current!==ctx.lastSavedLayout;},
    fetch:()=>pending,persistDesktopRecovery:async()=>{},postHost:(...args)=>ctx.posts.push(args),
    document:{getElementById:()=>ctx.button},
  };
  vm.createContext(ctx);vm.runInContext(saveCode,ctx);
  return {ctx,stored,resolve:()=>resolve({ok:true,json:async()=>({ok:true})}),reject};
}
(async()=>{
  // Deferred saves must acknowledge the submitted snapshot and its document only.
  {
    const {ctx,stored,resolve}=makeSave();ctx.current='B';
    const save=ctx.saveLayoutExplicit();ctx.current='C';resolve();assert.equal(await save,false);
    assert.equal(ctx.lastSavedLayout,'B');assert.equal(ctx.layoutDirty,true);assert.equal(ctx.removed,0);
    assert.equal(stored.get('json'),undefined);assert.equal(ctx.auto,1);scenarios++;
  }
  {
    const {ctx,resolve}=makeSave();ctx.current='B';const pending=ctx.saveLayoutExplicit();
    assert.equal(await ctx.saveLayoutExplicit(),false);resolve();assert.equal(await pending,true);
    assert.equal(ctx.lastSavedLayout,'B');assert.equal(ctx.removed,1);
    assert.equal(ctx.hasUnsavedDocumentChanges(),true,'local layout is not the project file');scenarios++;
  }
  {
    const {ctx,resolve,stored}=makeSave();ctx.current='B';const pending=ctx.saveLayoutExplicit();
    ctx.documentId='two';ctx.current='NEW';ctx.lastSavedLayout='NEW0';resolve();assert.equal(await pending,false);
    assert.equal(ctx.lastSavedLayout,'NEW0');assert.equal(stored.size,0);scenarios++;
  }
  {
    const {ctx,resolve}=makeSave();ctx.current='B';ctx.persistDesktopRecovery=async()=>{ctx.current='C';};
    const pending=ctx.saveLayoutExplicit();resolve();assert.equal(await pending,false);assert.equal(ctx.layoutDirty,true);scenarios++;
  }
  {
    const {ctx,reject}=makeSave();ctx.current='B';ctx.console={error:()=>{},warn:()=>{}};
    const pending=ctx.saveLayoutExplicit();reject(new Error('disk unavailable'));assert.equal(await pending,false);
    assert.equal(ctx.lastSavedLayout,'A');assert.equal(ctx.removed,0);assert.equal(ctx.layoutSaveInFlight,false);scenarios++;
  }
  {
    const {ctx}=makeSave();ctx.current='C';assert.equal(await ctx.markProjectSaved('x.sbeproj','B','one'),false);
    assert.equal(ctx.layoutDirty,true);assert.equal(ctx.lastSavedProjectLayout,'B');assert.equal(ctx.removed,0);scenarios++;
  }
  {
    const {ctx}=makeSave();assert.equal(await ctx.markProjectSaved('other.sbeproj','B','two'),false);
    assert.equal(ctx.currentProjectPath,'one.sbeproj');assert.equal(ctx.lastSavedProjectLayout,'A');scenarios++;
  }
  {
    const {ctx}=makeSave();ctx.recoveryNeedsSave=true;assert.equal(ctx.hasUnsavedDocumentChanges(),true);
    assert.equal(await ctx.markProjectSaved('one.sbeproj','A','one'),true);assert.equal(ctx.hasUnsavedDocumentChanges(),false);scenarios++;
  }
  {
    const {ctx}=makeSave();ctx.current='B';ctx.window.SpeechBubbleDesktopShell.isDocumentBusy=()=>true;
    assert.equal(await ctx.saveLayoutExplicit(),false);assert.equal(ctx.lastSavedLayout,'A');scenarios++;
  }
  // Restore the public palette API with source functions, not a copy of its logic.
  {
    const context={console,window:{},documentId:'doc-A',hostMode:'desktop',isPaletteWindow:false,documentLoadInFlight:false,
      state:{undo:[],redo:[]},current:'A',dirty:0,drafts:0,renders:0,
      createUuid:()=> 'sender-main',sceneSnapshot:()=>context.current,currentLayoutJson:()=>context.current,
      restoreScene:s=>context.current=s,storeUndo:s=>context.state.undo.push(s),refreshDirtyState:()=>context.dirty++,
      scheduleAutoSave:()=>context.drafts++,syncProperties:()=>{},requestRender:()=>context.renders++,updateActionState:()=>{},
      setStandaloneContext:id=>context.documentId=id,clearTimeout,setTimeout,
    };
    vm.createContext(context);vm.runInContext(part(html,'    let paletteSyncApplying=', '    function restoreScene('),context);
    const apply=(sequence,scene,documentId='doc-A')=>context.window.SpeechBubblePaletteSync.apply(JSON.stringify({version:1,sender:'palette',sequence,scene,documentId}));
    assert.equal(apply(1,'B'),true);assert.equal(context.dirty,1);assert.deepEqual(context.state.undo,['A']);assert.equal(context.drafts,1);scenarios++;
    assert.equal(apply(1,'B'),false);assert.equal(apply(0,'C'),false);assert.equal(context.current,'B');scenarios++;
    assert.equal(apply(2,'C','doc-B'),false);assert.equal(context.current,'B');scenarios++;
    assert.equal(apply(3,'B'),true);assert.equal(context.dirty,1);scenarios++;
    context.documentLoadInFlight=true;assert.equal(apply(4,'C'),false);scenarios++;
  }
  // Replacement choices, saving failure and edits during Save & Open.
  {
    const ctx={root:{SpeechBubbleDesktopEditor:{hasUnsavedChanges:()=>ctx.dirty}},dirty:true,choice:'cancel',saved:0,
      confirmUnsavedChanges:async()=>ctx.choice,saveProject:async()=>{ctx.saved++;ctx.dirty=false;return true;}};
    vm.createContext(ctx);vm.runInContext(part(shell,'  async function confirmDocumentReplacement(', '  async function requestNewProject('),ctx);
    assert.equal(await ctx.confirmDocumentReplacement('open'),false);assert.equal(ctx.saved,0);scenarios++;
    ctx.choice='discard';assert.equal(await ctx.confirmDocumentReplacement('open'),true);assert.equal(ctx.saved,0);scenarios++;
    ctx.choice='save';assert.equal(await ctx.confirmDocumentReplacement('open'),true);assert.equal(ctx.saved,1);scenarios++;
    ctx.dirty=true;ctx.saveProject=async()=>false;assert.equal(await ctx.confirmDocumentReplacement('open'),false);scenarios++;
    ctx.saveProject=async()=>true;assert.equal(await ctx.confirmDocumentReplacement('open'),false);scenarios++;
    ctx.saveProject=async()=>{throw new Error('disk');};await assert.rejects(ctx.confirmDocumentReplacement('open'),/disk/);scenarios++;
  }
  {
    const ctx={forgeApiBase:'/speech-bubble-editor'};vm.createContext(ctx);
    vm.runInContext(part(html,'    function userAssetIdFor(', '    function normalizeUserAssetPreset('),ctx);
    const id='a'.repeat(64);assert.equal(ctx.userAssetIdFor({asset_id:'user:'+id,asset_src:'http://old:123?token=old'}),id);
    assert.equal(ctx.userAssetSource(id),'/speech-bubble-editor/user-assets/asset/'+id);
    assert.equal(ctx.userAssetIdFor({asset_id:'builtin'}),'');assert.equal(ctx.userAssetIdFor({user_asset_id:'../bad'}),'');scenarios++;
  }
  {
    const ctx={};vm.createContext(ctx);vm.runInContext(part(html,'    function rasterBytes(', '    function clearFrameSurfaceCacheForSource('),ctx);
    const cache=new Map(),a={width:2,height:2};ctx.lruSet(cache,'a',a,3,32);ctx.lruSet(cache,'b',a,3,32);ctx.lruSet(cache,'c',a,3,32);
    assert.equal(cache.size,2);assert.equal(cache.has('a'),false);
    const big={width:50,height:50};assert.equal(ctx.lruSet(cache,'big',big,3,32),big);assert.equal(cache.size,2);
    assert.equal(a.width,2);scenarios++;
  }
  console.log(`save_integrity_test: OK (${scenarios} behavioral scenarios)`);
})().catch(error=>{console.error(error);process.exitCode=1;});
