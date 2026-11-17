# portals/pharmacy.py
"""
واجهة الصيدلي — إدارة مخزون الأدوية.
تتبع نفس نمط portals/doctor.py (Streamlit + shared.ui + shared.auth_guard).
"""

import streamlit as st
from shared.auth_guard import check_role
from shared.ui import render_header, render_footer
from src.inventory import Inventory


# ----------------------------------------------------------------------
# تهيئة كائن المخزون (cached) — يُحمَّل مرة واحدة لكل جلسة
# ----------------------------------------------------------------------
@st.cache_resource
def _get_inventory():
    """تحميل كائن Inventory (cached)."""
    try:
        return Inventory()
    except Exception as e:
        st.error(f"❌ فشل تحميل المخزون: {e}")
        return None


# ----------------------------------------------------------------------
# دوال مساعدة للعرض
# ----------------------------------------------------------------------
def _render_inventory_table(items):
    """عرض قائمة الأدوية كجدول في Streamlit."""
    if not items:
        st.info("📭 المخزون فارغ حالياً.")
        return

    # تجهيز البيانات للعرض
    table_data = []
    for item in items:
        table_data.append({
            "اسم الدواء": item.get("drug_name", ""),
            "الكمية": item.get("quantity", 0),
            "السعر": f"{item.get('price', 0):.2f}",
            "تاريخ الانتهاء": item.get("expiry_date", ""),
            "الشركة المصنعة": item.get("manufacturer", ""),
        })

    st.dataframe(table_data, use_container_width=True)


def _handle_add(inventory):
    """نموذج إضافة دواء جديد."""
    with st.form("add_drug_form", clear_on_submit=True):
        st.subheader("➕ إضافة دواء جديد")
        drug_name = st.text_input("اسم الدواء")
        quantity = st.number_input("الكمية", min_value=0, step=1, value=0)
        price = st.number_input("السعر", min_value=0.0, step=0.5, value=0.0, format="%.2f")
        expiry_date = st.date_input("تاريخ الانتهاء")
        manufacturer = st.text_input("الشركة المصنعة")

        submitted = st.form_submit_button("إضافة")

        if submitted:
            try:
                inventory.add_drug(
                    drug_name=drug_name,
                    quantity=int(quantity),
                    price=float(price),
                    expiry_date=expiry_date.strftime("%Y-%m-%d"),
                    manufacturer=manufacturer,
                )
                st.success(f"✅ تمت إضافة '{drug_name}' بنجاح.")
                st.rerun()
            except ValueError as e:
                st.error(f"❌ {e}")


def _handle_update(inventory):
    """نموذج تعديل دواء موجود."""
    items = inventory.get_all()
    if not items:
        st.info("📭 لا توجد أدوية للتعديل.")
        return

    names = [item["drug_name"] for item in items]
    selected = st.selectbox("اختر الدواء للتعديل", names)

    # جلب القيم الحالية
    current = next((i for i in items if i["drug_name"] == selected), None)
    if current is None:
        return

    with st.form("update_drug_form"):
        st.subheader(f"✏️ تعديل: {selected}")
        quantity = st.number_input(
            "الكمية", min_value=0, step=1, value=int(current["quantity"])
        )
        price = st.number_input(
            "السعر", min_value=0.0, step=0.5,
            value=float(current["price"]), format="%.2f"
        )
        expiry_date = st.text_input("تاريخ الانتهاء (YYYY-MM-DD)", value=current["expiry_date"])
        manufacturer = st.text_input("الشركة المصنعة", value=current["manufacturer"])

        submitted = st.form_submit_button("حفظ التعديلات")

        if submitted:
            try:
                inventory.update_drug(
                    selected,
                    quantity=int(quantity),
                    price=float(price),
                    expiry_date=expiry_date,
                    manufacturer=manufacturer,
                )
                st.success("✅ تم حفظ التعديلات.")
                st.rerun()
            except ValueError as e:
                st.error(f"❌ {e}")


def _handle_delete(inventory):
    """نموذج حذف دواء."""
    items = inventory.get_all()
    if not items:
        st.info("📭 لا توجد أدوية للحذف.")
        return

    names = [item["drug_name"] for item in items]
    selected = st.selectbox("اختر الدواء للحذف", names)

    confirm = st.checkbox(f"أؤكد رغبتي في حذف '{selected}' نهائياً")
    if st.button("🗑️ حذف") and confirm:
        try:
            inventory.delete_drug(selected)
            st.success(f"✅ تم حذف '{selected}'.")
            st.rerun()
        except ValueError as e:
            st.error(f"❌ {e}")


def _handle_search(inventory):
    """نموذج البحث."""
    query = st.text_input("🔍 ابحث باسم الدواء أو الشركة المصنعة")
    if query.strip():
        results = inventory.search_drug(query)
        st.markdown(f"**النتائج ({len(results)}):**")
        _render_inventory_table(results)


# ----------------------------------------------------------------------
# الواجهة الرئيسية
# ----------------------------------------------------------------------
def show_pharmacy_portal():
    """نقطة الدخول لواجهة الصيدلي."""
    check_role("pharmacy")  # التأكد من صلاحية الدور

    render_header("واجهة الصيدلي — إدارة المخزون")

    inventory = _get_inventory()
    if inventory is None:
        render_footer()
        return

    # التبويبات
    tab_view, tab_add, tab_update, tab_delete, tab_search = st.tabs([
        "📋 عرض الكل",
        "➕ إضافة",
        "✏️ تعديل",
        "🗑️ حذف",
        "🔍 بحث",
    ])

    with tab_view:
        st.subheader("📋 كل الأدوية في المخزون")
        _render_inventory_table(inventory.get_all())

    with tab_add:
        _handle_add(inventory)

    with tab_update:
        _handle_update(inventory)

    with tab_delete:
        _handle_delete(inventory)

    with tab_search:
        _handle_search(inventory)

    render_footer()