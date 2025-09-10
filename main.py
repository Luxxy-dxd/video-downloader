import os
import uuid
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, FileResponse
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

    return {
        "title": info.get("title"),
        "thumbnail": info.get("thumbnail"),
        "video_url": video_file,
        "audio_url": audio_file,
        "duration": info.get("duration")
    }

# ----------------------------
# GET endpoint
# ----------------------------
@app.get("/video-info")
async def video_info(url: str = Query(...)):
    try:
        data = download_video_audio(url)
        if not data["video_url"] and not data["audio_url"]:
            return JSONResponse({"error": "Video or audio URL not found"}, status_code=400)
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
        if not data["video_url"] and not data["audio_url"]:
            return JSONResponse({"error": "Video or audio URL not found"}, status_code=400)
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

# ----------------------------
# Serve video files
# ----------------------------
@app.get("/video-file")
async def get_video_file(file_path: str):
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return JSONResponse({"error": "File not found"}, status_code=404)

# ----------------------------
# Root endpoint
# ----------------------------
@app.get("/")
def root():
    return {"status": "ok", "message": "FB & Instagram Video API running 🚀"}
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
