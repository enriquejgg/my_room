# 📝 Code Guide: Understanding the Application

This document provides a detailed explanation of how the code works in both `app.py` (backend) and `index.html` (frontend).

---

## 🐍 Backend Code Structure (app.py)

### Overview
The Flask backend handles all server-side processing including audio conversion, speech recognition, text-to-speech generation, and pronunciation analysis.

---

### Section 1: Imports and Configuration (Lines 1-20)

```python
from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
from pydub import AudioSegment
import matplotlib
matplotlib.use('Agg')  # IMPORTANT: Non-interactive backend for server rendering
```

**Key Points:**
- `Flask`: Web framework for routing and HTTP handling
- `speech_recognition`: Wrapper for Google Speech-to-Text API
- `pydub`: Audio format conversion (WebM/OGG → WAV)
- `matplotlib.use('Agg')`: Required for generating plots on server without display
- `edge_tts`: Microsoft's Text-to-Speech with neural voices
- `scipy.signal`: For spectrograms and frequency analysis

**Configuration:**
```python
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit uploads to 16MB
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()  # Use system temp directory
```

---

### Section 2: Translations Dictionary (Lines 21-450)

Complete UI translations for 9 languages:

```python
TRANSLATIONS = {
    'en': {
        'title': 'Voice Transcriber',
        'subtitle': 'Record your voice...',
        # ... 50+ translation keys
    },
    'fr': { ... },
    'de': { ... },
    # ... 9 languages total
}
```

**Purpose:**
- Support international users
- Translate all UI elements
- Served via `/translations/<lang>` endpoint

---

### Section 3: Accent Voice Mappings (Lines 451-470)

Maps accent names to Microsoft Edge neural voice IDs:

```python
ACCENT_VOICES = {
    'american': 'en-US-GuyNeural',
    'english': 'en-GB-RyanNeural',
    'scottish': 'en-GB-ThomasNeural',
    # ... 9 accents total
}
```

**Usage:**
- Looked up when generating TTS audio
- Each voice has authentic regional characteristics

---

### Section 4: Utility Functions (Lines 471-500)

#### `generate_speech_sync(text, voice, output_path)`

**Purpose:** Synchronously generate speech using async edge-tts library

**Why It Exists:**
- edge-tts is async (uses asyncio)
- Flask is sync (uses threading)
- This function bridges the two

**How It Works:**
```python
def generate_speech_sync(text, voice, output_path):
    # Create isolated event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Run async TTS generation
        communicate = edge_tts.Communicate(text, voice)
        loop.run_until_complete(communicate.save(output_path))
    finally:
        # Clean up to prevent memory leaks
        loop.close()
```

**Key Concepts:**
- Creates new event loop per request
- Avoids conflicts with other async operations
- Properly closes loop to prevent resource leaks

---

### Section 5: Route Handlers (Lines 501-800)

#### Route 1: `GET /`
```python
@app.route('/')
def index():
    return render_template('index.html')
```

**Simple:** Just serves the main HTML page

---

#### Route 2: `GET /translations/<lang>`
```python
@app.route('/translations/<lang>')
def get_translations(lang):
    return jsonify(TRANSLATIONS.get(lang, TRANSLATIONS['en']))
```

**Purpose:** Provide UI translations for frontend
**Returns:** JSON dictionary of translated strings

---

#### Route 3: `POST /transcribe`

**Most Complex Route** - Handles audio transcription

**Processing Pipeline:**
```python
# 1. Receive audio file
audio_file = request.files['audio']
audio_data = audio_file.read()

# 2. Convert format (try multiple formats for browser compatibility)
try:
    audio = AudioSegment.from_file(io.BytesIO(audio_data), format="webm")
except:
    try:
        audio = AudioSegment.from_file(io.BytesIO(audio_data), format="ogg")
    except:
        audio = AudioSegment.from_file(io.BytesIO(audio_data), format="wav")

# 3. Convert to optimal format for recognition
audio = audio.set_frame_rate(16000).set_channels(1)  # 16kHz, mono

# 4. Save to temporary file
temp_wav_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_audio.wav')
audio.export(temp_wav_path, format="wav")

# 5. Initialize recognizer with optimal settings
recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = True  # Adapt to ambient noise
recognizer.energy_threshold = 4000          # Minimum energy to consider speech

# 6. Load audio and adjust for noise
with sr.AudioFile(temp_wav_path) as source:
    recognizer.adjust_for_ambient_noise(source, duration=0.5)
    audio_data = recognizer.record(source)

# 7. Perform recognition
text = recognizer.recognize_google(audio_data, language='en-US')

# 8. Clean up and return
os.remove(temp_wav_path)
return jsonify({'success': True, 'text': text})
```

