import os
import uuid
import shutil
import asyncio
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import yt_dlp
import subprocess
from datetime import datetime, timedelta

app = FastAPI(title="Advanced Social Media Video Downloader API")

TEMP_DIR = "temp_videos"
os.makedirs(TEMP_DIR, exist_ok=True)

# Auto cleanup: delete files older than 1 hour
async def cleanup_temp_files():
    while True:
        now = datetime.now()
        for f in os.listdir(TEMP_DIR):
            file_path = os.path.join(TEMP_DIR, f)
            if os.path.isfile(file_path):
                if now - datetime.fromtimestamp(os.path.getmtime(file_path)) > timedelta(hours=1):
                    os.remove(file_path)
        await asyncio.sleep(3600)  # run every hour

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_temp_files())

# Pydantic model for POST requests
class VideoRequest(BaseModel):
    url: str
    quality: str = "best"  # "best", "360", "720", "1080", etc.

def extract_video_info(url: str, quality: str = "best"):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "force_generic_extractor": True,
        "format": f"{quality}+bestaudio/best",
        "noplaylist": True,
        "extract_flat": False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        # Prepare quality list
        formats = []
        for f in info.get("formats", []):
            if f.get("vcodec") != "none":
                formats.append({
                    "format_id": f.get("format_id"),
                    "resolution": f.get("resolution"),
                    "ext": f.get("ext"),
                    "fps": f.get("fps"),
                    "url": f.get("url")
                })

        # Prepare audio-only URL
        audio_url = None
        for f in info.get("formats", []):
            if f.get("acodec") != "none" and f.get("vcodec") == "none":
                audio_url = f.get("url")
                break

        return {
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "uploader": info.get("uploader"),
            "formats": formats,
            "audio_url": audio_url,
            "original_url": url
        }

def download_and_merge_video(url: str, format_id: str = None):
    """
    Downloads video and audio separately if needed and merges them
    """
    ydl_opts = {
        "quiet": True,
        "format": format_id or "bestvideo+bestaudio/best",
        "outtmpl": f"{TEMP_DIR}/%(id)s.%(ext)s",
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_file = None
        audio_file = None

        # Check for separate streams
        if info.get("requested_formats"):
            for f in info["requested_formats"]:
                path = ydl.prepare_filename(f)
                if f.get("vcodec") != "none" and f.get("acodec") != "none":
                    video_file = path
                    audio_file = None
                    break
                if f.get("vcodec") != "none" and f.get("acodec") == "none":
                    video_file = path
                if f.get("vcodec") == "none" and f.get("acodec") != "none":
                    audio_file = path

        # Merge if both exist
        merged_file = None
        if video_file and audio_file:
            merged_file = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex}.mp4")
            subprocess.run([
                "ffmpeg", "-y", "-i", video_file, "-i", audio_file, "-c", "copy", merged_file
            ], check=True)
        else:
            merged_file = video_file or audio_file

        return merged_file

# GET endpoint
@app.get("/video-info")
async def video_info(url: str = Query(...), quality: str = Query("best")):
    try:
        info = extract_video_info(url, quality)
        return JSONResponse(info)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

# POST endpoint
@app.post("/video-info")
async def video_info_post(req: VideoRequest):
    try:
        info = extract_video_info(req.url, req.quality)
        return JSONResponse(info)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

# Endpoint to download merged video file
@app.get("/download")
async def download_video(url: str = Query(...), format_id: str = Query(None)):
    try:
        file_path = download_and_merge_video(url, format_id)
        if file_path and os.path.exists(file_path):
            return FileResponse(file_path, media_type="video/mp4", filename=os.path.basename(file_path))
        return JSONResponse({"error": "Failed to generate video"}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.get("/")
def root():
    return {"status": "ok", "message": "Advanced Video Downloader API running 🚀"}
