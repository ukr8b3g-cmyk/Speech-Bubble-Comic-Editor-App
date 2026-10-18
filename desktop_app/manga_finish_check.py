"""Explicit, headless distribution check; creates no desktop state or services."""
from pathlib import Path
from io import BytesIO
import hashlib
import json

def run_check(report_path):
    from .manga_finish import convert_image, MangaFinishSettings
    from PIL import Image
    import numpy as np
    import cv2
    raw=BytesIO()
    Image.new('RGBA',(129,131),(100,130,160,123)).save(raw,format='PNG')
    result=convert_image(raw.getvalue(),MangaFinishSettings())
    pixels=np.asarray(Image.open(BytesIO(result.png)))
    ok=pixels.shape==(131,129,4) and bool(np.all(pixels[:,:,3]==123))
    Path(report_path).write_text(json.dumps({'ok':ok,'opencv':cv2.__version__,
        'pixels_sha256':hashlib.sha256(pixels.tobytes()).hexdigest(),
        'width':result.width,'height':result.height},indent=2),encoding='utf-8')
    return 0 if ok else 1
