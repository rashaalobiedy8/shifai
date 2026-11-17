# src/inventory.py
"""
إدارة مخزون الصيدلية باستخدام ملف JSON.
يوفر كلاس Inventory عمليات CRUD كاملة على الأدوية.
"""

import json
import os
from datetime import datetime


class Inventory:
    """كلاس لإدارة مخزون الأدوية مع حفظ دائم في ملف JSON."""

    # الحقول المطلوبة لكل دواء
    FIELDS = ["drug_name", "quantity", "price", "expiry_date", "manufacturer"]

    def __init__(self, file_path="data/inventory.json"):
        """
        تهيئة المخزون.

        :param file_path: مسار ملف JSON لتخزين البيانات.
        """
        self.file_path = file_path
        self.items = []  # قائمة قواميس الأدوية
        self._load()

    # ------------------------------------------------------------------
    # عمليات التخزين (قراءة / حفظ)
    # ------------------------------------------------------------------
    def _load(self):
        """قراءة البيانات من ملف JSON إن وُجد، وإلا البدء بقائمة فارغة."""
        if not os.path.exists(self.file_path):
            self.items = []
            return

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.items = data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            # في حال تلف الملف أو تعذّر قراءته نبدأ بقائمة فارغة
            self.items = []

    def _save(self):
        """حفظ البيانات الحالية في ملف JSON مع إنشاء المجلد عند الحاجة."""
        directory = os.path.dirname(self.file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.items, f, ensure_ascii=False, indent=4)

    # ------------------------------------------------------------------
    # دوال مساعدة
    # ------------------------------------------------------------------
    def _find_index(self, drug_name):
        """
        إرجاع فهرس الدواء في القائمة حسب الاسم (غير حساس لحالة الأحرف).

        :return: الفهرس أو -1 إن لم يوجد.
        """
        name_lower = drug_name.strip().lower()
        for i, item in enumerate(self.items):
            if item.get("drug_name", "").strip().lower() == name_lower:
                return i
        return -1

    @staticmethod
    def _validate(quantity, price, expiry_date):
        """
        التحقق من صحة القيم المدخلة.

        :raises ValueError: عند إدخال قيم غير صحيحة.
        """
        if not isinstance(quantity, int) or quantity < 0:
            raise ValueError("الكمية يجب أن تكون عدداً صحيحاً غير سالب.")

        if not isinstance(price, (int, float)) or price < 0:
            raise ValueError("السعر يجب أن يكون رقماً غير سالب.")

        # التحقق من صيغة التاريخ YYYY-MM-DD
        try:
            datetime.strptime(expiry_date, "%Y-%m-%d")
        except (ValueError, TypeError):
            raise ValueError("تاريخ الانتهاء يجب أن يكون بصيغة YYYY-MM-DD.")

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def add_drug(self, drug_name, quantity, price, expiry_date, manufacturer):
        """
        إضافة دواء جديد إلى المخزون.

        :return: True عند النجاح.
        :raises ValueError: إذا كان الدواء موجوداً مسبقاً أو البيانات غير صحيحة.
        """
        if not drug_name or not drug_name.strip():
            raise ValueError("اسم الدواء مطلوب.")

        if self._find_index(drug_name) != -1:
            raise ValueError(f"الدواء '{drug_name}' موجود مسبقاً في المخزون.")

        self._validate(quantity, price, expiry_date)

        self.items.append({
            "drug_name": drug_name.strip(),
            "quantity": quantity,
            "price": float(price),
            "expiry_date": expiry_date,
            "manufacturer": manufacturer.strip() if manufacturer else "",
        })
        self._save()
        return True

    def update_drug(self, drug_name, **changes):
        """
        تعديل بيانات دواء موجود.

        :param drug_name: اسم الدواء (مفتاح البحث).
        :param changes: الحقول المراد تعديلها (quantity, price, expiry_date, manufacturer).
        :return: True عند النجاح.
        :raises ValueError: إذا لم يوجد الدواء أو القيم غير صحيحة.
        """
        idx = self._find_index(drug_name)
        if idx == -1:
            raise ValueError(f"الدواء '{drug_name}' غير موجود في المخزون.")

        allowed = {"quantity", "price", "expiry_date", "manufacturer"}
        unknown = set(changes) - allowed
        if unknown:
            raise ValueError(f"حقول غير معروفة للتعديل: {', '.join(unknown)}")

        # دمج القيم الجديدة مع القديمة للتحقق
        current = self.items[idx]
        new_quantity = changes.get("quantity", current["quantity"])
        new_price = changes.get("price", current["price"])
        new_expiry = changes.get("expiry_date", current["expiry_date"])

        self._validate(new_quantity, new_price, new_expiry)

        # تطبيق التعديلات
        current["quantity"] = new_quantity
        current["price"] = float(new_price)
        current["expiry_date"] = new_expiry
        if "manufacturer" in changes:
            current["manufacturer"] = (changes["manufacturer"] or "").strip()

        self._save()
        return True

    def delete_drug(self, drug_name):
        """
        حذف دواء من المخزون.

        :return: True عند النجاح.
        :raises ValueError: إذا لم يوجد الدواء.
        """
        idx = self._find_index(drug_name)
        if idx == -1:
            raise ValueError(f"الدواء '{drug_name}' غير موجود في المخزون.")

        del self.items[idx]
        self._save()
        return True

    def search_drug(self, query):
        """
        البحث عن دواء باسمه أو الشركة المصنعة (بحث جزئي، غير حساس لحالة الأحرف).

        :return: قائمة بالأدوية المطابقة.
        """
        if not query or not query.strip():
            return []

        q = query.strip().lower()
        results = []
        for item in self.items:
            if (q in item.get("drug_name", "").lower()
                    or q in item.get("manufacturer", "").lower()):
                results.append(item)
        return results

    def get_all(self):
        """إرجاع قائمة بكل الأدوية في المخزون."""
        return list(self.items)