**Error Handling:**
```python
except sr.UnknownValueError:
    # Couldn't understand audio
    return jsonify({'success': False, 'text': 'Could not understand audio...'})
    
except sr.RequestError:
    # Network/API error
    return jsonify({'success': False, 'text': 'Could not reach Google API...'})
```

**Why This Works:**
- Tries multiple formats (browser compatibility)
- Converts to optimal format (16kHz mono WAV)
- Adjusts for ambient noise
- Proper error handling for all cases

---

#### Route 4: `POST /text-to-speech`

**Purpose:** Generate speech in specified accent

**Process:**
```python
# 1. Parse request
data = request.get_json()
text = data.get('text', '')
accent = data.get('accent', 'american')

# 2. Get voice for accent
voice = ACCENT_VOICES.get(accent, ACCENT_VOICES['american'])

# 3. Generate speech (uses process ID for unique filename)
audio_path = os.path.join(app.config['UPLOAD_FOLDER'], f'tts_{accent}_{os.getpid()}.mp3')
generate_speech_sync(text, voice, audio_path)

# 4. Read and encode as base64
with open(audio_path, 'rb') as audio_file:
    audio_data = audio_file.read()
    audio_base64 = base64.b64encode(audio_data).decode()

# 5. Clean up and return
os.remove(audio_path)
return jsonify({'success': True, 'audio': audio_base64, 'accent': accent})
```

**Why Base64?**
- Can't send binary data in JSON
- Base64 encoding converts binary → text
- Frontend decodes back to binary for playback

---

#### Route 5: `POST /compare-pronunciation`

**Most Complex Analysis Route**

**High-Level Flow:**
```
1. Receive user audio + target accent + text
2. Convert user audio to WAV
3. Generate target accent audio
4. Extract audio samples as numpy arrays
5. Perform parallel analysis on both
6. Calculate similarity metrics
7. Generate comparison visualizations
8. Create personalized feedback
9. Return everything as JSON
```

**Key Processing Steps:**

```python
# Convert user audio
user_audio = AudioSegment.from_file(io.BytesIO(user_audio_data), format="webm")
user_audio = user_audio.set_frame_rate(16000).set_channels(1)

# Generate target audio
voice = ACCENT_VOICES.get(accent)
generate_speech_sync(text, voice, target_audio_path)
target_audio = AudioSegment.from_file(target_audio_path)

# Extract samples as numpy arrays
user_samples = np.array(user_audio.get_array_of_samples())
target_samples = np.array(target_audio.get_array_of_samples())

# Generate comparison (complex function)
comparison_viz, advice = generate_pronunciation_comparison(
    user_samples, target_samples, sample_rate, accent, text
)

# Extract words for practice
words = [word.strip('.,!?;:') for word in text.split()]

# Return everything
return jsonify({
    'success': True,
    'comparison': comparison_viz,  # Base64 image
    'advice': advice,              # List of feedback cards
    'words': words                 # List for practice
})
```

---

#### Route 6: `POST /practice-word`

**Purpose:** Analyze single word pronunciation

**Similar to full comparison but:**
- Works on single word
- Simpler visualization (2 panels)
- Shorter feedback (one paragraph)
- Faster processing

---

### Section 6: Comparison Functions (Lines 801-1100)

#### `generate_pronunciation_comparison(user_samples, target_samples, ...)`

**Purpose:** Create comprehensive comparison visualization

**Steps:**

**1. Normalize Audio:**
```python
# Normalize to -1 to 1 range
user_samples = user_samples / np.max(np.abs(user_samples))
target_samples = target_samples / np.max(np.abs(target_samples))

# Make same length
min_len = min(len(user_samples), len(target_samples))
user_samples = user_samples[:min_len]
target_samples = target_samples[:min_len]
```

