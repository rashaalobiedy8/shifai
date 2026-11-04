import streamlit as st
from shared.auth_guard import check_role
from shared.ui import render_header, render_footer
from src.health_record import HealthRecord
from src.qr_utils import make_patient_qr

def show_patient_portal():
    check_role("patient")
    
    # زرار تسجيل الخروج فوق
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🚪 خروج", width='stretch'):
            st.session_state["role"] = None
            st.rerun()

    render_header("واجهة المريض")

    # --- 1. التحقق من وجود ملف للمريض ---
    # مؤقتاً بنستخدم ID ثابت للتجربة، هنغيره لما نعمل تسجيل الدخول
    patient_id = "12345" 
    record = HealthRecord.load(patient_id)

    if record is None:
        # --- 2. شاشة إنشاء ملف جديد ---
        st.info("مرحباً بك! يبدو أنك تستخدم التطبيق لأول مرة. يرجى إنشاء ملفك الصحي.")
        
        with st.form("create_record_form"):
            st.subheader("بياناتك الأساسية")
            name = st.text_input("الاسم الكامل")
            age = st.number_input("العمر", min_value=1, max_value=120, value=30)
            gender = st.selectbox("الجنس", ["ذكر", "أنثى"])
            blood_type = st.selectbox("فصيلة الدم", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "غير معروف"])
            
            chronic = st.text_input("الأمراض المزمنة (افصل بينها بفاصلة)", placeholder="مثال: سكري, ضغط")
            allergies = st.text_input("الحساسية (افصل بينها بفاصلة)", placeholder="مثال: بنسلين, أسبرين")
            
            submitted = st.form_submit_button("حفظ وإنشاء الملف", width='stretch')
            
            if submitted:
                if not name.strip():
                    st.error("الرجاء إدخال الاسم.")
                else:
                    # إنشاء الملف وحفظه
                    new_record = HealthRecord(
                        patient_id=patient_id,
                        name=name,
                        age=age,
                        gender=gender,
                        blood_type=blood_type,
                        chronic_diseases=chronic,
                        allergies=allergies
                    )
                    st.success("تم إنشاء ملفك الصحي بنجاح!")
                    st.rerun() # إعادة تحميل الصفحة عشان تظهر البيانات
                    
    else:
        # --- 3. عرض الملف الصحي (لو موجود) ---
        tab1, tab2 = st.tabs(["📄 الملف الصحي", "📱 رمز الـ QR"])

        with tab1:
            st.subheader(f"مرحباً، {record.data.get('name', 'مستخدم')}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**العمر:** {record.data.get('age')} سنة")
                st.info(f"**فصيلة الدم:** {record.data.get('blood_type')}")
            with col2:
                chronic_list = record.data.get('chronic_diseases', [])
                allergy_list = record.data.get('allergies', [])
                
                st.warning(f"**الأمراض المزمنة:** {', '.join(chronic_list) if chronic_list else 'لا يوجد'}")
                st.error(f"**الحساسية:** {', '.join(allergy_list) if allergy_list else 'لا يوجد'}")

            st.divider()
            st.subheader("🗓️ سجل الزيارات الأخيرة")
            visits = record.data.get('visits', [])
            if visits:
                for v in reversed(visits):
                    with st.expander(f"زيارة في: {v.get('date')[:10]}"):
                        st.write(f"**الأعراض:** {', '.join(v.get('symptoms', []))}")
                        st.write(f"**التشخيص:** {v.get('diagnosis')}")
                        st.write(f"**الأدوية:** {', '.join(v.get('drugs', []))}")
                        if v.get('notes'):
                            st.write(f"**ملاحظات:** {v.get('notes')}")
            else:
                st.write("لا توجد زيارات مسجلة حتى الآن.")
                
        with tab2:
            st.subheader("رمز الـ QR الخاص بك")
            st.write("اعرض هذا الرمز للطبيب أو الصيدلي للوصول لملفك.")
            
            qr_image = make_patient_qr(patient_id)
            st.image(qr_image, caption=f"ID: {patient_id}", width=250)

    render_footer()