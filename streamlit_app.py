import streamlit as st
import google.generativeai as genai
import time
import random
import uuid
import asyncio
import aiohttp
from gtts import gTTS
import os

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

async def search_web_async(query, session):
    """Asynchronously searches the web using Google Custom Search API."""
    api_key = st.secrets["GOOGLE_API_KEY"]
    search_engine_id = st.secrets["GOOGLE_SEARCH_ENGINE_ID"]

    if not api_key or not search_engine_id:
        return None  # Return None if API keys are missing

    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": api_key, "cx": search_engine_id, "q": query}

    try:
        async with session.get(search_url, params=params) as response:
            if response.status == 200:
                return await response.json()  # Properly get the response JSON
            else:
                return None  # Return None on error
    except requests.exceptions.RequestException as e:
        return None  # Return None on exception

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
    current_time = time.time()
    if st.session_state.block_time:
        time_left = st.session_state.block_time - current_time
        if time_left > 0:
            st.warning(f"Session limit reached. Try again in {int(time_left)} seconds or upgrade to pro, https://evertechcms.in/gridai")
            st.stop()
        else:
            st.session_state.block_time = None

    if st.session_state.session_count >= 2:
        st.session_state.block_time = current_time + 1 * 60  # Block for 1 minute
        st.warning("Session limit reached. Please wait 1 minute or upgrade to Pro.")
        st.markdown("You can upgrade to the Pro model & Get lifetime access at just Rs 999 [here](https://forms.gle/TJWH9HJ4kqUTN7Hp9).", unsafe_allow_html=True)
        st.experimental_set_query_params(user_hash=st.session_state.user_hash, block_time=st.session_state.block_time)
        st.stop()

# Refresh the page after the block time has passed
def auto_refresh():
    if 'block_time' in st.session_state and st.session_state.block_time:
        time_left = st.session_state.block_time - time.time()
        if time_left <= 0:
            st.experimental_set_query_params(user_hash=st.session_state.user_hash)
            st.experimental_rerun()

# Call auto_refresh function to check block time and refresh if needed
auto_refresh()

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

def download_file(content, filename, label, mime_type):
    """Provides the option to download content as a file."""
    # Convert content to bytes
    content_bytes = content.encode('utf-8') if isinstance(content, str) else content
    
    # Use st.download_button to provide the file download
    st.download_button(
        label=label,
        data=content_bytes,
        file_name=filename,
        mime=mime_type,
        use_container_width=True
    )

def text_to_audio(text):
    """Convert text to audio using gTTS."""
    # Remove asterisks from text
    text = text.replace("*", "")
    tts = gTTS(text=text, lang='en')
    audio_path = f"generated_content_{uuid.uuid4()}.mp3"
    tts.save(audio_path)
    return audio_path

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
    /* Hide Streamlit's default UI elements */
    .css-1r6p8d1 {display: none;} /* Hides the Streamlit logo in the top left */
    .css-1v3t3fg {display: none;} /* Hides the star button */
    .css-1r6p8d1 .st-ae {display: none;} /* Hides the Streamlit logo */
    header {visibility: hidden;} /* Hides the header */
    .css-1tqja98 {visibility: hidden;} /* Hides the header bar */
    </style>
""", unsafe_allow_html=True)

# Instructional text with animation and clickable link
st.markdown("""
    <h3>🚀 Welcome to AI-Powered Ghostwriter!</h3>
    <p>Generate high-quality content and check for originality using Generative AI and Google Search. Access the <a href="https://evertechcms.in/gridai" target="_blank"><strong>Grid AI Pro</strong></a> model now!</p>
""", unsafe_allow_html=True)


# Prompt Input Field
prompt = st.text_area("Enter your prompt:", placeholder="Write a blog about AI trends in 2025.", height=150)

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
                        for result in search_results['items'][:10]:  # Show top 10 results
                            with st.expander(result.get('title', 'No Title')):
                                st.write(f"**Source:** [{result.get('link', 'Unknown')}]({result.get('link', '#')})")
                                st.write(f"**Snippet:** {result.get('snippet', 'No snippet available.')}")
                                st.write("---")
                    else:
                        st.success("No similar content found online. Your content seems original!")

                    # Trigger Streamlit balloons after generation
                    st.balloons()

                    # Allow download of the generated content
                    download_file(generated_text, "generated_content.txt", "Download as Text File", "text/plain")

    if 'generated_text' in st.session_state and st.session_state.generated_text:
        if st.button("Convert to Podcast"):
            with st.spinner("Generating podcast..."):
                generated_text = st.session_state.generated_text
                audio_path = text_to_audio(generated_text)
                with open(audio_path, "rb") as audio_file:
                    st.download_button(
                        label="Download as Podcast",
                        data=audio_file,
                        file_name="generated_content.mp3",
                        mime="audio/mpeg"
                    )
                os.remove(audio_path)  # Clean up the audio file after download

    if 'generated_text' in st.session_state and st.session_state.generated_text:
        if st.button("Regenerate Content"):
            regenerated_text = regenerate_content(st.session_state.generated_text)
            st.subheader("Regenerated Content:")
            st.markdown(regenerated_text)
            download_file(regenerated_text, "regenerated_content.txt", "Download as Text File", "text/plain")

            # Option to convert the regenerated content to audio
            if st.button("Convert Regenerated Content to Podcast"):
                with st.spinner("Generating podcast..."):
                    audio_path = text_to_audio(regenerated_text)
                    with open(audio_path, "rb") as audio_file:
                        st.download_button(
                            label="Download Regenerated Content as Podcast",
                            data=audio_file,
                            file_name="regenerated_content.mp3",
                            mime="audio/mpeg"
                        )
                    os.remove(audio_path)  # Clean up the audio file after download

# Run the async main function
asyncio.run(main())

# Footer with links
st.markdown("""
    <div class="footer">
        <p>Powered by Streamlit and Google Generative AI | <a href="https://github.com/yourusername/yourrepo" target="_blank">GitHub</a></p>
    </div>
""", unsafe_allow_html=True)
