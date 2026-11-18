# shared/ui.py

import streamlit as st


def apply_custom_css():
    """تطبيق التنسيقات العامة (ألوان الشعار + توافق الهاتف)."""
    st.markdown(
        """
        <style>
        /* ===================== متغيرات الهوية البصرية ===================== */
        :root {
            --brand-deep:    #0B3C5D;  /* أزرق بحري غامق */
            --brand-primary: #1B6CA8;  /* أزرق أساسي */
            --brand-cyan:    #22B8CF;  /* فيروزي */
            --brand-teal:    #0FA3A3;  /* تيل طبي */
            --brand-light:   #EAF6FB;  /* خلفية فاتحة */
            --brand-surface: #FFFFFF;  /* سطح البطاقات */
            --text-main:     #0B2233;
            --text-muted:    #5B7181;
            --border-soft:   #D6E6EF;
            --shadow-soft:   0 4px 18px rgba(11, 60, 93, 0.08);
            --radius-md:     12px;
            --radius-lg:     16px;
            --tap-target:    44px;     /* الحد الأدنى للمس */
        }

        /* ===================== أساسيات ===================== */
        html, body, .stApp {
            overflow-x: hidden;
        }
        * {
            -webkit-overflow-scrolling: touch;
        }
        img {
            max-width: 100%;
            height: auto;
        }

        /* ===================== الخلفية العامة ===================== */
        .stApp {
            background: linear-gradient(180deg, #F4FAFD 0%, var(--brand-light) 100%);
            color: var(--text-main);
            font-family: "Segoe UI", "Tahoma", "Cairo", sans-serif;
        }

        /* ===================== العناوين ===================== */
        h1, h2, h3, h4 {
            color: var(--brand-deep) !important;
            font-weight: 700;
            letter-spacing: 0.2px;
        }
        h1 {
            border-bottom: 3px solid var(--brand-cyan);
            padding-bottom: 8px;
        }
        p, label, span, div {
            color: var(--text-main);
        }
        .stCaption, small {
            color: var(--text-muted) !important;
        }

        /* ===================== الشريط الجانبي ===================== */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, var(--brand-deep) 0%, #082C45 100%);
            border-right: 2px solid var(--brand-cyan);
        }
        section[data-testid="stSidebar"] * {
            color: #EAF6FB !important;
        }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: #FFFFFF !important;
        }
        section[data-testid="stSidebar"] hr {
            border-color: rgba(34, 184, 207, 0.35);
        }

        /* ===================== الأزرار ===================== */
        .stButton > button,
        .stFormSubmitButton > button,
        .stDownloadButton > button {
            background: linear-gradient(135deg, var(--brand-primary) 0%, var(--brand-cyan) 100%);
            color: #FFFFFF !important;
            border: none;
            border-radius: var(--radius-md);
            padding: 0.55rem 1.2rem;
            font-weight: 600;
            box-shadow: var(--shadow-soft);
            transition: all 0.2s ease-in-out;
        }
        .stButton > button:hover,
        .stFormSubmitButton > button:hover,
        .stDownloadButton > button:hover {
            background: linear-gradient(135deg, var(--brand-cyan) 0%, var(--brand-teal) 100%);
            transform: translateY(-1px);
            box-shadow: 0 6px 22px rgba(34, 184, 207, 0.35);
        }
        .stButton > button:active,
        .stFormSubmitButton > button:active {
            transform: translateY(0);
        }

        /* أزرار ثانوية */
        .stButton > button[kind="secondary"] {
            background: var(--brand-surface) !important;
            color: var(--brand-primary) !important;
            border: 2px solid var(--brand-primary) !important;
        }
        .stButton > button[kind="secondary"]:hover {
            background: var(--brand-light) !important;
            color: var(--brand-deep) !important;
        }

        /* ===================== التبويبات ===================== */
        .stTabs [data-baseweb="tab-list"] {
            gap: 6px;
            border-bottom: 2px solid var(--border-soft);
        }
        .stTabs [data-baseweb="tab"] {
            background: var(--brand-surface);
            color: var(--brand-deep);
            border-radius: var(--radius-md) var(--radius-md) 0 0;
            padding: 8px 18px;
            font-weight: 600;
            border: 1px solid var(--border-soft);
            border-bottom: none;
            transition: all 0.2s ease-in-out;
        }
        .stTabs [data-baseweb="tab"]:hover {
            background: var(--brand-light);
            color: var(--brand-primary);
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, var(--brand-teal) 0%, var(--brand-cyan) 100%) !important;
            color: #FFFFFF !important;
            border-color: transparent !important;
        }
        .stTabs [data-baseweb="tab-highlight"] {
            background-color: var(--brand-cyan);
        }

        /* ===================== البطاقات والحاويات ===================== */
        div[data-testid="stMetric"],
        div[data-testid="stExpander"],
        .stForm {
            background: var(--brand-surface);
            border-radius: var(--radius-lg);
            padding: 14px;
            box-shadow: var(--shadow-soft);
            border: 1px solid var(--border-soft);
        }
        div[data-testid="stMetricValue"] {
            color: var(--brand-deep);
            font-weight: 700;
        }
        div[data-testid="stMetricLabel"] {
            color: var(--text-muted);
        }

        /* ===================== حقول الإدخال ===================== */
        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea,
        .stSelectbox div[data-baseweb="select"] > div,
        .stDateInput input {
            border: 1.5px solid var(--border-soft) !important;
            border-radius: var(--radius-md) !important;
            background: var(--brand-surface) !important;
            color: var(--text-main) !important;
        }
        .stTextInput input:focus,
        .stNumberInput input:focus,
        .stTextArea textarea:focus {
            border-color: var(--brand-cyan) !important;
            box-shadow: 0 0 0 3px rgba(34, 184, 207, 0.18) !important;
        }

        /* ===================== التنبيهات ===================== */
        div[data-testid="stAlert"] {
            border-radius: var(--radius-md);
            border-left: 5px solid var(--brand-cyan);
        }

        /* ===================== الأشرطة والتقدّم ===================== */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, var(--brand-primary), var(--brand-cyan));
        }

        /* ===================== روابط ===================== */
        a {
            color: var(--brand-primary) !important;
            text-decoration: none;
            font-weight: 600;
        }
        a:hover {
            color: var(--brand-cyan) !important;
        }

        /* ===================== الفواصل ===================== */
        hr {
            border: none;
            border-top: 2px solid var(--border-soft);
            margin: 1rem 0;
        }

        /* ===================== عناوين الأقسام الصغيرة ===================== */
        .section-title {
            color: var(--brand-deep);
            font-size: 1.15rem;
            font-weight: 700;
            border-right: 4px solid var(--brand-cyan);
            padding-right: 10px;
            margin: 12px 0;
        }

        /* ===================================================================
           ==================  استجابة الهاتف المحمول  ==================
           =================================================================== */
        @media (max-width: 768px) {

            /* --- الحاوية العامة --- */
            .block-container {
                padding-left: 0.8rem !important;
                padding-right: 0.8rem !important;
                padding-top: 1.2rem !important;
            }

            /* --- العناوين --- */
            h1 { font-size: 1.5rem !important; }
            h2 { font-size: 1.25rem !important; }
            h3 { font-size: 1.1rem !important; }

            /* --- الشريط الجانبي --- */
            section[data-testid="stSidebar"] {
                width: 85vw !important;
                min-width: 260px !important;
            }

            /* --- الأزرار: عرض كامل + هدف لمس مريح --- */
            .stButton > button,
            .stFormSubmitButton > button,
            .stDownloadButton > button {
                width: 100% !important;
                padding: 0.75rem 1rem !important;
                font-size: 1rem !important;
                min-height: var(--tap-target);
            }

            /* --- حقول الإدخال --- */
            .stTextInput input,
            .stNumberInput input,
            .stTextArea textarea,
            .stDateInput input,
            .stSelectbox div[data-baseweb="select"] > div {
                min-height: var(--tap-target) !important;
                font-size: 1rem !important;
                padding: 0.5rem 0.75rem !important;
            }

            /* --- التبويبات: تمرير أفقي --- */
            .stTabs [data-baseweb="tab-list"] {
                overflow-x: auto;
                flex-wrap: nowrap;
                scrollbar-width: thin;
                -webkit-overflow-scrolling: touch;
            }
            .stTabs [data-baseweb="tab"] {
                flex-shrink: 0;
                padding: 8px 14px;
                font-size: 0.95rem;
            }

            /* --- الجداول: تمرير أفقي --- */
            div[data-testid="stDataFrame"],
            div[data-testid="stTable"] {
                overflow-x: auto !important;
                -webkit-overflow-scrolling: touch;
            }

            /* --- الأعمدة: تكديس كامل (الخيار أ) --- */
            div[data-testid="column"] {
                min-width: 100% !important;
                flex: 1 1 100% !important;
            }

            /* --- المقاييس --- */
            div[data-testid="stMetric"] {
                padding: 10px !important;
            }
            div[data-testid="stMetricValue"] {
                font-size: 1.4rem !important;
            }

            /* --- التنبيهات --- */
            div[data-testid="stAlert"] {
                padding: 0.6rem !important;
                font-size: 0.95rem !important;
            }

            /* --- الصور --- */
            img {
                max-width: 100% !important;
                height: auto !important;
            }
        }

        /* ===================== شاشات صغيرة جداً (≤ 480px) ===================== */
        @media (max-width: 480px) {

            .block-container {
                padding-left: 0.5rem !important;
                padding-right: 0.5rem !important;
            }

            h1 { font-size: 1.3rem !important; }
            h2 { font-size: 1.1rem !important; }

            .stButton > button,
            .stFormSubmitButton > button {
                font-size: 0.95rem !important;
            }

            .section-title {
                font-size: 1rem !important;
            }

            div[data-testid="stDataFrame"] {
                font-size: 0.85rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )