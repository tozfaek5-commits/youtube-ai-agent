import os
from flask import Flask, request, jsonify
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import asyncio
import edge_tts
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip
import textwrap
import time

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

def upload_to_youtube(video_path, title, description, tags=[]):
    youtube = get_youtube_client()
    body = {
        "snippet": {"title": title[:95], "description": description, "tags": tags[:15], "categoryId": "27"},
        "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False}
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    return resp

async def generate_audio_edge(text, output_path):
    # صوت عربي احترافي من مايكروسوفت - لا ينحظر
    communicate = edge_tts.Communicate(text, "ar-SA-HamedNeural", rate="+0%", volume="+0%")
    await communicate.save(output_path)

def create_video_from_text(topic, output_path="/tmp/final_video.mp4"):
    script = f"موضوع اليوم: {topic}. في هذا الفيديو سنتعرف على أهم المعلومات حول {topic}. هذه المعلومات مفيدة جداً وستساعدك على فهم الموضوع بشكل أفضل."
    
    audio_path = "/tmp/audio.mp3"
    
    # محاولة توليد الصوت مع إعادة محاولة
    for attempt in range(3):
        try:
            asyncio.run(generate_audio_edge(script, audio_path))
            break
        except Exception as e:
            print(f"TTS attempt {attempt+1} failed: {e}")
            time.sleep(2)
            if attempt == 2:
                raise e
    
    img_path = "/tmp/bg.jpg"
    img = Image.new('RGB', (1280, 720), color=(15, 15, 30))
    draw = ImageDraw.Draw(img)
    try: font = ImageFont.truetype("arial.ttf", 60)
    except: font = ImageFont.load_default()
    wrapped = textwrap.fill(topic, width=20)
    draw.text((100, 300), wrapped, fill=(255, 255, 255), font=font, spacing=20)
    img.save(img_path)
    
    audio_clip = AudioFileClip(audio_path)
    image_clip = ImageClip(img_path, duration=audio_clip.duration).set_audio(audio_clip)
    image_clip.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac', logger=None)
    
    return output_path, script

@app.route("/")
def home():
    return jsonify({"status": "Live ✅ Fixed TTS", "youtube_configured": bool(os.getenv("GOOGLE_REFRESH_TOKEN"))})

@app.route("/test")
def test_page():
    return """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YouTube AI Agent</title>
<style>
body{font-family:Tahoma;background:#0f0f1e;color:#fff;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0}
.card{background:#1e1e3a;padding:30px;border-radius:15px;width:90%;max-width:500px;box-shadow:0 10px 30px rgba(0,0,0,0.5)}
h1{text-align:center;color:#ff4757}
input,textarea{width:100%;padding:12px;margin:10px 0;border-radius:8px;border:none;background:#2a2a4a;color:#fff;font-size:16px;box-sizing:border-box}
button{width:100%;padding:15px;background:#ff4757;color:#fff;border:none;border-radius:8px;font-size:18px;font-weight:bold;cursor:pointer;margin-top:10px}
button:hover{background:#e84118}
#result{margin-top:20px;padding:15px;background:#2a2a4a;border-radius:8px;display:none}
a{color:#70a1ff}
</style>
</head>
<body>
<div class="card">
<h1>🎬 YouTube AI Agent 🎬</h1>
<p style="text-align:center;color:#aaa">يكتب ويرفع كـ Private Draft - تم إصلاح الصوت</p>
<input id="topic" placeholder="موضوع الفيديو" value="قصة عن الجيران">
<input id="title" placeholder="عنوان الفيديو">
<textarea id="desc" placeholder="وصف الفيديو"></textarea>
<button onclick="generate()">🚀 ولّد وارفع كمسودة Private</button>
<div id="result"></div>
</div>
<script>
async function generate(){
  const topic=document.getElementById('topic').value;
  const title=document.getElementById('title').value || topic + ' | فيديو AI';
  const desc=document.getElementById('desc').value || 'فيديو تعليمي عن ' + topic;
  const btn=document.querySelector('button');
  const resDiv=document.getElementById('result');
  btn.innerText='⏳ جاري التوليد والرفع... دقيقة واحدة';
  btn.disabled=true;
  resDiv.style.display='block';
  resDiv.innerHTML='⏳ يتم توليد الصوت الاحترافي والفيديو ورفعه... لا تغلق الصفحة';
  try{
    const r=await fetch('/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topic,title,description:desc})});
    const data=await r.json();
    if(data.success){
      resDiv.innerHTML=`✅ <b>تم الرفع كمسودة Private!</b><br><br>🎬 <a href="${data.youtube_url}" target="_blank">${data.youtube_url}</a><br><br>🔒 اذهب إلى YouTube Studio > Content ستجده كـ Private`;
      btn.innerText='✅ تم بنجاح';
    }else{
      resDiv.innerHTML='❌ خطأ: '+data.error;
      btn.innerText='حاول مرة أخرى';
    }
  }catch(e){
    resDiv.innerHTML='❌ خطأ: '+e;
    btn.innerText='حاول مرة أخرى';
  }
  btn.disabled=false;
}
</script>
</body>
</html>
    """

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json or {}
    topic = data.get("topic", "قصة عن الجيران")
    title = data.get("title", f"{topic} | فيديو AI")
    description = data.get("description", f"فيديو عن {topic}")
    try:
        video_path, script = create_video_from_text(topic)
        result = upload_to_youtube(video_path, title, description, tags=[topic, "AI"])
        return jsonify({"success": True, "youtube_id": result["id"], "youtube_url": f"https://www.youtube.com/watch?v={result['id']}"})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
