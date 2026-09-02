import os
from flask import Flask, request, jsonify
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import asyncio

app = Flask(__name__)

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

@app.route("/")
def home():
    return jsonify({"status": "Live ✅ Final Fixed", "youtube_ready": bool(os.getenv("GOOGLE_REFRESH_TOKEN"))})

@app.route("/test")
def test_page():
    return """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head><meta charset="UTF-8"><title>YouTube AI</title>
<style>body{font-family:Tahoma;background:#0f0f1e;color:#fff;text-align:center;padding:40px}
.card{background:#1e1e3a;padding:25px;border-radius:12px;max-width:450px;margin:auto}
input{width:100%;padding:12px;margin:10px 0;border-radius:8px;border:none;background:#2a2a4a;color:#fff}
button{width:100%;padding:14px;background:#ff4757;color:#fff;border:none;border-radius:8px;font-weight:bold;cursor:pointer}
#res{margin-top:15px;padding:12px;background:#2a2a4a;border-radius:8px;display:none}
a{color:#70a1ff}
</style></head>
<body>
<div class="card">
<h2>🎬 YouTube AI Agent 🎬</h2>
<p style="color:#aaa;font-size:13px">تم إصلاح set_audio ✅</p>
<input id="topic" value="قصة عن تحقيق الحلم" placeholder="موضوع الفيديو">
<button id="btn" onclick="gen()">🚀 ولد وارفع كـ Private</button>
<div id="res"></div>
</div>
<script>
async function gen(){
  const t=document.getElementById('topic').value;
  const b=document.getElementById('btn');
  const r=document.getElementById('res');
  b.innerText='⏳ جاري التوليد... 60 ثانية'; b.disabled=true; r.style.display='block'; r.innerHTML='⏳ توليد صوت Hamed الاحترافي وفيديو ورفعه...';
  try{
    const resp=await fetch('/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topic:t})});
    const data=await resp.json();
    if(data.success){ r.innerHTML='✅ تم الرفع كـ Private!<br><br><a href="'+data.url+'" target="_blank">'+data.url+'</a><br><br>اذهب لـ YouTube Studio > Content'; b.innerText='✅ تم بنجاح'; }
    else{ r.innerHTML='❌ '+data.error; b.innerText='حاول مرة أخرى'; }
  }catch(e){ r.innerHTML='❌ '+e; b.innerText='حاول مرة أخرى'; }
  b.disabled=false;
}
</script>
</body></html>
"""

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json or {}
    topic = data.get("topic", "قصة عن تحقيق الحلم")
    try:
        import edge_tts
        from PIL import Image, ImageDraw
        import textwrap

        try:
            from moviepy.editor import ImageClip, AudioFileClip
        except ImportError:
            from moviepy import ImageClip, AudioFileClip

        async def make_audio(txt, out):
            await edge_tts.Communicate(txt, "ar-SA-HamedNeural").save(out)

        script = f"قصة عن {topic}. {topic} هو موضوع مهم جدا يستحق ان نتحدث عنه بالتفصيل."
        asyncio.run(make_audio(script, "/tmp/audio.mp3"))

        img = Image.new('RGB', (1280, 720), color=(15, 15, 35))
        draw = ImageDraw.Draw(img)
        draw.text((100, 300), textwrap.fill(topic, width=20), fill=(255,255,255))
        img.save("/tmp/bg.jpg")

        audio_clip = AudioFileClip("/tmp/audio.mp3")
        image_clip = ImageClip("/tmp/bg.jpg", duration=audio_clip.duration)

        # إصلاح moviepy v1 vs v2
        try:
            final_clip = image_clip.set_audio(audio_clip)  # v1
        except AttributeError:
            final_clip = image_clip.with_audio(audio_clip)  # v2 الجديد

        final_clip.write_videofile("/tmp/final.mp4", fps=24, codec='libx264', audio_codec='aac', logger=None)

        youtube = get_youtube_client()
        body = {"snippet": {"title": topic[:95], "description": f"فيديو عن {topic} - تم إنشاؤه تلقائيا", "categoryId": "27"}, "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False}}
        media = MediaFileUpload("/tmp/final.mp4", chunksize=-1, resumable=True, mimetype="video/mp4")
        req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        resp = None
        while resp is None:
            _, resp = req.next_chunk()

        return jsonify({"success": True, "url": f"https://www.youtube.com/watch?v={resp['id']}"})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
