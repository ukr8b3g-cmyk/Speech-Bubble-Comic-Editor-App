from __future__ import annotations

import hashlib
import os
import re
import struct
from functools import lru_cache
from pathlib import Path

from PIL import ImageFont

try:
    from fontTools.ttLib import TTFont
except ImportError:
    TTFont = None

_PREFERRED_FONTS = (
    "meiryo", "yu gothic", "noto sans cjk jp", "noto sans jp", "hiragino",
    "segoe ui", "arial", "helvetica", "times new roman", "dejavu sans",
    "liberation sans",
)

_FONT_LANGUAGE_META = {
    "ja": {"label": "日本語", "sample": "文字もじモジ"},
    "zh-hans": {"label": "简体中文", "sample": "字体示例"},
    "zh-hant": {"label": "繁體中文", "sample": "字體範例"},
    "ko": {"label": "한국어", "sample": "서체견본"},
    "latin": {"label": "Latin", "sample": "Sample Aa"},
    "arabic": {"label": "العربية", "sample": "أبجدية"},
    "hebrew": {"label": "עברית", "sample": "אבגדה"},
    "devanagari": {"label": "देवनागरी", "sample": "अक्षर"},
    "emoji": {"label": "Emoji", "sample": "😀 ★ ♪"},
    "symbol": {"label": "Symbols", "sample": "● ◆ ♪"},
    "other": {"label": "Other", "sample": "Sample"},
}

_FONT_LANGUAGE_HINTS = {
    "emoji": ("emoji", "color emoji"),
    "symbol": ("wingdings", "webdings", "symbol", "dingbat"),
    "ja": ("japanese", " cjk jp", " jp ", "meiryo", "yu gothic", "yu mincho", "ms gothic", "ms mincho", "biz ud", "hiragino", "kozuka", "ipaex", "ipagothic", "ipamincho"),
    "ko": ("korean", " cjk kr", " kr ", "malgun", "gulim", "dotum", "batang", "gungsuh", "nanum", "noto sans kr", "noto serif kr"),
    "zh-hans": ("simplified chinese", " cjk sc", " sc ", "hans", "simsun", "simhei", "simkai", "simfang", "microsoft yahei", "dengxian", "fangsong", "kaiti", "noto sans sc", "noto serif sc"),
    "zh-hant": ("traditional chinese", " cjk tc", " tc ", "hant", "mingliu", "microsoft jhenghei", "dfkai", "noto sans tc", "noto serif tc"),
    "arabic": ("arabic", "andalus", "sakkal", "urdu", "quran", "scheherazade"),
    "hebrew": ("hebrew", "aharoni", "david clm", "frank ruehl", "miriam", "nachlieli"),
    "devanagari": ("devanagari", "mangal", "kokila", "aparajita", "utsaah"),
}


def _font_roots():
    roots = []
    if os.name == "nt":
        roots.extend([
            Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Windows/Fonts",
        ])
    elif os.sys.platform == "darwin":
        roots.extend([Path("/System/Library/Fonts"), Path("/Library/Fonts"), Path.home() / "Library/Fonts"])
    else:
        roots.extend([
            Path("/usr/share/fonts"), Path("/usr/local/share/fonts"),
            Path.home() / ".fonts", Path.home() / ".local/share/fonts",
        ])
    return [root for root in roots if root.is_dir()]


def _glyph_signature(font, character):
    mask = font.getmask(character)
    return mask.size, bytes(mask)


def _font_supports(font, character, missing_signature):
    try:
        return _glyph_signature(font, character) != missing_signature
    except (OSError, ValueError):
        return False


