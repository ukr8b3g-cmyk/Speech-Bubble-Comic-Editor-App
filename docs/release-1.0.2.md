# Speech Bubble Comic Editor App v1.0.2 — Windows x64

Manga Finishを既存の「コミック変換」に追加し、レイヤーパネルの見出し表示を修正しました。一枚画像・4コマ漫画・コミックの3ワークスペースと、既存の`.sbeproj`形式の互換性を維持しています。公開済みv1.0.1とその配布ファイルは変更せず、そのまま残しています。

## 変更内容

- **2026-10-18 再配布:** 画面左上とページタイトルに残っていた1.0.1表記を1.0.2へ修正しました。配布前の自動検証に画面のバージョン一致チェックを追加し、EXE・ZIP・SHA-256を更新しています。v1.0.2のソースタグも修正後のコミットへ更新し、v1.0.1は変更していません。

- **Manga Finish:** MangaScreen / Mangazin由来の線画・黒ベタ・トーン・45度網点による漫画仕上げを追加。既存のコミック変換画面内で使用できます。OpenCVによるローカルCPU処理で、AIモデルやGPUは不要です。
- **6プリセット:** 標準、線画くっきり、柔らかいトーン、黒ベタ強調、細密スクリーン、なめらかグレー。標準はMangaScreen本来の既定値に合わせ、階調の保持は1.0です。各パラメーターの調整、カスタム表示、プリセットへのリセットに対応します。
- **表示順:** 単純グレースケール → Manga Finish → 白黒コミック → 単純モノクロ → XDoG 100 → カスタム。初期選択は従来どおり単純グレースケールです。
- **原寸確認:** 長辺768pxの自動プレビューに加え、原寸確認と100%表示を用意。同じ変換元・設定では、確認済みの原寸PNGを適用に再利用します。
- **元画像の保持:** 一枚画像では新しい画像レイヤー、4コマ／コミックではPage Imagesへ追加します。従来の白黒変換・XDoG設定とは独立しています。
- **レイヤー見出し:** 狭いパネルでも「レイヤー」を横一行に保ち、操作ボタンを必要に応じて次の行へ折り返します。
- **ライセンス:** `Copyright (c) 2026 ashukae`とMITライセンス全文を`THIRD-PARTY-NOTICES.md`および`_internal/licenses/MangaScreen-MIT.txt`へ同梱。OpenCVのライセンス表記も配布物に含めます。

## ダウンロード

- [Windows Installer EXE](https://github.com/ukr8b3g-cmyk/Speech-Bubble-Comic-Editor-App/releases/download/v1.0.2/SpeechBubbleComicEditorApp-v1.0.2-win-x64-setup.exe)
- [Portable ZIP](https://github.com/ukr8b3g-cmyk/Speech-Bubble-Comic-Editor-App/releases/download/v1.0.2/SpeechBubbleComicEditorApp-v1.0.2-win-x64-portable.zip)
- [SHA-256チェックサム](https://github.com/ukr8b3g-cmyk/Speech-Bubble-Comic-Editor-App/releases/download/v1.0.2/SHA256SUMS.txt)
- [以前のv1.0.1](https://github.com/ukr8b3g-cmyk/Speech-Bubble-Comic-Editor-App/releases/tag/v1.0.1)

通常利用はInstaller EXEを実行してください。ZIP版は展開後に`SpeechBubbleComicEditorApp.exe`を起動します。セットアップの圧縮はv1.0.1と同じ`lzma2`・Solid圧縮です。フォントや編集環境の違いに備え、大切なプロジェクトは更新前にバックアップしてください。

## 検証と制限

ローカルではPython回帰テスト38件、JavaScript回帰スクリプト25本、Chromeでの3ワークスペース操作、原寸PNGの適用、コミックのUndo / Redo、プロジェクト保存・再読込を確認しました。レイヤー見出しは日英・幅240～360pxで確認しています。

Windows CIはPython・JavaScript回帰テスト、同じビルドからのInstaller／ZIP作成、SHA-256検証、ZIP内のMIT／OpenCVライセンスとソース資産の照合、配布EXEの自己検証を通してから公開します。

Manga Finishの入力上限は64MiB・2,000万画素・各辺8192px、同時処理は1件です。縮小プレビューでは網点にざらつきやモアレが見える場合があるため、適用前に原寸確認を使用してください。キャンセル後も実行中CPU処理が終わるまで待つ場合があります。

クリーンWindowsでのインストール／更新／アンインストール、ネイティブファイル選択、WebView2での一連の編集操作は今回の自動検証に含みません。フォントはプロジェクトへ埋め込みません。
