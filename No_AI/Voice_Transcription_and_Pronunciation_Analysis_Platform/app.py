"""
=================================================================================
VOICE TRANSCRIPTION AND PRONUNCIATION ANALYSIS APPLICATION
=================================================================================

This Flask application provides a comprehensive platform for voice recording,
speech-to-text transcription, multi-accent audio playback, and detailed
pronunciation analysis with educational feedback.

MAIN FEATURES:
--------------
1. Voice Recording: Capture up to 10 seconds of audio with real-time timer
2. Speech-to-Text: Automatic transcription using Google Speech Recognition
3. Multi-Accent Playback: Listen to transcribed text in 9 English accents
4. Pronunciation Comparison: Detailed analysis comparing user vs native pronunciation
5. Word-by-Word Practice: Targeted practice for individual words with instant feedback
6. Multi-Language Interface: Support for 9 languages (EN, FR, DE, IT, ES, ZH, KO, JA, RU)

TECHNICAL ARCHITECTURE:
-----------------------
- Backend: Flask web framework (Python)
- Speech Recognition: Google Speech-to-Text API via SpeechRecognition library
- Text-to-Speech: Microsoft Edge TTS with neural voices (edge-tts)
- Audio Processing: pydub for format conversion, scipy for signal processing
- Visualization: matplotlib for generating comparison plots
- Audio Format: WebM/OGG input converted to WAV (16kHz, mono)

API ENDPOINTS:
--------------
- GET  /                     : Serve main interface
- GET  /translations/<lang>  : Get UI translations for specified language
- POST /transcribe           : Convert audio to text
- POST /text-to-speech       : Generate speech in specified accent
- POST /compare-pronunciation: Compare full sentence pronunciation
- POST /practice-word        : Analyze single word pronunciation

AUTHOR: Voice Learning Platform
VERSION: 2.0
"""

# ============================================================================
# IMPORTS AND DEPENDENCIES
# ============================================================================

from flask import Flask, render_template, request, jsonify, send_file
import speech_recognition as sr  # Google Speech Recognition
import os
from werkzeug.utils import secure_filename
import tempfile  # For temporary file storage
from pydub import AudioSegment  # Audio format conversion
import io
import numpy as np  # Numerical operations for audio processing
import base64  # Encoding images for web transfer
import matplotlib

matplotlib.use('Agg')  # Non-interactive backend for server-side plotting
import matplotlib.pyplot as plt
from scipy import signal  # Signal processing for spectrograms and analysis
import asyncio  # Async operations for edge-tts
import edge_tts  # Microsoft Edge Text-to-Speech

# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit uploads to 16MB
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()  # Use system temp directory

# ============================================================================
# LANGUAGE TRANSLATIONS
# ============================================================================
# Complete UI translations for 9 languages to support international users
# Each dictionary contains all UI strings, labels, messages, and instructions

TRANSLATIONS = {
    'en': {
        # Main interface
        'title': 'Voice Transcriber',
        'subtitle': 'Record your voice and see it transcribed in real-time',

        # Recording states
        'ready': 'Ready to record',
        'recording': 'Recording...',
        'processing': 'Processing...',
        'listening': 'Listening...',

        # Button labels
        'start_recording': 'Start Recording',
        'stop_recording': 'Stop Recording',
        'compare_pronunciation': 'Compare My Pronunciation',
        'try_again': '🔄 Try Again',

        # Section titles
        'transcription': 'Transcription',
        'listen_accents': 'Listen in Different Accents',
        'pronunciation_analysis': 'Pronunciation Analysis',
        'comparison_title': 'Pronunciation Comparison & Feedback',
        'practice_words': 'Practice Word by Word',

        # Instructions and hints
        'transcription_placeholder': 'Your transcribed text will appear here...',
        'click_to_hear': 'Click to hear your text',
        'click_to_zoom': 'Click any plot to zoom in',
        'practice_instructions': 'Click a word to hear it, then record your pronunciation',
        'now_say': 'Now say:',
        'recording_word': 'Recording... (3 seconds)',

        # Accent names
        'american': 'American',
        'english': 'British',
        'scottish': 'Scottish',
        'irish': 'Irish',
        'australian': 'Australian',
        'new_zealand': 'New Zealand',
        'south_african': 'South African',
        'indian': 'Indian',
        'nigerian': 'Nigerian',

        # Status messages
        'playing': 'Playing',
        'analyzing': 'Analyzing...',

        # Visualization labels
        'waveform': 'Waveform',
        'spectrogram': 'Spectrogram',
        'energy_envelope': 'Energy Envelope',
        'zero_crossing': 'Zero Crossing Rate',
        'frequency_spectrum': 'Frequency Spectrum',
        'statistics': 'Statistics',

        # Descriptions
        'waveform_desc': 'Shows amplitude over time',
        'spectrogram_desc': 'Frequency patterns over time',
        'energy_desc': 'Speech intensity and emphasis',
        'zcr_desc': 'Voiced vs unvoiced sounds',
        'spectrum_desc': 'Dominant frequencies',
        'stats_desc': 'Detailed audio metrics',

        # Error messages
        'error_no_audio': 'Could not understand audio. Please speak more clearly and ensure there\'s minimal background noise.',
        'error_connection': 'Could not request results from Google Speech Recognition service. Please check your internet connection.',

        # Settings
        'language': 'Language'
    },

    # French translations
    'fr': {
        'title': 'Transcripteur Vocal',
        'subtitle': 'Enregistrez votre voix et voyez-la transcrite en temps réel',
        'ready': 'Prêt à enregistrer',
        'recording': 'Enregistrement...',
        'processing': 'Traitement...',
        'start_recording': 'Démarrer l\'enregistrement',
        'stop_recording': 'Arrêter l\'enregistrement',
        'transcription': 'Transcription',
        'transcription_placeholder': 'Votre texte transcrit apparaîtra ici...',
        'listen_accents': 'Écouter en différents accents',
        'click_to_hear': 'Cliquez pour entendre votre texte',
        'american': 'Américain',
        'english': 'Britannique',
        'scottish': 'Écossais',
        'irish': 'Irlandais',
        'australian': 'Australien',
        'new_zealand': 'Néo-zélandais',
        'south_african': 'Sud-africain',
        'indian': 'Indien',
        'nigerian': 'Nigérian',
        'playing': 'Lecture',
        'compare_pronunciation': 'Comparer ma prononciation',
        'analyzing': 'Analyse...',
        'pronunciation_analysis': 'Analyse de prononciation',
        'click_to_zoom': 'Cliquez sur un graphique pour zoomer',
        'comparison_title': 'Comparaison et retours de prononciation',
        'waveform': 'Forme d\'onde',
        'spectrogram': 'Spectrogramme',
        'energy_envelope': 'Enveloppe d\'énergie',
        'zero_crossing': 'Taux de passage par zéro',
        'frequency_spectrum': 'Spectre de fréquences',
        'statistics': 'Statistiques',
        'waveform_desc': 'Montre l\'amplitude dans le temps',
        'spectrogram_desc': 'Motifs de fréquence dans le temps',
        'energy_desc': 'Intensité et emphase de la parole',
        'zcr_desc': 'Sons voisés vs non-voisés',
        'spectrum_desc': 'Fréquences dominantes',
        'stats_desc': 'Métriques audio détaillées',
        'listening': 'Écoute...',
        'error_no_audio': 'Impossible de comprendre l\'audio. Veuillez parler plus clairement et assurez-vous qu\'il y a un minimum de bruit de fond.',
        'error_connection': 'Impossible d\'obtenir les résultats du service de reconnaissance vocale Google. Veuillez vérifier votre connexion Internet.',
        'language': 'Langue',
        'practice_words': 'Pratiquer mot par mot',
        'practice_instructions': 'Cliquez sur un mot pour l\'entendre, puis enregistrez votre prononciation',
        'now_say': 'Maintenant dites:',
        'recording_word': 'Enregistrement... (3 secondes)',
        'try_again': '🔄 Réessayer'
    },

    # Add remaining languages (DE, IT, ES, ZH, KO, JA, RU) - truncated for brevity
    # Full translations available in production code
}

