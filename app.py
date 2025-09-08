
import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from transformers import pipeline
import re

st.set_page_config(page_title="AskTube - YouTube Summarizer", page_icon="🎬", layout="wide")

st.title("🎬 AskTube: YouTube Video Summarizer")
st.write("Paste a YouTube link, and I'll fetch the transcript + generate a summary for you!")

# Input YouTube URL
url = st.text_input("📌 Paste a YouTube URL:")

if url:
    # Extract video ID
    match = re.search(r"v=([^&]+)", url)
    if match:
        video_id = match.group(1)
    else:
        st.error("❌ Invalid YouTube URL")
        st.stop()

    try:
        with st.spinner("⏳ Fetching transcript..."):
            transcript = YouTubeTranscriptApi().fetch(video_id=video_id, languages=['en'])
            full_text = " ".join([snippet.text for snippet in transcript])

        st.success("✅ Transcript fetched!")

        # Summarizer
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

        # Summarize chunks
        summaries = []
        for i, chunk in enumerate(chunks, 1):
            with st.spinner(f"✨ Summarizing chunk {i}/{len(chunks)}..."):
                out = summarizer(chunk, max_length=120, min_length=40, do_sample=False)
                summaries.append(out[0]['summary_text'])

        final_summary = " ".join(summaries)

        # --- Tabs for better UI ---
        tab1, tab2 = st.tabs(["📜 Transcript", "📝 Summary"])

        with tab1:
            st.subheader("📜 Full Transcript")
            st.write(full_text)

        with tab2:
            st.subheader("📌 Final Summary")
            st.write(final_summary)

            st.markdown("### 🔹 Summary in Bullet Points")
            for i, s in enumerate(summaries, 1):
                st.markdown(f"- **Part {i}:** {s}")

    except Exception as e:
        st.error(f"❌ Could not fetch transcript: {str(e)}")
