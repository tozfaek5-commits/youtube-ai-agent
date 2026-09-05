import os
from flask import Flask, request, jsonify
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import asyncio
import edge_tts
from PIL import Image, ImageDraw, ImageFont
import textwrap
import time

# يحاول moviepy الجديد، إذا فشل يحاول القديم
try:
    from moviepy.editor import ImageClip, AudioFileClip
except ImportError:
    from moviepy import ImageClip, AudioFileClip

app = Flask(__name__)

def get_youtube_client():
    creds = Credentials(token=None, refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"), token_uri="https://oauth2.googleapis.com/token", client_id=os.getenv("GOOGLE_CLIENT_ID"), client_secret=os.getenv("GOOGLE_CLIENT_SECRET"), scopes=["https://www.googleapis.com/auth/youtube.upload"])
    creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)

def upload_to_youtube(video_path, title, description, tags=[]):
    youtube = get_youtube_client()
    body = {"snippet": {"title": title[:95], "description": description, "tags": tags[:15], "categoryId": "27"}, "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False}}
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    return resp

async def generate_audio_edge(text, output_path):
    communicate = edge_tts.Communicate(text, "ar-SA-HamedNeural")
    await communicate.save(output_path)

def create_video_from_text(topic, output_path="/tmp/final_video.mp4"):
    script = f"موضوع اليوم: {topic}. سنتعرف على أهم المعلومات حول {topic}."
    audio_path = "/tmp/audio.mp3"
    for attempt in range(3):
        try:
            asyncio.run(generate_audio_edge(script, audio_path))
            break
        except Exception as e:
            time.sleep(2)
            if attempt == 2: raise e
    img_path = "/tmp/bg.jpg"
    img = Image.new('RGB', (1280, 720), color=(15, 15, 30))
    draw = ImageDraw.Draw(img)
    try: font = ImageFont.truetype("arial.ttf", 60)
    except: font = ImageFont.load_default()
    wrapped = textwrap.fill(topic, width=20)
    draw.text((100, 300), wrapped, fill=(255,255,255), font=font, spacing=20)
    img.save(img_path)
    audio_clip = AudioFileClip(audio_path)
    image_clip = ImageClip(img_path, duration=audio_clip.duration).set_audio(audio_clip)
    image_clip.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac', logger=None)
    return output_path, script

@app.route("/")
def home():
    return jsonify({"status": "Live ✅ Fixed", "youtube_configured": bool(os.getenv("GOOGLE_REFRESH_TOKEN"))})

@app.route("/test")
def test_page():
    return open("test.html").read() if os.path.exists("test.html") else "<h1>Use /generate POST</h1>"

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
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
