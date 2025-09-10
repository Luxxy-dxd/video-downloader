from fastapi import FastAPI, Query, Response
from fastapi.responses import StreamingResponse
import yt_dlp
import io

app = FastAPI(title="Facebook Direct Streaming API")

# ----------------------------
# Core function: stream video with audio
# ----------------------------
def stream_facebook_video(url: str):
    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "quiet": True,
        "outtmpl": "-",  # "-" means stream to stdout
        "noplaylist": True,
    }
    # yt-dlp can write to a file-like object
    buffer = io.BytesIO()
    ydl_opts["progress_hooks"] = []
    ydl_opts["postprocessors"] = []

    class StreamWriter(io.RawIOBase):
        def __init__(self):
            self.buffer = io.BytesIO()
        def write(self, b):
            self.buffer.write(b)
            return len(b)
        def getvalue(self):
            self.buffer.seek(0)
            return self.buffer

    stream_writer = StreamWriter()
    ydl_opts["outtmpl"] = "-"  # ensure streaming mode

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        # stream directly to StreamingResponse
        ydl.download([url])
    return info

# ----------------------------
# GET endpoint: direct stream
# ----------------------------
@app.get("/fb-download")
async def fb_download(url: str = Query(...)):
    try:
        # yt-dlp does not have built-in streaming yet, but we can give **direct video URL**
        ydl_opts = {"format": "bestvideo+bestaudio/best", "quiet": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            direct_url = info.get("url")  # this is a direct URL to video with audio

        return {"title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "video_url": direct_url}

    except Exception as e:
        return {"error": str(e)}

# ----------------------------
# Root
# ----------------------------
@app.get("/")
def root():
    return {"status": "ok", "message": "Facebook Direct Streaming API running 🚀"}
