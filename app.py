import os
import tempfile
from pathlib import Path

import streamlit as st
from yt_dlp import YoutubeDL

st.set_page_config(page_title="Video/Audio Fetcher", page_icon="🎬")
st.title("🎬 Video/Audio Fetcher")
st.caption("Use only for content you own or that’s licensed. Respect each platform’s ToS.")

# ---- UI ----
url = st.text_input("Paste video URL")
fmt = st.selectbox("Format", ["MP4 video (≤720p)", "M4A audio"])
cookie_file = st.file_uploader(
    "Optional: upload cookies.txt (helps with age/region/login-gated videos)",
    type=["txt"],
)
go = st.button("Fetch")

progress = st.progress(0)
status = st.empty()

# ---- Progress hook for yt-dlp ----
def hook(d):
    if d.get("status") == "downloading":
        pct = d.get("_percent_str", "0%").strip().replace("%", "")
        try:
            progress.progress(min(100, int(float(pct))))
        except Exception:
            pass
        eta = d.get("_eta_str", "")
        speed = d.get("_speed_str", "")
        status.write(f"ETA: {eta}  •  Speed: {speed}")

# ---- Main ----
if go and url:
    st.info("Reminder: download only content you own or that’s explicitly licensed.")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            outtmpl = os.path.join(tmpdir, "%(title)s.%(ext)s")

            # Optional cookies: save uploaded file to a temp path for yt-dlp
            cookie_path = None
            if cookie_file is not None:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmpc:
                    tmpc.write(cookie_file.read())
                    cookie_path = tmpc.name

            # Realistic headers help avoid 403s from some CDNs
            UA = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
            )

            # Base options shared by both formats
            base_opts = {
    "noplaylist": True,
    "outtmpl": outtmpl,
    "progress_hooks": [hook],
    "quiet": True,
    "force_ipv4": True,  # <-- Force IPv4 instead of IPv6
    "http_headers": {
        "User-Agent": UA,
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": url,
    },
    "extractor_args": {"youtube": {"player_client": ["android"]}},
}
            if cookie_path:
                base_opts["cookiefile"] = cookie_path

            # Prefer formats that often avoid ffmpeg merging on free hosting
            if fmt.startswith("MP4"):
                ydl_opts = {
                    **base_opts,
                    "format": (
                        "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]"
                        "/best[ext=mp4]/best"
                    ),
                }
            else:  # M4A audio
                ydl_opts = {
                    **base_opts,
                    "format": "bestaudio[ext=m4a]/bestaudio",
                }

            # Download
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                guessed_path = ydl.prepare_filename(info)

            # Present file to user
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

st.divider()
st.caption("Built with Streamlit + yt-dlp. If you hit 403/429 on cloud hosting, try a different source, use cookies, or run locally.")
