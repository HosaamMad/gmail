from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
import json

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# صلاحية الوصول للصور فقط
SCOPES = ["https://www.googleapis.com/auth/photoslibrary.readonly"]
REDIRECT_URI = "https://google-photos-viewer.onrender.com/callback"  # غيّره حسب رابطك في Render

# تحميل بيانات OAuth من متغير البيئة
CLIENT_SECRET_DATA = json.loads(os.getenv("CLIENT_SECRET_JSON"))

@app.get("/login")
def login():
    flow = Flow.from_client_config(
        CLIENT_SECRET_DATA,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(
        prompt="consent",
        access_type="offline",
        include_granted_scopes="true"
    )
    return RedirectResponse(auth_url)

@app.get("/callback")
def callback(request: Request):
    try:
        code = request.query_params.get("code")
        if not code:
            return {"error": "رمز الدخول غير موجود"}

        flow = Flow.from_client_config(
            CLIENT_SECRET_DATA,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials

        photos_service = build("photoslibrary", "v1", credentials=credentials)
        response = photos_service.mediaItems().list(pageSize=10).execute()
        media_items = response.get("mediaItems", [])

        print(f"📸 عدد الصور المسترجعة: {len(media_items)}")
        for item in media_items:
            print(item.get("filename", "بدون اسم"), item.get("baseUrl", "بدون رابط"))

        return templates.TemplateResponse("index.html", {
            "request": request,
            "media_items": media_items
        })

    except Exception as e:
        print(f"⚠️ خطأ أثناء المعالجة: {e}")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "media_items": [],
            "error": str(e)
        })
