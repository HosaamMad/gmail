from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ✅ صلاحية الوصول للصور فقط
SCOPES = ["https://www.googleapis.com/auth/photoslibrary.readonly"]
REDIRECT_URI = "http://localhost:8000/callback"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRET_FILE = os.path.join(BASE_DIR, "client_secrets.json")


@app.get("/login")
def login():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
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

        flow = Flow.from_client_secrets_file(
            CLIENT_SECRET_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # 🔗 الاتصال بـ Photos API
        photos_service = build("photoslibrary", "v1", credentials=credentials)

        # 📸 جلب الصور من المكتبة مباشرة
        response = photos_service.mediaItems().list(pageSize=10).execute()
        media_items = response.get("mediaItems", [])

        # 🖨️ فحص داخلي
        print(f"📸 عدد الصور المسترجعة: {len(media_items)}")
        for item in media_items:
            print(item.get("filename", "بدون اسم"), item.get("baseUrl", "بدون رابط"))

        # ✅ عرض الصور في واجهة HTML
        return templates.TemplateResponse("index.html", {
            "request": request,
            "media_items": media_items
        })

    except Exception as e:
        print(f"⚠️ حدث خطأ أثناء المعالجة: {e}")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "media_items": [],
            "error": str(e)
        })