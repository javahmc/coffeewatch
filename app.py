import os
import tempfile
from pathlib import Path

import streamlit as st
from yt_dlp import YoutubeDL

st.set_page_config(page_title="Video Fetcher (for content you own)", page_icon="🎬")
st.title("🎬 Video/Audio Fetcher")
st.caption("Use only for content you own or that’s licensed for download. Respect site ToS.")

url = st.text_input("Paste video URL")
fmt = st.selectbox("Format", ["MP4 video (≤720p)", "M4A audio"])
go = st.button("Fetch")

progress = st.progress(0)
status = st.empty()

def hook(d):
    if d.get("status") == "downloading":
        pct = d.get("_percent_str", "0%").strip().replace("%","")
        try:
            progress.progress(min(100, int(float(pct))))
        except:
            pass
        status.write(f"ETA: {d.get('_eta_str','')} | Speed: {d.get('_speed_str','')}")

if go and url:
    st.info("Reminder: download only content you own or that's explicitly licensed.")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            outtmpl = os.path.join(tmpdir, "%(title)s.%(ext)s")

            if fmt.startswith("MP4"):
                ydl_opts = {
                    # Prefer formats that often avoid ffmpeg merging on free hosting
                    "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    "noplaylist": True,
                    "outtmpl": outtmpl,
                    "progress_hooks": [hook],
                    "quiet": True,
                }
            else:
                ydl_opts = {
                    "format": "bestaudio[ext=m4a]/bestaudio",
                    "noplaylist": True,
                    "outtmpl": outtmpl,
                    "progress_hooks": [hook],
                    "quiet": True,
                }

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                guessed_path = ydl.prepare_filename(info)

            path = Path(guessed_path)
            progress.progress(100)
            status.write("Done ✓")

            st.success(f"Ready: {path.name}")
            with open(path, "rb") as f:
                st.download_button(
                    label="Download file",
                    data=f.read(),
                    file_name=path.name,
                    mime="application/octet-stream",
                )
    except Exception as e:
        st.error(f"Error: {e}")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")

base_opts = {
    "noplaylist": True,
    "outtmpl": outtmpl,
    "progress_hooks": [hook],
    "quiet": True,
    # help with 403s / rate limiting on some hosts
    "http_headers": {
        "User-Agent": UA,
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": url,  # harmless for most sites; helps some
    },
    # yt-specific: use android client (often bypasses 403/throttling)
    "extractor_args": {"youtube": {"player_client": ["android"]}},
}

if fmt.startswith("MP4"):
    ydl_opts = {
        **base_opts,
        "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    }
else:
    ydl_opts = {
        **base_opts,
        "format": "bestaudio[ext=m4a]/bestaudio",
    }

