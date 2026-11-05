import streamlit as st
from shared.auth_guard import check_role
from shared.ui import render_header, render_footer
from src.health_record import HealthRecord

def show_doctor_portal():
    check_role("doctor")
    
    # زرار تسجيل الخروج
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🚪 خروج", use_container_width=True):
            st.session_state["role"] = None
            st.rerun()

    render_header("واجهة الطبيب")

    # --- قسم البحث عن مريض ---
    st.subheader("🔍 البحث عن مريض")
    st.write("أدخل رقم المريض (ID) أو امسح الـ QR الخاص به للوصول إلى ملفه الصحي.")
    
    # لو الطبيب جاي من مسح QR، بنجيب الرقم تلقائياً
    default_id = st.session_state.get("scanned_patient_id", "")
    patient_id_input = st.text_input("رقم المريض (ID):", value=default_id, placeholder="مثال: 12345")
    
    # نمسح الرقم من الـ session عشان لو الطبيب عمل refresh الصفحة ما يفضلش معلق
    if "scanned_patient_id" in st.session_state:
        del st.session_state["scanned_patient_id"]

    if patient_id_input:
        # محاولة تحميل ملف المريض
        record = HealthRecord.load(patient_id_input.strip())
        
        if record is None:
            st.error("لم يتم العثور على مريض بهذا الرقم. تأكد من الرقم وحاول مرة أخرى.")
        else:
            # عرض بيانات المريض
            st.success(f"تم العثور على المريض: {record.data.get('name')}")
            
            with st.expander("📄 عرض الملف الصحي", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**العمر:** {record.data.get('age')} سنة")
                    st.write(f"**الجنس:** {record.data.get('gender')}")
                    st.write(f"**فصيلة الدم:** {record.data.get('blood_type')}")
                with col2:
                    st.write(f"**الأمراض المزمنة:** {', '.join(record.data.get('chronic_diseases', [])) or 'لا يوجد'}")
                    st.write(f"**الحساسية:** {', '.join(record.data.get('allergies', [])) or 'لا يوجد'}")
                
                st.divider()
                st.write("**سجل الزيارات السابقة:**")
                visits = record.data.get('visits', [])
                if visits:
                    for v in reversed(visits):
                        st.write(f"- بتاريخ {v.get('date')[:10]}: {v.get('diagnosis')}")
                else:
                    st.write("لا توجد زيارات مسجلة.")

            st.divider()
            
            # --- قسم التنبؤ بالدواء وفحص التفاعلات ---
            st.subheader("💊 أدوات الدواء")
            
            tab1, tab2 = st.tabs(["أداة التنبؤ بالدواء", "فحص التفاعلات"])
            
            with tab1:
                st.write("هنا سيتم وضع أداة التنبؤ بالدواء (Drug Prediction) قريباً.")
                # ملاحظة: هنستدعي الموديل من src/preprocess.py أو train_model.py هنا لاحقاً
                
            with tab2:
                st.write("هنا سيتم وضع فحص التفاعلات الدوائية قريباً.")
                # ملاحظة: هنستدعي الدالة من src/interactions.py هنا لاحقاً

    render_footer()