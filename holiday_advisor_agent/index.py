# =============================================================================
# Iter – AI Travel Planning Assistant
# Backend: Flask + Anthropic Claude API
# =============================================================================
# Architecture overview:
#   - Flask serves a single-page HTML frontend (templates/index.html).
#   - On load, the user enters their name and uploads a destination photo.
#   - The /upload-photo endpoint sends the image to Claude for location detection.
#   - Subsequent conversation turns are handled by /send-message, which maintains
#     a running message history inside the Flask server-side session so Claude
#     always has full context of the conversation.
# =============================================================================

from flask import Flask, render_template, request, jsonify, session
import anthropic          # Anthropic Python SDK – wraps the Claude REST API
import base64             # Used to encode binary image data as a string for the API
import os                 # File-system helpers and environment-variable access
from datetime import datetime  # Timestamps shown in chat messages
import secrets            # Cryptographically-safe random bytes for the session key

# ---------------------------------------------------------------------------
# Optional: load a .env file so developers can store ANTHROPIC_API_KEY there
# instead of exporting it to the shell environment.  The dotenv package is not
# listed as a hard dependency, so the import is wrapped in try/except.
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()          # Reads key=value pairs from .env into os.environ
except ImportError:
    pass                   # dotenv not installed – rely on the real environment


# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------

app = Flask(__name__)

# A random hex string used to sign Flask's client-side session cookie.
# secrets.token_hex(16) produces 32 hex characters (128 bits of entropy),
# which is secure enough for a session secret.
app.secret_key = secrets.token_hex(16)

# ---------------------------------------------------------------------------
# Anthropic client initialisation
# ---------------------------------------------------------------------------
# We only create the client when the API key is present.  This lets the app
# start (and show a graceful error message) even if the key is missing,
# rather than crashing at import time.
api_key = os.environ.get("ANTHROPIC_API_KEY", "")
client = anthropic.Anthropic(api_key=api_key) if api_key else None


# ===========================================================================
# ROUTE: /   –   Serve the landing / greeting page
# ===========================================================================
@app.route('/')
def index():
    """
    Renders the main page (templates/index.html) and clears any existing
    session data so that each new browser visit starts a fresh conversation.
    """
    session.clear()                    # Drop leftover state from a previous session
    return render_template('index.html')