def _font_name_table_text(path, name_ids):
    if TTFont is None:
        return None
    try:
        table = TTFont(str(path), lazy=True)["name"]
    except Exception:
        return None
    records = []
    for record in table.names:
        if record.nameID not in name_ids:
            continue
        try:
            value = record.toUnicode().strip()
        except Exception:
            continue
        if not value or value.count("?") * 2 >= len(value):
            continue
        language_rank = 0 if record.langID in {0x411, 0x409} else 1
        platform_rank = 0 if record.platformID == 3 else 1 if record.platformID == 0 else 2
        records.append((language_rank, platform_rank, value))
    return min(records, default=(None, None, None))[2]


def _font_display_names(path, fallback_family, fallback_style):
    def clean(value, fallback):
        text = str(value or "").strip()
        if not text or "??" in text or "\ufffd" in text:
            text = str(fallback or "").strip()
        return text

    family = clean(_font_name_table_text(path, (16, 1)), fallback_family)
    if not family or "??" in family or "\ufffd" in family:
        family = Path(path).stem
    style = clean(_font_name_table_text(path, (17, 2)), fallback_style)
    if not style or "??" in style or "\ufffd" in style:
        style = "Regular"
    return family, style


def _font_cmap_is_browser_safe(path):
    """Reject cmap references that Chromium's OpenType Sanitizer will refuse."""
    try:
        data = Path(path).read_bytes()
        if len(data) < 12 or data[:4] == b"ttcf":
            return True
        table_count = struct.unpack_from(">H", data, 4)[0]
        tables = {}
        for index in range(table_count):
            record = 12 + index * 16
            if record + 16 > len(data):
                return False
            tag, _checksum, offset, length = struct.unpack_from(">4sIII", data, record)
            if offset + length > len(data):
                return False
            tables[tag] = (offset, length)
        if b"cmap" not in tables or b"maxp" not in tables:
            return False
        maxp_offset, maxp_length = tables[b"maxp"]
        if maxp_length < 6:
            return False
        glyph_count = struct.unpack_from(">H", data, maxp_offset + 4)[0]
        cmap_offset, cmap_length = tables[b"cmap"]
        if cmap_length < 4:
            return False
        subtable_count = struct.unpack_from(">H", data, cmap_offset + 2)[0]
        checked_offsets = set()
        for index in range(subtable_count):
            record = cmap_offset + 4 + index * 8
            if record + 8 > cmap_offset + cmap_length:
                return False
            subtable_relative = struct.unpack_from(">I", data, record + 4)[0]
            subtable = cmap_offset + subtable_relative
            if subtable in checked_offsets:
                continue
            checked_offsets.add(subtable)
            if subtable + 2 > cmap_offset + cmap_length:
                return False
            font_format = struct.unpack_from(">H", data, subtable)[0]
            if font_format == 4:
                if subtable + 14 > len(data):
                    return False
                length = struct.unpack_from(">H", data, subtable + 2)[0]
                segment_count_x2 = struct.unpack_from(">H", data, subtable + 6)[0]
                segment_count = segment_count_x2 // 2
                if not segment_count or segment_count_x2 % 2 or subtable + length > len(data):
                    return False
                end_codes = subtable + 14
                start_codes = end_codes + segment_count * 2 + 2
                deltas = start_codes + segment_count * 2
                range_offsets = deltas + segment_count * 2
                if range_offsets + segment_count * 2 > subtable + length:
                    return False
                for segment in range(segment_count):
                    start = struct.unpack_from(">H", data, start_codes + segment * 2)[0]
                    end = struct.unpack_from(">H", data, end_codes + segment * 2)[0]
                    delta = struct.unpack_from(">h", data, deltas + segment * 2)[0]
                    range_offset = struct.unpack_from(">H", data, range_offsets + segment * 2)[0]
                    if start > end:
                        return False
                    for codepoint in range(start, end + 1):
                        if range_offset:
                            glyph_position = range_offsets + segment * 2 + range_offset + (codepoint - start) * 2
                            if glyph_position + 2 > subtable + length:
                                return False
                            glyph = struct.unpack_from(">H", data, glyph_position)[0]
                            if glyph:
                                glyph = (glyph + delta) & 0xFFFF
                        else:
                            glyph = (codepoint + delta) & 0xFFFF
                        if glyph and glyph >= glyph_count:
                            return False
            elif font_format in {12, 13}:
                if subtable + 16 > len(data):
                    return False
                length = struct.unpack_from(">I", data, subtable + 4)[0]
                group_count = struct.unpack_from(">I", data, subtable + 12)[0]
                if subtable + length > len(data) or subtable + 16 + group_count * 12 > subtable + length:
                    return False
                for group in range(group_count):
                    start, end, glyph = struct.unpack_from(">III", data, subtable + 16 + group * 12)
                    maximum = glyph if font_format == 13 else glyph + (end - start)
                    if start > end or (maximum and maximum >= glyph_count):
                        return False
        return True
    except (OSError, ValueError, struct.error):
        return False