# ============================================================================
# ACCENT VOICE MAPPINGS
# ============================================================================
# Microsoft Edge TTS neural voices for each English accent
# Each voice is carefully selected to provide authentic regional pronunciation

ACCENT_VOICES = {
    'american': 'en-US-GuyNeural',  # Standard American English
    'english': 'en-GB-RyanNeural',  # British English (Received Pronunciation)
    'scottish': 'en-GB-ThomasNeural',  # Scottish English
    'irish': 'en-IE-ConnorNeural',  # Irish English
    'australian': 'en-AU-WilliamNeural',  # Australian English
    'new_zealand': 'en-NZ-MitchellNeural',  # New Zealand English
    'south_african': 'en-ZA-LukeNeural',  # South African English
    'indian': 'en-IN-PrabhatNeural',  # Indian English
    'nigerian': 'en-NG-AbeoNeural'  # Nigerian English
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_speech_sync(text, voice, output_path):
    """
    Synchronously generate speech using edge-tts (Microsoft Edge TTS).

    This function wraps the async edge-tts library in a synchronous interface
    that works with Flask's threading model. It creates a new event loop for
    each request to avoid conflicts with other async operations.

    Parameters:
    -----------
    text : str
        The text to convert to speech
    voice : str
        Microsoft Edge voice ID (e.g., 'en-US-GuyNeural')
    output_path : str
        File path where the generated MP3 will be saved

    Technical Notes:
    ----------------
    - Creates isolated event loop per request to avoid threading issues
    - Properly closes loop after completion to prevent memory leaks
    - Uses process ID in filenames to prevent collisions in multi-user scenarios
    """
    # Create a new event loop for this request
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Run the async generation in this loop
        communicate = edge_tts.Communicate(text, voice)
        loop.run_until_complete(communicate.save(output_path))
    finally:
        # Clean up the loop
        loop.close()


# ============================================================================
# ROUTE HANDLERS
# ============================================================================

@app.route('/')
def index():
    """
    Serve the main application interface.

    Returns:
    --------
    HTML template : index.html
        Main single-page application with all features
    """
    return render_template('index.html')


@app.route('/translations/<lang>')
def get_translations(lang):
    """
    Get UI translations for specified language.

    This endpoint supports the multi-language interface by providing
    all UI strings in the requested language. If the language is not
    supported, it defaults to English.

    Parameters:
    -----------
    lang : str
        Two-letter language code (e.g., 'en', 'fr', 'de')

    Returns:
    --------
    JSON : dict
        Dictionary containing all UI translations

    Example:
    --------
    GET /translations/fr
    Returns: {"title": "Transcripteur Vocal", ...}
    """
    return jsonify(TRANSLATIONS.get(lang, TRANSLATIONS['en']))


@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """
    Convert uploaded audio to text using Google Speech Recognition.

    This endpoint handles the core speech-to-text functionality:
    1. Receives audio file (WebM/OGG from browser MediaRecorder)
    2. Converts to WAV format (16kHz, mono) for compatibility
    3. Applies noise reduction and energy threshold adjustment
    4. Performs speech recognition using Google's API

    Request Format:
    ---------------
    - Content-Type: multipart/form-data
    - Field: 'audio' (audio file in WebM or OGG format)

    Response Format:
    ----------------
    Success: {"success": true, "text": "transcribed text"}
    Error: {"success": false, "text": "error message"}

    Audio Processing Pipeline:
    --------------------------
    1. Try WebM format first (Chrome, Edge)
    2. Fallback to OGG format (Firefox)
    3. Final fallback to WAV format
    4. Convert to 16kHz mono WAV for recognition
    5. Apply ambient noise adjustment
    6. Set dynamic energy threshold for better accuracy

    Technical Notes:
    ----------------
    - Uses temporary files to avoid memory issues with large audio
    - Cleans up temporary files after processing
    - Handles various audio formats from different browsers
    - Implements error handling for network and recognition failures
    """
    try:
        # Check if audio file was uploaded
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'text': 'No audio file provided'
            })

        audio_file = request.files['audio']

        # Read audio data into memory
        audio_data = audio_file.read()

        # Convert audio to WAV format (required for speech recognition)
        # Try multiple formats as different browsers use different codecs
        try:
            # Try WebM format first (Chrome, Edge)
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format="webm")
        except:
            try:
                # Try OGG format (Firefox)
                audio = AudioSegment.from_file(io.BytesIO(audio_data), format="ogg")
            except:
                # Final fallback to WAV
                audio = AudioSegment.from_file(io.BytesIO(audio_data), format="wav")

        # Convert to 16kHz mono for optimal speech recognition
        audio = audio.set_frame_rate(16000).set_channels(1)

        # Save to temporary file
        temp_wav_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_audio.wav')
        audio.export(temp_wav_path, format="wav")

        # Initialize speech recognizer
        recognizer = sr.Recognizer()

        # Optimize recognition parameters
        recognizer.dynamic_energy_threshold = True  # Adapt to ambient noise
        recognizer.energy_threshold = 4000  # Minimum audio energy to consider as speech

        # Load and process audio file
        with sr.AudioFile(temp_wav_path) as source:
            # Adjust for ambient noise (first 0.5 seconds)
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            # Record the audio
            audio_data = recognizer.record(source)

        # Perform speech recognition using Google's API
        try:
            text = recognizer.recognize_google(audio_data, language='en-US')

            # Clean up temporary file
            if os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)

            return jsonify({
                'success': True,
                'text': text
            })

        except sr.UnknownValueError:
            # Audio was unclear or contained no speech
            if os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)
            return jsonify({
                'success': False,
                'text': 'Could not understand audio. Please speak more clearly and ensure there\'s minimal background noise.'
            })
        except sr.RequestError as e:
            # Network error or API issue
            if os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)
            return jsonify({
                'success': False,
                'text': f'Could not request results from Google Speech Recognition service. Please check your internet connection.'
            })

    except Exception as e:
        # Unexpected error
        print(f"Error in transcription: {str(e)}")
        return jsonify({
            'success': False,
            'text': f'Error processing audio: {str(e)}'
        })


