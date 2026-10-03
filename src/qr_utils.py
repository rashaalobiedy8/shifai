# src/qr_utils.py
"""
أدوات QR لـ Shifai:
- توليد QR لملف المريض (رابط HTTPS يفتح التطبيق مباشرة)
- توليد QR يحتوي الملف كاملاً (Base64 + zlib) للعمل بدون إنترنت
- قراءة وتحليل نصوص QR
"""
from __future__ import annotations

import io
import json
import os
import base64
import zlib
from typing import Any, Dict, Optional

import qrcode
from qrcode.constants import ERROR_CORRECT_M
from PIL import Image


# ============================================================
# ثوابت
# ============================================================
DEFAULT_BASE_URL = os.getenv(
    "SHIFAI_BASE_URL",
    "https://shifai-libya.streamlit.app"
)

# مخططات قديمة (للتوافق الخلفي مع QR مُولّد سابقاً)
SHIFAI_SCHEME = "shifai://patient/"
RECORD_SCHEME = "shifai://record/"


# ============================================================
# 1) توليد صورة QR
# ============================================================
def make_qr_image(data: str, box_size: int = 10, border: int = 4) -> Image.Image:
    """ينشئ صورة QR جاهزة للعرض أو الحفظ."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


def _safe_base_url(url: Optional[str]) -> str:
    """يمنع أي رابط غير HTTPS — يحوّل shifai:// إلى HTTPS تلقائياً."""
    if not url or not url.strip():
        return DEFAULT_BASE_URL
    url = url.strip().rstrip("/")
    if url.startswith("shifai://") or not url.startswith("https://"):
        return DEFAULT_BASE_URL
    return url


def patient_url(patient_id: str, base_url: Optional[str] = None) -> str:
    """يرجّع الرابط النصي — استخدميه في caption بدل الكتابة اليدوية."""
    base = _safe_base_url(base_url)
    return f"{base}/?patient={patient_id}"


def make_patient_qr(patient_id: str, base_url: Optional[str] = None) -> Image.Image:
    """QR برابط HTTPS يفتح التطبيق على ملف المريض مباشرة."""
    url = patient_url(patient_id, base_url)
    print(f"[QR] Generated URL: {url}")  # يظهر في Streamlit Cloud logs
    return make_qr_image(url)


# ============================================================
# 2) QR يحتوي الملف كاملاً (Base64)
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


def parse_qr_text(text: str):
    """يحلّل نص QR ويرجّع dict يوصف نوعه."""
    text = (text or "").strip()

    # 1) رابط HTTPS جديد: https://shifai-libya.streamlit.app/?patient=xxx
    if "?patient=" in text:
        try:
            pid = text.split("?patient=")[1].split("&")[0].strip()
            if pid:
                return {"kind": "patient", "patient_id": pid}
        except Exception:
            pass

    # 2) مخططات قديمة (توافق خلفي)
    if text.startswith(SHIFAI_SCHEME):
        pid = text[len(SHIFAI_SCHEME):].strip()
        return {"kind": "patient", "patient_id": pid} if pid else None
    if text.startswith(RECORD_SCHEME):
        token = text[len(RECORD_SCHEME):].strip()
        return {"kind": "record", "token": token} if token else None

    return None


def estimate_record_qr_ok(record: Dict[str, Any], max_chars: int = 2000) -> bool:
    """يتأكد أن الملف صغير كفاية ليُخزَّن داخل QR."""
    try:
        return len(encode_record(record)) <= max_chars
    except Exception:
        return False