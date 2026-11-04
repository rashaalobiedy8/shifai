import streamlit as st
import os

def apply_custom_css():
    """تطبيق الألوان والخطوط بناءً على هوية shifai (الأزرق والأبيض)"""
    st.markdown("""
        <style>
        /* الألوان الأساسية */
        :root {
            --primary-blue: #0077b6;
            --light-blue: #00b4d8;
            --bg-color: #f8f9fa;
        }
        
        /* خلفية التطبيق */
        .stApp {
            background-color: var(--bg-color);
        }
        
        /* تنسيق العناوين */
        h1, h2, h3 {
            color: var(--primary-blue) !important;
            text-align: center;
        }
        
        /* تنسيق الأزرار */
        .stButton>button {
            background-color: var(--primary-blue);
            color: white;
            border-radius: 10px;
            border: none;
            padding: 10px 24px;
            transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: var(--light-blue);
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

def render_header(title: str):
    """عرض الشعار والعنوان في أعلى الصفحة"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # تأكد أن مسار الصورة صحيح بناءً على الهيكل بتاعك
        logo_path = "assets/logo.jpg"
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
        else:
            st.warning("⚠️ لم يتم العثور على الشعار في assets/logo.png")
        
        st.markdown(f"<h2 style='text-align: center;'>{title}</h2>", unsafe_allow_html=True)

def render_footer():
    """تذييل بسيط"""
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: gray;'>رفيقك الذكي في رحلة الشفاء</p>", unsafe_allow_html=True)