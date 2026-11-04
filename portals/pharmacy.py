import streamlit as st
from shared.auth_guard import check_role
from shared.ui import render_header, render_footer

def show_pharmacy_portal():
    check_role("pharmacy")
    render_header("واجهة الصيدلي")
    st.info("هنا سيتم مسح الـ QR وفحص التفاعلات ومخزون الأدوية.")
    if st.button("تسجيل خروج"):
        st.session_state["role"] = None
        st.rerun()
    render_footer()