# Manga Finish — 実装と検証

既存の「コミック変換」への同居実装です。独立したウィンドウやアプリは追加せず、一枚画像・4コマ・コミックの3ワークスペースと`.sbeproj`の形式を維持します。v1.0.2で追加しました。公開済み1.0.1配布物にはManga Finishを含みません。

## 最終設定

変換モードは「単純グレースケール → Manga Finish → 白黒コミック → 単純モノクロ → XDoG 100 → カスタム」の順です。初期選択は単純グレースケールです。

仕様v1.1実装後の調整として、標準だけ階調の保持を0.8からMangaScreen本来の既定値1.0へ変更しました。ほかの5プリセットは変更していません。UIとプリセットの正本は[`web/manga-finish-settings.js`](../web/manga-finish-settings.js)、API既定値と入力検証は[`desktop_app/manga_finish.py`](../desktop_app/manga_finish.py)です。

| プリセット | 網点密度 | 白の基準 | 黒ベタの基準 | 薄いトーン | 濃いトーン | 階調の保持 | 白線 | 45度網点 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 標準 | 200 | 0.80 | 0.30 | 0.18 | 0.42 | 1.00 | ON | ON |
| 線画くっきり | 200 | 0.76 | 0.35 | 0.15 | 0.45 | 0.55 | ON | ON |
| 柔らかいトーン | 180 | 0.78 | 0.26 | 0.12 | 0.32 | 0.95 | ON | ON |
| 黒ベタ強調 | 180 | 0.84 | 0.46 | 0.22 | 0.56 | 0.60 | ON | ON |
| 細密スクリーン | 280 | 0.80 | 0.30 | 0.18 | 0.42 | 0.75 | ON | ON |
| なめらかグレー | 200 | 0.80 | 0.30 | 0.18 | 0.42 | 0.95 | ON | OFF |

| 項目 | API名 | 入力範囲 |
| --- | --- | --- |
| 網点密度 | `screen_lines` | 整数80～400（画像幅に対する線数） |
| 白の基準 | `white_point` | 0.45～0.95 |
| 黒ベタの基準 | `black_point` | 0.05～0.70 |
| 薄いトーン | `light_tone` | 0.02～0.50 |
| 濃いトーン | `dark_tone` | 0.20～0.85 |
| 階調の保持 | `gradation` | 0～1 |
| 黒ベタ内の白線 | `white_lines` | Boolean |
| 45度網点 | `halftone` | Boolean |

白の基準は黒ベタの基準より0.02以上大きく、薄いトーンは濃いトーン以下にする必要があります。数値を調整するとカスタムになり、元のプリセットへのリセットができます。旧版の保存値は、未調整の標準0.8だけを1.0へ移行します。カスタム0.8やほかのプリセットは維持します。

## 処理と保存

- Python / OpenCVによるCPU処理。`opencv-python-headless==4.13.0.92`をDesktop依存関係に含め、Windowsビルドへ同梱します。
- `POST /desktop/comic-conversion/manga-finish`へ画像本体を送信し、設定はクエリーで指定します。Desktopの既存トークン認証を使用し、PNGを返します。
- 自動プレビューは長辺768px、原寸確認・適用は元解像度。原寸結果は変換元・設定・編集先が一致する場合に再利用します。
- 入力はPNG / JPEG / WebP / BMPの静止画。最大64MiB、2,000万画素、各辺8192px。EXIF回転を反映し、アルファを保持します。
- 処理受付は同時1件、待機キューなし。設定不正は422、容量超過は413、処理中は429、処理機能を読み込めない場合は503です。
- キャンセルで結果の適用を止めます。実行中CPU処理の強制停止は行わず、終了まで受付枠を保持します。画面や変換元の切替後に古い結果を適用しません。
- 256pxタイルと画像全体の座標で網点を生成します。枠線・紙色・余白の処理は移植していません。
- 一枚画像では新しい画像レイヤー、4コマ／コミックでは新しいPage Imageとして追加します。元画像、従来の白黒変換設定、XDoG設定は保持します。

## 確認方法

リポジトリのルートで実行します。ソース起動の環境は`setup_and_start.cmd`で作成できます。

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-desktop.txt
.\.venv\Scripts\python.exe -m compileall -q desktop_app speech_bubble_editor desktop_launcher.py
.\.venv\Scripts\python.exe -m pytest tests -q
node --check web/comic-converter.js
node --check web/manga-finish-settings.js
node tests/manga_finish_settings_test.cjs
node tests/comic_converter_integration_test.cjs
```

テスト実行には`pytest`とNode.jsが必要です。既存のGitHub Actionsは`tests`以下のPythonテストと`*test.cjs`を列挙するため、Manga Finishの追加テストも対象です。

配布EXEでは次の自己検証を使用できます。UIやテストサーバーは起動せず、合成RGBA画像を変換した結果を指定先のJSONへ保存します。書き込み可能な絶対パスを指定してください。

```powershell
.\SpeechBubbleComicEditorApp.exe --manga-finish-self-test C:\Temp\manga-finish-check.json
```

通常のWindowsビルドは既存の`build_release.ps1 -Version "1.0.2"`を使用します。公開済み1.0.1の配布物は置換せず、v1.0.2を別Releaseで公開します。

## ローカル確認済みの範囲

- Python回帰テスト38件、Node.js回帰スクリプト25本。
- 網点生成の原方式との比較、および標準1.0と固定したMangaScreen実装の合成画像比較で画素差0。すべての入力画像に対する画素一致や画質を保証する試験ではありません。
- Chromeの分離したテスト環境で、3ワークスペース、6プリセット、カスタム／リセット、原寸PNGの適用と再利用、コミックのUndo / Redo、`.sbeproj`保存・再読込を確認。
- 最終表示順、初期選択が単純グレースケールであること、標準の階調1.0、従来変換への切替を確認。
- ローカルEXE・ZIP・セットアップを作成。配布EXEの自己検証、同梱Web資産とソースの一致、OpenCVのライセンス同梱を確認。

Windows CPUでの処理全体の予備測定では、4096×4096が約19.4秒・最大約1085MiB、5000×4000が約41.8秒・約1305MiBでした。測定環境・画像・設定に依存し、網点部分だけの旧Linuxベンチマークとは比較条件が異なります。

v1.0.2はWindows CIで回帰テスト・配布物・ライセンス同梱・EXE自己検証を行い、成功後に公開します。クリーンWindowsでのインストール／更新／アンインストール、WebView2での一連の編集操作は未確認です。変更点は[リリースノート](release-1.0.2.md)を参照してください。

## 出典

[MangaScreen](https://github.com/ashukae/ComfyUI-MangaScreen)と[Mangazin](https://github.com/arthur-cma/Mangazin)を出典とします。著作権表示とMITライセンス全文は[`THIRD-PARTY-NOTICES.md`](../THIRD-PARTY-NOTICES.md#manga-finish)に含め、Windows配布物にも同梱します。
