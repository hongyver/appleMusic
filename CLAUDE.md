# CLAUDE.md — appleMusic

## Project Overview

**appleMusic** is a Korean-language web application that generates AI-curated Apple Music playlists. A user describes their mood or theme in natural language; the backend calls GPT-4o to recommend songs, searches Apple Music for each track, and creates a playlist directly in the user's Apple Music library.

---

## Architecture

```
appleMusic/
├── app.py               # Flask web server (routes, SSE)
├── apple.py             # OpenAI/GPT-4o integration
├── appleApi.py          # Apple Music REST API wrapper
├── createAppleToken.py  # Apple Developer JWT generator
├── templates/
│   └── index.html       # Single-page UI (MusicKit.js)
├── static/
│   ├── css/index.css    # Styling (Apple Music pink #fa2a55)
│   └── js/applemusic.js # Frontend logic (auth, SSE, requests)
├── AuthKey_6598LR43L7.p8  # Apple private key (DO NOT COMMIT)
├── .env                   # Secrets (gitignored)
└── README.md
```

### Data Flow

```
User prompt
  └─► app.py /make_playlist
        ├─► apple.py get_play_list()   → GPT-4o → "[artist][title][desc]" strings
        │     └─► extract_songs()      → list of (artist, title, description) tuples
        └─► appleApi.py
              ├─► find_apple_music_track_id()  → Apple Music Catalog search
              ├─► create_apple_music_playlist() → create library playlist
              └─► add_tracks_to_playlist()      → add matched tracks
```

Real-time progress is pushed to the browser via **Server-Sent Events (SSE)** on `/status`.

---

## Running the Application

### Prerequisites

Install Python dependencies (no `requirements.txt` exists yet — install manually):

```bash
pip install flask openai requests python-dotenv tiktoken PyJWT
```

### Environment Variables

Create a `.env` file (already gitignored):

```
OPENAI_API_KEY=sk-...
APPLE_MUSIC_DEV_TOKEN=<JWT from createAppleToken.py>
```

### Generate Apple Developer Token

```bash
python createAppleToken.py
```

Copy the output into `.env` as `APPLE_MUSIC_DEV_TOKEN`. The token is valid for 6 months (ES256 JWT signed with the `.p8` key).

### Start the Server

```bash
python app.py
```

Server listens on `0.0.0.0:9876`. Open `http://localhost:9876` in a browser.

### CLI Mode (standalone recommendations, no Apple Music)

```bash
python apple.py -p "rainy evening jazz vibes" -n 20
```

---

## Key Modules

### `app.py`
- **`GET /`** — serves `index.html`
- **`POST /receive_token`** — receives the MusicKit user token from the browser and stores it in the Flask session
- **`POST /make_playlist`** — main endpoint: calls `get_play_list()` then `create_apple_music_playlist()` + `add_tracks_to_playlist()`
- **`GET /status`** — SSE stream; clients poll this to display real-time progress messages
- Global `current_status` string is the shared state between the worker logic and the SSE endpoint

### `apple.py`
- **`get_play_list(prompt, num_songs)`** — sends a prompt to GPT-4o (model: `gpt-4o`, temperature=1, top_p=1.0) and returns raw text
- **`extract_songs(text)`** — regex `\[([^\]]+)\]\[([^\]]+)\]\[([^\]]+)\]` extracts `(artist, title, description)` triples
- **`count_chat_tokens(messages)`** — estimates token cost (tiktoken `cl100k_base`); prints KRW/USD costs

### `appleApi.py`
- **`find_apple_music_track_id(title, artist, dev_token, user_token)`** — searches catalog; fuzzy-matches by removing spaces and lowercasing; falls back to first result
- **`create_apple_music_playlist(name, description, dev_token, user_token)`** — creates a new library playlist via `POST /v1/me/library/playlists`
- **`add_tracks_to_playlist(playlist_id, track_ids, dev_token, user_token)`** — `POST /v1/me/library/playlists/{id}/tracks`

### `createAppleToken.py`
- Reads `AuthKey_6598LR43L7.p8`, signs a JWT with algorithm ES256
- Hard-codes `TEAM_ID` and `KEY_ID` (Apple Developer credentials)

---

## Frontend (`static/js/applemusic.js`)

- Loads **MusicKit.js v1** from Apple CDN; configures it with the developer token injected into the page by Flask
- `authorize()` — prompts Apple Music login; stores the resulting user token in `localStorage` and POSTs it to `/receive_token`
- `makePlaylist()` — POSTs `{prompt, num_songs}` to `/make_playlist`; opens an SSE connection to `/status` to display live progress
- Tokens are persisted in `localStorage` to avoid re-authorization on page reload

---

## Code Conventions

- **Language:** Comments, UI labels, print statements, and docstrings are written in **Korean**
- **Python naming:** `snake_case` for functions and variables
- **JavaScript naming:** `camelCase` for variables and DOM references
- **No test suite** — no pytest, unittest, or any test files currently exist
- **No `requirements.txt`** — dependencies must be installed manually (adding one is a good first improvement)

---

## Environment & Secrets

| File | Status | Notes |
|------|--------|-------|
| `.env` | Gitignored | Contains `OPENAI_API_KEY`, `APPLE_MUSIC_DEV_TOKEN` |
| `AuthKey_6598LR43L7.p8` | **Tracked in git** | Apple private key — should be removed from git history |
| `app.secret_key` | Hard-coded in `app.py` | Should be moved to `.env` |

> **Security note:** The `.p8` private key file is currently committed to the repository. It should be removed from git history and added to `.gitignore`.

---

## Common Tasks

### Add a new API route
Edit `app.py`. Follow the existing pattern: use `request.json` for POST bodies, return `jsonify(...)`.

### Change the GPT model or prompt
Edit `apple.py` → `get_play_list()`. The system prompt and model name are defined inline in that function.

### Modify Apple Music API calls
Edit `appleApi.py`. The base URL is `https://api.music.apple.com`. All requests require both `Authorization: Bearer <dev_token>` and `Music-User-Token: <user_token>` headers.

### Update the UI
Edit `templates/index.html` and `static/js/applemusic.js`. The page uses vanilla JS with no bundler or framework.

### Regenerate the developer token
```bash
python createAppleToken.py
```
Update `APPLE_MUSIC_DEV_TOKEN` in `.env`.

---

## Known Limitations & TODOs

- No `requirements.txt` — dependency installation is manual
- No error handling when Apple Music search returns zero results
- Exchange rate (1 USD = 1,350 KRW) for cost display is hard-coded in `apple.py`
- No tests of any kind
- Apple `.p8` private key is committed to git (security risk)
- `app.secret_key` is a predictable hard-coded string
- User token stored in `localStorage` is vulnerable to XSS
