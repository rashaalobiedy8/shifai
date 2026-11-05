import streamlit as st
from portals.patient import show_patient_portal
from portals.doctor import show_doctor_portal
from portals.pharmacy import show_pharmacy_portal
from shared.ui import apply_custom_css, render_header, render_footer

import streamlit as st
from shared.ui import apply_custom_css, render_header, render_footer

# --- قراءة الـ URL لو جاي من مسح QR ---
query_params = st.query_params
scanned_patient_id = query_params.get("patient")

if scanned_patient_id:
    # لو اللينك فيه رقم مريض، حول المستخدم لواجهة الطبيب فوراً
    st.session_state["role"] = "doctor"
    st.session_state["scanned_patient_id"] = scanned_patient_id
 
# إعدادات الصفحة
st.set_page_config(page_title="Shifai - شفائي", page_icon="💙", layout="centered")

# تطبيق التنسيقات
apply_custom_css()

# تهيئة الـ Session State
if "role" not in st.session_state:
    st.session_state["role"] = None

# دالة لتغيير الصفحة
def select_role(role):
    st.session_state["role"] = role
    st.rerun()

# شاشة اختيار الدور (Role Selector)
def show_role_selector():
    render_header("مرحباً بك في شفائي")
    
    st.markdown("<h3 style='text-align: center;'>اختر نوع حسابك للبدء</h3>", unsafe_allow_html=True)
    st.write("") # مسافة
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("<div style='text-align: center; font-size: 50px;'>🧑‍🦽</div>", unsafe_allow_html=True)
        if st.button("مريض", use_container_width=True):
            select_role("patient")
            
    with col2:
        st.markdown("<div style='text-align: center; font-size: 50px;'>👨‍⚕️</div>", unsafe_allow_html=True)
        if st.button("طبيب", use_container_width=True):
            select_role("doctor")
            
    with col3:
        st.markdown("<div style='text-align: center; font-size: 50px;'>💊</div>", unsafe_allow_html=True)
        if st.button("صيدلي", use_container_width=True):
            select_role("pharmacy")
            
    render_footer()

# استدعاء الواجهات
from portals.patient import show_patient_portal
from portals.doctor import show_doctor_portal
from portals.pharmacy import show_pharmacy_portal

# التوجيه بناءً على الدور
if st.session_state["role"] is None:
    show_role_selector()
elif st.session_state["role"] == "patient":
    show_patient_portal()
elif st.session_state["role"] == "doctor":
    show_doctor_portal()
elif st.session_state["role"] == "pharmacy":
    show_pharmacy_portal()