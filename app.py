import streamlit as st
import pandas as pd
import numpy as np
import pickle
from rapidfuzz import fuzz
import sys
sys.path.insert(0, '.')
from src import config
import hashlib
from datetime import datetime
from src.qr_utils import (
    make_patient_qr,
    make_full_record_qr,
    qr_to_png_bytes,
    parse_qr_text,
    decode_record,
    estimate_record_qr_ok,
)

# ============ إعداد الصفحة ============
st.set_page_config(
    page_title="شفائي - الملف الصحي الرقمي",
    page_icon="🩺",
    layout="wide"
)

# ============ قراءة patient_id من رابط QR ============
try:
    _qp = st.query_params
    _auto_pid = _qp.get("patient", None)
    if _auto_pid:
        st.session_state["_auto_scan_pid"] = _auto_pid
except Exception:
    pass

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

    # --- الموديل ---
    try:
        with open(config.MODEL_FILE, 'rb') as f:
            systems['drug_model'] = pickle.load(f)
        print(f"✅ الموديل محمّل: {config.MODEL_FILE}")
    except Exception as e:
        systems['drug_model'] = None
        print(f"❌ خطأ في الموديل: {e}")

    # --- التفاعلات ---
    try:
        systems['interactions'] = pd.read_excel(config.INTERACTIONS_FILE)
        print(f"✅ التفاعلات: {len(systems['interactions'])} صف")
    except Exception as e:
        systems['interactions'] = None
        print(f"❌ خطأ في التفاعلات: {e}")

    # --- PK-DDI ---
    try:
        systems['pk_ddi'] = pd.read_excel(config.PK_DDI_FILE)
        print(f"✅ PK-DDI: {len(systems['pk_ddi'])} صف")
    except Exception as e:
        systems['pk_ddi'] = None
        print(f"❌ خطأ في PK-DDI: {e}")

    # --- QA ---
    try:
        systems['qa_data'] = pd.read_csv(config.QA_DATA_FILE)
        print(f"✅ QA: {len(systems['qa_data'])} سؤال")
    except Exception as e:
        systems['qa_data'] = None
        print(f"❌ خطأ في QA: {e}")

    # --- Interaction Checker ---
    try:
        from src.interactions import InteractionChecker
        systems['interaction_checker'] = InteractionChecker()
        print("✅ InteractionChecker جاهز")
    except Exception as e:
        systems['interaction_checker'] = None
        print(f"❌ خطأ في InteractionChecker: {e}")

    # --- Drug Info Checker ---
    try:
        from src.drug_info import DrugInfoChecker
        systems['drug_info_checker'] = DrugInfoChecker()
        print("✅ DrugInfoChecker جاهز")
    except Exception as e:
        systems['drug_info_checker'] = None
        print(f"❌ خطأ في DrugInfoChecker: {e}")

    # --- الصيدليات ---
    systems['pharmacies'] = [
        {'name': 'صيدلية الأمل', 'location': 'شارع جمال عبد الناصر', 'phone': '061-1234567', 'hours': '8:00 - 22:00'},
        {'name': 'صيدلية الشفاء', 'location': 'شارع عمر المختار', 'phone': '061-7654321', 'hours': '24 ساعة'},
        {'name': 'صيدلية بنغازي', 'location': 'شارع الاستقلال', 'phone': '061-9876543', 'hours': '9:00 - 23:00'},
        {'name': 'صيدلية السلام', 'location': 'شارع فلسطين', 'phone': '061-3456789', 'hours': '8:00 - 21:00'},
        {'name': 'صيدلية النور', 'location': 'شارع دبي', 'phone': '061-2345678', 'hours': '10:00 - 22:00'},
    ]

    # --- المخزون ---
    np.random.seed(42)
    medicines = [
    'باراسيتامول', 'بنادول', 'Panadol', 'أدول', 'Adol',
    'إيبوبروفين', 'بروفين', 'Brufen',
    'أسبرين', 'Aspirin',
    'أموكسيسيلين', 'Amoxicillin',
    'أوميبرازول', 'Omeprazole',
    'أتورفاستاتين', 'Atorvastatin',
    'ميتفورمين', 'Metformin', 'غلوكوفاج',
    'أملوديبين', 'Amlodipine',
    'وارفارين', 'Warfarin',
    'سيتيريزين', 'Cetirizine',
    'فولتارين', 'Voltaren',
    'كونكور', 'Concor',
]
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
# ============ تهيئة مخزن الملفات الصحية ============
if "health_records" not in st.session_state:
    st.session_state["health_records"] = {}

def save_record(record: dict) -> None:
    pid = str(record.get("patient_id", "")).strip()
    if pid:
        st.session_state["health_records"][pid] = record