**2. Calculate Spectrograms:**
```python
# Use scipy.signal.spectrogram
frequencies_u, times_u, spectrogram_u = signal.spectrogram(
    user_samples, 
    sample_rate, 
    nperseg=512  # Window size for FFT
)

# Convert to decibels
spectrogram_db_u = 10 * np.log10(spectrogram_u + 1e-10)
```

**What is a Spectrogram?**
- Shows how frequencies change over time
- X-axis: Time
- Y-axis: Frequency
- Color: Intensity (energy at that frequency)
- Like a "fingerprint" of sound

**3. Extract Pitch:**
```python
# Find dominant frequency at each time point
user_freqs = []
for i in range(spectrogram_u.shape[1]):
    # Find frequency bin with maximum energy
    dominant_freq = frequencies_u[np.argmax(spectrogram_u[:, i])]
    user_freqs.append(dominant_freq)

# Calculate average pitch
user_pitch_mean = np.mean(user_freqs)
```

**4. Calculate Energy:**
```python
# Root Mean Square energy over short windows
window_size = int(0.02 * sample_rate)  # 20ms windows
user_energy = np.convolve(
    user_samples**2, 
    np.ones(window_size)/window_size, 
    mode='same'
)
```

**5. Calculate Similarity:**
```python
# Spectral correlation (0 to 1)
min_spec_len = min(spectrogram_u.shape[1], spectrogram_t.shape[1])
spectral_correlation = np.corrcoef(
    spectrogram_u[:, :min_spec_len].flatten(),
    spectrogram_t[:, :min_spec_len].flatten()
)[0, 1]

# Convert to percentage
similarity_percent = max(0, spectral_correlation * 100)
```

**6. Create Visualization:**
```python
# Create figure with 5 rows
fig = plt.figure(figsize=(18, 14))
gs = fig.add_gridspec(5, 2, hspace=0.4, wspace=0.35)

# Row 1: Title with similarity score
ax_title = fig.add_subplot(gs[0, :])
# ... add title and score badge

# Row 2: Waveform overlay
ax1 = fig.add_subplot(gs[1, :])
ax1.plot(time, user_samples, color='#ff6b6b', label='Your pronunciation')
ax1.plot(time, target_samples, color='#667eea', label='Target accent')

# Row 3: Spectrograms side-by-side
ax2 = fig.add_subplot(gs[2, 0])  # User
ax3 = fig.add_subplot(gs[2, 1])  # Target
# ... plot spectrograms with pcolormesh

# Row 4: Pitch and Energy overlays
ax4 = fig.add_subplot(gs[3, 0])  # Pitch
ax5 = fig.add_subplot(gs[3, 1])  # Energy
# ... plot comparisons

# Row 5: Metrics table
ax6 = fig.add_subplot(gs[4, :])
# ... add text box with statistics

# Save to base64
buffer = io.BytesIO()
plt.savefig(buffer, format='png', dpi=130)
buffer.seek(0)
image_base64 = base64.b64encode(buffer.read()).decode()
plt.close(fig)  # IMPORTANT: Close to free memory
```

**7. Generate Advice:**
```python
advice = generate_pronunciation_advice(
    pitch_diff, 
    energy_diff, 
    similarity_percent, 
    accent, 
    user_pitch_mean, 
    target_pitch_mean
)
```

---

#### `generate_pronunciation_advice(...)`

**Purpose:** Create personalized feedback cards

**Logic:**
```python
advice = []

# Overall assessment
if similarity >= 80:
    advice.append({
        'level': 'excellent',
        'title': '🎉 Excellent Pronunciation!',
        'text': 'Your pronunciation is very close...'
    })
elif similarity >= 60:
    advice.append({
        'level': 'good',
        'title': '👍 Good Pronunciation',
        'text': 'You\'re doing well!...'
    })
else:
    advice.append({
        'level': 'needs-work',
        'title': '💪 Room for Improvement',
        'text': 'Focus on the key differences...'
    })

# Pitch advice
if abs(pitch_diff) > 20:  # Threshold for significant difference
    if pitch_diff > 0:
        advice.append({
            'level': 'tip',
            'title': '🎵 Lower Your Pitch',
            'text': f'Your voice is {abs(pitch_diff):.0f} Hz higher...'
        })
    else:
        advice.append({
            'level': 'tip',
            'title': '🎵 Raise Your Pitch',
            'text': f'Your voice is {abs(pitch_diff):.0f} Hz lower...'
        })

# Energy advice
# ... similar logic for energy

# Accent-specific tips (pre-written for each accent)
accent_tips = {
    'american': {
        'title': '🇺🇸 American Accent Tips',
        'text': 'Focus on rhotic "r" sounds...'
    },
    # ... for each accent
}

advice.append(accent_tips[accent])

return advice
```

