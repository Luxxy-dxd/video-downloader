from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import yt_dlp

app = FastAPI(title="FB & Instagram Video API")

def get_video_info(url: str):
    ydl_opts = {
        "quiet": True,
        "skip_download": True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "url": info.get("url"),
            "duration": info.get("duration")
        }

@app.get("/video-info")
async def video_info(url: str = Query(..., description="Facebook or Instagram video URL")):
    try:
        data = get_video_info(url)
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

@app.get("/")
def root():
    return {"status": "ok", "message": "FB & Instagram Video API running 🚀"}
