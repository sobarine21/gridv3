import streamlit as st
import google.generativeai as genai
import requests
import time
import random
import uuid
import asyncio
import aiohttp
import wave
import io
import datetime
from sklearn.feature_extraction.text import CountVectorizer
from wordcloud import WordCloud
import langid

# ---- Helper Functions ----

# Set up Hugging Face API details (for transcription)
API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3-turbo"
API_TOKEN = st.secrets["HUGGINGFACE_API_TOKEN"]
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

# Constants for rate limiting
MAX_DURATION_SECONDS = 120  # Max duration for the uploaded file (2 minutes)
USER_ACTION_LIMIT = 2  # Limit the number of user actions per 10 minutes
RATE_LIMIT_PERIOD = 600  # 10 minutes in seconds (600 seconds)

def transcribe_audio(file):
    """Transcribe audio file to text using Hugging Face Whisper API."""
    try:
        data = file.read()
        response = requests.post(API_URL, headers=HEADERS, data=data)
        if response.status_code == 200:
            return response.json()  # Return transcription
        else:
            return {"error": f"API Error: {response.status_code} - {response.text}"}
    except Exception as e:
        return {"error": str(e)}

def extract_keywords(text):
    """Extract keywords using CountVectorizer."""
    vectorizer = CountVectorizer(stop_words='english', max_features=10)
    X = vectorizer.fit_transform([text])
    keywords = vectorizer.get_feature_names_out()
    return keywords

def detect_language(text):
    """Detect the language of the text."""
    lang, confidence = langid.classify(text)
    return lang, confidence

def calculate_speech_rate(text, duration_seconds):
    """Calculate speech rate in words per minute."""
    words = text.split()
    num_words = len(words)
    if duration_seconds > 0:
        speech_rate = num_words / (duration_seconds / 60)
    else:
        speech_rate = 0
    return speech_rate

def generate_word_cloud(text):
    """Generate a word cloud from the transcription."""
    wordcloud = WordCloud(width=800, height=400, background_color='black').generate(text)
    return wordcloud

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

# ---- Main Streamlit App ----

# Initialize session tracking
if 'last_action_time' not in st.session_state:
    st.session_state.last_action_time = datetime.datetime.now()
    st.session_state.action_count = 0
if 'generated_text' not in st.session_state:
    st.session_state.generated_text = ""

def check_rate_limit():
    """Check if the user has reached the session limit."""
    current_time = datetime.datetime.now()
    time_diff = (current_time - st.session_state.last_action_time).total_seconds()

    if time_diff < RATE_LIMIT_PERIOD and st.session_state.action_count >= USER_ACTION_LIMIT:
        remaining_time = RATE_LIMIT_PERIOD - time_diff
        st.warning(f"Please wait {int(remaining_time)} seconds before making another request.")
        return False
    
    if time_diff >= RATE_LIMIT_PERIOD:
        st.session_state.action_count = 0

    return True

# App Title and Description
st.set_page_config(page_title="🎙️ Voice to Story Creator", layout="centered")
st.markdown("<h1 style='color:#00adb5;'>Voice to Story Creator</h1>", unsafe_allow_html=True)
st.write("Turn voice notes into AI-generated stories powered by voice transcriptions, NLP & Generative AI.")

# File uploader with file size limit (2 mins of audio)
uploaded_file = st.file_uploader("Upload your audio file (max duration: 2 minutes)", type=["wav", "flac", "mp3"])

if uploaded_file is not None:
    # Check rate limit before allowing file upload
    if check_rate_limit():
        st.session_state.action_count += 1
        st.session_state.last_action_time = datetime.datetime.now()

        # Display uploaded audio
        st.audio(uploaded_file, format="audio/mp3", start_time=0)

        # Checking the duration of the audio file
        try:
            audio = uploaded_file.getvalue()
            with wave.open(io.BytesIO(audio), 'rb') as audio_file:
                framerate = audio_file.getframerate()
                frames = audio_file.getnframes()
                duration_seconds = frames / float(framerate)

                if duration_seconds > MAX_DURATION_SECONDS:
                    st.error(f"Error: Audio duration exceeds the 2-minute limit. Your audio is {duration_seconds:.2f} seconds.")
                else:
                    # Add a loading spinner while transcription happens
                    with st.spinner("Transcribing audio... Please wait."):
                        time.sleep(2)  # Simulate waiting time

                        # Transcribe the uploaded audio file
                        result = transcribe_audio(uploaded_file)

                        # Display the result
                        if "text" in result:
                            st.success("Transcription Complete:")
                            transcription_text = result["text"]
                            st.write(transcription_text)

                            # Language Detection
                            lang, confidence = detect_language(transcription_text)
                            st.subheader("Language Detection")
                            st.write(f"Detected Language: {lang}, Confidence: {confidence}")

                            # Keyword Extraction
                            keywords = extract_keywords(transcription_text)
                            st.subheader("Keyword Extraction")
                            st.write(keywords)

                            # Speech Rate Calculation
                            try:
                                speech_rate = calculate_speech_rate(transcription_text, duration_seconds)
                                st.subheader("Speech Rate")
                                st.write(f"Speech Rate: {speech_rate} words per minute")
                            except ZeroDivisionError:
                                st.error("Error: The duration of the audio is zero, which caused a division by zero error.")

                            # Word Cloud Visualization
                            wordcloud = generate_word_cloud(transcription_text)
                            st.subheader("Word Cloud")
                            st.image(wordcloud.to_array(), use_container_width=True)

                            # Add download button for the transcription text
                            st.download_button(
                                label="Download Transcription",
                                data=transcription_text,
                                file_name="transcription.txt",
                                mime="text/plain"
                            )

                            # Add download button for analysis results
                            analysis_results = f"""
                            Language Detection:
                            Detected Language: {lang}, Confidence: {confidence}

                            Keyword Extraction:
                            {keywords}

                            Speech Rate: {speech_rate} words per minute
                            """
                            st.download_button(
                                label="Download Analysis Results",
                                data=analysis_results,
                                file_name="analysis_results.txt",
                                mime="text/plain"
                            )

                            # Generative AI Analysis
                            st.subheader("Generative AI Analysis")
                            prompt = f"Create a creative story based on the following transcription: {transcription_text}"

                            # Let user decide if they want to use AI to generate a story
                            if st.button("Generate Story"):
                                with st.spinner("Generating Story... Please wait."):
                                    try:
                                        # Load and configure the model with Google's gemini-1.5-flash
                                        model = genai.GenerativeModel('gemini-1.5-flash')

                                        # Generate response from the model
                                        response = model.generate_content(prompt)

                                        # Display response in Streamlit
                                        st.write("Generated Story:")
                                        st.write(response.text)
                                    except Exception as e:
                                        st.error(f"Error: {e}")

        except Exception as e:
            st.error(f"Error processing the audio file: {e}")

# Footer with links
st.markdown("""
    <div class="footer">
        <p>Powered by Streamlit and Google Generative AI | <a href="https://github.com/yourusername/yourrepo" target="_blank">GitHub</a></p>
    </div>
""", unsafe_allow_html=True)
