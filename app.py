import streamlit as st
import yt_dlp
from faster_whisper import WhisperModel
from transformers import pipeline
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import re
import os

st.set_page_config(page_title="SumTube - YouTube Summarizer", page_icon="🎬", layout="centered")
st.title("🎬 SumTube: YouTube Video Summarizer")
st.write("Paste a YouTube link, download audio, fetch transcript, and generate AI-powered summary!")

# --- Input ---
url = st.text_input("📌 Paste a YouTube URL:")

if url:
    match = re.search(r"v=([^&]+)", url)
    if match:
        video_id = match.group(1)
    else:
        st.error("❌ Invalid YouTube URL")
        st.stop()

    try:
        # --- Step 1: Download audio ---
        st.info("⏳ Downloading audio...")
        audio_file = f"{video_id}.mp3"
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': video_id,
            'quiet': True,
            'no_warnings': True,
            'proxy': 'http://156.228.112.99:3129',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        st.success(f"✅ Audio downloaded: {audio_file}")

        # --- Step 2: Transcribe audio ---
        st.info("⏳ Transcribing audio...")
        model = WhisperModel("base")  # can switch to "small" or "tiny" for faster processing
        segments, info = model.transcribe(audio_file)
        full_text = " ".join([segment.text for segment in segments])
        st.success("✅ Transcription completed!")

        # --- Step 3: Summarize ---
        st.info("⏳ Summarizing text...")
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

        # Chunking
        max_chunk = 800
        sentences = full_text.split(". ")
        chunks, current_chunk = [], ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_chunk:
                current_chunk += sentence + ". "
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        if current_chunk:
            chunks.append(current_chunk.strip())

        # Summarize each chunk
        summaries = []
        for i, chunk in enumerate(chunks, 1):
            with st.spinner(f"✨ Summarizing chunk {i}/{len(chunks)}..."):
                out = summarizer(chunk, max_length=120, min_length=40, do_sample=False)
                summaries.append(out[0]['summary_text'])

        final_summary = " ".join(summaries)

        # --- Step 4: Tabs ---
        tab_summary, tab_audio, tab_transcript = st.tabs(["📝 Summary", "🎵 Audio", "📜 Transcript"])

        with tab_summary:
            st.subheader("📌 Final Summary")
            st.write(final_summary)

            st.markdown("### 🔹 Summary in Bullet Points")
            for i, s in enumerate(summaries, 1):
                st.markdown(f"- **Part {i}:** {s}")

            # PDF export
            def create_pdf(summary_text, bullet_points):
                buffer = io.BytesIO()
                c = canvas.Canvas(buffer, pagesize=letter)
                width, height = letter

                c.setFont("Helvetica-Bold", 16)
                c.drawString(50, height - 50, "YouTube Video Summary")

                c.setFont("Helvetica", 12)
                y = height - 100
                c.drawString(50, y, "Final Summary:")
                y -= 20

                text_obj = c.beginText(50, y)
                text_obj.setFont("Helvetica", 11)
                for line in summary_text.split(". "):
                    text_obj.textLine(line.strip())
                c.drawText(text_obj)

                y = text_obj.getY() - 40
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y, "Bullet Points:")
                y -= 20

                text_obj = c.beginText(50, y)
                text_obj.setFont("Helvetica", 11)
                for i, point in enumerate(bullet_points, 1):
                    for line in point.split(". "):
                        text_obj.textLine(f"{i}. {line.strip()}")
                c.drawText(text_obj)

                c.showPage()
                c.save()
                buffer.seek(0)
                return buffer

            pdf_buffer = create_pdf(final_summary, summaries)
            st.download_button(
                label="⬇️ Download Summary as PDF",
                data=pdf_buffer,
                file_name=f"{video_id}_summary.pdf",
                mime="application/pdf"
            )

        with tab_audio:
            st.subheader("🎵 Downloaded Audio")
            audio_bytes = open(audio_file, "rb").read()
            st.audio(audio_bytes, format="audio/mp3")

        with tab_transcript:
            st.subheader("📜 Full Transcript")
            st.write(full_text)

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
