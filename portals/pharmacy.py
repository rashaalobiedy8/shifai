# portals/pharmacy.py
"""
واجهة الصيدلي — إدارة المخزون + التحقق من وصفة المريض.
تتبع نمط portals/doctor.py (Streamlit + shared.ui + HealthRecord).
"""

import streamlit as st
from shared.ui import render_header, render_footer
from src.inventory import Inventory
from src.health_record import HealthRecord


# ----------------------------------------------------------------------
# تهيئة كائن المخزون (cached)
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
# أدوات مساعدة للعرض
# ----------------------------------------------------------------------
def _render_inventory_table(items):
    """عرض قائمة الأدوية كجدول."""
    if not items:
        st.info("📭 المخزون فارغ حالياً.")
        return

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


def _check_prescription_availability(record, inventory):
    """
    مقارنة الأدوية الموصوفة للمريض مع المخزون.
    يفترض أن record.data['prescriptions'] قائمة بأسماء الأدوية.
    """
    prescriptions = record.data.get("prescriptions", [])
    if not prescriptions:
        st.info("ℹ️ لا توجد أدوية موصوفة مسجلة لهذا المريض.")
        return

    inventory_names = {item["drug_name"].lower(): item for item in inventory.get_all()}

    results = []
    for drug in prescriptions:
        key = drug.strip().lower()
        if key in inventory_names:
            item = inventory_names[key]
            status = "✅ متوفر" if item["quantity"] > 0 else "⚠️ نافد"
            results.append({
                "الدواء الموصوف": drug,
                "الحالة": status,
                "الكمية المتاحة": item["quantity"],
                "السعر": f"{item['price']:.2f}",
            })
        else:
            results.append({
                "الدواء الموصوف": drug,
                "الحالة": "❌ غير موجود في المخزون",
                "الكمية المتاحة": "-",
                "السعر": "-",
            })

    st.dataframe(results, use_container_width=True)


# ----------------------------------------------------------------------
# نماذج إدارة المخزون
# ----------------------------------------------------------------------
def _handle_add(inventory):
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
    items = inventory.get_all()
    if not items:
        st.info("📭 لا توجد أدوية للتعديل.")
        return

    names = [item["drug_name"] for item in items]
    selected = st.selectbox("اختر الدواء للتعديل", names, key="update_select")

    current = next((i for i in items if i["drug_name"] == selected), None)
    if current is None:
        return

    with st.form("update_drug_form"):
        st.subheader(f"✏️ تعديل: {selected}")
        quantity = st.number_input("الكمية", min_value=0, step=1, value=int(current["quantity"]))
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
    items = inventory.get_all()
    if not items:
        st.info("📭 لا توجد أدوية للحذف.")
        return

    names = [item["drug_name"] for item in items]
    selected = st.selectbox("اختر الدواء للحذف", names, key="delete_select")

    confirm = st.checkbox(f"أؤكد رغبتي في حذف '{selected}' نهائياً", key="delete_confirm")
    if st.button("🗑️ حذف", key="delete_btn") and confirm:
        try:
            inventory.delete_drug(selected)
            st.success(f"✅ تم حذف '{selected}'.")
            st.rerun()
        except ValueError as e:
            st.error(f"❌ {e}")


def _handle_search(inventory):
    query = st.text_input("🔍 ابحث باسم الدواء أو الشركة المصنعة", key="search_query")
    if query.strip():
        results = inventory.search_drug(query)
        st.markdown(f"**النتائج ({len(results)}):**")
        _render_inventory_table(results)


# ----------------------------------------------------------------------
# قسم المريض (خليط أ + ب)
# ----------------------------------------------------------------------
def _render_patient_section(inventory):
    st.subheader("🔍 البحث عن مريض")
    st.write("أدخل رقم المريض (ID) لعرض وصفته والتحقق من توفر الأدوية في المخزون.")

    default_id = st.session_state.get("scanned_patient_id", "")
    patient_id_input = st.text_input(
        "رقم المريض (ID):", value=default_id, placeholder="مثال: 12345",
        key="pharmacy_patient_id",
    )

    if "scanned_patient_id" in st.session_state:
        del st.session_state["scanned_patient_id"]

    if not patient_id_input:
        return

    record = HealthRecord.load(patient_id_input.strip())
    if record is None:
        st.error("❌ لم يتم العثور على مريض بهذا الرقم.")
        return

    st.success(f"✅ تم العثور على المريض: {record.data.get('name')}")

    # بيانات المريض الأساسية
    with st.expander("📄 بيانات المريض", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**العمر:** {record.data.get('age')} سنة")
            st.write(f"**الجنس:** {record.data.get('gender')}")
        with col2:
            st.write(f"**الحساسية:** {', '.join(record.data.get('allergies', [])) or 'لا يوجد'}")
            st.write(f"**الأمراض المزمنة:** {', '.join(record.data.get('chronic_diseases', [])) or 'لا يوجد'}")

    # الأدوية الموصوفة (الجزء أ)
    with st.expander("💊 الأدوية الموصوفة", expanded=True):
        prescriptions = record.data.get("prescriptions", [])
        if prescriptions:
            for drug in prescriptions:
                st.write(f"- {drug}")
        else:
            st.info("لا توجد أدوية موصوفة مسجلة.")

    # التحقق من توفر الأدوية (الجزء ب)
    with st.expander("📦 التحقق من توفر الأدوية في المخزون", expanded=True):
        _check_prescription_availability(record, inventory)


# ----------------------------------------------------------------------
# الواجهة الرئيسية
# ----------------------------------------------------------------------
def show_pharmacy_portal():
    """نقطة الدخول لواجهة الصيدلي."""
    render_header("واجهة الصيدلي — إدارة المخزون")

    inventory = _get_inventory()
    if inventory is None:
        render_footer()
        return

    if st.button("🔙 العودة للصفحة الرئيسية"):
        st.session_state["role"] = None
        st.rerun()

    st.divider()

    # القسم 1: المريض
    _render_patient_section(inventory)

    st.divider()

    # القسم 2: المخزون
    st.subheader("📦 إدارة المخزون")
    tab_view, tab_add, tab_update, tab_delete, tab_search = st.tabs([
        "📋 عرض الكل",
        "➕ إضافة",
        "✏️ تعديل",
        "🗑️ حذف",
        "🔍 بحث",
    ])

    with tab_view:
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