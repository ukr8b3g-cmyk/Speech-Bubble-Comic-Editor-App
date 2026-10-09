import json
from unittest.mock import patch
from PIL import Image
from desktop_app.localization import localized_error
from speech_bubble_editor import renderer


def test_dynamic_catalog_preserves_english_and_search(tmp_path):
    pack=tmp_path/'pack';pack.mkdir()
    Image.new('RGBA',(8,8)).save(pack/'asset.png')
    (pack/'manifest.json').write_text(json.dumps({'id':'test','items':[{
        'id':'external','label':'日本語','displayNameEn':'English name',
        'asset':'asset.png','keywords':'existing keyword','aliases':['別名'],'tags':['tag'],
    }]}),encoding='utf-8')
    renderer.get_sfx_asset_catalog.cache_clear()
    try:
        with patch.object(renderer,'_SFX_ASSET_ROOT',tmp_path):
            item=renderer.get_sfx_asset_catalog()['items'][0]
            assert item['displayNameEn']=='English name'
            assert all(term in item['keywords'] for term in ['日本語','existing keyword','別名','tag'])
    finally:
        renderer.get_sfx_asset_catalog.cache_clear()


def test_error_language_preserves_user_content():
    ja='出力フォルダーが存在しません。'
    assert localized_error(ja,'ja')==ja
    assert localized_error(ja,'en')=='The output folder does not exist.'
    assert localized_error('手入力の素材名','en')=='手入力の素材名'
