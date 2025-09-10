from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import yt_dlp

app = FastAPI(title="FB & Instagram Video API")

def get_video_info(url: str):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "force_generic_extractor": True,
        "format": "bestvideo+bestaudio/best"  # merge video+audio if available
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        # Try to get merged video+audio URL
        video_url = info.get("url")
        if not video_url and info.get("requested_formats"):
            # pick first format with audio
            for f in info["requested_formats"]:
                if f.get("acodec") != "none":
                    video_url = f.get("url")
                    break

        return {
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "url": video_url,
            "duration": info.get("duration")
        }

# GET endpoint
@app.get("/video-info")
async def video_info(url: str = Query(..., description="Facebook or Instagram video URL")):
    try:
        data = get_video_info(url)
        if not data["url"]:
            return JSONResponse(
                content={"error": "Video URL not found or only video-only stream available"},
                status_code=400
            )
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

# POST endpoint (easier for long URLs)
from pydantic import BaseModel

class VideoRequest(BaseModel):
    url: str

@app.post("/video-info")
async def video_info_post(req: VideoRequest):
    try:
        data = get_video_info(req.url)
        if not data["url"]:
            return JSONResponse(
                content={"error": "Video URL not found or only video-only stream available"},
                status_code=400
            )
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

# Root endpoint for testing
@app.get("/")
def root():
    return {"status": "ok", "message": "FB & Instagram Video API running 🚀"}
