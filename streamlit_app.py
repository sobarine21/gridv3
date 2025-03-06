import streamlit as st
import google.generativeai as genai
import time
import random
import uuid
import asyncio
import aiohttp
import requests
from io import StringIO

# ---- Helper Functions ----

def get_next_model_and_key():
    """Cycle through available Gemini models and corresponding API keys."""
    models_and_keys = [
        ('gemini-1.5-flash', st.secrets["API_KEY_GEMINI_1_5_FLASH"]),
        ('gemini-2.0-flash', st.secrets["API_KEY_GEMINI_2_0_FLASH"]),
        ('gemini-1.5-flash-8b', st.secrets["API_KEY_GEMINI_1_5_FLASH_8B"]),
        ('gemini-2.0-flash-exp', st.secrets["API_KEY_GEMINI_2_0_FLASH_EXP"]),
    ]
    
    model, api_key = random.choice(models_and_keys)
    return model, api_key

async def generate_content_async(prompt, session):
    """Asynchronously generates content using Generative AI."""
    model, api_key = get_next_model_and_key()
    genai.configure(api_key=api_key)
    generative_model = genai.GenerativeModel(model)

    try:
        response = await asyncio.to_thread(generative_model.generate_content, prompt)
        if response and response.text:
            return response.text.strip()
        else:
            return "No valid response generated."
    except Exception as e:
        return f"Error generating content: {str(e)}"

async def transcribe_audio(audio_file):
    """Transcribe audio using Hugging Face Whisper API."""
    API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3-turbo"
    API_TOKEN = st.secrets["HUGGINGFACE_API_TOKEN"]
    HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

    files = {'file': audio_file}
    
    try:
        response = requests.post(API_URL, headers=HEADERS, files=files)
        if response.status_code == 200:
            transcription = response.json()
            return transcription.get("text", "Transcription failed.")
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error transcribing audio: {str(e)}"

def initialize_session():
    """Initializes session variables securely."""
    if 'session_count' not in st.session_state:
        st.session_state.session_count = 0
    if 'block_time' not in st.session_state:
        st.session_state.block_time = None
    if 'user_hash' not in st.session_state:
        st.session_state.user_hash = str(uuid.uuid4())  # Unique session identifier
    if 'generated_text' not in st.session_state:
        st.session_state.generated_text = ""

def check_session_limit():
    """Checks if the user has reached the session limit and manages block time."""
    if st.session_state.block_time:
        time_left = st.session_state.block_time - time.time()
        if time_left > 0:
            st.warning(f"Session limit reached. Try again in {int(time_left)} seconds or upgrade to pro, https://evertechcms.in/gridai")
            st.stop()
        else:
            st.session_state.block_time = None

    if st.session_state.session_count >= 5:
        st.session_state.block_time = time.time() + 15 * 60  # Block for 15 minutes
        st.warning("Session limit reached. Please wait 15 minutes or upgrade to Pro.")
        st.markdown("You can upgrade to the Pro model & Get lifetime access at just Rs 999 [here](https://forms.gle/TJWH9HJ4kqUTN7Hp9).", unsafe_allow_html=True)
        st.stop()

def regenerate_content(original_content):
    """Generates rewritten content to ensure originality."""
    try:
        model, api_key = get_next_model_and_key()
        genai.configure(api_key=api_key)
        generative_model = genai.GenerativeModel(model)

        prompt = f"Rewrite the following content to make it original:\n\n{original_content}"
        response = generative_model.generate_content(prompt)

        if response and response.text:
            return response.text.strip()
        else:
            return "Regeneration failed."

    except Exception as e:
        return f"Error regenerating content: {str(e)}"

def download_file(content, file_format="txt"):
    """Provides the option to download generated content as a file (txt or html)."""
    if file_format == "txt":
        content_bytes = content.encode('utf-8')
        file_name = "generated_content.txt"
        mime_type = "text/plain"
    elif file_format == "html":
        # Fix: Replace '\n' with '<br>' properly, outside the f-string
        content_with_br = content.replace('\n', '<br>')
        html_content = f"<html><body>{content_with_br}</body></html>"
        content_bytes = html_content.encode('utf-8')
        file_name = "generated_content.html"
        mime_type = "text/html"

    st.download_button(
        label=f"Download as {file_format.upper()} File",
        data=content_bytes,
        file_name=file_name,
        mime=mime_type,
        use_container_width=True
    )

# ---- Main Streamlit App ----

# Initialize session tracking
initialize_session()

# App Title and Description
st.set_page_config(page_title="AI-Powered Ghostwriter", page_icon=":robot:", layout="centered")
st.markdown("""
    <style>
    body {
        background: linear-gradient(to right, #00c6ff, #0072ff);
        color: white;
        font-family: 'Arial', sans-serif;
    }
    .stButton>button {
        background-color: #00d1b2;
        color: white;
        padding: 12px 24px;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-size: 16px;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #00b59d;
    }
    .stTextArea textarea {
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid #00d1b2;
        color: white;
        padding: 10px;
        font-size: 16px;
        border-radius: 8px;
        width: 100%;
        max-width: 800px;
        height: 150px;
        box-sizing: border-box;
    }
    .stTextArea textarea:focus {
        outline: none;
        border-color: #00b59d;
    }
    .stMarkdown h3 {
        text-align: center;
        color: #f0f0f0;
        font-size: 28px;
        font-weight: bold;
    }
    .stMarkdown p {
        color: #f0f0f0;
        font-size: 18px;
        text-align: center;
        padding-bottom: 20px;
    }
    .stSpinner {
        color: #00d1b2;
    }
    .stImage img {
        border-radius: 15px;
    }
    .footer {
        text-align: center;
        color: #ffffff;
        padding: 15px;
        font-size: 14px;
    }
    .footer a {
        color: #00d1b2;
        text-decoration: none;
    }
    </style>
""", unsafe_allow_html=True)

# Instructional text with animation and clickable link
st.markdown("""
    <h3>🚀 Welcome to AI-Powered Ghostwriter!</h3>
    <p>Generate high-quality content and check for originality using Generative AI and Google Search. Access the <a href="https://evertechcms.in/gridai" target="_blank"><strong>Grid AI Pro</strong></a> model now!</p>
""", unsafe_allow_html=True)

# File Upload for Podcast
audio_file = st.file_uploader("Upload a Podcast (audio file)", type=["mp3", "wav", "ogg"])

# Session management to check for block time and session limits
check_session_limit()

# Asyncio Event Loop for Concurrency
async def main():
    if st.button("Generate Response"):
        if not audio_file and not prompt.strip():
            st.warning("Please enter a valid prompt or upload an audio file.")
        else:
            if audio_file:
                st.spinner("Transcribing audio file...")
                transcription = await transcribe_audio(audio_file)
                prompt = transcription  # Use the transcription as the prompt

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

                    # Trigger Streamlit balloons after generation
                    st.balloons()

                    # Allow download of the generated content
                    download_file(generated_text, file_format="html")

    if st.session_state.get('generated_text'):
        if st.button("Regenerate Content"):
            regenerated_text = regenerate_content(st.session_state.generated_text)
            st.subheader("Regenerated Content:")
            st.markdown(regenerated_text)
            download_file(regenerated_text, file_format="html")

# Run the async main function
asyncio.run(main())

# Footer with links
st.markdown("""
    <div class="footer">
        <p>Powered by Streamlit and Google Generative AI | <a href="https://github.com/yourusername/yourrepo" target="_blank">GitHub</a></p>
    </div>
""", unsafe_allow_html=True)
