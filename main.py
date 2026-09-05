import os
import asyncio
from flask import Flask, request, jsonify
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import edge_tts
from PIL import Image, ImageDraw, ImageFont
import textwrap

app = Flask(__name__)

COLORS = [
    ((15,15,30), (50,30,80)),
    ((20,30,20), (40,80,40)),
    ((30,15,15), (80,30,30)),
    ((15,30,35), (30,70,80)),
    ((35,25,15), (80,60,30)),
    ((25,15,35), (60,30,70)),
]

# --- إصلاح التوافق مع MoviePy 2.x ---
try:
    from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
except ImportError:
    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

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

def upload_to_youtube(video_path, title, description):
    youtube = get_youtube_client()
    body = {
        "snippet": {
            "title": title[:95],
            "description": description,
            "tags": title.split()[:15],
            "categoryId": "27"
        },
        "status": {
            "privacyStatus": "private",
            "selfDeclaredMadeForKids": False
        }
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    return resp

async def gen_audio(text, out):
    await edge_tts.Communicate(text, "ar-SA-HamedNeural", rate="+5%").save(out)

def run_async(coro):
    """يعمل مع Flask و gunicorn بدون مشاكل event loop"""
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(coro)
        loop.close()
        return result

def create_image_with_text(text, idx, path):
    bg1, bg2 = COLORS[idx % len(COLORS)]
    img = Image.new('RGB', (1280, 720), color=bg1)
    draw = ImageDraw.Draw(img)
    for y in range(720):
        r = int(bg1[0] + (bg2[0]-bg1[0]) * y/720)
        g = int(bg1[1] + (bg2[1]-bg1[1]) * y/720)
        b = int(bg1[2] + (bg2[2]-bg1[2]) * y/720)
        draw.line([(0,y), (1280,y)], fill=(r,g,b))
    
    # خط متوافق مع سيرفرات لينكس (Render)
    font_big = None
    for font_path in ["arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVuSans.ttf"]:
        try:
            font_big = ImageFont.truetype(font_path, 55)
            break
        except:
            continue
    if font_big is None:
        font_big = ImageFont.load_default()

    wrapped = textwrap.fill(text, width=28)
    # ظل للنص
    draw.text((104, 304), wrapped, fill=(0,0,0), font=font_big, spacing=15, align="center")
    draw.text((100, 300), wrapped, fill=(255,255,255), font=font_big, spacing=15, align="center")
    img.save(path)
    return path

def add_audio_to_clip(clip, audio):
    """متوافق مع MoviePy 1.x و 2.x"""
    if hasattr(clip, 'with_audio'):
        return clip.with_audio(audio)
    else:
        return clip.set_audio(audio)

def create_long_video(topic, output_path="/tmp/final_video.mp4"):
    scenes = [
        f"موضوع اليوم: {topic}",
        f"هل تعلم ان {topic} من اهم المواضيع التي يجب ان نعرفها؟",
        f"في البداية، {topic} يساعدنا على فهم الكثير من الامور المهمة حولنا.",
        f"ثانيا، هناك فوائد عديدة ل {topic} تجعل حياتنا افضل واكثر تنظيما.",
        f"ايضا، الكثير من الناس يجهلون اهمية {topic} وكيفية الاستفادة منه.",
        f"في الختام، نتمنى ان تكونوا استفدتم من هذا الفيديو عن {topic}، لا تنسوا الاشتراك.",
    ]

    clips = []
    temp_files = []
    for i, text in enumerate(scenes):
        audio_path = f"/tmp/audio_{i}.mp3"
        img_path = f"/tmp/img_{i}.jpg"
        temp_files.extend([audio_path, img_path])
        
        run_async(gen_audio(text, audio_path))
        create_image_with_text(text, i, img_path)
        
        audio_clip = AudioFileClip(audio_path)
        image_clip = ImageClip(img_path, duration=audio_clip.duration + 0.4)
        image_clip = add_audio_to_clip(image_clip, audio_clip)
        clips.append(image_clip)

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac', logger=None)
    
    # اغلاق الكليبات لتوفير الذاكرة
    for c in clips:
        c.close()
    final.close()
    
    return output_path

@app.route("/")
def home():
    return jsonify({"status": "Live Pro ✅", "video": "long 60s + 6 images", "fix": "with_audio"})

@app.route("/test")
def test_page():
    return """<html dir=rtl lang=ar><head><meta charset=UTF-8><meta name=viewport content="width=device-width, initial-scale=1.0">
<style>body{font-family:Tahoma;background:#0f0f1e;color:#fff;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0}
.card{background:#1e1e3a;padding:30px;border-radius:15px;width:90%;max-width:500px} h1{color:#ff4757;text-align:center}
input{width:100%;padding:12px;margin:10px 0;border-radius:8px;border:none;background:#2a2a4a;color:#fff;font-size:16px;box-sizing:border-box}
button{width:100%;padding:15px;background:#ff4757;color:#fff;border:none;border-radius:8px;font-size:18px;font-weight:bold;cursor:pointer}
#result{margin-top:20px;padding:15px;background:#2a2a4a;border-radius:8px;display:none} a{color:#70a1ff}</style>
</head><body><div class="card">
<h1>🎬 النسخة الاحترافية PRO</h1><p style="text-align:center;color:#aaa">فيديو طويل 60 ثانية + 6 مشاهد متحركة</p>
<input id="topic" value="فوائد الصيام" placeholder="موضوع الفيديو">
<button onclick="generate()">🚀 ولّد فيديو طويل</button>
<div id="result"></div></div>
<script>
async function generate(){
  const topic=document.getElementById('topic').value;
  const btn=document.querySelector('button');
  const res=document.getElementById('result');
  btn.innerText='⏳ جاري توليد 6 مشاهد... (دقيقتين)'; btn.disabled=true;
  res.style.display='block'; res.innerHTML='⏳ يتم توليد الصوت والصور... لا تغلق الصفحة';
  try{
    const r=await fetch('/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topic})});
    const data=await r.json();
    if(data.success){res.innerHTML=`✅ تم!<br><br>🎬 <a href="${data.url}" target="_blank">${data.url}</a><br><br>المدة: 60 ثانية - 6 صور`; btn.innerText='✅ تم بنجاح';}
    else{res.innerHTML='❌ '+data.error; btn.innerText='حاول مرة أخرى';}
  }catch(e){res.innerHTML='❌ '+e; btn.innerText='حاول مرة أخرى';}
  btn.disabled=false;
}
</script></body></html>"""

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json or {}
    topic = data.get("topic", "فوائد الصيام")
    title = f"{topic} | معلومات مهمة لا تفوتك"
    desc = f"فيديو شامل عن {topic}\n\n# {topic.replace(' ', '_')} #معلومات"
    try:
        video_path = create_long_video(topic)
        result = upload_to_youtube(video_path, title, desc)
        return jsonify({"success": True, "url": f"https://www.youtube.com/watch?v={result['id']}"})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
