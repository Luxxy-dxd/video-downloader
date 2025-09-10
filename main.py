from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pytube import YouTube
import instaloader
from TikTokApi import TikTokApi
import snscrape.modules.twitter as sntwitter
import praw
from facebook_scraper import get_posts
import re

app = FastAPI(title="Multi-Social Video API")

# ---------- YOUTUBE ----------
def youtube_info(url: str):
    yt = YouTube(url)
    return {
        "title": yt.title,
        "thumbnail": yt.thumbnail_url,
        "url": yt.streams.get_highest_resolution().url,
        "duration": yt.length
    }

# ---------- INSTAGRAM ----------
def instagram_info(url: str):
    loader = instaloader.Instaloader(download_pictures=False, download_videos=False, download_comments=False)
    post = instaloader.Post.from_shortcode(loader.context, url.split("/")[-2])
    return {
        "title": post.title if post.title else "Instagram Post",
        "thumbnail": post.url,
        "url": post.video_url,
        "duration": post.video_duration
    }

# ---------- TIKTOK ----------
def tiktok_info(url: str):
    with TikTokApi() as api:
        video = api.video(url=url).info()
        return {
            "title": video["desc"],
            "thumbnail": video["video"]["cover"],
            "url": video["video"]["playAddr"],
            "duration": video["video"]["duration"]
        }

# ---------- TWITTER ----------
def twitter_info(url: str):
    tweet_id = url.split("/")[-1]
    tweet = next(sntwitter.TwitterTweetScraper(tweet_id).get_items())
    media = tweet.media[0] if tweet.media else None
    return {
        "title": tweet.content,
        "thumbnail": media.fullUrl if media else None,
        "url": media.fullUrl if media else None,
        "duration": None
    }

# ---------- REDDIT ----------
def reddit_info(url: str):
    reddit = praw.Reddit(client_id="YOUR_ID", client_secret="YOUR_SECRET", user_agent="scraper")
    submission_id = url.split("/")[-3]
    submission = reddit.submission(id=submission_id)
    return {
        "title": submission.title,
        "thumbnail": submission.thumbnail,
        "url": submission.url,
        "duration": None
    }

# ---------- FACEBOOK ----------
def facebook_info(url: str):
    for post in get_posts(post_urls=[url], cookies="cookies.json"):
        return {
            "title": post["text"][:50] if post["text"] else "Facebook Post",
            "thumbnail": post["image"],
            "url": post["video"],
            "duration": None
        }

# ---------- DETECTOR ----------
@app.get("/video-info")
async def video_info(url: str = Query(..., description="Video URL")):
    try:
        if "youtube.com" in url or "youtu.be" in url:
            return JSONResponse(content=youtube_info(url))
        elif "instagram.com" in url:
            return JSONResponse(content=instagram_info(url))
        elif "tiktok.com" in url:
            return JSONResponse(content=tiktok_info(url))
        elif "twitter.com" in url or "x.com" in url:
            return JSONResponse(content=twitter_info(url))
        elif "reddit.com" in url:
            return JSONResponse(content=reddit_info(url))
        elif "facebook.com" in url:
            return JSONResponse(content=facebook_info(url))
        else:
            return JSONResponse(content={"error": "Unsupported platform"}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