# ===========================================================================
# ROUTE: /upload-photo   –   Accept the destination photo and start the chat
# ===========================================================================
@app.route('/upload-photo', methods=['POST'])
def upload_photo():
    """
    Handles the initial form submission from the greeting page.

    Expected multipart/form-data fields:
        photo    – the image file chosen by the user
        userName – the user's display name (plain text)

    Flow:
        1. Validate inputs.
        2. Base64-encode the image so it can be sent inside a JSON body.
        3. Ask Claude to identify the destination in the photo.
        4. Build a system prompt that primes Claude to act as a travel agent.
        5. Store conversation state in the server-side session.
        6. Return the detected location and Claude's opening message to the
           front-end, which then switches from the greeting page to the chat UI.

    Returns JSON:
        success (bool), location (str|None), initial_message (str)
    """

    # --- Input validation ---------------------------------------------------
    if 'photo' not in request.files:
        return jsonify({'error': 'No photo uploaded'}), 400

    photo = request.files['photo']
    user_name = request.form.get('userName', '')

    if not user_name:
        return jsonify({'error': 'Name is required'}), 400

    if photo.filename == '':
        return jsonify({'error': 'No photo selected'}), 400

    # --- Persist user identity for the lifetime of this session -------------
    session['user_name'] = user_name
    session['chat_history'] = []           # Human-readable log shown in the UI
    session['conversation_messages'] = []  # Full message list sent to the API

    try:
        # --- Image encoding -------------------------------------------------
        # Claude's vision API expects image bytes as a base64 string.
        # standard_b64encode returns bytes; .decode('utf-8') converts to str.
        img_data = base64.standard_b64encode(photo.read()).decode('utf-8')

        # Infer the MIME type from the file extension so the API knows the
        # image format.  Defaults to image/jpeg for unrecognised extensions.
        ext = os.path.splitext(photo.filename)[1].lower()
        media_type_map = {
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
            '.png': 'image/png', '.gif': 'image/gif', '.bmp': 'image/bmp'
        }
        media_type = media_type_map.get(ext, 'image/jpeg')

        # --- Graceful degradation when no API key is configured -------------
        if not client:
            return jsonify({
                'success': True,
                'location': None,
                'message': 'API key not configured. Please tell me your destination.'
            })

        # --- Step 1: Location detection via Claude vision -------------------
        # We send a single-turn request (no system prompt, no history) just to
        # classify the photo.  A tightly scoped prompt makes the answer easy
        # to parse: either a place name or the literal word "UNKNOWN".
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": img_data   # The encoded image bytes
                        }
                    },
                    {
                        "type": "text",
                        "text": (
                            "Identify the location in this photo. "
                            "Provide the specific city and country if recognizable. "
                            "If you can identify it, respond with just the location name "
                            "(e.g., 'Paris, France'). "
                            "If you cannot identify it with confidence, respond with exactly: 'UNKNOWN'"
                        )
                    }
                ]
            }]
        )

        # response.content is a list of content blocks; [0].text is the text reply.
        location = response.content[0].text.strip()

        # --- Step 2: Build the opening greeting based on whether the location
        #             was recognised --------------------------------------------
        if location == "UNKNOWN" or "cannot" in location.lower() or "unable" in location.lower():
            # Claude couldn't identify the landmark – ask the user to clarify.
            detected_location = None
            initial_msg = (
                f"Hello {user_name}! I'm Iter, your AI travel planning assistant. "
                "I couldn't identify the location from your photo. "
                "Could you please tell me where you'd like to travel?"
            )
        else:
            detected_location = location
            initial_msg = (
                f"Hello {user_name}! I'm Iter, your AI travel planning assistant. "
                f"I can see you're interested in visiting {detected_location}! "
                "Let me help you plan an amazing trip.\n\n"
                "To create the perfect itinerary for you, I'd like to know:\n\n"
                "1. Which country will you be departing from?\n"
                "2. What are your travel dates?\n"
                "3. What's your daily budget?\n"
                "4. What type of accommodation do you prefer?\n"
                "5. What activities interest you most?"
            )

        # --- Step 3: Build the system prompt --------------------------------
        # This defines Claude's persona and responsibilities for the entire
        # conversation.  It is injected as the first user turn (a common pattern
        # when a model doesn't have a dedicated system-prompt parameter) so that
        # it stays in context for every subsequent exchange.
        system_prompt = (
            f"You are Iter, a friendly and professional AI travel planning assistant. "
            f"You are helping {user_name} plan a trip."
        )

        if detected_location:
            system_prompt += f" The destination is {detected_location}."

        system_prompt += """

Your tasks:
1. Gather travel preferences: departure country, dates, daily budget, accommodation preferences, and preferred activities
2. Create a detailed itinerary with:
   - Daily activities and attractions
   - Travel times from departure country to destination
   - Travel times between different places at the destination
   - Realistic scheduling
3. Provide 3 tour operators in the customer's home country who could assist

Important guidelines:
- Be polite, friendly, and conversational
- Always remind customers that all suggestions must be confirmed by them
- Provide accurate, realistic travel information
- Consider actual travel times and logistics
- Ask clarifying questions if needed
- Keep responses well-structured but natural

When you have all information, create a comprehensive itinerary and suggest tour operators."""

        # --- Step 4: Seed the conversation history --------------------------
        # We store the conversation as a list of {role, content} dicts –
        # exactly the format the Anthropic API expects in the `messages` param.
        # The system prompt is injected as the first user turn; Claude's opening
        # greeting is stored as the first assistant turn.  All future exchanges
        # append to this list, giving the model a full view of the dialogue.
        session['conversation_messages'] = [
            {"role": "user",      "content": system_prompt},
            {"role": "assistant", "content": initial_msg}
        ]

        # chat_history is a parallel list used only by the front-end; it carries
        # sender labels and formatted timestamps that the UI needs but the API
        # doesn't care about.
        session['chat_history'] = [{
            'sender':    'Iter',
            'message':   initial_msg,
            'timestamp': datetime.now().strftime("%H:%M")
        }]

        return jsonify({
            'success':         True,
            'location':        detected_location,
            'initial_message': initial_msg
        })

    except Exception as e:
        # Surface any unexpected errors (network issues, API errors, etc.)
        return jsonify({'error': f'Failed to process photo: {str(e)}'}), 500


