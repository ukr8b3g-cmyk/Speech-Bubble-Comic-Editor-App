"""Regressions for portable artwork, overlay exports and bounded image work."""
import asyncio
import hashlib
import io
import json
import threading
import zipfile
from pathlib import Path
from unittest import mock

import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from desktop_app.project_store import ProjectStore
from desktop_app.server import create_app
from desktop_app.settings_store import SettingsStore
from speech_bubble_editor import api
from speech_bubble_editor.image_cache import image_lru_cache
from speech_bubble_editor.user_assets import UserAssetStore
from test_desktop_core import current_layout, make_paths, png_data_url


def artwork():
    stream = io.BytesIO()
    Image.new('RGBA', (8, 6), (10, 20, 30, 128)).save(stream, format='PNG')
    data = stream.getvalue()
    return hashlib.sha256(data).hexdigest(), data


def rewrite_archive(path, mutate):
    with zipfile.ZipFile(path) as z:
        contents = {name: z.read(name) for name in z.namelist()}
    mutate(contents)
    with zipfile.ZipFile(path, 'w') as z:
        for name, data in contents.items():
            z.writestr(name, data)


def asset_payload(asset_id):
    element = {'id': 'stamp-1', 'type': 'sfx', 'asset_id': 'user:' + asset_id,
               'asset_src': f'http://127.0.0.1:9999/speech-bubble-editor/user-assets/asset/{asset_id}?token=old',
               'x': 5, 'y': 5, 'w': 8, 'h': 6, 'visible': False, 'text': '日本語は保持'}
    return {'layout': current_layout(single_elements=[element], general_elements=[dict(element)]), 'images': []}


def test_custom_artwork_round_trip_portable_without_presets(tmp_path):
    ident, data = artwork()
    store_a = UserAssetStore(tmp_path / 'a')
    store_a.restore_project_asset(ident, data)
    source = asset_payload(ident)
    before = json.dumps(source, ensure_ascii=False)
    path = tmp_path / 'portable.sbeproj'
    saved = ProjectStore(store_a).save(path, source)
    assert json.dumps(source, ensure_ascii=False) == before
    assert saved['manifest']['version'] == 1
    assert len(saved['manifest']['user_assets']) == 1
    with zipfile.ZipFile(path) as z:
        assert sum(n.startswith('user-assets/') for n in z.namelist()) == 1
        assert b'token=old' not in z.read('layout.json')
        assert b'127.0.0.1' not in z.read('layout.json')
    store_b = UserAssetStore(tmp_path / 'b')
    loaded = ProjectStore(store_b).load(path)
    assert loaded['missing_user_assets'] == []
    for item in loaded['user_assets']:
        store_b.restore_project_asset(item['id'], item['data'])
    assert store_b.asset_path(ident).read_bytes() == data
    assert not list((tmp_path / 'b').glob('*.json')), 'Do not overwrite/create gallery preset indexes'
    assert loaded['layout']['elements'][0]['text'] == '日本語は保持'


def test_missing_artwork_does_not_replace_existing_project(tmp_path):
    ident, _ = artwork()
    store = ProjectStore(UserAssetStore(tmp_path / 'assets'))
    path = tmp_path / 'keep.sbeproj'
    store.save(path, {'layout': current_layout(), 'images': []})
    before = path.read_bytes()
    with pytest.raises(ValueError, match='user asset is missing'):
        store.save(path, asset_payload(ident))
    assert path.read_bytes() == before


@pytest.mark.parametrize('damage', ['missing', 'checksum', 'manifest_id'])
def test_damaged_embedded_artwork_rejected(tmp_path, damage):
    ident, data = artwork()
    assets = UserAssetStore(tmp_path / 'assets')
    assets.restore_project_asset(ident, data)
    store = ProjectStore(assets)
    path = tmp_path / 'bad.sbeproj'
    saved = store.save(path, asset_payload(ident))
    entry = saved['manifest']['user_assets'][0]['path']
    def corrupt(contents):
        if damage == 'missing':
            del contents[entry]
        elif damage == 'checksum':
            other = io.BytesIO(); Image.new('RGBA', (8, 6), (0, 0, 0, 0)).save(other, format='PNG')
            contents[entry] = other.getvalue()
        else:
            value = json.loads(contents['manifest.json']); value['user_assets'][0]['id'] = 'a' * 64
            contents['manifest.json'] = json.dumps(value).encode()
    rewrite_archive(path, corrupt)
    with pytest.raises((ValueError, KeyError)):
        store.load(path)


def test_legacy_archive_without_artwork_is_readable_and_warns(tmp_path):
    ident, data = artwork()
    assets = UserAssetStore(tmp_path / 'a'); assets.restore_project_asset(ident, data)
    path = tmp_path / 'legacy.sbeproj'
    ProjectStore(assets).save(path, asset_payload(ident))
    def legacy(contents):
        manifest = json.loads(contents['manifest.json']); manifest.pop('user_assets')
        contents['manifest.json'] = json.dumps(manifest).encode()
        for name in list(contents):
            if name.startswith('user-assets/'): del contents[name]
    rewrite_archive(path, legacy)
    old_bytes = path.read_bytes()
    loaded = ProjectStore(UserAssetStore(tmp_path / 'b')).load(path)
    assert loaded['missing_user_assets'] == [ident]
    assert path.read_bytes() == old_bytes


