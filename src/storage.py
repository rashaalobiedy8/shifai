# -*- coding: utf-8 -*-
"""
طبقة تخزين موحّدة - SQLite محلياً، Supabase اختيارياً
====================================================
تدعم backend عبر متغير البيئة STORAGE_BACKEND:
  - STORAGE_BACKEND=sqlite    (افتراضي)
  - STORAGE_BACKEND=supabase

واجهة موحّدة:
  - save(patient_id, data)
  - load(patient_id) -> dict | None
  - list_all() -> list[str]
  - delete(patient_id) -> bool
  - exists(patient_id) -> bool
"""
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# تحميل .env إن وُجد (اختياري - لا يفشل لو مش موجود)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ============ الإعدادات ============
BACKEND = os.getenv("STORAGE_BACKEND", "sqlite").lower().strip()
DB_PATH = Path(__file__).parent.parent / "data" / "shifai.db"
SUPABASE_TABLE = "patients"


def _now_iso() -> str:
    """وقت UTC بصيغة ISO 8601 - متوافق مع Supabase timestamptz و SQLite text."""
    return datetime.now(timezone.utc).isoformat()


# ============ الواجهة الأساسية ============
class BaseStorage:
    """واجهة مشتركة بين كل تطبيقات التخزين."""

    def save(self, patient_id: str, data: dict) -> None:
        raise NotImplementedError

    def load(self, patient_id: str) -> Optional[dict]:
        raise NotImplementedError

    def list_all(self) -> list:
        raise NotImplementedError

    def delete(self, patient_id: str) -> bool:
        raise NotImplementedError

    def exists(self, patient_id: str) -> bool:
        raise NotImplementedError


# ============ SQLite ============
class SQLiteStorage(BaseStorage):
    """تخزين محلي عبر SQLite - يبقى بعد refresh/إعادة تشغيل."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    patient_id TEXT PRIMARY KEY,
                    data_json  TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_updated_at
                ON patients(updated_at DESC)
            """)
            conn.commit()

    def save(self, patient_id: str, data: dict) -> None:
        pid = str(patient_id).strip()
        if not pid:
            raise ValueError("patient_id مطلوب")

        now = _now_iso()
        payload = dict(data)
        payload["patient_id"] = pid
        payload["updated_at"] = now
        payload.setdefault("created_at", now)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO patients (patient_id, data_json, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(patient_id) DO UPDATE SET
                    data_json  = excluded.data_json,
                    updated_at = excluded.updated_at
            """, (
                pid,
                json.dumps(payload, ensure_ascii=False),
                payload["created_at"],
                now,
            ))
            conn.commit()

    def load(self, patient_id: str) -> Optional[dict]:
        pid = str(patient_id).strip()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT data_json FROM patients WHERE patient_id = ?",
                (pid,),
            )
            row = cur.fetchone()
            return json.loads(row[0]) if row else None

    def list_all(self) -> list:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT patient_id FROM patients ORDER BY updated_at DESC"
            )
            return [r[0] for r in cur.fetchall()]

    def delete(self, patient_id: str) -> bool:
        pid = str(patient_id).strip()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("DELETE FROM patients WHERE patient_id = ?", (pid,))
            conn.commit()
            return cur.rowcount > 0

    def exists(self, patient_id: str) -> bool:
        pid = str(patient_id).strip()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT 1 FROM patients WHERE patient_id = ? LIMIT 1",
                (pid,),
            )
            return cur.fetchone() is not None


# ============ Supabase ============
class SupabaseStorage(BaseStorage):
    """
    تخزين سحابي عبر Supabase.
    يستخدم جدول patients مع عمود data من نوع jsonb.

    يقرأ متغيرات البيئة:
      - SUPABASE_URL
      - SUPABASE_SERVICE_KEY  (مفضّل)
      - SUPABASE_KEY          (بديل للتوافق)
    """

    def __init__(self):
        try:
            from supabase import create_client
        except ImportError:
            raise ImportError(
                "مكتبة supabase غير مثبّتة. شغّل: pip install supabase"
            )

        url = os.getenv("SUPABASE_URL")
        key = (
            os.getenv("SUPABASE_SERVICE_KEY")
            or os.getenv("SUPABASE_KEY")
        )

        if not url or not key:
            raise ValueError(
                "SUPABASE_URL و SUPABASE_SERVICE_KEY (أو SUPABASE_KEY) مطلوبان"
            )

        self.client = create_client(url, key)
        self.table = SUPABASE_TABLE

    def save(self, patient_id: str, data: dict) -> None:
        pid = str(patient_id).strip()
        if not pid:
            raise ValueError("patient_id مطلوب")

        now = _now_iso()
        payload = dict(data)
        payload["patient_id"] = pid
        payload["updated_at"] = now
        payload.setdefault("created_at", now)

        # upsert: insert أو update حسب الـ primary key
        self.client.table(self.table).upsert(
            {
                "patient_id": pid,
                "data": payload,
            },
            on_conflict="patient_id",
        ).execute()

    def load(self, patient_id: str) -> Optional[dict]:
        pid = str(patient_id).strip()
        res = (
            self.client.table(self.table)
            .select("data")
            .eq("patient_id", pid)
            .limit(1)
            .execute()
        )
        if not res.data:
            return None
        row = res.data[0]
        return row.get("data")

    def list_all(self) -> list:
        res = (
            self.client.table(self.table)
            .select("patient_id")
            .order("updated_at", desc=True)
            .execute()
        )
        return [r["patient_id"] for r in (res.data or [])]

    def delete(self, patient_id: str) -> bool:
        pid = str(patient_id).strip()
        res = (
            self.client.table(self.table)
            .delete()
            .eq("patient_id", pid)
            .execute()
        )
        # supabase-py بيرجّع data بالصفوف المحذوفة
        return bool(res.data)

    def exists(self, patient_id: str) -> bool:
        pid = str(patient_id).strip()
        res = (
            self.client.table(self.table)
            .select("patient_id")
            .eq("patient_id", pid)
            .limit(1)
            .execute()
        )
        return bool(res.data)


# ============ المصنع ============
_storage_instance = None


def get_storage() -> BaseStorage:
    """
    يعيد نسخة واحدة (singleton) من طبقة التخزين المناسبة.
    يعتمد على STORAGE_BACKEND في متغيرات البيئة.
    """
    global _storage_instance
    if _storage_instance is None:
        if BACKEND == "supabase":
            _storage_instance = SupabaseStorage()
        else:
            _storage_instance = SQLiteStorage()
    return _storage_instance


# ============ اختبار سريع ============
if __name__ == "__main__":
    s = get_storage()
    print(f"✅ Backend: {BACKEND}")
    print(f"🗄️  DB path: {DB_PATH}")

    test_id = "test_001"
    s.save(test_id, {"name": "اختبار", "age": 30})
    print(f"✅ محفوظ: {test_id}")

    loaded = s.load(test_id)
    print(f"✅ محمّل: {loaded}")

    print(f"✅ موجود: {s.exists(test_id)}")
    print(f"📋 كل السجلات: {s.list_all()}")

    s.delete(test_id)
    print(f"🗑️  محذوف: {not s.exists(test_id)}")