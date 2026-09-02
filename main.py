import os
import uuid
from flask import Flask, request, jsonify
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# لمكتبات الفيديو
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip
import textwrap

app = Flask(__name__)

# ========== إعداد يوتيوب ==========
def get_youtube_client():
    creds = Credentials(
        token=None,
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )
    creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)

def upload_to_youtube(video_path, title, description, tags=[]):
    youtube = get_youtube_client()
    body = {
        "snippet": {
            "title": title[:95],
            "description": description,
            "tags": tags[:15],
            "categoryId": "27"
        },
        "status": {
            "privacyStatus": "private", # قاعدتك الذهبية: مسودة خاصة
            "selfDeclaredMadeForKids": False
        }
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    return resp

# ========== توليد الفيديو ==========
def create_video_from_text(topic, output_path="/tmp/final_video.mp4"):
    # 1. توليد النص
    script = f"""
    موضوع اليوم: {topic}.
    في هذا الفيديو سنتعرف على أهم المعلومات حول {topic}.
    هذه المعلومات مفيدة جداً وستساعدك على فهم الموضوع بشكل أفضل.
    لا تنسى الاشتراك في القناة وتفعيل الجرس ليصلك كل جديد.
    """
    
    # 2. توليد الصوت
    audio_path = "/tmp/audio.mp3"
    tts = gTTS(text=script, lang='ar', slow=False)
    tts.save(audio_path)
    
    # 3. توليد صورة بخلفية
    img_path = "/tmp/bg.jpg"
    img = Image.new('RGB', (1280, 720), color=(15, 15, 30))
    draw = ImageDraw.Draw(img)
    
    # حاول تحميل خط عربي إن وجد
    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        font = ImageFont.load_default()
    
    wrapped = textwrap.fill(topic, width=25)
    draw.text((100, 300), wrapped, fill=(255, 255, 255), font=font, spacing=20)
    img.save(img_path)
    
    # 4. دمج الصورة والصوت
    audio_clip = AudioFileClip(audio_path)
    image_clip = ImageClip(img_path, duration=audio_clip.duration)
    image_clip = image_clip.set_audio(audio_clip)
    image_clip.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')
    
    return output_path, script

# ========== الروابط ==========
@app.route("/")
def home():
    return jsonify({
        "status": "Live ✅",
        "message": "YouTube AI Agent Ready - Full Auto (Generate + Private Upload)",
        "youtube_configured": bool(os.getenv("GOOGLE_REFRESH_TOKEN")),
        "endpoints": {
            "POST /generate": "body: {topic, title, description}"
        }
    })

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json or {}
    topic = data.get("topic", "فوائد الصيام")
    title = data.get("title", f"{topic} | فيديو AI")
    description = data.get("description", f"فيديو تعليمي عن {topic} تم توليده بواسطة الذكاء الاصطناعي")
    
    try:
        video_path, script = create_video_from_text(topic)
        result = upload_to_youtube(video_path, title, description, tags=[topic, "AI", "تعليم"])
        
        return jsonify({
            "success": True,
            "topic": topic,
            "youtube_id": result["id"],
            "youtube_url": f"https://www.youtube.com/watch?v={result['id']}",
            "status": "PRIVATE - اذهب لـ YouTube Studio وانشره يدوياً",
            "script": script
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