def test_project_open_restores_artwork_using_current_server_token(tmp_path, monkeypatch):
    ident, data = artwork(); assets = UserAssetStore(tmp_path / 'source')
    assets.restore_project_asset(ident, data)
    path = tmp_path / 'portable.sbeproj'; ProjectStore(assets).save(path, asset_payload(ident))
    monkeypatch.setenv('SPEECH_BUBBLE_DESKTOP_DATA_ROOT', str(tmp_path))
    app = create_app(make_paths(tmp_path / 'destination'), 'new-token')
    with TestClient(app) as client:
        result = client.post('/desktop/project/open', json={'path': str(path)}, headers={'X-SBE-Token': 'new-token'})
        assert result.status_code == 200, result.text
        assert 'user_assets' not in result.json(), 'Binary blobs stay server-side'
        route = result.json()['layout']['elements'][0]['asset_src']
        assert client.get(route + '?token=new-token').content == data
        assert client.get(route + '?token=old').status_code == 403


@pytest.mark.parametrize('fmt', ['png', 'jpeg', 'webp'])
@pytest.mark.parametrize('enabled', [False, True])
def test_overlay_saved_for_all_formats(tmp_path, monkeypatch, fmt, enabled):
    monkeypatch.setenv('SPEECH_BUBBLE_DESKTOP_DATA_ROOT', str(tmp_path))
    paths = make_paths(tmp_path)
    SettingsStore(paths.settings).save({'save_overlay': enabled, 'output_format': fmt, 'supersample': 1})
    app = create_app(paths, 'token')
    with TestClient(app) as client:
        redirect = client.get('/', follow_redirects=False)
        assert ('saveOverlay=1' if enabled else 'saveOverlay=0') in redirect.headers['location']
        payload = {'render_mode': 'browser_canvas_v1', 'layout_json': json.dumps({'canvas': {'width': 2, 'height': 2}, 'elements': []}),
                   'composite_data_url': png_data_url(), 'overlay_data_url': png_data_url(),
                   'desktop_output_dir': str(tmp_path), 'name': 'overlay-test'}
        response = client.post('/speech-bubble-editor/export', json=payload, headers={'X-SBE-Token': 'token'})
        assert response.status_code == 200, response.text
        result = response.json()
        assert bool(result['overlay_filename']) is enabled
        assert (tmp_path / result['filename']).is_file()
        if enabled:
            with Image.open(tmp_path / result['overlay_filename']) as image:
                assert image.format == 'PNG' and image.size == (2, 2)
        else:
            assert not list(tmp_path.glob('*_overlay.png'))


def test_large_header_rejected_before_pixel_decode():
    source = mock.MagicMock()
    source.__enter__.return_value = source
    source.width, source.height = 20000, 20000
    with mock.patch.object(api.Image, 'open', return_value=source):
        with pytest.raises(ValueError, match='dimensions'):
            api._decode_image_bytes(b'header')
    source.load.assert_not_called()
    source.convert.assert_not_called()


def test_export_does_not_block_event_loop(tmp_path, monkeypatch):
    monkeypatch.setenv('SPEECH_BUBBLE_DESKTOP_DATA_ROOT', str(tmp_path))
    app = create_app(make_paths(tmp_path), 'token')
    entered, release = threading.Event(), threading.Event()
    original = api._browser_canvas_export
    def delayed(*args):
        entered.set()
        assert release.wait(5)
        return original(*args)
    monkeypatch.setattr(api, '_browser_canvas_export', delayed)
    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://local', headers={'X-SBE-Token': 'token'}) as client:
            payload = {'render_mode': 'browser_canvas_v1', 'layout_json': '{"canvas":{"width":2,"height":2},"elements":[]}',
                       'composite_data_url': png_data_url(), 'desktop_output_dir': str(tmp_path)}
            task = asyncio.create_task(client.post('/speech-bubble-editor/export', json=payload))
            try:
                assert await asyncio.to_thread(entered.wait, 2)
                health = await asyncio.wait_for(client.get('/desktop/health'), 1)
                assert health.status_code == 200
            finally:
                release.set()
            assert (await task).status_code == 200
    asyncio.run(scenario())


def test_byte_lru_budget_aliases_and_clear():
    calls = []
    @image_lru_cache(max_entries=3, max_bytes=32)
    def image(key, width=2):
        calls.append(key)
        return Image.new('RGBA', (width, 2), (7, 8, 9, 255))
    retained = image('a'); image('b'); image('a'); image('c')
    assert image.cache_info().bytes == 32 and image.cache_info().entries == 2
    assert image('a') is retained
    image('b')
    assert calls.count('b') == 2
    oversized = image('big', 20)
    assert image.cache_info().bytes <= 32
    image.cache_clear()
    assert image.cache_info().bytes == 0 and image.cache_info().entries == 0
    assert retained.getpixel((0, 0)) == oversized.getpixel((0, 0)) == (7, 8, 9, 255)
