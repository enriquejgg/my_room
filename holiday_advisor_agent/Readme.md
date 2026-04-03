# Iter – AI Travel Planning Assistant

> A conversational travel-planning web app powered by Flask and Anthropic's Claude API.  
> Upload a photo of any landmark; Iter identifies your destination and builds a personalised itinerary through natural conversation.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Project Structure](#project-structure)
5. [Prerequisites](#prerequisites)
6. [Installation & Setup](#installation--setup)
7. [Configuration](#configuration)
8. [Running the App](#running-the-app)
9. [API Reference](#api-reference)
10. [How the Conversation Works](#how-the-conversation-works)
11. [Frontend Walkthrough](#frontend-walkthrough)
12. [Key Design Decisions](#key-design-decisions)
13. [Error Handling & Graceful Degradation](#error-handling--graceful-degradation)
14. [Extending the Project](#extending-the-project)
15. [Known Limitations](#known-limitations)

---

## Overview

Iter is a single-page web application that acts as an AI-powered travel agent. Users:

1. Enter their name.
2. Upload a photo of a destination (landmark, city skyline, famous site).
3. Chat with **Iter**, an AI assistant that identifies the destination, collects travel preferences, and produces a full day-by-day itinerary — including departure logistics, accommodation suggestions, activity schedule, and recommended tour operators.

---

## Features

| Feature | Description |
|---|---|
| **Vision-based location detection** | Claude's multimodal API analyses the uploaded photo and extracts the destination name. |
| **Stateful multi-turn conversation** | The full conversation history is sent with every API call, giving Claude complete context. |
| **Personalised system prompt** | Each session injects the user's name and detected destination into Claude's instructions. |
| **Graceful degradation** | The app still starts and shows helpful messages even when the API key is missing. |
| **Session isolation** | Each browser tab gets its own independent conversation stored in Flask's server-side session. |
| **Keyboard-friendly UI** | Enter sends a message; Shift+Enter inserts a newline; Enter in the name field clicks Continue. |

---

## Architecture

```
Browser
  │
  │  HTML/CSS/JS (index.html)
  │  • Greeting page (name + photo upload)
  │  • Chat interface (message history + input bar)
  │
  │  fetch() calls
  │
  ▼
Flask App (index.py)
  │
  ├── GET  /              → Serve index.html, clear session
  ├── POST /upload-photo  → Detect location via Claude vision
  │                          Seed conversation history in session
  │                          Return opening message
  ├── POST /send-message  → Append user turn, call Claude,
  │                          append reply, return to UI
  ├── POST /reset         → Wipe session, front-end reloads
  └── GET  /get-history   → Return session chat log (debug)
  │
  ▼
Anthropic Claude API
  • claude-sonnet-4-20250514
  • Vision call  (max_tokens=1000) – location detection
  • Chat call    (max_tokens=4000) – conversation replies
```

---

## Project Structure

```
iter/
├── index.py                  # Flask application (backend)
├── templates/
│   └── index.html            # Single-page frontend
├── static/                   # Static assets (CSS, images – currently empty)
├── .env                      # API key (not committed to version control)
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

> **Note:** Flask requires HTML templates to be placed inside a `templates/` subdirectory. The app creates both `templates/` and `static/` automatically on first run if they are missing.

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.9 or later |
| pip | Latest |
| Anthropic API key | Any active key with Claude Sonnet access |

---

## Installation & Setup

```bash
# 1. Clone or download the project
git clone <your-repo-url>
cd iter

# 2. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install flask anthropic python-dotenv

# 4. Place index.html inside the templates folder
mkdir -p templates static
mv index.html templates/

# 5. Set your API key (see Configuration below)
```

### requirements.txt

```
flask>=3.0
anthropic>=0.25
python-dotenv>=1.0
```

---

## Configuration

The app reads `ANTHROPIC_API_KEY` from the environment. Two ways to set it:

**Option A – `.env` file (recommended for development)**

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=sk-ant-...
```

The app loads this automatically via `python-dotenv` if installed.

**Option B – Shell export**

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # macOS / Linux
set ANTHROPIC_API_KEY=sk-ant-...      # Windows CMD
```

> **Security:** Never commit your API key to version control. Add `.env` to `.gitignore`.

---

## Running the App

```bash
python index.py
```

The server starts on `http://0.0.0.0:5000`. Open `http://localhost:5000` in your browser.

The `debug=True` flag enables:
- Automatic server restart when code changes are saved.
- Detailed error tracebacks in the browser.

**Disable `debug=True` before deploying to production.**

---

## API Reference

### `GET /`

Clears the session and renders the greeting page.

**Response:** HTML page.

---

### `POST /upload-photo`

Accepts the user's name and destination photo. Identifies the location via Claude's vision API and seeds the conversation.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `photo` | File | Yes | Image file (JPEG, PNG, GIF, BMP) |
| `userName` | String | Yes | Display name for the user |

**Response:** `application/json`

```json
{
  "success": true,
  "location": "Paris, France",
  "initial_message": "Hello Alice! I'm Iter..."
}
```

| Field | Type | Description |
|---|---|---|
| `success` | Boolean | `true` on success |
| `location` | String \| null | Detected destination, or `null` if unrecognised |
| `initial_message` | String | Iter's opening chat message |

**Error responses:**

```json
{ "error": "No photo uploaded" }           // 400
{ "error": "Failed to process photo: ..." }// 500
```

---

### `POST /send-message`

Sends a user message to Claude and returns the AI reply.

**Request:** `application/json`

```json
{ "message": "I'd like to go for two weeks in July." }
```

**Response:** `application/json`

```json
{
  "response": "Great! Two weeks in July is perfect for Paris...",
  "timestamp": "14:35"
}
```

**Error responses:**

```json
{ "error": "Message cannot be empty" }          // 400
{ "error": "Session expired. Please start over." }// 401
{ "error": "Sorry, I encountered an error: ..." } // 500
```

---

### `POST /reset`

Wipes the server-side session. The front-end reloads the page after calling this.

**Response:** `{ "success": true }`

---

### `GET /get-history`

Returns the stored chat log for the current session (primarily for debugging).

**Response:**

```json
{
  "history": [
    { "sender": "Iter", "message": "Hello!", "timestamp": "14:00" },
    { "sender": "You",  "message": "Hi!",    "timestamp": "14:01" }
  ],
  "user_name": "Alice"
}
```

---

## How the Conversation Works

### Session Data

Flask's session cookie stores two parallel data structures:

| Key | Purpose |
|---|---|
| `user_name` | Display name, used in prompts and error messages |
| `conversation_messages` | Full `[{role, content}]` history sent to the Claude API |
| `chat_history` | Human-readable log with sender labels and timestamps for the UI |

### Conversation Seeding

When `/upload-photo` succeeds, the session is seeded with:

```
conversation_messages = [
  { "role": "user",      "content": "<system prompt with persona + destination>" },
  { "role": "assistant", "content": "<Iter's opening greeting>" }
]
```

Injecting the system prompt as the first user turn is a common pattern that keeps the instructions inside the conversation window without needing a separate system-prompt parameter.

### Multi-turn Context

Every call to `/send-message` appends the new user turn, calls Claude with **the entire history**, then appends Claude's reply. This means Claude always sees the full dialogue and can reference anything said earlier — departure country, dates, budget, etc. — when generating the itinerary.

---

## Frontend Walkthrough

### Two-view Single Page

The HTML file contains both views inside a single `.container` div:

- `.greeting-page` — visible on load.
- `.chat-interface` — `display: none` until `submitGreeting()` succeeds, then switched to `display: flex`.

### Key JavaScript Functions

| Function | Triggered by | Does |
|---|---|---|
| `checkContinueButton()` | Name input / file picker | Enables Continue only when both fields are filled |
| `submitGreeting()` | Continue button / Enter key | POSTs to `/upload-photo`; swaps views on success |
| `addMessage(sender, msg)` | After every API response | Creates a styled bubble and appends it to the log |
| `sendMessage()` | Send button / Enter key | POSTs to `/send-message`; renders the reply |
| `handleKeyPress(e)` | Textarea keypress | Sends on Enter; allows Shift+Enter for newlines |
| `resetChat()` | Reset Chat button | Confirms, calls `/reset`, then reloads the page |

### Hidden File Input Pattern

The native file picker (`<input type="file">`) is hidden with CSS. A styled green button calls `document.getElementById('photoInput').click()` to trigger the OS file dialog. This is a standard technique for customising the appearance of file inputs across all browsers.

---

## Key Design Decisions

**Why send the full conversation history every turn?**  
The Claude API is stateless — it has no memory between requests. Sending the full history ensures Claude can always reference earlier answers (e.g. the user's budget mentioned three turns ago) when crafting the itinerary.

**Why store the system prompt as a user turn instead of a `system` parameter?**  
It keeps the initialisation code uniform. The system prompt + Claude's greeting are stored in the same list as all subsequent messages, making the session structure simple to inspect and extend.

**Why use Flask's server-side session instead of localStorage?**  
Storing conversation history server-side means the API key and conversation context never reach the browser. It also makes it straightforward to add authentication or rate-limiting later.

**Why two parallel history lists (`chat_history` and `conversation_messages`)?**  
The Claude API needs raw `{role, content}` objects. The UI needs sender labels and human-readable timestamps. Keeping them separate avoids polluting the API payload with display-only fields.

---

## Error Handling & Graceful Degradation

| Scenario | Behaviour |
|---|---|
| Missing API key | App starts; placeholder messages guide the user |
| Unrecognisable photo | Iter asks the user to type the destination manually |
| API/network error on photo upload | Inline red error banner; Continue button re-enabled |
| API/network error on chat message | Error displayed as an Iter message in the chat |
| Expired/missing session | 401 response; front-end prompts the user to start over |

---

## Extending the Project

**Add persistent storage**  
Replace Flask sessions with a database (SQLite + SQLAlchemy) so conversation history survives server restarts.

**Add user authentication**  
Integrate Flask-Login so multiple users can have separate conversation histories.

**Stream responses**  
Use `client.messages.stream()` and Server-Sent Events (SSE) to stream Claude's reply token-by-token instead of waiting for the full response.

**Deploy to the cloud**  
- Set `debug=False` and use a production WSGI server such as Gunicorn.  
- Set the `ANTHROPIC_API_KEY` environment variable via the hosting platform's secret manager.  
- Example: `gunicorn -w 4 index:app`

**Add a map view**  
After the itinerary is generated, parse day/location data and render pins on a Leaflet.js or Google Maps embed.

---

## Known Limitations

- **Session size:** Long conversations increase the session cookie size. Flask's default cookie-based session has a 4 KB limit. Switch to `flask-session` with a server-side backend (Redis, filesystem) for lengthy itineraries.
- **No streaming:** The UI shows a static "Sending…" state while waiting for the full API response. Streaming would improve perceived responsiveness.
- **Single-file deployment:** `index.html` mixes structure, styles, and scripts. For larger teams, split into separate CSS and JS files under `static/`.
- **No input sanitisation for XSS:** `addMessage()` injects `message` directly as `innerHTML`. For a public deployment, sanitise or escape user-supplied content before insertion.