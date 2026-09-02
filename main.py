import os
from flask import Flask, request, jsonify
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip
import textwrap

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

def create_video_from_text(topic, output_path="/tmp/final_video.mp4"):
    script = f"موضوع اليوم: {topic}. في هذا الفيديو سنتعرف على أهم المعلومات حول {topic}. هذه المعلومات مفيدة جداً."
    audio_path = "/tmp/audio.mp3"
    tts = gTTS(text=script, lang='ar', slow=False)
    tts.save(audio_path)
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
    image_clip.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')
    return output_path, script

@app.route("/")
def home():
    return jsonify({"status": "Live ✅", "youtube_configured": bool(os.getenv("GOOGLE_REFRESH_TOKEN"))})

@app.route("/test")
def test_page():
    return """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>اختبار YouTube AI Agent</title>
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
<h1>🎬 YouTube AI Agent</h1>
<p style="text-align:center;color:#aaa">يكتب ويرفع كـ Private Draft</p>
<input id="topic" placeholder="موضوع الفيديو - مثال: فوائد الصيام" value="فوائد الصيام">
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
  btn.innerText='⏳ جاري التوليد والرفع... قد يستغرق دقيقة';
  btn.disabled=true;
  resDiv.style.display='block';
  resDiv.innerHTML='⏳ يتم توليد الصوت والفيديو ورفعه... لا تغلق الصفحة';
  try{
    const r=await fetch('/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topic,title,description:desc})});
    const data=await r.json();
    if(data.success){
      resDiv.innerHTML=`✅ <b>تم الرفع كمسودة Private!</b><br><br>🎬 <a href="${data.youtube_url}" target="_blank">${data.youtube_url}</a><br><br>🔒 اذهب إلى YouTube Studio > Content ستجده كـ Private<br>اضغط Publish عندما تريد نشره يدوياً`;
      btn.innerText='✅ تم بنجاح - جرب موضوع آخر';
    }else{
      resDiv.innerHTML='❌ خطأ: '+data.error;
      btn.innerText='حاول مرة أخرى';
    }
  }catch(e){
    resDiv.innerHTML='❌ خطأ في الاتصال: '+e;
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
    topic = data.get("topic", "فوائد الصيام")
    title = data.get("title", f"{topic} | فيديو AI")
    description = data.get("description", f"فيديو تعليمي عن {topic}")
    try:
        video_path, script = create_video_from_text(topic)
        result = upload_to_youtube(video_path, title, description, tags=[topic, "AI"])
        return jsonify({"success": True, "youtube_id": result["id"], "youtube_url": f"https://www.youtube.com/watch?v={result['id']}", "status": "PRIVATE"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
