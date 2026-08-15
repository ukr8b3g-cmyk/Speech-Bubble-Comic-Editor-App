# Privacy Policy / プライバシー方針

## 日本語

Speech Bubble Comic Editor AppはWindows PC内でローカル動作します。本アプリには、テレメトリー、利用解析、広告、開発者運営サーバー、クラウド同期、および画像・レイアウト・プリセット・設定・診断情報の自動アップロード機能はありません。

ローカルには次の情報が保存されます。

- ホストの`config/speech-bubble-editor/`: レイアウト、User Presets、アセット、サムネイル、アーカイブ、プリセット設定、保存先記憶用情報
- ローカル設定ファイル: Speech Bubble Comic Editor Appの設定値
- ブラウザーのlocalStorage／IndexedDB: 下書き、単体画像、再表示用画像、UI状態、お気に入り、使用回数、診断結果
- ローカルのモデル保存先: ユーザーが取得を許可したAI背景削除モデル
- ユーザーが選択した出力先: 書き出した画像と任意のOverlay

AI背景削除は画像をWindows PC内で処理し、画像を外部へ送信しません。初回にユーザーが確認画面で許可した場合だけ、isnet-animeモデル（約168MB）をGitHub Releaseから取得します。Settingsからモデルを削除できます。

ユーザー操作によりGitHubや文書リンクを開く場合があります。ホストアプリ、ブラウザー、インストーラー、Git、GitHub自体が行うその他の通信は本方針の対象外です。

## English

Speech Bubble Comic Editor App runs locally on your Windows PC. It does not include telemetry, analytics, advertising, a developer-operated server, cloud synchronization, or automatic upload of images, layouts, presets, settings, or diagnostics.

The following data is stored locally:

- Host `config/speech-bubble-editor/`: layouts, user presets, assets, thumbnails, archives, preset settings, and export-directory memory
- Local settings file: Speech Bubble Comic Editor App settings
- Browser localStorage/IndexedDB: drafts, standalone and retained images, UI state, favorites, usage counts, and diagnostic results
- Local model storage: the AI background-removal model downloaded after user consent
- User-selected output location: exported images and optional overlays

AI background removal processes images locally on the Windows PC and does not upload them. Only after the user confirms the first-use prompt, the app downloads the isnet-anime model (about 168 MB) from a GitHub Release. The model can be removed from Settings.

GitHub or documentation links may open only after a user action. Other network activity performed by the host application, browser, installer, Git, or GitHub itself is outside this policy.
