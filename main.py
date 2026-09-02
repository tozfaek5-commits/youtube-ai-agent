import os, random
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

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

@app.route('/')
def home():
    return jsonify({
        "agent": "مدير قناة يوتيوب AI",
        "niche": "القصص + الربح من الإنترنت",
        "today": get_today_tasks(),
        "publishing": {
            "long_videos": "3 في الأسبوع - 8:00 مساءً KSA",
            "shorts": "5 يوميا - 10ص، 1ظ، 5م، 8م، 11م"
        },
        "endpoints": ["/api/idea", "/api/script?topic=...", "/api/seo?topic=...", "/api/comment?text=..."]
    })

@app.route('/api/idea')
def idea():
    cat = request.args.get('cat', random.choice(list(IDEAS.keys())))
    return jsonify({"category": cat, "idea": random.choice(IDEAS[cat]), "ctr_potential": "88%", "keyword": "سهل"})

@app.route('/api/script')
def script():
    topic = request.args.get('topic', 'الربح من القصص')
    is_short = request.args.get('type', 'long') == 'short'
    if is_short:
        return jsonify({"hook": f"هل تعلم أن {topic} يمكن أن يغير حياتك في 30 ثانية؟", "body": f"القصة تبدأ عندما... {topic}", "cta": "اشترك للمزيد"})
    else:
        return jsonify({"hook": f"في أول 3 ثوان: سر {topic} الذي لا يخبرك به أحد", "intro": f"اليوم نحكي قصة حقيقية عن {topic}", "story": "الجزء 1: البداية... الجزء 2: التحدي... الجزء 3: الحل...", "cta": "اكتب في التعليقات رأيك"})

@app.route('/api/seo')
def seo():
    topic = request.args.get('topic', 'الربح من القصص')
    return jsonify({
        "titles": [f"لن تصدق كيف ربحت من {topic}", f"سر {topic} في 2026", f"جربت {topic} والنتيجة صدمتني"],
        "description": f"في هذا الفيديو نتحدث عن {topic} بطريقة شرعية وملتزمة بسياسات يوتيوب.\n#قصص #ربح_من_الانترنت",
        "tags": [topic, "قصص واقعية", "الربح من الانترنت", "اليمن"],
        "thumbnail": f"{topic} - قبل وبعد",
        "rules": "لا عناوين مضللة - لا نسخ حرفي - مراجعة بشرية إجبارية"
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