---

### Section 7: Word Practice Functions (Lines 1100-1300)

#### `generate_word_comparison(user_samples, target_samples, ...)`

**Simplified version of full comparison:**
- 2-panel visualization (waveform + spectrograms)
- Faster processing
- Single feedback paragraph

**Key Difference:**
```python
# Compact 2-row layout instead of 5-row
fig, axes = plt.subplots(2, 1, figsize=(10, 6))

# Row 1: Waveform overlay
# Row 2: Side-by-side spectrograms (using subfigures)
```

#### `generate_word_feedback(...)`

**Creates concise, word-specific feedback:**
```python
feedback = []

# Quality assessment
if similarity >= 85:
    feedback.append("✅ Excellent!")
# ... etc

# Pitch tip (if needed)
if abs(pitch_diff) > 30:
    feedback.append(f"🎵 Lower your pitch by ~{abs(pitch_diff):.0f} Hz.")

# Word-specific tip
word_lower = word.lower()
if word_lower[0] in 'aeiou':
    feedback.append(f"💡 Focus on the vowel sound at the start of '{word}'.")

# Join into single string
return ' '.join(feedback)
```

---

## 🌐 Frontend Code Structure (index.html)

### Overview
Single-page application with HTML structure, CSS styling, and JavaScript logic all in one file.

---

### Section 1: HTML Structure (Lines 1-100)

#### Meta Tags and Setup
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voice Transcriber</title>
    
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Instrument+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
```

**Fonts Used:**
- `DM Serif Display`: Elegant serif for title
- `Instrument Sans`: Modern sans-serif for UI

#### Language Selector
```html
<div class="language-selector">
    <select id="languageSelect" onchange="changeLanguage(this.value)">
        <option value="en">🇬🇧 English</option>
        <option value="fr">🇫🇷 Français</option>
        <!-- ... 9 languages total -->
    </select>
</div>
```

#### Main Sections
```html
<!-- 1. Recording Section -->
<div class="recording-section">
    <div class="visualizer-container">
        <!-- Microphone icon -->
        <!-- Status text -->
        <!-- Timer display -->
    </div>
    <div class="controls">
        <button id="startBtn" onclick="startRecording()">Start Recording</button>
        <button id="stopBtn" onclick="stopRecording()">Stop Recording</button>
    </div>
</div>

<!-- 2. Transcription Display -->
<div class="transcription-section">
    <div id="transcription">Your text will appear here...</div>
</div>

<!-- 3. Accent Selection -->
<div class="accent-section" id="accentSection">
    <div class="accent-grid">
        <button onclick="playAccent('american')">🇺🇸 American</button>
        <!-- ... 9 accent buttons -->
    </div>
    <div id="audioPlayerContainer">
        <audio id="accentAudioPlayer" controls></audio>
    </div>
</div>

<!-- 4. Comparison Results -->
<div class="comparison-section" id="comparisonSection">
    <img id="comparisonImg" />
    <div id="adviceContainer"></div>
    
    <!-- 5. Word Practice -->
    <div id="wordPracticeSection">
        <div id="wordsGrid"></div>
        <div id="wordResult"></div>
    </div>
