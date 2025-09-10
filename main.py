from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import yt_dlp

app = FastAPI(title="FB & Instagram Video API")

def get_video_info(url: str):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "force_generic_extractor": True,
        "format": "bestvideo+bestaudio/best"
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        # Default values
        merged_url = None
        audio_url = None

        # Check requested_formats for video+audio and audio-only
        if info.get("requested_formats"):
            for f in info["requested_formats"]:
                # Best merged video+audio
                if not merged_url and f.get("acodec") != "none" and f.get("vcodec") != "none":
                    merged_url = f.get("url")
                # Best audio-only
                if not audio_url and f.get("acodec") != "none" and f.get("vcodec") == "none":
                    audio_url = f.get("url")
        else:
            # fallback if requested_formats not available
            merged_url = info.get("url")
            audio_url = info.get("url") if info.get("acodec") != "none" else None

        return {
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "video_url": merged_url,
            "audio_url": audio_url,
            "duration": info.get("duration")
        }

# GET endpoint
@app.get("/video-info")
async def video_info(url: str = Query(..., description="Facebook or Instagram video URL")):
    try:
        data = get_video_info(url)
        if not data["video_url"] and not data["audio_url"]:
            return JSONResponse(
                content={"error": "Video or audio URL not found"},
                status_code=400
            )
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

# POST endpoint
class VideoRequest(BaseModel):
    url: str

@app.post("/video-info")
async def video_info_post(req: VideoRequest):
    try:
        data = get_video_info(req.url)
        if not data["video_url"] and not data["audio_url"]:
            return JSONResponse(
                content={"error": "Video or audio URL not found"},
                status_code=400
            )
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

# Root endpoint
@app.get("/")
def root():
    return {"status": "ok", "message": "FB & Instagram Video API running 🚀"}
