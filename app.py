import os
import tempfile
from pathlib import Path

import streamlit as st
from yt_dlp import YoutubeDL

st.set_page_config(page_title="Video/Audio Fetcher", page_icon="🎬")
st.title("🎬 Video/Audio Fetcher")
st.caption("Use only for content you own or that’s licensed. Respect each platform’s ToS.")

# ---------- UI ----------
url = st.text_input("Paste video URL")
fmt = st.selectbox("Format", ["MP4 video (≤720p)", "M4A audio"])
cookie_file = st.file_uploader(
    "Optional: upload cookies.txt (helps with age/region/login-gated videos)",
    type=["txt"],
)
go = st.button("Fetch")

progress = st.progress(0)
status = st.empty()


# ---------- Progress hook ----------
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


# ---------- yt-dlp options builder (with base opts patch) ----------
def build_opts(outtmpl, url, fmt_choice, cookie_path, force_ipv4=None, force_ipv6=None):
    # realistic UA helps; yt-dlp will still impersonate via curl-cffi underneath
    UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    )

    base_opts = {
        "noplaylist": True,
        "outtmpl": outtmpl,
        "progress_hooks": [hook],
        "quiet": True,

        # --- anti-403 stack ---
        "impersonate": "chrome",  # requires yt-dlp[default,curl-cffi]
        "http_headers": {
            "User-Agent": UA,
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": url,
        },
        # Use Android client path first (often less throttling)
        "extractor_args": {"youtube": {"player_client": ["android"]}},

        # Retry strategy to ride out transient 403/429
        "retries": 15,
        "fragment_retries": 15,
        "retry_sleep": "linear=1:6:1",
        "throttled_rate": "100K",
    }

    if cookie_path:
        base_opts["cookiefile"] = cookie_path
    if force_ipv4:
        base_opts["force_ipv4"] = True
    if force_ipv6:
        base_opts["force_ipv6"] = True

    # Prefer mp4+m4a for easy merges; cap at 720p to avoid picky CDN variants
    if fmt_choice.startswith("MP4"):
        base_opts["format"] = (
            "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]"
            "/best[ext=mp4]/best"
        )
    else:
        base_opts["format"] = "bestaudio[ext=m4a]/bestaudio"

    return base_opts


# ---------- IPv4-first with IPv6 fallback ----------
def try_download(url, fmt_choice, cookie_path, prefer_ipv="v4"):
    """
    Try IPv4 first; if 403/Forbidden, auto-retry with IPv6.
    Returns Path to the downloaded file.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        outtmpl = os.path.join(tmpdir, "%(title)s.%(ext)s")

        def run(ipver):
            opts = build_opts(
                outtmpl, url, fmt_choice, cookie_path,
                force_ipv4=(ipver == "v4"),
                force_ipv6=(ipver == "v6"),
            )
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return Path(ydl.prepare_filename(info))

        try:
            return run(prefer_ipv)
        except Exception as e1:
            # if clearly a 403-ish, flip IP family once
            if "403" in str(e1) or "Forbidden" in str(e1):
                alt = "v6" if prefer_ipv == "v4" else "v4"
                return run(alt)
            raise


# ---------- Main ----------
if go and url:
    st.info("Reminder: download only content you own or that’s explicitly licensed.")
    try:
        # persist cookies if provided
        cookie_path = None
        if cookie_file is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmpc:
                tmpc.write(cookie_file.read())
                cookie_path = tmpc.name

        path = try_download(url, fmt, cookie_path, prefer_ipv="v4")

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
st.caption(
    "Built with Streamlit + yt-dlp. If you hit 403/429 on cloud hosting, try a different source,"
    " use cookies, or run locally. This tool is for owner-licensed content only."
)
