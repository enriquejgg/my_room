# 🎤 Voice Transcription & Pronunciation Analysis Platform

A comprehensive web application for voice recording, speech-to-text transcription, multi-accent audio playback, and detailed pronunciation analysis with educational feedback. Perfect for language learners, accent coaches, actors, and anyone looking to improve their English pronunciation.

![Version](https://img.shields.io/badge/version-2.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![Flask](https://img.shields.io/badge/flask-2.0+-lightgrey.svg)

---

## 📋 Table of Contents

- [Features Overview](#-features-overview)
- [Quick Start](#-quick-start)
- [Detailed Features](#-detailed-features)
- [Technical Architecture](#-technical-architecture)
- [Installation Guide](#-installation-guide)
- [Usage Instructions](#-usage-instructions)
- [API Documentation](#-api-documentation)
- [Code Structure](#-code-structure)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Features Overview

### 🎙️ Core Features
1. **Voice Recording**: 10-second max with live timer and visual feedback
2. **Speech-to-Text**: Automatic transcription using Google's API
3. **Multi-Accent Playback**: Listen in 9 English accents with neural voices
4. **Pronunciation Analysis**: Comprehensive comparison with visual feedback
5. **Word-by-Word Practice**: Targeted practice with instant feedback
6. **Multi-Language UI**: Interface in 9 languages

### 🌟 Key Highlights
- ✅ No installation required on user device
- ✅ Browser-based with no plugins needed
- ✅ Real-time processing and feedback
- ✅ Professional visualization and analysis
- ✅ Educational feedback with actionable tips
- ✅ Unlimited practice attempts

---

## ⚡ Quick Start

```bash
# 1. Install FFmpeg
sudo apt-get install ffmpeg  # Ubuntu/Debian
brew install ffmpeg          # macOS

# 2. Clone and setup
git clone <repository-url>
cd voice-transcription-app

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run application
python app.py

# 5. Open browser
# Navigate to http://localhost:5000
```

---

## 🔍 Detailed Features

### 1️⃣ Voice Recording System

**Capabilities:**
- Real-time audio capture using HTML5 MediaRecorder API
- Visual recording indicator with pulsing animation
- Live countdown timer showing elapsed time
- Warning indicator when approaching 10-second limit
- Automatic stop at 10 seconds to prevent cutoff
- High-quality audio capture (16kHz sampling rate, mono channel)

**Technical Implementation:**
```javascript
// Browser captures audio
MediaRecorder API → WebM/OGG format → Flask backend

// Backend converts
WebM/OGG → WAV (16kHz, mono) → Speech Recognition
```

**User Experience:**
```
Click "Start" → Visual feedback + Timer → Speak (max 10s) → Auto-stop/Manual stop
```

---

### 2️⃣ Speech-to-Text Transcription

**Features:**
- Automatic conversion of speech to text
- Support for English language recognition
- Ambient noise adjustment for better accuracy
- Dynamic energy threshold adaptation
- Real-time processing (typically 2-3 seconds)

**Processing Pipeline:**
```
Audio Recording
    ↓
Format Conversion (WebM/OGG → WAV)
    ↓
Noise Reduction & Normalization
    ↓
Google Speech Recognition API
    ↓
Transcribed Text Display
```

**Accuracy Optimization:**
- Pre-processing: Ambient noise adjustment (0.5s sample)
- Format: 16kHz mono WAV for best recognition
- Threshold: Dynamic energy threshold adapts to environment
- Language: English (US) with high accuracy model

---

### 3️⃣ Multi-Accent Audio Playback

**Supported Accents:**

| Flag | Accent | Voice Model | Region |
|------|--------|-------------|--------|
| 🇺🇸 | American | en-US-GuyNeural | Standard American English |
| 🇬🇧 | British | en-GB-RyanNeural | Received Pronunciation |
| 🏴󐁧󐁢󐁳󐁣󐁴󐁿 | Scottish | en-GB-ThomasNeural | Scottish English |
| 🇮🇪 | Irish | en-IE-ConnorNeural | Irish English |
| 🇦🇺 | Australian | en-AU-WilliamNeural | Australian English |
| 🇳🇿 | New Zealand | en-NZ-MitchellNeural | New Zealand English |
| 🇿🇦 | South African | en-ZA-LukeNeural | South African English |
| 🇮🇳 | Indian | en-IN-PrabhatNeural | Indian English |
| 🇳🇬 | Nigerian | en-NG-AbeoNeural | Nigerian English |

**Technology:**
- Microsoft Edge Text-to-Speech (neural voices)
- High-quality, natural-sounding pronunciation
- Authentic regional characteristics
- MP3 format for broad compatibility

**Accent Characteristics:**
- **American**: Rhotic R's, relatively flat intonation
- **British**: Non-rhotic, crisp vowels, wider pitch range
- **Scottish**: Rolled R's, guttural sounds, rising intonation
- **Irish**: Melodic lilt, soft consonants, rhythmic patterns
- **Australian**: Rising intonation, nasal tone, vowel shifts
- **New Zealand**: Vowel centralization, "i" → "u" shift
- **South African**: Clipped vowels, crisp consonants
- **Indian**: Syllable-timed delivery, retroflex consonants
- **Nigerian**: Melodic, equal syllable weight

---

### 4️⃣ Pronunciation Comparison & Analysis

**Automatic Generation:**
When you click an accent button:
1. Audio plays in selected accent
2. Comparison analysis generates in background
3. Results display automatically

**Visual Comparison Components:**

#### **1. Title Section**
- Overall similarity score (0-100%)
- Color-coded badge:
  - 🌟 80%+ = Excellent (Green)
  - 👍 60-79% = Good (Blue)
  - 💪 <60% = Needs Work (Yellow)

#### **2. Waveform Overlay**
- Red line = Your pronunciation
- Blue line = Target accent
- Shows amplitude variations over time
- Identifies timing and rhythm differences

#### **3. Side-by-Side Spectrograms**
- Left: Your frequency patterns
- Right: Target accent patterns
- Color intensity = Energy at each frequency
- Range: 0-4000 Hz (speech range)
- Reveals vowel and consonant characteristics

#### **4. Pitch Contour Comparison**
- Overlaid pitch lines over time
- Horizontal reference lines show averages
- Identifies melody and intonation patterns
- Measured in Hz (Hertz)

#### **5. Energy Envelope Comparison**
- Shows speech intensity over time
- Reveals emphasis and stress patterns
- Identifies volume variations
- Helps with word stress and rhythm

#### **6. Detailed Metrics Panel**
```
╔═══════════════════════════════════════╗
║     DETAILED ANALYSIS REPORT          ║
╠═══════════════════════════════════════╣
║ Similarity Score: 78.5%               ║
║                                       ║
║ PITCH ANALYSIS:                       ║
║ • Your Average: 195.3 Hz              ║
║ • Target Average: 240.8 Hz            ║
║ • Difference: 45.5 Hz ↑               ║
║                                       ║
║ ENERGY ANALYSIS:                      ║
║ • Your Energy: 0.007112               ║
║ • Target Energy: 0.023262             ║
║ • Intensity Level: Lower              ║
║                                       ║
║ KEY FINDINGS:                         ║
║ • Pitch: 45 Hz HIGHER than target     ║
║ • Energy: LESS emphatic delivery      ║
╚═══════════════════════════════════════╝
```

**Personalized Feedback Cards:**

1. **Overall Assessment**
   - Quality rating (Excellent/Good/Needs Work)
   - Similarity percentage
   - Encouragement and motivation

2. **Pitch Correction**
   - Specific Hz difference
   - Direction (raise/lower)
   - Practical advice (e.g., "speak in a more relaxed tone")

3. **Energy & Emphasis**
   - Volume and stress patterns
   - Over/under emphasis identification
   - Tips for dynamic delivery

4. **Accent-Specific Tips**
   - Customized for each accent
   - Focus on characteristic features
   - Examples:
     - American: "Focus on rhotic R sounds"
     - British: "Use non-rhotic pronunciation, crisp vowels"
     - Australian: "Raise pitch at end of statements"

5. **Practice Recommendations**
   - Listen to native speakers
   - Shadow pronunciation
   - Record regularly
   - Focus on one aspect at a time

---

### 5️⃣ Word-by-Word Practice System

**Workflow:**
```
Click word → Hear in accent → Record (3s) → Instant feedback
```

**Practice Interface:**

#### **Word Grid Display**
```
┌─────────┐ ┌─────────┐ ┌─────────┐
│ Hello   │ │ how     │ │ are     │
│      ①  │ │      ②  │ │         │
└─────────┘ └─────────┘ └─────────┘
```
- Green highlight = Practiced
- Number badge = Practice count
- Unlimited attempts
- Practice in any order

#### **Recording Modal**
```
╔═══════════════════════╗
║     Now say:          ║
║                       ║
║      "Hello"          ║
║                       ║
║    Recording...       ║
║    (3 seconds)        ║
╚═══════════════════════╝
```

#### **Results Display**
```
┌────────────────────────────────┐
│ "Hello"              85% ✓     │
├────────────────────────────────┤
│ [Waveform Comparison]          │
│ [Spectrogram Comparison]       │
├────────────────────────────────┤
│ ✅ Excellent! Your             │
│ pronunciation is very close.   │
│ 🎵 Minor pitch adjustment:     │
│ Lower by ~12 Hz.               │
│ 💡 Focus on the initial 'H'    │
│ sound - make it softer.        │
├────────────────────────────────┤
│ [🔄 Try Again]                 │
└────────────────────────────────┘
```

**Analysis Metrics:**
- Similarity: 0-100% match
- Pitch comparison: Hz difference
- Energy analysis: Intensity match
- Specific phonetic tips
- Visual waveform + spectrogram

**Benefits:**
- 🎯 Focus on difficult words
- 📈 Track improvement
- 🔄 Immediate retry
- ⚡ Fast feedback
- 🎓 Learn specifics

---

### 6️⃣ Multi-Language Interface

**Supported Languages:**
- 🇬🇧 English
- 🇫🇷 French (Français)
- 🇩🇪 German (Deutsch)
- 🇮🇹 Italian (Italiano)
- 🇪🇸 Spanish (Español)
- 🇨🇳 Chinese (中文)
- 🇰🇷 Korean (한국어)
- 🇯🇵 Japanese (日本語)
- 🇷🇺 Russian (Русский)

**Features:**
- Complete UI translation
- Language selector in top-right
- Instant switching (no reload)
- Preference saved in browser
- Professional native translations

**Translated Elements:**
- All button labels
- Section titles
- Instructions
- Status messages
- Error messages
- Feedback text
- Visualization labels

---

## 🏗️ Technical Architecture

### System Overview

```
┌─────────────────────────────────────────────┐
│              FRONTEND (Browser)             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │   HTML   │  │   CSS    │  │JavaScript│ │
│  │  +Jinja  │  │  Anims   │  │  Logic   │ │
│  └──────────┘  └──────────┘  └──────────┘ │
└─────────────────────┬───────────────────────┘
                      │ HTTP/JSON
                      ↓
┌─────────────────────────────────────────────┐
│              BACKEND (Flask)                │
│  ┌──────────────────────────────────────┐  │
│  │         Route Handlers               │  │
│  │  /transcribe  /text-to-speech       │  │
│  │  /compare-pronunciation             │  │
│  │  /practice-word  /translations      │  │
│  └──────────────────────────────────────┘  │
└─────────────────────┬───────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │  Google  │  │   Edge   │  │  Audio   │
  │  Speech  │  │   TTS    │  │Processing│
  │   API    │  │  (MS)    │  │  (pydub) │
  └──────────┘  └──────────┘  └──────────┘
```

### Technology Stack

#### **Backend Technologies**
```
Flask 2.0+          → Web framework & routing
SpeechRecognition   → Google Speech-to-Text wrapper
edge-tts 6.1+       → Microsoft Edge TTS API
pydub 0.25+         → Audio format conversion
numpy 1.24+         → Numerical array operations
scipy 1.10+         → Signal processing & FFT
matplotlib 3.7+     → Visualization generation
Python 3.8+         → Core language
```

#### **Frontend Technologies**
```
HTML5               → Structure & semantic markup
CSS3                → Styling, animations, gradients
Vanilla JavaScript  → Logic (no frameworks)
MediaRecorder API   → Browser audio capture
Canvas API          → Visual effects
Fetch API           → AJAX requests
LocalStorage        → Language preference
```

#### **External Services**
```
Google Speech API   → Speech recognition (free tier)
Microsoft Edge TTS  → Neural voice synthesis (free)
FFmpeg              → Audio codec support
```

### Audio Processing Pipeline

```
┌────────────────────────────────────────────┐
│ 1. RECORDING                               │
│    MediaRecorder → WebM/OGG format         │
└────────────┬───────────────────────────────┘
             ↓
┌────────────────────────────────────────────┐
│ 2. FORMAT CONVERSION                       │
│    pydub: WebM/OGG → WAV (16kHz, mono)     │
└────────────┬───────────────────────────────┘
             ↓
┌────────────────────────────────────────────┐
│ 3. TRANSCRIPTION                           │
│    Google API → Text output                │
└────────────┬───────────────────────────────┘
             ↓
┌────────────────────────────────────────────┐
│ 4. TTS GENERATION                          │
│    Edge TTS → Accent audio (MP3)           │
└────────────┬───────────────────────────────┘
             ↓
┌────────────────────────────────────────────┐
│ 5. SIGNAL PROCESSING                       │
│    • FFT → Spectrograms                    │
│    • scipy.signal → Frequency analysis     │
│    • numpy → Statistical calculations      │
└────────────┬───────────────────────────────┘
             ↓
┌────────────────────────────────────────────┐
│ 6. VISUALIZATION                           │
│    matplotlib → PNG images → Base64        │
└────────────┬───────────────────────────────┘
             ↓
┌────────────────────────────────────────────┐
│ 7. DISPLAY                                 │
│    Browser renders Base64 images           │
└────────────────────────────────────────────┘
```

### Data Flow for Pronunciation Comparison

```
User Recording (WebM)
    ↓
Convert to WAV
    ↓
Generate Target Audio (TTS)
    ↓
Extract Audio Samples (numpy arrays)
    ↓
┌────────────────────────────────────┐
│ PARALLEL PROCESSING                │
├────────────────┬───────────────────┤
│ User Audio     │ Target Audio      │
│ • Normalize    │ • Normalize       │
│ • Spectrogram  │ • Spectrogram     │
│ • Pitch track  │ • Pitch track     │
│ • Energy calc  │ • Energy calc     │
└────────────────┴───────────────────┘
    ↓
Calculate Similarity Metrics
    ↓
Generate Comparison Plots
    ↓
Create Feedback Text
    ↓
Encode as Base64
    ↓
Return JSON to Frontend
    ↓
Display to User
```

---

## 🚀 Installation Guide

### Prerequisites

Before installation, ensure you have:
- ✅ Python 3.8 or higher
- ✅ pip (Python package manager)
- ✅ FFmpeg (audio processing)
- ✅ Modern web browser
- ✅ Microphone access
- ✅ Internet connection

### Step-by-Step Installation

#### **Step 1: Install FFmpeg**

FFmpeg is required for audio format conversion.

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg

# Verify installation
ffmpeg -version
```

**macOS:**
```bash
brew install ffmpeg

# Verify installation
ffmpeg -version
```

**Windows:**
1. Download from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to system PATH
4. Restart terminal
5. Verify: `ffmpeg -version`

#### **Step 2: Clone Repository**

```bash
git clone <repository-url>
cd voice-transcription-app
```

#### **Step 3: Create Virtual Environment**

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

#### **Step 4: Install Python Dependencies**

```bash
pip install -r requirements.txt
```

**requirements.txt contents:**
```
Flask==2.3.0
SpeechRecognition==3.10.0
pydub==0.25.1
edge-tts==6.1.9
numpy==1.24.0
matplotlib==3.7.0
scipy==1.10.0
Werkzeug==2.3.0
```

#### **Step 5: Verify Installation**

```bash
python app.py
```

Expected output:
```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server.
 * Running on http://0.0.0.0:5000
```

#### **Step 6: Access Application**

Open your web browser and navigate to:
```
http://localhost:5000
```

You should see the Voice Transcriber interface.

### Troubleshooting Installation

**Issue: "FFmpeg not found"**
```bash
# Check if FFmpeg is installed
which ffmpeg  # Linux/macOS
where ffmpeg  # Windows

# If not found, reinstall and add to PATH
```

**Issue: "pip install fails"**
```bash
# Upgrade pip
pip install --upgrade pip

# Install packages individually
pip install Flask
pip install SpeechRecognition
# etc.
```

**Issue: "Port 5000 already in use"**
```bash
# Change port in app.py
app.run(debug=True, host='0.0.0.0', port=8080)
```

---

## 📖 Usage Instructions

### Complete User Journey

#### **1. Initial Setup**

**Allow Microphone Access:**
- Browser will request permission on first visit
- Click "Allow" when prompted
- Required for recording feature

**Select Language (Optional):**
- Click language selector in top-right corner
- Choose your preferred language
- Interface updates immediately
- Preference saved for future visits

#### **2. Record Your Voice**

**Start Recording:**
```
Click "Start Recording" → Visual feedback appears
```

**While Recording:**
- Speak clearly in English
- Watch live timer (maximum 10 seconds)
- Yellow warning appears at 8+ seconds
- Recording stops automatically at 10 seconds

**Manual Stop:**
```
Click "Stop Recording" anytime before 10 seconds
```

**Tips for Good Recording:**
- Speak at normal conversational pace
- Pronounce words clearly
- Use complete sentences
- Minimize background noise
- Keep microphone 15-30cm from mouth

#### **3. Review Transcription**

**Automatic Display:**
- Transcribed text appears automatically
- Processing typically takes 2-3 seconds
- Text displayed in white box

**If Transcription is Unclear:**
- Record again with clearer pronunciation
- Reduce background noise
- Speak more slowly
- Check microphone position

#### **4. Choose an Accent**

**Select Accent Button:**
```
Click any accent (e.g., "American 🇺🇸")
```

**What Happens:**
1. Audio plays automatically in selected accent
2. Comparison analysis generates in background
3. Results appear when ready (5-10 seconds)

**Accent Selection Tips:**
- Start with familiar accent (e.g., American)
- Try different accents to compare
- Listen to regional characteristics
- Note differences in pronunciation

#### **5. Review Pronunciation Analysis**

**Scroll Down to See:**

**Similarity Score:**
- Displayed at top with color badge
- 80%+ = Excellent ✨
- 60-79% = Good 👍
- <60% = Needs Work 💪

**Visual Comparisons:**
- Waveform overlay (timing/rhythm)
- Spectrograms (frequency patterns)
- Pitch contours (melody/intonation)
- Energy envelopes (emphasis/stress)

**Detailed Metrics:**
- Pitch difference in Hz
- Energy level comparison
- Key findings and insights

**Click to Zoom:**
- Click any visualization
- Opens full-screen modal
- Press ESC to close

#### **6. Read Feedback Cards**

**Card Types:**

1. **Overall Assessment**
   - Quality rating
   - Encouragement

2. **Pitch Correction**
   - Specific adjustment needed
   - Direction (raise/lower)

3. **Energy Adjustment**
   - Volume/emphasis tips

4. **Accent-Specific Tips**
   - Regional characteristics
   - Sound focus areas

5. **Practice Recommendations**
   - General improvement strategies

#### **7. Practice Individual Words**

**Locate Word Practice Section:**
- Scroll below feedback cards
- See "Practice Word by Word" title
- Grid of clickable word cards

**Practice a Word:**
```
Step 1: Click word (e.g., "Hello")
Step 2: Listen to pronunciation in selected accent
Step 3: Recording modal appears after audio
Step 4: Say the word (3 seconds auto-record)
Step 5: Review results immediately
```

**Results Display:**
- Similarity percentage with color badge
- Compact waveform comparison
- Compact spectrogram comparison
- Specific pronunciation feedback
- "Try Again" button for retry

**Practice Strategy:**
1. Start with lowest-scoring words
2. Listen carefully to target pronunciation
3. Focus on one aspect (pitch OR energy)
4. Practice multiple times
5. Track improvement with badges

**Practice Tracking:**
- Green circle with number = practice count
- Practiced words highlighted in green
- Practice any word unlimited times
- Practice in any order

#### **8. Try Different Accents**

**Experiment:**
- Go back to accent selection
- Click different accent button
- New comparison generates automatically
- Compare your pronunciation across accents

**Learning Approach:**
- Master one accent first
- Note differences between accents
- Practice accent-specific features
- Use feedback to guide practice

---

## 🔌 API Documentation

### Endpoint: `GET /`

**Description:** Serve main application interface

**Response:**
- HTML template with full application

---

### Endpoint: `GET /translations/<lang>`

**Description:** Get UI translations for specified language

**Parameters:**
- `lang` (path): Two-letter language code

**Example Request:**
```http
GET /translations/fr HTTP/1.1
Host: localhost:5000
```

**Example Response:**
```json
{
  "title": "Transcripteur Vocal",
  "subtitle": "Enregistrez votre voix...",
  ...
}
```

---

### Endpoint: `POST /transcribe`

**Description:** Convert audio to text using speech recognition

**Request Format:**
```http
POST /transcribe HTTP/1.1
Content-Type: multipart/form-data

audio: [binary audio file]
```

**Request Parameters:**
- `audio` (file): Audio file in WebM, OGG, or WAV format

**Success Response:**
```json
{
  "success": true,
  "text": "Hello how are you today"
}
```

**Error Response:**
```json
{
  "success": false,
  "text": "Could not understand audio..."
}
```

---

### Endpoint: `POST /text-to-speech`

**Description:** Generate speech in specified accent

**Request Format:**
```http
POST /text-to-speech HTTP/1.1
Content-Type: application/json

{
  "text": "Hello world",
  "accent": "british"
}
```

**Request Parameters:**
- `text` (string): Text to convert to speech
- `accent` (string): Accent identifier (american, british, etc.)

**Success Response:**
```json
{
  "success": true,
  "audio": "base64_encoded_mp3_data",
  "accent": "british"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error message"
}
```

---

### Endpoint: `POST /compare-pronunciation`

**Description:** Compare user pronunciation with target accent

**Request Format:**
```http
POST /compare-pronunciation HTTP/1.1
Content-Type: multipart/form-data

user_audio: [binary audio file]
accent: "american"
text: "Hello world"
```

**Request Parameters:**
- `user_audio` (file): User's recorded audio
- `accent` (string): Target accent for comparison
- `text` (string): Transcribed text

**Success Response:**
```json
{
  "success": true,
  "comparison": "base64_encoded_png_image",
  "advice": [
    {
      "level": "good",
      "title": "👍 Good Pronunciation",
      "text": "You're doing well! With a few adjustments..."
    },
    {
      "level": "tip",
      "title": "🎵 Lower Your Pitch",
      "text": "Your voice is 45 Hz higher than the target..."
    }
  ],
  "words": ["Hello", "world"]
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error message"
}
```

---

### Endpoint: `POST /practice-word`

**Description:** Analyze single word pronunciation

**Request Format:**
```http
POST /practice-word HTTP/1.1
Content-Type: multipart/form-data

user_audio: [binary audio file]
accent: "american"
word: "hello"
```

**Request Parameters:**
- `user_audio` (file): User's word recording
- `accent` (string): Target accent
- `word` (string): Word being practiced

**Success Response:**
```json
{
  "success": true,
  "visualization": "base64_encoded_png_image",
  "similarity": 85.3,
  "feedback": "✅ Excellent! Your pronunciation is very close. 🎵 Lower pitch by ~12 Hz..."
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error message"
}
```

---

## 📂 Code Structure

### File Organization

```
voice-transcription-app/
│
├── app.py                          # Main Flask application (1400+ lines)
│   │
│   ├── Imports & Configuration     # Lines 1-20
│   │   ├── Flask setup
│   │   ├── Library imports
│   │   └── App configuration
│   │
│   ├── Translations Dictionary     # Lines 21-450
│   │   ├── English (en)
│   │   ├── French (fr)
│   │   ├── German (de)
│   │   ├── Italian (it)
│   │   ├── Spanish (es)
│   │   ├── Chinese (zh)
│   │   ├── Korean (ko)
│   │   ├── Japanese (ja)
│   │   └── Russian (ru)
│   │
│   ├── Accent Voice Mappings      # Lines 451-470
│   │   └── Edge TTS voice IDs
│   │
│   ├── Utility Functions          # Lines 471-500
│   │   └── generate_speech_sync()
│   │
│   ├── Route Handlers             # Lines 501-800
│   │   ├── GET /
│   │   ├── GET /translations/<lang>
│   │   ├── POST /transcribe
│   │   ├── POST /text-to-speech
│   │   ├── POST /compare-pronunciation
│   │   └── POST /practice-word
│   │
│   ├── Comparison Functions       # Lines 801-1100
│   │   ├── generate_pronunciation_comparison()
│   │   ├── generate_pronunciation_advice()
│   │   ├── generate_word_comparison()
│   │   └── generate_word_feedback()
│   │
│   └── Main Execution             # Lines 1380+
│       └── app.run()
│
├── templates/
│   └── index.html                  # Single-page application (1500+ lines)
│       │
│       ├── HTML Structure          # Lines 1-100
│       │   ├── Head & meta tags
│       │   ├── Language selector
│       │   ├── Recording section
│       │   ├── Transcription display
│       │   ├── Accent selection
│       │   ├── Comparison section
│       │   └── Word practice section
│       │
│       ├── CSS Styling             # Lines 100-800
│       │   ├── Global styles
│       │   ├── Component styles
│       │   ├── Animations
│       │   ├── Responsive design
│       │   └── Color schemes
│       │
│       └── JavaScript Logic        # Lines 800-1500
│           ├── Translation system
│           ├── Recording functions
│           ├── Transcription handler
│           ├── Accent playback
│           ├── Comparison generation
│           ├── Word practice system
│           └── Helper functions
│
├── requirements.txt                # Python dependencies
├── README.md                       # This documentation
└── .gitignore                      # Git ignore rules
```

### Key Functions Explained

#### **Backend (app.py)**

**Audio Processing:**
```python
# Convert WebM/OGG to WAV
audio = AudioSegment.from_file(io.BytesIO(audio_data), format="webm")
audio = audio.set_frame_rate(16000).set_channels(1)
```

**Speech Recognition:**
```python
recognizer = sr.Recognizer()
recognizer.adjust_for_ambient_noise(source, duration=0.5)
text = recognizer.recognize_google(audio_data, language='en-US')
```

**Text-to-Speech:**
```python
communicate = edge_tts.Communicate(text, voice)
loop.run_until_complete(communicate.save(output_path))
```

**Visualization Generation:**
```python
# Create matplotlib figure
fig = plt.figure(figsize=(18, 14))

# Generate spectrograms
frequencies, times, spectrogram = signal.spectrogram(samples, sample_rate)

# Plot comparison
plt.pcolormesh(times, frequencies, spectrogram_db, cmap='Blues')

# Save as base64
buffer = io.BytesIO()
plt.savefig(buffer, format='png', dpi=130)
image_base64 = base64.b64encode(buffer.read()).decode()
```

#### **Frontend (index.html)**

**Recording:**
```javascript
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
mediaRecorder = new MediaRecorder(stream);

mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
mediaRecorder.onstop = () => {
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
    sendAudioForTranscription(audioBlob);
};
```

**Accent Playback:**
```javascript
async function playAccent(accent) {
    const response = await fetch('/text-to-speech', {
        method: 'POST',
        body: JSON.stringify({ text, accent })
    });

    const result = await response.json();
    const audioBlob = base64ToBlob(result.audio, 'audio/mp3');
    audioPlayer.src = URL.createObjectURL(audioBlob);
    audioPlayer.play();

    // Automatically trigger comparison
    generateComparison(accent);
}
```

**Word Practice:**
```javascript
async function practiceWord(word) {
    // Play target pronunciation
    await playWordAudio(word, currentAccent);

    // Record user attempt
    const userBlob = await recordWordAttempt();

    // Analyze pronunciation
    const result = await analyzeWordPronunciation(word, userBlob);

    // Display results
    displayWordResult(word, result.similarity, result.visualization);
}
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Optional: Flask environment
export FLASK_ENV=development  # or production
export FLASK_DEBUG=1          # Enable debug mode

# Optional: Change port
export FLASK_PORT=5000

# Optional: Host binding
export FLASK_HOST=0.0.0.0     # Listen on all interfaces
```

### Application Settings

**In app.py:**
```python
# File upload settings
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Temporary file directory
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Audio settings
SAMPLE_RATE = 16000  # 16kHz
CHANNELS = 1         # Mono

# Recognition settings
recognizer.energy_threshold = 4000
recognizer.dynamic_energy_threshold = True
```

**In index.html:**
```javascript
// Recording constraints
const MAX_DURATION = 10000;  // 10 seconds

// Warning threshold
const WARNING_TIME = 8000;   // 8 seconds

// Word recording duration
const WORD_RECORD_TIME = 3000;  // 3 seconds
```

### Performance Tuning

**For Faster Processing:**
```python
# Reduce spectrogram resolution
nperseg=256  # Instead of 512

# Lower image DPI
dpi=100  # Instead of 130

# Skip detailed analysis for quick feedback
```

**For Better Quality:**
```python
# Increase spectrogram resolution
nperseg=1024

# Higher image DPI
dpi=150

# More detailed frequency analysis
```

---

## 🐛 Troubleshooting

### Common Issues and Solutions

#### **Issue: Microphone Not Working**

**Symptoms:**
- "Start Recording" button doesn't work
- No audio captured

**Solutions:**
1. Check browser permissions
   - Click padlock/info icon in address bar
   - Ensure microphone is allowed
   - Reload page after granting permission

2. Check system settings
   - Verify microphone is connected
   - Test in system sound settings
   - Ensure no other app is using microphone

3. Try different browser
   - Chrome recommended
   - Firefox also supported
   - Safari may have restrictions

---

#### **Issue: "Could Not Understand Audio"**

**Symptoms:**
- Transcription fails
- Error message displayed

**Solutions:**
1. Improve recording quality
   - Speak more clearly
   - Reduce background noise
   - Speak at normal pace (not too fast/slow)

2. Check recording environment
   - Move to quieter location
   - Close windows
   - Turn off fans/AC

3. Verify internet connection
   - Speech recognition requires internet
   - Test with: `ping google.com`

4. Check audio levels
   - Speak at comfortable volume
   - Don't whisper or shout
   - Maintain consistent distance

---

#### **Issue: No Accent Audio Plays**

**Symptoms:**
- Silence after clicking accent button
- Loading indicator never stops

**Solutions:**
1. Check internet connection
   - Edge TTS requires internet
   - Test with: `ping microsoft.com`

2. Verify browser audio
   - Check if browser is muted
   - Check system volume
   - Test with YouTube video

3. Clear browser cache
   - Ctrl+Shift+Delete (Chrome)
   - Clear cached files
   - Reload application

4. Check console for errors
   - Press F12
   - Look in Console tab
   - Report any red errors

---

#### **Issue: Comparison Not Generating**

**Symptoms:**
- No visualization appears
- Section stays hidden

**Solutions:**
1. Ensure recording completed
   - Verify transcription appeared
   - Check that audio was captured

2. Wait for processing
   - Comparison takes 5-10 seconds
   - Be patient for first comparison

3. Check browser console
   - Press F12
   - Look for JavaScript errors
   - Check Network tab for failed requests

4. Verify file sizes
   - Recording should be < 16MB
   - Check uploads are completing

---

#### **Issue: FFmpeg Errors**

**Symptoms:**
- "FFmpeg not found"
- Audio conversion fails

**Solutions:**
1. Verify FFmpeg installation
   ```bash
   ffmpeg -version  # Should show version info
   ```

2. Check system PATH
   ```bash
   which ffmpeg    # Linux/macOS
   where ffmpeg    # Windows
   ```

3. Reinstall FFmpeg
   ```bash
   # Ubuntu/Debian
   sudo apt-get remove ffmpeg
   sudo apt-get install ffmpeg

   # macOS
   brew reinstall ffmpeg
   ```

4. Restart application
   ```bash
   # Stop Flask (Ctrl+C)
   python app.py  # Restart
   ```

---

#### **Issue: Python Package Errors**

**Symptoms:**
- Import errors
- Module not found

**Solutions:**
1. Verify virtual environment
   ```bash
   which python  # Should show venv path
   ```

2. Reinstall dependencies
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt --force-reinstall
   ```

3. Install individually
   ```bash
   pip install Flask
   pip install SpeechRecognition
   pip install pydub
   pip install edge-tts
   pip install numpy
   pip install matplotlib
   pip install scipy
   ```

4. Check Python version
   ```bash
   python --version  # Should be 3.8+
   ```

---

#### **Issue: Port Already in Use**

**Symptoms:**
- "Address already in use"
- Application won't start

**Solutions:**
1. Change port in code
   ```python
   # In app.py
   app.run(debug=True, port=8080)
   ```

2. Kill existing process
   ```bash
   # Find process
   lsof -i :5000  # Linux/macOS
   netstat -ano | findstr :5000  # Windows

   # Kill process
   kill -9 <PID>  # Linux/macOS
   taskkill /PID <PID> /F  # Windows
   ```

---

#### **Issue: Slow Performance**

**Symptoms:**
- Long processing times
- Delays in responses

**Solutions:**
1. Reduce visualization quality
   ```python
   # In app.py
   dpi=80  # Lower DPI
   figsize=(12, 8)  # Smaller figure
   ```

2. Check system resources
   - Close unnecessary applications
   - Monitor CPU/RAM usage
   - Ensure adequate free disk space

3. Optimize audio processing
   ```python
   # Use lower sample rates
   audio.set_frame_rate(8000)  # Instead of 16000
   ```

4. Use production server
   ```bash
   # Install gunicorn
   pip install gunicorn

   # Run with gunicorn
   gunicorn -w 4 app:app
   ```

---

### Debug Mode

Enable detailed logging:
```python
# In app.py
import logging
logging.basicConfig(level=logging.DEBUG)

# Add to functions
print(f"Debug: Processing audio of length {len(samples)}")
```

Check browser console:
```javascript
// Press F12 in browser
// Console tab shows JavaScript errors
// Network tab shows API requests/responses
```

---

## 📧 Support & Contact

### Getting Help

**Documentation:**
- README: You're reading it!
- Code comments: Inline documentation
- Wiki: [GitHub Wiki](https://github.com/yourusername/voice-transcription-app/wiki)

**Issues:**
- GitHub Issues: [Report bugs or request features](https://github.com/yourusername/voice-transcription-app/issues)
- Include: OS, Python version, error messages, steps to reproduce

**Community:**
- Discussions: [GitHub Discussions](https://github.com/yourusername/voice-transcription-app/discussions)
- Stack Overflow: Tag `voice-transcription-app`

---

## 📜 License

MIT License - Free to use for personal and commercial projects.

---

## 🙏 Acknowledgments

### Technologies Used
- **Google Speech Recognition**: High-quality speech-to-text
- **Microsoft Edge TTS**: Natural neural voices
- **FFmpeg**: Essential audio processing
- **Flask**: Elegant web framework
- **matplotlib**: Professional visualizations
- **scipy**: Advanced signal processing

### Inspiration
Built for language learners, educators, and anyone passionate about pronunciation improvement.

---

**Version 2.0** | Last Updated: December 2024 | Made with ❤️ for language learners worldwide