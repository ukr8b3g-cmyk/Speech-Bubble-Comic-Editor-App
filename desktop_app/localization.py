"""Translate application-owned error messages without changing user content."""
import locale

ERROR_MESSAGES = {
    "画像サイズが大きすぎます。": "The image file is too large.",
    "出力フォルダーは絶対パスで指定してください。": "Use an absolute path for the output folder.",
    "出力フォルダーが存在しません。": "The output folder does not exist.",
    "出力先はフォルダーを指定してください。": "Choose a folder as the output destination.",
    "出力フォルダーへ書き込めません。": "The output folder is not writable.",
    "モデルのダウンロードをキャンセルしました。": "Model download cancelled.",
    "モデルのファイルサイズが一致しません。": "The model file size does not match.",
    "モデルのSHA-256が一致しません。": "The model SHA-256 does not match.",
    "ダウンロード中はモデルを削除できません。": "The model cannot be deleted during a download.",
    "背景削除モデルがありません。最初にモデルを取得してください。": "Download the background-removal model first.",
    "ONNX Runtimeを読み込めませんでした。": "Could not load ONNX Runtime.",
    "画像が空、またはサイズが大きすぎます。": "The image is empty or too large.",
    "画像を読み込めませんでした。": "Could not load the image.",
    "画像の解像度が大きすぎます。": "The image resolution is too large.",
}


def localized_error(message, language="auto"):
    if language == "auto":
        language = "ja" if str(locale.getlocale()[0] or "").lower().startswith("ja") else "en"
    if language != "en" or not isinstance(message, str):
        return message
    if message.startswith("モデルを取得できませんでした: "):
        detail = message.removeprefix("モデルを取得できませんでした: ")
        return "Could not download the model: " + ERROR_MESSAGES.get(detail, detail)
    return ERROR_MESSAGES.get(message, message)
