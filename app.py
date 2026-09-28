import streamlit as st
import pandas as pd
import numpy as np
import pickle
from fuzzywuzzy import fuzz
import hashlib
from datetime import datetime

# ============ إعداد الصفحة ============
st.set_page_config(
    page_title="شفائي - الملف الصحي الرقمي",
    page_icon="🩺",
    layout="wide"
)

# ============ CSS عربي ============
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    * { font-family: 'Tajawal', sans-serif; direction: rtl; }
    .main-header {
        background: linear-gradient(135deg, #2E86C1, #3498DB);
        padding: 30px; border-radius: 15px; color: white; text-align: center;
        margin-bottom: 30px;
    }
    .stButton>button {
        background: #2E86C1; color: white; border-radius: 10px;
        padding: 10px 30px; font-weight: bold; width: 100%;
    }
    .success-box {
        background: #d4edda; padding: 20px; border-radius: 10px;
        border-right: 5px solid #27AE60;
    }
    .danger-box {
        background: #f8d7da; padding: 20px; border-radius: 10px;
        border-right: 5px solid #E74C3C;
    }
    .warning-box {
        background: #fff3cd; padding: 20px; border-radius: 10px;
        border-right: 5px solid #F39C12;
    }
</style>
""", unsafe_allow_html=True)

# ============ العنوان ============
st.markdown("""
<div class="main-header">
    <h1>🩺 تطبيق شفائي</h1>
    <p>الملف الصحي الرقمي الأول في بنغازي - ليبيا</p>
    <p style="font-size: 14px;">فريق Hacktivists | مؤسسة رؤية</p>
</div>
""", unsafe_allow_html=True)

# ============ تحميل الأنظمة ============
@st.cache_resource
def load_systems():
    systems = {}
    
    try:
        with open('drug_prediction_model.pkl', 'rb') as f:
            systems['drug_model'] = pickle.load(f)
    except:
        systems['drug_model'] = None
    
    try:
        systems['interactions'] = pd.read_excel('db_drug_interactions.xlsx')
    except:
        systems['interactions'] = None
    
    try:
        systems['pk_ddi'] = pd.read_excel('PK-DDI DB.xlsx')
    except:
        systems['pk_ddi'] = None
    
    try:
        systems['qa_data'] = pd.read_excel('AHD_english_small.xlsx')
    except:
        systems['qa_data'] = None
    
    systems['pharmacies'] = [
        {'name': 'صيدلية الأمل', 'location': 'شارع جمال عبد الناصر', 'phone': '061-1234567', 'hours': '8:00 - 22:00'},
        {'name': 'صيدلية الشفاء', 'location': 'شارع عمر المختار', 'phone': '061-7654321', 'hours': '24 ساعة'},
        {'name': 'صيدلية بنغازي', 'location': 'شارع الاستقلال', 'phone': '061-9876543', 'hours': '9:00 - 23:00'},
        {'name': 'صيدلية السلام', 'location': 'شارع فلسطين', 'phone': '061-3456789', 'hours': '8:00 - 21:00'},
        {'name': 'صيدلية الحياة', 'location': 'طريق المطار', 'phone': '061-2345678', 'hours': '10:00 - 22:00'},
    ]
    
    np.random.seed(42)
    medicines = ['باراسيتامول', 'إيبوبروفين', 'أموكسيسيلين', 'أوميبرازول', 'ميتفورمين',
                 'أسبرين', 'وارفارين', 'أتورفاستاتين', 'أملوديبين', 'ليسينوبريل']
    inventory = {}
    for pharm in systems['pharmacies']:
        inventory[pharm['name']] = {}
        for med in medicines:
            inventory[pharm['name']][med] = {
                'price': round(np.random.uniform(10, 60), 2),
                'quantity': int(np.random.randint(20, 150))
            }
    systems['inventory'] = inventory
    
    return systems

systems = load_systems()

# ============ التبويبات ============
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 الملف الصحي",
    "💊 التفاعلات الدوائية",
    "🔮 التنبؤ بالدواء",
    "🏥 البحث عن دواء",
    "❓ استفسار طبي"
])

# ============ تبويب 1 ============
with tab1:
    st.header("📋 إنشاء ملف صحي جديد")
    
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("الاسم الكامل")
        age = st.number_input("العمر", min_value=1, max_value=120, value=30)
        gender = st.selectbox("الجنس", ["ذكر", "أنثى"])
    with col2:
        blood = st.selectbox("فصيلة الدم", ["A+","A-","B+","B-","AB+","AB-","O+","O-"])
        diseases = st.text_input("الأمراض المزمنة (مفصولة بفواصل)")
        allergies = st.text_input("الحساسية (مفصولة بفواصل)")
    
    if st.button("إنشاء الملف الصحي"):
        if not name:
            st.error("❌ الرجاء إدخال الاسم")
        else:
            patient_id = hashlib.sha256(f"{name}{age}{datetime.now()}".encode()).hexdigest()[:16]
            st.markdown(f"""
            <div class="success-box">
                <h3>✅ تم إنشاء الملف الصحي بنجاح!</h3>
                <p><strong>رقم الملف:</strong> {patient_id}</p>
                <p><strong>الاسم:</strong> {name}</p>
                <p><strong>العمر:</strong> {age} سنة</p>
                <p><strong>فصيلة الدم:</strong> {blood}</p>
                <p>🔒 شارك هذا الرقم مع طبيبك للاطلاع على ملفك</p>
            </div>
            """, unsafe_allow_html=True)

# ============ تبويب 2 ============
with tab2:
    st.header("💊 فحص التفاعلات الدوائية")
    
    drugs_input = st.text_input("الأدوية (مفصولة بفواصل)", 
                                 placeholder="مثال: باراسيتامول, إيبوبروفين, أسبرين")
    
    if st.button("فحص التفاعلات"):
        if not drugs_input:
            st.error("❌ الرجاء إدخال الأدوية")
        else:
            drugs = [d.strip() for d in drugs_input.split(',') if d.strip()]
            
            if len(drugs) < 2:
                st.warning("⚠️ أدخل دواءين على الأقل")
            else:
                interactions_found = []
                df = systems.get('interactions')
                
                if df is not None:
                    cols = df.columns.tolist()
                    for i in range(len(drugs)):
                        for j in range(i+1, len(drugs)):
                            d1, d2 = drugs[i], drugs[j]
                            match = df[
                                ((df[cols[0]].astype(str).str.lower() == d1.lower()) & 
                                 (df[cols[1]].astype(str).str.lower() == d2.lower())) |
                                ((df[cols[0]].astype(str).str.lower() == d2.lower()) & 
                                 (df[cols[1]].astype(str).str.lower() == d1.lower()))
                            ]
                            if not match.empty:
                                interactions_found.append({
                                    'd1': d1, 'd2': d2,
                                    'desc': str(match.iloc[0][cols[2]]) if len(cols) > 2 else 'تفاعل موثق'
                                })
                
                if interactions_found:
                    for inter in interactions_found:
                        st.markdown(f"""
                        <div class="danger-box">
                            <h4>🔴 {inter['d1']} + {inter['d2']}</h4>
                            <p>{inter['desc']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="success-box">
                        <h3>✅ لا توجد تفاعلات دوائية معروفة بين هذه الأدوية</h3>
                    </div>
                    """, unsafe_allow_html=True)

# ============ تبويب 3 ============
with tab3:
    st.header("🔮 التنبؤ بالدواء المناسب")
    
    col1, col2 = st.columns(2)
    with col1:
        p_age = st.number_input("العمر", min_value=1, max_value=120, value=45, key='p_age')
        p_gender = st.selectbox("الجنس", ["M", "F"])
    with col2:
        p_bp = st.selectbox("ضغط الدم", ["HIGH", "LOW", "NORMAL"])
        p_chol = st.selectbox("الكوليسترول", ["HIGH", "NORMAL"])
    p_nak = st.number_input("Na_to_K", min_value=0.0, max_value=50.0, value=12.5, step=0.1)
    
    if st.button("🔮 تنبؤ بالدواء"):
        model_data = systems.get('drug_model')
        if model_data is None:
            st.error("❌ النموذج غير محمّل")
        else:
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
                st.error(f"خطأ: {e}")

# ============ تبويب 4 ============
with tab4:
    st.header("🏥 البحث عن دواء في الصيدليات")
    
    med_search = st.text_input("اسم الدواء", placeholder="مثال: باراسيتامول")
    
    if st.button("🔍 بحث"):
        if not med_search:
            st.error("❌ الرجاء إدخال اسم الدواء")
        else:
            results = []
            inventory = systems.get('inventory', {})
            pharmacies = systems.get('pharmacies', [])
            
            for pharm in pharmacies:
                for med_name, info in inventory.get(pharm['name'], {}).items():
                    if med_search.lower() in med_name.lower():
                        results.append({
                            'pharmacy': pharm['name'],
                            'location': pharm['location'],
                            'phone': pharm['phone'],
                            'hours': pharm['hours'],
                            'price': info['price'],
                            'quantity': info['quantity']
                        })
            
            if results:
                results.sort(key=lambda x: x['price'])
                st.success(f"✅ تم العثور على {med_search} في {len(results)} صيدلية")
                
                df_results = pd.DataFrame([{
                    'الصيدلية': r['pharmacy'],
                    'الموقع': r['location'],
                    'السعر (دينار)': f"{r['price']:.2f}",
                    'الكمية': r['quantity'],
                    'الهاتف': r['phone'],
                    'مواعيد العمل': r['hours']
                } for r in results])
                
                st.dataframe(df_results, use_container_width=True)
            else:
                st.warning(f"لم يتم العثور على {med_search}")

# ============ تبويب 5 ============
with tab5:
    st.header("❓ اسأل عن استفسارك الطبي")
    
    query = st.text_area("سؤالك", placeholder="اكتب سؤالك الطبي هنا...")
    
    if st.button("📤 إرسال"):
        if not query:
            st.error("❌ الرجاء كتابة سؤالك")
        else:
            qa_data = systems.get('qa_data')
            if qa_data is None:
                st.warning("⚠️ قاعدة الأسئلة الطبية غير محمّلة")
            else:
                qa_data = qa_data.dropna(subset=['Question', 'Answer'])
                
                best_match = None
                best_score = 0
                
                for _, row in qa_data.iterrows():
                    score = fuzz.token_sort_ratio(query.lower(), str(row['Question']).lower())
                    if score > best_score:
                        best_score = score
                        best_match = row
                
                if best_match is not None and best_score > 50:
                    st.markdown(f"""
                    <div class="success-box">
                        <h3>📋 أفضل إجابة</h3>
                        <p><strong>السؤال المشابه:</strong> {best_match['Question']}</p>
                        <p><strong>الإجابة:</strong> {best_match['Answer']}</p>
                        <p><strong>نسبة التطابق:</strong> {best_score}%</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ لم أجد إجابة مناسبة، يرجى استشارة الطبيب")