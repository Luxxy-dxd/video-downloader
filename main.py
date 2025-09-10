import os
import uuid
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import yt_dlp

app = FastAPI(title="FB & Instagram Video API")

# Temporary folder for downloads
TEMP_DIR = "temp_videos"
os.makedirs(TEMP_DIR, exist_ok=True)

# ----------------------------
# Core function: download video+audio and audio-only
# ----------------------------
def download_video_audio(url: str):
    # Options for video+audio
    video_opts = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": f"{TEMP_DIR}/%(id)s.%(ext)s",
        "quiet": True,
    }

    # Options for audio-only
    audio_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{TEMP_DIR}/%(id)s_audio.%(ext)s",
        "quiet": True,
    }

    # Download video+audio
    with yt_dlp.YoutubeDL(video_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        video_file = ydl.prepare_filename(info)
        ydl.download([url])

    # Download audio-only
    with yt_dlp.YoutubeDL(audio_opts) as ydl:
        info_audio = ydl.extract_info(url, download=False)
        audio_file = ydl.prepare_filename(info_audio)
        ydl.download([url])

    # Return direct file paths
    return {
        "title": info.get("title"),
        "thumbnail": info.get("thumbnail"),
        "video_url": f"/video-file?file_path={video_file}",
        "audio_url": f"/video-file?file_path={audio_file}",
        "duration": info.get("duration")
    }

# ----------------------------
# GET endpoint
# ----------------------------
@app.get("/video-info")
async def video_info(url: str = Query(...)):
    try:
        data = download_video_audio(url)
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

# ----------------------------
# POST endpoint
# ----------------------------
class VideoRequest(BaseModel):
    url: str

@app.post("/video-info")
async def video_info_post(req: VideoRequest):
    try:
        data = download_video_audio(req.url)
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

# ----------------------------
# Serve video files
# ----------------------------
from fastapi.responses import FileResponse

@app.get("/video-file")
async def get_video_file(file_path: str):
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='application/octet-stream')
    return JSONResponse({"error": "File not found"}, status_code=404)

# ----------------------------
# Root endpoint
# ----------------------------
@app.get("/")
def root():
    return {"status": "ok", "message": "FB & Instagram Video API running 🚀"}
