import streamlit as st
import google.generativeai as genai
import time
import random
import uuid
import asyncio
import aiohttp
import requests  # For HuggingFace API requests

# ---- Helper Functions ----
# Existing code...

# Set up Hugging Face API details (for transcription)
API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3-turbo"
API_TOKEN = st.secrets["HUGGINGFACE_API_TOKEN"]
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

def transcribe_audio(audio_file):
    """Transcribes audio to text using Hugging Face's Whisper model."""
    try:
        # Send audio file to Hugging Face API for transcription
        response = requests.post(
            API_URL,
            headers=HEADERS,
            files={"file": audio_file},
        )

        if response.status_code == 200:
            transcription = response.json().get("text", "")
            if transcription:
                return transcription
            else:
                return "No transcription result found."
        else:
            return f"Error during transcription: {response.status_code}"

    except requests.exceptions.RequestException as e:
        return f"Error transcribing audio: {str(e)}"

def generate_blog_from_transcription(transcription):
    """Generates a blog post based on transcribed text."""
    prompt = f"Generate a detailed blog post based on the following text:\n\n{transcription}"
    return generate_content_async(prompt, None)  # Call the existing generate_content_async function.

def download_file(content, file_format="markdown"):
    """Provides the option to download generated content in HTML or Markdown format."""
    if file_format == "markdown":
        # Convert content to markdown format
        content = f"# Generated Blog\n\n{content}"
    elif file_format == "html":
        # Convert content to HTML format
        content = f"<html><body><h1>Generated Blog</h1><p>{content.replace('\n', '<br>')}</p></body></html>"
    
    content_bytes = content.encode('utf-8')
    st.download_button(
        label=f"Download as {file_format.upper()} File",
        data=content_bytes,
        file_name=f"generated_blog.{file_format}",
        mime=f"text/{file_format}",
        use_container_width=True,
    )

# ---- Main Streamlit App ----
# Initialize session tracking
initialize_session()

# App Title and Description
st.set_page_config(page_title="AI-Powered Ghostwriter", page_icon=":robot:", layout="centered")
st.markdown("""<style>/* Existing styling code */</style>""", unsafe_allow_html=True)

# Instructional text with animation and clickable link
st.markdown("""<h3>🚀 Welcome to AI-Powered Ghostwriter!</h3> <p>Generate high-quality content and check for originality using Generative AI and Google Search. Access the <a href="https://evertechcms.in/gridai" target="_blank"><strong>Grid AI Pro</strong></a> model now!</p>""", unsafe_allow_html=True)

# Add Audio Upload Option
st.markdown("### Upload Podcast for Transcription:")
audio_file = st.file_uploader("Choose an audio file", type=["mp3", "wav", "m4a"])

# If audio file is uploaded, transcribe and generate content
if audio_file:
    st.audio(audio_file, format="audio/wav")
    transcription = transcribe_audio(audio_file)

    if transcription != "No transcription result found.":
        st.subheader("Transcribed Text:")
        st.write(transcription)

        # Generate a blog post from the transcription
        st.subheader("Generating Blog Post from Transcription:")
        generated_blog = asyncio.run(generate_blog_from_transcription(transcription))

        st.subheader("Generated Blog Post:")
        st.markdown(generated_blog)

        # Download options
        st.markdown("### Download the Generated Blog Post:")
        file_format = st.selectbox("Choose File Format", ["markdown", "html"])
        download_file(generated_blog, file_format)

    else:
        st.warning("Transcription failed. Please try again with another file.")

# ---- Content Generation (Existing functionality) ----
# (This section will remain mostly unchanged, as it handles general content generation from text prompts)

# Session management to check for block time and session limits
check_session_limit()

# Asyncio Event Loop for Concurrency
async def main():
    if st.button("Generate Response"):
        if not prompt.strip():
            st.warning("Please enter a valid prompt.")
        else:
            # Show spinner and countdown before AI request
            with st.spinner("Please wait, generating response..."):
                countdown_time = 5
                countdown_text = st.empty()  # Create an empty container to update the text
                
                # Countdown loop with dynamic updates
                for i in range(countdown_time, 0, -1):
                    countdown_text.markdown(f"Generating response in **{i} seconds...**")
                    time.sleep(1)  # Simulate countdown delay
                
                # After countdown, make the AI request
                async with aiohttp.ClientSession() as session:
                    generated_text = await generate_content_async(prompt, session)
                    
                    # Increment session count
                    st.session_state.session_count += 1
                    st.session_state.generated_text = generated_text  # Store for potential regeneration
                    
                    # Display the generated content safely
                    st.subheader("Generated Content:")
                    st.markdown(generated_text)

                    # Check for similar content online asynchronously
                    st.subheader("Searching for Similar Content Online:")
                    search_results = await search_web_async(generated_text, session)
                    
                    # Validate search results before accessing
                    if search_results is None:
                        st.warning("Error or no results from the web search.")
                    elif isinstance(search_results, dict) and 'items' in search_results and search_results['items']:
                        st.warning("Similar content found on the web:")
                        for result in search_results['items'][:10]:  # Show top 5 results
                            with st.expander(result.get('title', 'No Title')):
                                st.write(f"**Source:** [{result.get('link', 'Unknown')}]({result.get('link', '#')})")
                                st.write(f"**Snippet:** {result.get('snippet', 'No snippet available.')}")
                                st.write("---")
                    else:
                        st.success("No similar content found online. Your content seems original!")

                    # Trigger Streamlit balloons after generation
                    st.balloons()

                    # Allow download of the generated content
                    download_file(generated_text)

    if st.session_state.get('generated_text'):
        if st.button("Regenerate Content"):
            regenerated_text = regenerate_content(st.session_state.generated_text)
            st.subheader("Regenerated Content:")
            st.markdown(regenerated_text)
            download_file(regenerated_text)

# Run the async main function
asyncio.run(main())

# Footer with links
st.markdown("""<div class="footer"> <p>Powered by Streamlit and Google Generative AI | <a href="https://github.com/yourusername/yourrepo" target="_blank">GitHub</a></p> </div>""", unsafe_allow_html=True)
