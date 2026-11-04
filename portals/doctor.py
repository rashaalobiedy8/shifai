import streamlit as st
from shared.auth_guard import check_role
from shared.ui import render_header, render_footer

def show_doctor_portal():
    check_role("doctor")
    render_header("واجهة الطبيب")
    st.info("هنا سيتم مسح الـ QR وعرض التاريخ المرضي وأداة التنبؤ.")
    if st.button("تسجيل خروج"):
        st.session_state["role"] = None
        st.rerun()
    render_footer()