# ===========================================================================
# ROUTE: /send-message   –   Forward user turns to Claude and return the reply
# ===========================================================================
@app.route('/send-message', methods=['POST'])
def send_message():
    """
    Accepts a JSON body with a 'message' field, appends it to the session's
    conversation history, calls Claude, appends the reply, and returns it.

    This is the main chat endpoint.  Because the full message history is sent
    with every request, Claude always has the complete context of the
    conversation without needing server-side state beyond the session.

    Expected JSON body:
        { "message": "<user text>" }

    Returns JSON:
        { "response": "<Claude reply>", "timestamp": "HH:MM" }
    """
    data = request.get_json()
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({'error': 'Message cannot be empty'}), 400

    # Guard against tampered or expired sessions (e.g. server restart)
    if 'user_name' not in session:
        return jsonify({'error': 'Session expired. Please start over.'}), 401

    # Record the user's message in the UI-facing history
    timestamp = datetime.now().strftime("%H:%M")
    session['chat_history'].append({
        'sender':    'You',
        'message':   user_message,
        'timestamp': timestamp
    })

    # --- Graceful degradation without API key -------------------------------
    if not client:
        ai_response = "Sorry, I'm not properly configured. Please set up the API key."
        session['chat_history'].append({
            'sender':    'Iter',
            'message':   ai_response,
            'timestamp': datetime.now().strftime("%H:%M")
        })
        return jsonify({'response': ai_response, 'timestamp': datetime.now().strftime("%H:%M")})

    try:
        # Retrieve the full message history built up across previous turns
        conversation_messages = session.get('conversation_messages', [])

        # Append the new user turn
        conversation_messages.append({
            "role":    "user",
            "content": user_message
        })

        # --- Call Claude with the complete conversation history -------------
        # max_tokens=4000 allows long itinerary responses.
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=conversation_messages   # Full history → full context
        )

        ai_response = response.content[0].text

        # Append Claude's reply so it is included in the next API call
        conversation_messages.append({
            "role":    "assistant",
            "content": ai_response
        })

        # Persist the updated history back into the session
        session['conversation_messages'] = conversation_messages

        # Record Claude's reply in the UI history too
        ai_timestamp = datetime.now().strftime("%H:%M")
        session['chat_history'].append({
            'sender':    'Iter',
            'message':   ai_response,
            'timestamp': ai_timestamp
        })

        return jsonify({'response': ai_response, 'timestamp': ai_timestamp})

    except Exception as e:
        error_msg = f"Sorry, I encountered an error: {str(e)}"
        session['chat_history'].append({
            'sender':    'Iter',
            'message':   error_msg,
            'timestamp': datetime.now().strftime("%H:%M")
        })
        return jsonify({'error': error_msg}), 500


# ===========================================================================
# ROUTE: /reset   –   Wipe the current session and start fresh
# ===========================================================================
@app.route('/reset', methods=['POST'])
def reset_chat():
    """
    Clears the Flask session, effectively logging out the user and wiping
    the entire conversation history.  The front-end then reloads the page,
    returning the user to the greeting screen.
    """
    session.clear()
    return jsonify({'success': True})


# ===========================================================================
# ROUTE: /get-history   –   Return the stored chat history (diagnostic/debug)
# ===========================================================================
@app.route('/get-history', methods=['GET'])
def get_history():
    """
    Returns the current session's chat log.  Mainly useful for debugging or
    if the front-end needs to re-render messages after a partial page refresh.
    """
    return jsonify({
        'history':   session.get('chat_history', []),
        'user_name': session.get('user_name', '')
    })


# ===========================================================================
# Entry point
# ===========================================================================
if __name__ == '__main__':
    # Ensure Flask's expected directory structure exists before starting.
    # Flask looks for HTML files in ./templates/ and static assets in ./static/.
    if not os.path.exists('templates'):
        os.makedirs('templates')
    if not os.path.exists('static'):
        os.makedirs('static')

    # debug=True enables auto-reload on code changes and shows detailed
    # tracebacks in the browser – turn this off in production.
    # host='0.0.0.0' makes the server reachable from other devices on the
    # same network (e.g. when testing on a phone).
    app.run(debug=True, host='0.0.0.0', port=5000)