@app.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    """
    Convert text to speech with specified accent using Microsoft Edge TTS.

    This endpoint generates high-quality neural voice audio in various English
    accents. The audio is returned as base64-encoded MP3 for immediate playback.

    Request Format:
    ---------------
    Content-Type: application/json
    Body: {
        "text": "text to speak",
        "accent": "american" | "english" | "scottish" | etc.
    }

    Response Format:
    ----------------
    Success: {
        "success": true,
        "audio": "base64_encoded_mp3_data",
        "accent": "accent_name"
    }
    Error: {
        "success": false,
        "error": "error message"
    }

    Supported Accents:
    ------------------
    - american: Standard American English
    - english: British English (RP)
    - scottish: Scottish English
    - irish: Irish English
    - australian: Australian English
    - new_zealand: New Zealand English
    - south_african: South African English
    - indian: Indian English
    - nigerian: Nigerian English

    Technical Notes:
    ----------------
    - Uses Microsoft Edge neural voices for natural-sounding speech
    - Generates MP3 format for broad compatibility
    - Uses process ID in temp filenames to avoid collisions
    - Cleans up temporary files after encoding
    """
    try:
        # Parse request data
        data = request.get_json()
        text = data.get('text', '')
        accent = data.get('accent', 'american')

        if not text:
            return jsonify({'error': 'No text provided'}), 400

        # Get voice for requested accent
        voice = ACCENT_VOICES.get(accent, ACCENT_VOICES['american'])

        # Generate speech using edge-tts
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], f'tts_{accent}_{os.getpid()}.mp3')

        # Use synchronous wrapper for edge-tts
        generate_speech_sync(text, voice, audio_path)

        # Read generated audio and encode as base64
        with open(audio_path, 'rb') as audio_file:
            audio_data = audio_file.read()
            audio_base64 = base64.b64encode(audio_data).decode()

        # Clean up temporary file
        if os.path.exists(audio_path):
            os.remove(audio_path)

        return jsonify({
            'success': True,
            'audio': audio_base64,
            'accent': accent
        })

    except Exception as e:
        print(f"Error generating speech: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Error generating speech: {str(e)}'
        }), 500


# Additional routes and functions continue...
# (compare-pronunciation, practice-word, visualization generation functions)
# Full implementation available in production code

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)