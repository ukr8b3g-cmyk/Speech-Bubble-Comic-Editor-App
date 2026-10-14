"""Real Desktop HTTP + Chromium; native pickers are deterministic test bridges.

Run with an installed Playwright/Chromium. Does not exercise native WebView2,
ONNX inference, or the Windows installer.
"""
from pathlib import Path
import json
import os
import socket
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests' / 'desktop')]
import uvicorn
from playwright.sync_api import sync_playwright
from desktop_app.server import create_app
from desktop_app.settings_store import SettingsStore
from desktop_app.project_store import ProjectStore
from speech_bubble_editor.user_assets import UserAssetStore
from test_desktop_core import current_layout, make_paths
from test_save_integrity import artwork, asset_payload


def main():
    observations = []
    with tempfile.TemporaryDirectory(prefix='sbe-browser-') as temporary:
        root = Path(temporary)
        paths = make_paths(root / 'data')
        SettingsStore(paths.settings).save({'language': 'en', 'startup_behavior': 'new', 'auto_save': False,
                                           'auto_export_to_directory': True, 'export_directory': str(root), 'save_overlay': True})
        other = root / 'other.sbeproj'
        ProjectStore().save(other, {'title':'OTHER', 'layout': current_layout(single_elements=[
            {'id':'original-text','type':'text','text':'Other document','x':10,'y':10,'w':240,'h':100}]), 'images': []})
        ident, data = artwork(); original_assets = UserAssetStore(root / 'original-assets')
        original_assets.restore_project_asset(ident, data)
        stamp_path = root / 'stamp.sbeproj'
        stamp_payload = asset_payload(ident)
        for workspace in stamp_payload['layout']['workspaces'].values():
            for item in workspace['elements']: item['visible']=True
        stamp_payload['layout']['elements'][0]['visible']=True
        ProjectStore(original_assets).save(stamp_path, stamp_payload)
        app = create_app(paths, 'test-launch-token')
        listener = socket.socket(); listener.bind(('127.0.0.1',0)); listener.listen(128)
        port=listener.getsockname()[1]
        server=uvicorn.Server(uvicorn.Config(app, log_level='error'))
        thread=threading.Thread(target=server.run, kwargs={'sockets':[listener]}, daemon=True);thread.start()
        for _ in range(100):
            if server.started: break
            time.sleep(.05)
        assert server.started
        try:
            with sync_playwright() as pw:
                executable=os.environ.get('SBE_CHROMIUM_EXECUTABLE') or ('/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else None)
                browser=pw.chromium.launch(headless=True, **({'executable_path':executable} if executable else {}))
                page=browser.new_page(viewport={'width':1440,'height':1000})
                errors=[]; page.on('pageerror', lambda err:errors.append(str(err)))
                page.add_init_script('''window.__openPath="";window.__savePath="";
                  window.pywebview={api:{choose_project_open:async()=>window.__openPath,choose_project_save:async()=>window.__savePath,
                  main_update:async()=>true,save_window_state:async()=>true}};''')
                page.goto(f'http://127.0.0.1:{port}/',wait_until='networkidle')
                page.wait_for_function('!!window.SpeechBubbleDesktopEditor && !!window.SpeechBubbleDesktopShell')
                def snapshot(): return page.evaluate('window.SpeechBubbleDesktopEditor.snapshot()')
                def load(path):
                    payload=page.request.post(f'http://127.0.0.1:{port}/desktop/project/open', headers={'X-SBE-Token':'test-launch-token'},data={'path':str(path)})
                    assert payload.ok,payload.text()
                    page.evaluate('(p)=>window.SpeechBubbleDesktopEditor.loadProject(p)',payload.json())
                def open_later(path):
                    page.evaluate('p=>{window.__openPath=p;window.__openResult="pending";window.SpeechBubbleDesktopShell.openProject().then(v=>window.__openResult=v===false?"cancelled":"opened").catch(e=>window.__openResult="error:"+e.message)}',str(path))
                load(other)
                page.locator('#addText').click()
                before=snapshot()
                assert page.evaluate('window.SpeechBubbleDesktopEditor.hasUnsavedChanges()')
                open_later(other)
                page.locator('dialog[open] button[value=cancel]').click()
                page.wait_for_function('window.__openResult==="cancelled"')
                after=snapshot();assert after['layout']==before['layout'] and after['document_id']==before['document_id']
                assert not page.locator('#undo').is_disabled()
                observations.append('Open cancelled: layout, document identity and Undo retained')

                open_later(other)
                page.locator('dialog[open] button[value=save]').click()  # native save picker returns empty
                page.wait_for_function('window.__openResult==="cancelled"')
                assert snapshot()['layout']==before['layout']
                observations.append('Save & Open: cancelled save preserves document')

                broken=root/'broken.sbeproj';broken.write_bytes(b'not-a-project')
                open_later(broken)
                page.wait_for_function('window.__openResult.startsWith("error:")')
                assert snapshot()['layout']==before['layout']
                observations.append('Invalid project: no replacement')
                open_later(other);page.locator('dialog[open] button[value=discard]').click()
                page.wait_for_function('window.__openResult==="opened"')
                assert snapshot()['layout']['elements'][0]['text']=='Other document'
                assert not page.evaluate('window.SpeechBubbleDesktopEditor.hasUnsavedChanges()')
                observations.append('Discard & Open: validated document replaces once')

                page.locator('#addText').click()
                captured=[]
                page.route('**/layout/**',lambda route:captured.append(route) if route.request.method=='PUT' else route.continue_())
                page.locator('#saveLayout').click()
                page.wait_for_timeout(100);assert len(captured)==1
                sent=json.loads(captured[0].request.post_data)['layout_json']
                page.locator('#addText').click()
                newer=snapshot()['layout']
                assert newer!=json.loads(sent)
                captured.pop().continue_()
                page.wait_for_function('!document.getElementById("saveLayout").disabled')
                assert page.evaluate('window.SpeechBubbleDesktopEditor.hasUnsavedChanges()')
                assert snapshot()['layout']==newer
                page.unroute('**/layout/**')
                observations.append('Layout save race: later edit remains dirty and intact')

                page.locator('#saveLayout').click()
                page.wait_for_function('!document.getElementById("saveLayout").disabled')
                assert page.evaluate('window.SpeechBubbleDesktopEditor.hasUnsavedChanges()'), 'Layout is not the project file'
                assert 'project file not updated' in page.locator('#saveState').inner_text().lower()
                observations.append('Layout/project saved states remain distinct')

                page.evaluate('p=>window.__savePath=p',str(root/'saved.sbeproj'))
                assert page.evaluate('window.SpeechBubbleDesktopShell.saveProject()')
                assert not page.evaluate('window.SpeechBubbleDesktopEditor.hasUnsavedChanges()')
                before=snapshot()['layout']
                changed=page.evaluate('''()=>{const m=JSON.parse(window.SpeechBubblePaletteSync.snapshot());
                    const s=JSON.parse(m.scene);s.workspaces[s.activeWorkspace].elements[0].text="Palette edit";
                    m.scene=JSON.stringify(s);m.sender="test-palette";m.sequence=1;
                    return window.SpeechBubblePaletteSync.apply(JSON.stringify(m));}''')
                assert changed and page.evaluate('window.SpeechBubbleDesktopEditor.hasUnsavedChanges()')
                page.locator('#undo').click()
                assert snapshot()['layout']==before
                observations.append('Detached palette protocol: dirty, Undo, no document loss')

                captured=[]
                page.route('**/desktop/project/save',lambda route:captured.append(route))
                page.evaluate('()=>{window.__saveResult="pending";window.SpeechBubbleDesktopShell.saveProject().then(()=>window.__saveResult="saved").catch(e=>window.__saveResult=e.message)}')
                page.wait_for_timeout(100);assert len(captured)==1
                page.locator('#addText').click();newer=snapshot()['layout'];captured.pop().continue_()
                page.wait_for_function('window.__saveResult!=="pending"')
                assert 'unsaved' in page.evaluate('window.__saveResult')
                assert snapshot()['layout']==newer and page.evaluate('window.SpeechBubbleDesktopEditor.hasUnsavedChanges()')
                page.unroute('**/desktop/project/save')
                observations.append('Project save race: later edit not acknowledged')

                # Open archive into a store without source presets and export actual artwork.
                load(stamp_path)
                page.locator('#exportImage').click()
                page.wait_for_function('!document.getElementById("exportImage").disabled')
                page.wait_for_timeout(250)
                overlays=list(root.glob('*_overlay.png'));assert overlays, page.locator('#saveState').inner_text()
                from PIL import Image
                with Image.open(overlays[-1]) as im:
                    assert im.getbbox() is not None, 'Custom stamp must be present in Overlay'
                observations.append('Portable custom artwork renders with new server token; Overlay written')
                # A stale palette message cannot replace a newly opened document.
                assert page.evaluate('''()=>window.SpeechBubblePaletteSync.apply(JSON.stringify({version:1,documentId:"old-doc",sender:"test-palette",sequence:99,scene:"{}"}))''') is False
                observations.append('Stale palette document rejected')
                assert not errors, errors
                print(json.dumps({'passed':len(observations),'observations':observations,'page_errors':errors,
                                  'scope':'Chromium + real Desktop HTTP; native pickers stubbed'}, ensure_ascii=False,indent=2))
                browser.close()
        finally:
            server.should_exit=True;thread.join(10);listener.close()
            assert not thread.is_alive()

if __name__=='__main__': main()
