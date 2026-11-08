import streamlit as st
from shared.auth_guard import check_role
from shared.ui import render_header, render_footer
from src.health_record import HealthRecord

import pickle
from src import config

@st.cache_resource
def _load_drug_model():
    """تحميل نموذج التنبؤ بالدواء (cached)."""
    try:
        with open(config.MODEL_FILE, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        st.error(f"❌ فشل تحميل النموذج: {e}")
        return None

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
                st.write("أدخل البيانات الحيوية للمريض للتنبؤ بالدواء المناسب.")

                model_data = _load_drug_model()

                if model_data is None:
                    st.error("❌ النموذج غير محمّل. تأكد من وجود ملف النموذج في config.MODEL_FILE.")
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                        p_age = st.number_input("العمر", min_value=1, max_value=120, value=45, key='doc_p_age')
                        p_gender = st.selectbox("الجنس", ["M", "F"], key='doc_p_gender')
                    with col2:
                        p_bp = st.selectbox("ضغط الدم", ["HIGH", "LOW", "NORMAL"], key='doc_p_bp')
                        p_chol = st.selectbox("الكوليسترول", ["HIGH", "NORMAL"], key='doc_p_chol')
                    p_nak = st.number_input("Na_to_K", min_value=0.0, max_value=50.0, value=12.5, step=0.1, key='doc_p_nak')

                    if st.button("🔮 تنبؤ بالدواء", key='doc_predict_btn'):
                        try:
                            g = model_data['le_sex'].transform([p_gender])[0]
                            bp = model_data['le_bp'].transform([p_bp])[0]
                            ch = model_data['le_cholesterol'].transform([p_chol])[0]
                            pred = model_data['model'].predict([[p_age, g, bp, ch, p_nak]])
                            drug = model_data['le_drug'].inverse_transform(pred)[0]

                            st.markdown(f"""
                            <div class="success-box">
                                <h2>💊 الدواء المناسب المتوقع</h2>
                                <h1 style="color: #27AE60;">{drug}</h1>
                                <p>⚠️ هذه توصية أولية، يرجى استشارة الطبيب</p>
                            </div>
                            """, unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"❌ خطأ أثناء التنبؤ: {e}")
                
            with tab2:
                st.write("هنا سيتم وضع فحص التفاعلات الدوائية قريباً.")

    render_footer()