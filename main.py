import os
from flask import Flask, request, jsonify
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = Flask(__name__)

def get_youtube_client():
    """ينشئ اتصال يوتيوب باستخدام الـ Refresh Token الدائم"""
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
    """يرفع الفيديو كمسودة Private - يحترم قاعدتك الذهبية"""
    youtube = get_youtube_client()
    
    body = {
        "snippet": {
            "title": title[:95] + " #AI",
            "description": description + "\n\nتم التوليد تلقائياً - مسودة بانتظار موافقتك",
            "tags": tags[:15],
            "categoryId": "27"  # Education
        },
        "status": {
            "privacyStatus": "private",  # مهم جداً: مسودة خاصة فقط
            "selfDeclaredMadeForKids": False
        }
    }
    
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    
    request_upload = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status, response = request_upload.next_chunk()
        if status:
            print(f"Upload {int(status.progress() * 100)}%")
    
    return response

@app.route("/")
def home():
    return jsonify({
        "status": "Live ✅",
        "message": "YouTube AI Agent Ready - Uploads as Private Draft",
        "youtube_configured": bool(os.getenv("GOOGLE_REFRESH_TOKEN"))
    })

@app.route("/upload", methods=["POST"])
def upload_endpoint():
    """
    استدع هذا الـ Endpoint بعد توليد الفيديو
    body: { "video_path": "/tmp/video.mp4", "title": "...", "description": "..." }
    """
    data = request.json
    video_path = data.get("video_path")
    title = data.get("title", "فيديو AI جديد")
    description = data.get("description", "تم توليده بواسطة AI Agent")
    tags = data.get("tags", ["AI", "education"])

    if not os.path.exists(video_path):
        return jsonify({"error": f"Video file not found: {video_path}"}), 400

    try:
        result = upload_to_youtube(video_path, title, description, tags)
        return jsonify({
            "success": True,
            "youtube_id": result["id"],
            "youtube_url": f"https://www.youtube.com/watch?v={result['id']}",
            "status": "private - بانتظار موافقتك في YouTube Studio",
            "message": "تم الرفع كمسودة! ادخل YouTube Studio وانشره يدوياً عندما تريد"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