def load_record(patient_id: str):
    return st.session_state["health_records"].get(str(patient_id).strip())
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
    sub_create, sub_qr, sub_scan = st.tabs(
        ["🆕 إنشاء ملف", "📱 عرض QR", "🩺 مسح QR (للطبيب)"]
    )

    # ---------- تبويب فرعي 1: إنشاء ملف ----------
    with sub_create:
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
                patient_id = hashlib.sha256(
                    f"{name}{age}{datetime.now()}".encode()
                ).hexdigest()[:16]

                record = {
                    "patient_id": patient_id,
                    "name": name,
                    "age": int(age),
                    "gender": gender,
                    "blood_type": blood,
                    "chronic": [x.strip() for x in diseases.split(",") if x.strip()],
                    "allergies": [x.strip() for x in allergies.split(",") if x.strip()],
                    "medications": [],
                    "notes": "",
                }
                save_record(record)
                st.session_state["_last_pid"] = patient_id

                st.markdown(f"""
                <div class="success-box">
                    <h3>✅ تم إنشاء الملف الصحي بنجاح!</h3>
                    <p><strong>رقم الملف:</strong> {patient_id}</p>
                    <p><strong>الاسم:</strong> {name}</p>
                    <p><strong>العمر:</strong> {age} سنة</p>
                    <p><strong>فصيلة الدم:</strong> {blood}</p>
                    <p>👉 انتقلي لتبويب «📱 عرض QR» لتوليد كود المشاركة</p>
                </div>
                """, unsafe_allow_html=True)

    # ---------- تبويب فرعي 2: عرض QR ----------
    with sub_qr:
        st.header("📱 رمز QR للملف الصحي")
        default_pid = st.session_state.get("_last_pid", "")
        pid = st.text_input("رقم المريض", value=default_pid, key="qr_pid").strip()

        if not pid:
            st.info("👆 أدخلي رقم المريض لعرض QR الخاص به")
        else:
            record = load_record(pid)
            if not record:
                st.error("❌ لا يوجد ملف بهذا الرقم في هذه الجلسة")
            else:
                st.markdown("### 🔗 QR أساسي (رابط المريض)")
                st.caption("خفيف وسريع — يشتغل مع الطبيب على نفس الجهاز/الجلسة")

                img_basic = make_patient_qr(pid)
                st.image(
                    qr_to_png_bytes(img_basic),
                    caption=f"shifai://patient/{pid}",
                    width=260,
                )
                st.download_button(
                    "⬇️ تنزيل QR أساسي (PNG)",
                    data=qr_to_png_bytes(img_basic),
                    file_name=f"shifai_qr_{pid}.png",
                    mime="image/png",
                    key="dl_basic",
                )

                st.markdown("---")
                st.markdown("### 📦 QR كامل (يحتوي كل بيانات الملف)")
                st.caption("يعمل على أي جهاز — لكن أكبر حجماً")

                if estimate_record_qr_ok(record):
                    img_full = make_full_record_qr(record)
                    st.image(
                        qr_to_png_bytes(img_full),
                        caption="QR مضغوط يحتوي الملف كاملاً",
                        width=320,
                    )
                    st.download_button(
                        "⬇️ تنزيل QR كامل (PNG)",
                        data=qr_to_png_bytes(img_full),
                        file_name=f"shifai_fullqr_{pid}.png",
                        mime="image/png",
                        key="dl_full",
                    )
                else:
                    st.warning("⚠️ الملف كبير جداً ليُضمَّن في QR كامل. استخدمي QR الأساسي.")

    # ---------- تبويب فرعي 3: مسح QR (للطبيب) ----------
    with sub_scan:
        st.header("🩺 مسح QR (للطبيب)")
        st.caption("الصقي هنا النص المستخرج من ماسح QR")
                # فحص تلقائي: لو جاي patient_id من رابط QR
        auto_pid = st.session_state.pop("_auto_scan_pid", None)
        if auto_pid:
            st.success(f"✅ تم استقبال ملف من QR: {auto_pid}")
            rec = load_record(auto_pid)
            if rec:
                _render_patient_record(rec)
            else:
                st.warning(
                    f"⚠️ الملف {auto_pid} غير موجود في هذه الجلسة.\n\n"
                    "**الحل:** استخدمي QR الكامل، أو أنشئي الملف من نفس الجهاز."
                )
            st.markdown("---")
            st.caption("أو الصقي نص QR يدوياً:")
            
        qr_text = st.text_area(
            "نص QR",
            height=100,
            key="qr_input",
            placeholder="shifai://patient/xxxx  أو  shifai://record/xxxx",
        )

        if st.button("🔍 فحص الملف", key="scan_btn"):
            parsed = parse_qr_text(qr_text)

            if not parsed:
                st.error("❌ نص QR غير صالح. تأكدي أنه يبدأ بـ shifai://")
            elif parsed["kind"] == "patient":
                pid2 = parsed["patient_id"]
                rec = load_record(pid2)
                if rec:
                    st.success(f"✅ تم العثور على الملف: {pid2}")
                    _render_patient_record(rec)
                else:
                    st.warning(
                        f"⚠️ الملف {pid2} غير موجود في هذه الجلسة.\n\n"
                        "اطلبي من المريض QR الكامل أو أنشئي الملف على نفس الجهاز."
                    )
            elif parsed["kind"] == "record":
                try:
                    rec = decode_record(parsed["token"])
                    st.success(f"✅ تم فك تشفير الملف: {rec.get('patient_id','؟')}")
                    _render_patient_record(rec)
                except Exception as e:
                    st.error(f"❌ فشل فك التشفير: {e}")


def _render_patient_record(rec: dict):
    """عرض الملف الصحي بشكل مرتّب."""
    st.markdown("---")
    st.markdown(f"### 👤 {rec.get('name') or 'بدون اسم'}")

    c1, c2, c3 = st.columns(3)
    c1.metric("رقم المريض", rec.get("patient_id", "-"))
    c2.metric("العمر", rec.get("age", "-"))
    c3.metric("فصيلة الدم", rec.get("blood_type") or "-")

    st.markdown(f"**الجنس:** {rec.get('gender') or '-'}")

    for key, label, icon in [
        ("chronic", "الأمراض المزمنة", "🩺"),
        ("allergies", "الحساسية", "⚠️"),
        ("medications", "الأدوية الحالية", "💊"),
    ]:
        items = rec.get(key) or []
        if items:
            st.markdown(f"**{icon} {label}:**")
            for it in items:
                st.markdown(f"- {it}")

    if rec.get("notes"):
        st.markdown("**📝 ملاحظات:**")
        st.info(rec["notes"])
        
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