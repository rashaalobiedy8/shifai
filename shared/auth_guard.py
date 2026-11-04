import streamlit as st

def check_role(required_role: str):
    """
    يتحقق من أن المستخدم الحالي يمتلك الدور المطلوب.
    إذا لم يكن يمتلكه، يتم توجيهه للصفحة الرئيسية.
    """
    current_role = st.session_state.get("role", None)
    
    if current_role != required_role:
        st.error("⚠️ غير مصرح لك بالدخول لهذه الصفحة. جاري تحويلك...")
        st.session_state["role"] = None
        st.rerun()