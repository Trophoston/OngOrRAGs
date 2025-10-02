# OngOrRAGs

Simple FastAPI service exposing Example:

```
# Get user by email
curl -s 'http://localhost:8000/user?email=ongor.fun@gmail.com'

# Call Gemini without user history
curl -s -X POST http://localhost:8000/call \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"hello gemini"}'

# Call Gemini with user history (personalized response)
curl -s -X POST http://localhost:8000/call \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"How am I doing?","user_mail":"ongor.fun@gmail.com","language":"thai"}'
```ll endpoint that proxies a prompt to Google's Gemini via `google-genai` and returns generated text.

## Quick start

1) Install dependencies

```
pip install -r requirements.txt
```

2) Provide your Google API key (required by google-genai). You can set it via environment or .env:

Option A: export var

```
export GOOGLE_API_KEY="<your_api_key>"
```

Option B: .env file (both names are supported)

```
GOOGLE_API_KEY=<your_api_key>
# or
GEMINIKEY=<your_api_key>
```

3) Run the server

```
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API

- GET /user
  - Query parameter: `email` (required)
  - Returns: Top 10 most recent user records matching the email from data_dashbord.json (sorted by timestamp, newest first)
  - Example: `GET /user?email=ongor.fun@gmail.com`

- POST /call
  - Request body: `{ "prompt": "hello gemini", "user_mail": "ongor.fun@gmail.com", "persona": "optional persona override", "language": "thai" }`
  - Query parameters: `prompt`, `user_mail`, `persona`, `lang` (all optional if using JSON body)
  - If `user_mail` is provided, the user's 10 most recent game history records will be included in the context sent to Gemini
  - Response: `{ "text": "...model output..." }`Example:

```
curl -s -X POST http://localhost:8000/call \
	-H 'Content-Type: application/json' \
		-d '{"prompt":"hello gemini"}'
```
### Ongor persona

By default, the service prompts Gemini to respond as “Ongor,” an award‑winning elder care mascot with a warm, respectful tone and concise guidance. You can override the persona:

- JSON body override:

```
{
	"prompt": "How can I help my grandma stay active?",
	"persona": "Reply as a cheerful coach named Ongor who focuses on safe daily routines."
}
```

- Query override:

```
curl -s 'http://localhost:8000/call?prompt=hello&persona=Reply%20as%20a%20cheerful%20coach%20named%20Ongor'
```

### Language control

Ask for Thai responses either via JSON or query parameter:

- JSON body:

```
{
	"prompt": "แนะนำกิจกรรมสำหรับผู้สูงอายุหน่อย",
	"language": "thai"
}
```

- Query parameter (alias `lang` supported):

```
curl -s 'http://localhost:8000/call?prompt=สวัสดี&lang=thai'
```

Root endpoint for a quick check:

```
curl http://localhost:8000/
```