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
        "format": "bestvideo+bestaudio/best"  # try to merge video+audio
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        video_url = None
        audio_url = None

        # Check requested_formats
        if info.get("requested_formats"):
            # Find best video+audio
            for f in info["requested_formats"]:
                if f.get("acodec") != "none" and f.get("vcodec") != "none":
                    video_url = f.get("url")
                    break  # pick first merged stream
            # Find best audio-only
            for f in info["requested_formats"]:
                if f.get("acodec") != "none" and f.get("vcodec") == "none":
                    audio_url = f.get("url")
                    break
        else:
            # Fallback
            if info.get("acodec") != "none" and info.get("vcodec") != "none":
                video_url = info.get("url")
            if info.get("acodec") != "none" and info.get("vcodec") == "none":
                audio_url = info.get("url")

        # If merged video+audio not found, fallback to video-only stream
        if not video_url:
            if info.get("formats"):
                for f in reversed(info["formats"]):  # pick best video-only
                    if f.get("vcodec") != "none":
                        video_url = f.get("url")
                        break

        return {
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "video_url": video_url,
            "audio_url": audio_url,
            "duration": info.get("duration")
        }

# GET endpoint
@app.get("/video-info")
async def video_info(url: str = Query(...)):
    try:
        data = get_video_info(url)
        if not data["video_url"] and not data["audio_url"]:
            return JSONResponse({"error": "Video or audio URL not found"}, status_code=400)
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

# POST endpoint
class VideoRequest(BaseModel):
    url: str

@app.post("/video-info")
async def video_info_post(req: VideoRequest):
    try:
        data = get_video_info(req.url)
        if not data["video_url"] and not data["audio_url"]:
            return JSONResponse({"error": "Video or audio URL not found"}, status_code=400)
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.get("/")
def root():
    return {"status": "ok", "message": "FB & Instagram Video API running 🚀"}