def _font_language(family, style, font):
    searchable = f" {family} {style} ".lower()
    for language in ("emoji", "symbol", "ja", "ko", "zh-hans", "zh-hant", "arabic", "hebrew", "devanagari"):
        if any(hint in searchable for hint in _FONT_LANGUAGE_HINTS[language]):
            return language
    if re.search(r"[\u3040-\u30ff]", family):
        return "ja"
    if re.search(r"[\uac00-\ud7af]", family):
        return "ko"
    try:
        missing = _glyph_signature(font, chr(0x10FFFF))
    except (OSError, ValueError):
        return "other"
    supports = lambda character: _font_supports(font, character, missing)
    if supports("한"): return "ko"
    if supports("あ") and supports("ア"): return "ja"
    if supports("汉"): return "zh-hans"
    if supports("漢"): return "zh-hant"
    if supports("अ"): return "devanagari"
    if supports("ا") and not supports("A"): return "arabic"
    if supports("א") and not supports("A"): return "hebrew"
    if supports("A"): return "latin"
    return "other"


@lru_cache(maxsize=1)
def system_fonts():
    fonts = []
    seen = set()
    for root in _font_roots():
        for path in root.rglob("*"):
            if path.suffix.lower() not in {".ttf", ".otf", ".ttc", ".otc"}:
                continue
            try:
                normalized = str(path.resolve())
            except OSError:
                continue
            if normalized.lower() in seen:
                continue
            seen.add(normalized.lower())
            try:
                font = ImageFont.truetype(normalized, 12)
                fallback_family, fallback_style = font.getname()
            except (OSError, ValueError):
                continue
            if not _font_cmap_is_browser_safe(normalized):
                continue
            family, style = _font_display_names(normalized, fallback_family, fallback_style)
            name = family if style in {"Regular", "Normal", "Book"} else f"{family} — {style}"
            lower_name = name.lower()
            rank = next((i for i, preferred in enumerate(_PREFERRED_FONTS) if preferred in lower_name), 999)
            language = _font_language(family, style, font)
            try:
                missing = _glyph_signature(font, chr(0x10FFFF))
                supports_latin = _font_supports(font, "A", missing)
            except (OSError, ValueError):
                supports_latin = language == "latin"
            meta = _FONT_LANGUAGE_META[language]
            fonts.append({
                "id": hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:20],
                "name": name,
                "family": family,
                "style": style,
                "path": normalized,
                "recommended": rank < 999,
                "rank": rank,
                "language": language,
                "language_label": meta["label"],
                "sample": meta["sample"],
                "supports_latin": supports_latin,
                "primary_style": style.lower() in {"regular", "normal", "book", "roman"},
            })
    fonts.sort(key=lambda item: (item["rank"], item["name"].lower(), item["path"].lower()))
    for item in fonts:
        item.pop("rank", None)
    return fonts


def public_fonts():
    return [{key: value for key, value in font.items() if key != "path"} for font in system_fonts()]


def font_by_id(font_id):
    return next((font for font in system_fonts() if font["id"] == font_id), None)


def clear_font_cache():
    system_fonts.cache_clear()