</div>
```

---

### Section 2: CSS Styling (Lines 100-800)

#### CSS Variables
```css
:root {
    --primary: #2c3e50;      /* Dark blue-gray */
    --accent: #ff6b6b;       /* Coral red */
    --accent-dark: #ff5252;  /* Darker red */
    --surface: #ffffff;      /* White */
    --text: #2c3e50;         /* Dark text */
    --text-light: #6c757d;   /* Light gray text */
}
```

#### Key Design Patterns

**Gradient Background:**
```css
body {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

**Card Shadows:**
```css
.container {
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}
```

**Smooth Animations:**
```css
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.container {
    animation: fadeIn 0.8s ease-out;
}
```

**Hover Effects:**
```css
.btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(255, 107, 107, 0.4);
}
```

**Recording Pulse Animation:**
```css
@keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.05); opacity: 0.8; }
}

.recording-indicator {
    animation: pulse 1.5s ease-in-out infinite;
}
```

---

### Section 3: JavaScript Logic (Lines 800-1500)

#### Global Variables
```javascript
let mediaRecorder;           // MediaRecorder instance
let audioChunks = [];        // Stores recorded audio chunks
let startTime;               // Recording start timestamp
let timerInterval;           // Timer interval ID
const MAX_DURATION = 10000;  // 10 seconds
let currentTranscription = ""; // Transcribed text
let currentAudio = null;     // Currently playing audio
let currentAccent = "";      // Selected accent
let userAudioBlob = null;    // User's recording for comparison
let practiceWords = [];      // Words from sentence
let wordPracticeCounts = {}; // Track practice attempts
```

---

#### Translation System

**Load Translations:**
```javascript
async function loadTranslations(lang) {
    try {
        // Fetch from backend
        const response = await fetch(`/translations/${lang}`);
        translations = await response.json();
        currentLanguage = lang;
        
        // Update all text
        updatePageText();
        
        // Save preference
        localStorage.setItem('preferredLanguage', lang);
    } catch (error) {
        console.error('Error loading translations:', error);
    }
}
```

**Update Page Text:**
```javascript
function updatePageText() {
    // Find all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        if (translations[key]) {
            element.textContent = translations[key];
        }
    });
}
```

**How It Works:**
1. HTML elements have `data-i18n="key"` attribute
2. JavaScript looks up key in translations dictionary
3. Updates textContent with translated value
4. Happens instantly on language change

---

#### Recording System

**Start Recording:**
```javascript
async function startRecording() {
    try {
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,    // Remove echo
                noiseSuppression: true,    // Reduce background noise
                sampleRate: 16000          // 16kHz sampling
            }
        });
        
        // Create MediaRecorder
        mediaRecorder = new MediaRecorder(stream, {
            mimeType: 'audio/webm'  // Chrome format
        });
        
        // Reset audio chunks
        audioChunks = [];
        
        // Collect audio data
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        // Handle stop event
        mediaRecorder.onstop = () => {
            // Create blob from chunks
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            
            // Stop all tracks (releases microphone)
            stream.getTracks().forEach(track => track.stop());
            
            // Send for transcription
            sendAudioForTranscription(audioBlob);
        };
        
        // Start recording
        mediaRecorder.start();
        
        // Start timer
        startTime = Date.now();
        timerInterval = setInterval(updateTimer, 100);
        
        // Auto-stop at 10 seconds
        autoStopTimeout = setTimeout(() => {
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                stopRecording();
            }
        }, MAX_DURATION);
        
        // Update UI
        document.getElementById('startBtn').disabled = true;
        document.getElementById('stopBtn').disabled = false;
        document.getElementById('status').textContent = translations.recording;
        document.getElementById('micIcon').classList.add('recording');
        
    } catch (error) {
        console.error('Error accessing microphone:', error);
        alert('Could not access microphone. Please check permissions.');
    }
}
```

**Key Concepts:**
- `getUserMedia`: Browser API to access camera/microphone
- `MediaRecorder`: Records media streams
- `Blob`: Binary Large Object (holds audio data)
- Event handlers: ondataavailable, onstop
- Auto-stop: setTimeout for 10-second limit

**Update Timer:**
```javascript
function updateTimer() {
    const elapsed = Date.now() - startTime;
    const seconds = Math.floor(elapsed / 1000);
    const milliseconds = Math.floor((elapsed % 1000) / 100);
    
    // Format: MM:SS
    const display = `00:${seconds.toString().padStart(2, '0')}`;
    document.getElementById('timer').textContent = display;
    
    // Warning at 8+ seconds
    if (elapsed >= 8000) {
        document.getElementById('timer').classList.add('warning');
    }
}
```

**Stop Recording:**
```javascript
function stopRecording() {
    // Stop MediaRecorder
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
    }
    
    // Clear timers
    clearInterval(timerInterval);
    clearTimeout(autoStopTimeout);
    
    // Update UI
    document.getElementById('startBtn').disabled = false;
    document.getElementById('stopBtn').disabled = true;
    document.getElementById('status').textContent = translations.processing;
    // ... more UI updates
}
```

---

#### Transcription Handler

**Send Audio for Transcription:**
```javascript
async function sendAudioForTranscription(audioBlob) {
    // Create FormData (for file upload)
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');
    
    // Store for later comparison
    userAudioBlob = audioBlob;
    
    try {
        // Send to backend
        const response = await fetch('/transcribe', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        // Update UI
        const transcriptionElement = document.getElementById('transcription');
        transcriptionElement.classList.remove('loading');
        
        if (result.success) {
            // Show transcription
            transcriptionElement.textContent = result.text;
            transcriptionElement.classList.remove('empty', 'error');
            
            // Store for TTS
            currentTranscription = result.text;
            
            // Show accent selection
            document.getElementById('accentSection').style.display = 'block';
            
            // Scroll to accents
            setTimeout(() => {
                document.getElementById('accentSection')
                    .scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }, 300);
        } else {
            // Show error
            transcriptionElement.textContent = result.text;
            transcriptionElement.classList.add('error');
        }
        
        // Reset status
        document.getElementById('status').textContent = translations.ready;
        document.getElementById('timer').textContent = '00:00';
        
    } catch (error) {
        console.error('Error:', error);
        // ... error handling
    }
}
```

**Key Concepts:**
- `FormData`: For uploading files
- `fetch`: Modern AJAX API
- `await`: Wait for promise to resolve
- Smooth scrolling: `scrollIntoView` with behavior
- Error handling: try-catch block

---

#### Accent Playback and Comparison

**Play Accent:**
```javascript
async function playAccent(accent) {
    // Validation
    if (!currentTranscription) {
        alert('No transcription available...');
        return;
    }
    
    // Store accent
    currentAccent = accent;
    
    // Stop current audio
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
    }
    
    // UI feedback
    document.querySelectorAll('.accent-btn').forEach(btn => {
        btn.classList.remove('playing', 'loading');
    });
    const clickedBtn = document.querySelector(`.accent-btn[data-accent="${accent}"]`);
    clickedBtn.classList.add('loading');
    
    try {
        // Request TTS
        const response = await fetch('/text-to-speech', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: currentTranscription,
                accent: accent
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Show audio player
            const audioPlayer = document.getElementById('accentAudioPlayer');
            
            // Convert base64 to blob
            const audioBlob = base64ToBlob(result.audio, 'audio/mp3');
            const audioUrl = URL.createObjectURL(audioBlob);
            
            // Play audio
            audioPlayer.src = audioUrl;
            audioPlayer.play();
            currentAudio = audioPlayer;
            
            // UI updates
            clickedBtn.classList.remove('loading');
            clickedBtn.classList.add('playing');
            
            // AUTOMATICALLY TRIGGER COMPARISON
            generateComparison(accent);
            
            // Remove playing class when done
            audioPlayer.onended = () => {
                clickedBtn.classList.remove('playing');
            };
        }
    } catch (error) {
        console.error('Error:', error);
        clickedBtn.classList.remove('loading');
    }
}
```

**Helper: Base64 to Blob:**
```javascript
function base64ToBlob(base64, contentType) {
    // Decode base64
    const byteCharacters = atob(base64);
    
    // Convert to byte array
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    
    // Create blob
    return new Blob([byteArray], { type: contentType });
}
```

**Generate Comparison:**
```javascript
async function generateComparison(accent) {
    if (!userAudioBlob || !currentTranscription) return;
    
    // Show comparison section with loading state
    const comparisonSection = document.getElementById('comparisonSection');
    const comparisonImg = document.getElementById('comparisonImg');
    comparisonSection.style.display = 'block';
    comparisonImg.style.opacity = '0.3';  // Dim while loading
    
    try {
        // Prepare form data
        const formData = new FormData();
        formData.append('user_audio', userAudioBlob, 'user_recording.wav');
        formData.append('accent', accent);
        formData.append('text', currentTranscription);
        
        // Send request
        const response = await fetch('/compare-pronunciation', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Show comparison image
            comparisonImg.src = 'data:image/png;base64,' + result.comparison;
            comparisonImg.style.opacity = '1';
            
            // Add zoom on click
            comparisonImg.onclick = () => openComparisonModal();
            
            // Display advice cards
            const adviceContainer = document.getElementById('adviceContainer');
            adviceContainer.innerHTML = '';
            
            result.advice.forEach((advice, index) => {
                const card = document.createElement('div');
                card.className = `advice-card ${advice.level}`;
                card.style.animationDelay = `${index * 0.1}s`;  // Stagger animation
                card.innerHTML = `
                    <h3>${advice.title}</h3>
                    <p>${advice.text}</p>
                `;
                adviceContainer.appendChild(card);
            });
            
            // Display word practice
            if (result.words && result.words.length > 0) {
                practiceWords = result.words;
                displayWordPractice(result.words);
            }
            
            // Scroll to results
            setTimeout(() => {
                comparisonSection.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start' 
                });
            }, 500);
        }
    } catch (error) {
        console.error('Error:', error);
        comparisonImg.style.opacity = '1';
    }
}
```

---

#### Word Practice System

**Display Word Grid:**
```javascript
function displayWordPractice(words) {
    const wordsGrid = document.getElementById('wordsGrid');
    wordsGrid.innerHTML = '';
    wordPracticeCounts = {};
    
    // Create card for each word
    words.forEach(word => {
        const wordCard = document.createElement('div');
        wordCard.className = 'word-card';
        wordCard.textContent = word;
        wordCard.onclick = () => practiceWord(word, wordCard);
        wordsGrid.appendChild(wordCard);
        wordPracticeCounts[word] = 0;
    });
    
    // Show section
    document.getElementById('wordPracticeSection').style.display = 'block';
}
```

**Practice Word:**
```javascript
async function practiceWord(word, cardElement) {
    currentPracticeWord = word;
    
    // Highlight card
    document.querySelectorAll('.word-card').forEach(card => {
        card.classList.remove('active');
    });
    cardElement.classList.add('active');
    
    try {
        // 1. Generate and play target pronunciation
        const response = await fetch('/text-to-speech', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: word,
                accent: currentAccent
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Play word
            const audioBlob = base64ToBlob(result.audio, 'audio/mp3');
            const audio = new Audio(URL.createObjectURL(audioBlob));
            audio.play();
            
            // 2. After audio finishes, start recording
            audio.onended = () => {
                setTimeout(() => {
                    startWordRecording(word);
                }, 500);  // Short pause before recording
            };
        }
    } catch (error) {
        console.error('Error:', error);
    }
}
```

**Record Word Attempt:**
```javascript
async function startWordRecording(word) {
    // Show modal
    const modal = document.getElementById('recordingModal');
    document.getElementById('wordToPractice').textContent = word;
    modal.style.display = 'block';
    
    try {
        // Get microphone access
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                sampleRate: 16000
            }
        });
        
        // Record for 3 seconds
        let chunks = [];
        const recorder = new MediaRecorder(stream);
        
        recorder.ondataavailable = (e) => chunks.push(e.data);
        recorder.onstop = async () => {
            const blob = new Blob(chunks, { type: 'audio/webm' });
            stream.getTracks().forEach(track => track.stop());
            modal.style.display = 'none';
            
            // Analyze pronunciation
            await analyzeWordPronunciation(word, blob);
        };
        
        recorder.start();
        
        // Auto-stop after 3 seconds
        setTimeout(() => recorder.stop(), 3000);
        
    } catch (error) {
        console.error('Error:', error);
        modal.style.display = 'none';
        alert('Could not access microphone');
    }
}
```

**Analyze and Display Results:**
```javascript
async function analyzeWordPronunciation(word, audioBlob) {
    try {
        // Send for analysis
        const formData = new FormData();
        formData.append('user_audio', audioBlob, 'word_recording.wav');
        formData.append('accent', currentAccent);
        formData.append('word', word);
        
        const response = await fetch('/practice-word', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Update practice count
            wordPracticeCounts[word]++;
            updateWordCard(word);
            
            // Display results
            displayWordResult(
                word, 
                result.similarity, 
                result.visualization, 
                result.feedback
            );
        }
    } catch (error) {
        console.error('Error:', error);
    }
}
```

**Display Results:**
```javascript
function displayWordResult(word, similarity, visualization, feedback) {
    // Show result section
    const resultSection = document.getElementById('wordResult');
    resultSection.style.display = 'block';
    
    // Update word
    document.getElementById('practicedWord').textContent = `"${word}"`;
    
    // Update similarity badge
    const badge = document.getElementById('similarityBadge');
    badge.textContent = `${similarity}%`;
    
    // Color code badge
    badge.className = 'similarity-badge';
    if (similarity >= 85) badge.classList.add('excellent');
    else if (similarity >= 70) badge.classList.add('good');
    else if (similarity >= 50) badge.classList.add('fair');
    else badge.classList.add('needs-work');
    
    // Show visualization
    document.getElementById('wordVizImg').src = 
        'data:image/png;base64,' + visualization;
    
    // Show feedback
    document.getElementById('wordFeedback').textContent = feedback;
    
    // Scroll to result
    setTimeout(() => {
        resultSection.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'nearest' 
        });
    }, 300);
}
```

---

## 🔑 Key Programming Concepts

### 1. Asynchronous Programming

**Callbacks:**
```javascript
audio.onended = () => {
    // This runs AFTER audio finishes
    startRecording();
};
```

**Promises:**
```javascript
fetch('/api/endpoint')
    .then(response => response.json())
    .then(data => console.log(data))
    .catch(error => console.error(error));
```

**Async/Await (Modern):**
```javascript
async function myFunction() {
    try {
        const response = await fetch('/api/endpoint');
        const data = await response.json();
        console.log(data);
    } catch (error) {
        console.error(error);
    }
}
```

### 2. Event-Driven Programming

**DOM Events:**
```javascript
button.onclick = handleClick;  // Callback
button.addEventListener('click', handleClick);  // Listener
```

**MediaRecorder Events:**
```javascript
recorder.ondataavailable = (event) => { /* handle data */ };
recorder.onstop = () => { /* handle stop */ };
```

### 3. Binary Data Handling

**Blob → Base64:**
```javascript
const reader = new FileReader();
reader.onloadend = () => {
    const base64 = reader.result.split(',')[1];
};
reader.readAsDataURL(blob);
```

**Base64 → Blob:**
```javascript
const byteCharacters = atob(base64String);
const byteArray = new Uint8Array(byteCharacters.length);
const blob = new Blob([byteArray], { type: 'audio/mp3' });
```

### 4. Audio Processing

**FFT (Fast Fourier Transform):**
- Converts time-domain signal → frequency-domain
- Used for spectrograms
- Shows which frequencies are present

**Spectrogram:**
- 2D representation of audio
- X-axis: Time
- Y-axis: Frequency
- Color: Intensity
- Created using sliding window FFT

**RMS Energy:**
```python
energy = np.sqrt(np.mean(samples**2))
```

---

## 🎯 Best Practices

### Security
- ✅ Validate all user inputs
- ✅ Limit file upload sizes
- ✅ Clean up temporary files
- ✅ Use HTTPS in production
- ✅ Sanitize error messages

### Performance
- ✅ Close matplotlib figures (plt.close())
- ✅ Use temporary files for large audio
- ✅ Clean up event loops
- ✅ Minimize DOM manipulations
- ✅ Use CSS animations over JavaScript

### Error Handling
- ✅ Try-catch blocks around API calls
- ✅ Graceful degradation
- ✅ User-friendly error messages
- ✅ Console logging for debugging
- ✅ Cleanup in finally blocks

### Code Organization
- ✅ Clear function names
- ✅ Single responsibility principle
- ✅ Modular design
- ✅ Comments for complex logic
- ✅ Consistent naming conventions

---

## 📚 Further Learning

### Concepts to Explore
- **Digital Signal Processing**: Understanding audio at a deeper level
- **Machine Learning**: Advanced pronunciation analysis
- **WebRTC**: Peer-to-peer audio streaming
- **Web Audio API**: Advanced audio manipulation in browser
- **Docker**: Containerizing the application

### Recommended Resources
- **MDN Web Docs**: JavaScript and Web APIs
- **Flask Documentation**: Python web development
- **scipy Documentation**: Signal processing
- **Web Audio API**: Advanced audio
- **FFmpeg Documentation**: Audio/video processing

---

**End of Code Guide**

This document provides a comprehensive understanding of how the application works. For specific implementation details, refer to the inline comments in the actual code files.