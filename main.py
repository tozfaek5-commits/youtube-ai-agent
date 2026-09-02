import os, random, json
from flask import Flask, request, Response
from datetime import datetime

app = Flask(__name__)

def json_ar(data):
    # يرجع JSON بالعربي الصحيح بدون \uXXXX
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype='application/json; charset=utf-8'
    )

IDEAS = {
    "قصص": [
        "قصة شاب يمني ربح 1000$ من قناة قصص بدون ظهور",
        "قصة رجل خسر كل شيء ثم بدأ من الصفر بقصص الأنبياء",
        "كيف حولت قصة واحدة قناة صغيرة إلى 100 ألف مشترك"
    ],
    "ربح": [
        "3 مواقع تدفع لك مقابل كتابة القصص القصيرة",
        "كيف تربح من يوتيوب شورتس بالقصص في 2026",
        "طريقة تحويل القصص إلى كتب وبيعها على أمازون"
    ]
}

@app.route('/')
def home():
    # صفحة HTML جميلة بدل JSON المشفر
    return """
    <html dir='rtl' lang='ar'>
    <head><meta charset='utf-8'><title>مدير قناة يوتيوب AI</title></head>
    <body style='font-family:Arial; padding:20px; background:#f5f5f5'>
    <h1>🤖 مدير قناة يوتيوب AI - شغال!</h1>
    <p><b>المجال:</b> القصص + الربح من الإنترنت</p>
    <p><b>اليوم:</b> """ + get_today_tasks() + """</p>
    <h2>🔗 جرب الوكيل:</h2>
    <ul>
      <li><a href='/api/idea'>/api/idea - ولّد فكرة جديدة</a></li>
      <li><a href='/api/script?topic=الربح من القصص'>/api/script?topic=الربح من القصص</a></li>
      <li><a href='/api/script?topic=قصة نجاح&type=short'>/api/script?type=short (شورت)</a></li>
      <li><a href='/api/seo?topic=الربح من الانترنت'>/api/seo?topic=الربح من الانترنت</a></li>
    </ul>
    <p>✅ النشر: 3 طويلة في الأسبوع 8م KSA - 5 شورتات يوميا 10ص،1ظ،5م،8م،11م</p>
    </body></html>
    """

def get_today_tasks():
    day = datetime.now().strftime("%A")
    mapping = {
        "Monday": "فيديو طويل كامل",
        "Tuesday": "شورت + رد على التعليقات",
        "Wednesday": "فيديو طويل كامل",
        "Thursday": "شورت + رد على التعليقات",
        "Friday": "فيديو طويل كامل",
        "Saturday": "تحليل منافسين",
        "Sunday": "تقرير النمو + خطة الأسبوع القادم"
    }
    return mapping.get(day, "بحث فكرة + شورت + ردود")

@app.route('/api/idea')
def idea():
    cat = random.choice(list(IDEAS.keys()))
    return json_ar({"الفئة": cat, "الفكرة": random.choice(IDEAS[cat]), "CTR المتوقع": "88%", "الصعوبة": "سهل", "قاعدة": "لا نسخ حرفي - لا عناوين مضللة"})

@app.route('/api/script')
def script():
    topic = request.args.get('topic', 'الربح من القصص')
    is_short = request.args.get('type', 'long') == 'short'
    if is_short:
        return json_ar({"النوع": "شورت 45 ثانية", "الهوك": f"هل تعلم أن {topic} يمكن أن يغير حياتك في 30 ثانية؟", "القصة": f"القصة تبدأ عندما جربت {topic}...", "دعوة": "اشترك للمزيد"})
    else:
        return json_ar({"النوع": "فيديو طويل 8 دقائق", "الهوك": f"في أول 3 ثوان: سر {topic} الذي لا يخبرك به أحد", "المقدمة": f"اليوم نحكي قصة حقيقية عن {topic}", "المحتوى": "الجزء 1: البداية... الجزء 2: التحدي... الجزء 3: الحل...", "الختام": "اكتب رأيك في التعليقات"})

@app.route('/api/seo')
def seo():
    topic = request.args.get('topic', 'الربح من القصص')
    return json_ar({
        "العناوين المقترحة": [f"لن تصدق كيف ربحت من {topic}", f"سر {topic} في 2026", f"جربت {topic} والنتيجة صدمتني"],
        "الوصف": f"في هذا الفيديو نتحدث عن {topic} بطريقة شرعية وملتزمة بسياسات يوتيوب.\n#قصص #ربح_من_الانترنت",
        "التاغات": [topic, "قصص واقعية", "الربح من الانترنت", "اليمن"],
        "فكرة Thumbnail": f"{topic} - قبل وبعد + وجه متفاجئ",
        "قاعدة ذهبية": "لا نشر دون موافقة بشرية نهائية"
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
