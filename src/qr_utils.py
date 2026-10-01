# src/qr_utils.py
"""
أدوات توليد وقراءة QR Code للملف الصحي في shifai.
"""
from __future__ import annotations
import io
import json
import base64
import zlib
from typing import Any, Dict, Optional

import qrcode
from qrcode.constants import ERROR_CORRECT_M
from PIL import Image

SHIFAI_SCHEME = "shifai://patient/"
RECORD_SCHEME = "shifai://record/"


# ============================================================
# 1) توليد QR أساسي (رابط المريض فقط - خفيف)
# ============================================================
def make_qr_image(data: str, box_size: int = 10, border: int = 4) -> Image.Image:
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


def make_patient_qr(patient_id: str) -> Image.Image:
    return make_qr_image(f"{SHIFAI_SCHEME}{patient_id}")


# ============================================================
# 2) QR كامل (الملف كله مضغوط Base64 - للنقل بين الأجهزة)
# ============================================================
def encode_record(record: Dict[str, Any]) -> str:
    raw = json.dumps(record, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    comp = zlib.compress(raw, level=9)
    return base64.urlsafe_b64encode(comp).decode("ascii")


def decode_record(token: str) -> Dict[str, Any]:
    comp = base64.urlsafe_b64decode(token.encode("ascii"))
    raw = zlib.decompress(comp)
    return json.loads(raw.decode("utf-8"))


def make_full_record_qr(record: Dict[str, Any]) -> Image.Image:
    token = encode_record(record)
    return make_qr_image(f"{RECORD_SCHEME}{token}", box_size=6)


# ============================================================
# 3) أدوات مساعدة
# ============================================================
def qr_to_png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def parse_qr_text(text: str) -> Optional[Dict[str, str]]:
    """يحلّل النص المستخرج من QR."""
    text = (text or "").strip()
    if text.startswith(SHIFAI_SCHEME):
        pid = text[len(SHIFAI_SCHEME):].strip()
        return {"kind": "patient", "patient_id": pid} if pid else None
    if text.startswith(RECORD_SCHEME):
        token = text[len(RECORD_SCHEME):].strip()
        return {"kind": "record", "token": token} if token else None
    return None


def estimate_record_qr_ok(record: Dict[str, Any], max_chars: int = 2000) -> bool:
    """يتحقق إذا الملف صغير كفاية ليتحول لـ QR كامل."""
    try:
        return len(encode_record(record)) <= max_chars
    except Exception:
        return False