import streamlit as st
import yt_dlp
import os
import tempfile

# ----------------- THEME & PAGE SETUP -----------------
st.set_page_config(
    page_title="Java's Coffee Download Bar",
    page_icon="☕",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Inline CSS for coffee vibes
coffee_css = """
<style>
    body {
        background-color: #f5f0e6; /* light coffee cream */
        color: #3e2723; /* dark roast */
    }
    .stApp {
        background-color: #f5f0e6;
    }
    .stTextInput > div > div > input {
        background-color: #fff8f0;
        color: #3e2723;
    }
    .stDownloadButton button {
        background-color: #795548;
        color: white;
        border-radius: 8px;
    }
    .stDownloadButton button:hover {
        background-color: #5d4037;
    }
</style>
"""
st.markdown(coffee_css, unsafe_allow_html=True)

# ----------------- HEADER -----------------
st.title("☕ Java's Coffee Download Bar")
st.write("Pull up a chair, pour yourself a cup, and grab that video.")

# ----------------- INPUT -----------------
video_url = st.text_input("Enter the video URL", placeholder="https://...")

# ----------------- DOWNLOAD LOGIC -----------------
if st.button("Brew & Download"):
    if not video_url.strip():
        st.error("Please enter a video URL first.")
    else:
        with st.spinner("☕ Brewing your download... please wait..."):
            try:
                # Temporary file
                temp_dir = tempfile.mkdtemp()
                ydl_opts = {
                    'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                    'format': 'bestvideo+bestaudio/best',
                    'merge_output_format': 'mp4',
                    'noplaylist': True,
                    'nocheckcertificate': True,
                    'geo_bypass': True,
                    'quiet': True,
                    'restrictfilenames': True,
                    'socket_timeout': 15,
                    'source_address': '0.0.0.0'  # Forces IPv4 to avoid some 403 errors
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=True)
                    file_path = ydl.prepare_filename(info)
                    if not file_path.endswith(".mp4"):
                        mp4_path = file_path.rsplit('.', 1)[0] + ".mp4"
                        os.rename(file_path, mp4_path)
                        file_path = mp4_path

                with open(file_path, "rb") as f:
                    st.download_button(
                        label="☕ Grab Your Fresh Brew",
                        data=f,
                        file_name=os.path.basename(file_path),
                        mime="video/mp4"
                    )

            except Exception as e:
                st.error(f"Uh-oh, your brew spilled: {e}")
