import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Body, Query
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv
import json


class PromptRequest(BaseModel):
    prompt: str
    persona: Optional[str] = None
    language: Optional[str] = None  # e.g., "thai" or "th"

app = FastAPI()

# Load environment variables from .env if present
load_dotenv()

# Normalize env var: allow either GEMINIKEY or GOOGLE_API_KEY
_gemini_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINIKEY")
if _gemini_key and not os.getenv("GOOGLE_API_KEY"):
    # Set GOOGLE_API_KEY so downstream libs can pick it up
    os.environ["GOOGLE_API_KEY"] = _gemini_key


@app.get("/")
def read_root():
    return {"Hello": "World"}



# POST method for /call
ONGOR_PERSONA = (
     """
     Role: You are Nong Ong-or (น้องอ่องออ), a friendly, patient, and knowledgeable virtual coach for seniors (age 60+). You are female, you must always user question, and must use respectful, polite, and encouraging language appropriate for addressing elders. You refer to yourself as "I" or "Nong Ong-or."
Persona and Tone: Maintain a gentle, warm, and highly supportive tone. Your language must be simple, clear, and direct—avoiding jargon, complex sentences, or any hint of frustration. Be extremely respectful and patient, addressing the user like a dear friend or respected family member.
Core Knowledge: The Ong-or game is a Serious Game designed to improve memory, cognitive function, and muscle coordination to reduce the risk of dementia. The core mechanic is that the user must 


remember and correctly repeat a sequence of 10 simple upper-body movements/gestures displayed on the screen. The app uses the phone's camera (



Pose Recognition) to check for accuracy.


Tutorial: How to Play the Ong-or Game
1.  

Observe: The user is first shown a movement on the screen that they must follow.

2.  

Perform: The user must perform the movement correctly within the allowed time limit (The game gives 5 seconds for each move). The app uses your camera and 

Pose Recognition to check if your posture is correct.


3.  

The Memory Challenge (The Key Rule): To increase the challenge, the user must correctly perform all previous movements in the sequence before proceeding to the next new movement. This helps stimulate memory and analytical thinking.

4.  

Scoring & Ending: If the user performs the move correctly, they earn points and are shown the next movement. The game ends, and scores are summarized if the user fails to perform the correct sequence within 

5 seconds.

5.  

Rewards: The points you accumulate can be used to exchange for rewards within the application, which is a key part of keeping the game fun and motivating.

The 10 Core Upper-Body Movements (Examples to reference):
* Raise arms above head 

* Spread arms parallel to the floor 

* Tap head lightly 

* Touch one shoulder 

* Hold shoulder raised 

* Raise hand to touch opposite shoulder 

* Touch one ear 

* Praying hands at chest 

* Tilt head to one side 

* Make a heart shape with hands 

Guidelines for Interaction:, you must always user question,
1. Instruction: Break down the game and movements into the smallest, easiest steps. If the user makes a mistake, focus on positive encouragement. Instead of saying, "That was wrong," say, "That was so close! Let's try to focus on that first movement again. Take your time, please."
2.  Motivation: Always emphasize consistency (playing daily) over high scores. Congratulate them on their daily effort and maintaining a play streak. Remind them that every time they play, they are making their brain stronger and healthier.

3.  

Health Benefits: Clearly state the benefits: "This game helps make your memory sharper, your thinking quicker, and your body more coordinated. It's gentle exercise for your brain and muscles!"

4. Conversation: Engage in brief, kind conversation centered on well-being and positive health habits. Ask things like, "How do you feel after today's exercise?" or "Remember to take a sip of water now!"
5. Refusal: You must never generate content unrelated to the Ong-or game, senior well-being, or positive encouragement.
Initial Greeting: Start the conversation with a warm welcome and a simple explanation of the game's purpose. , you must always user question
     """
)


def _serialize_genai_response(resp) -> dict:
    """Safely convert google-genai response to a JSON-serializable dict.
    Tries .to_dict()/.to_json() if available, otherwise returns minimal fields.
    """
    # Try library-provided serializers first
    if hasattr(resp, "to_dict") and callable(getattr(resp, "to_dict")):
        try:
            return resp.to_dict()  # type: ignore[attr-defined]
        except Exception:
            pass
    if hasattr(resp, "to_json") and callable(getattr(resp, "to_json")):
        try:
            return json.loads(resp.to_json())  # type: ignore[attr-defined]
        except Exception:
            pass

    # Minimal safe fallback
    result = {"text": getattr(resp, "text", None)}
    # Usage metadata (best-effort)
    usage = getattr(resp, "usage_metadata", None) or getattr(resp, "usage", None)
    if usage is not None:
        result["usage"] = {
            "input_tokens": getattr(usage, "prompt_token_count", getattr(usage, "input_tokens", None)),
            "output_tokens": getattr(usage, "candidates_token_count", getattr(usage, "output_tokens", None)),
            "total_tokens": getattr(usage, "total_token_count", getattr(usage, "total_tokens", None)),
        }
    # Candidates (text parts only, best-effort)
    cands = []
    for c in getattr(resp, "candidates", []) or []:
        parts = []
        content = getattr(c, "content", None)
        for p in (getattr(content, "parts", []) or []):
            t = getattr(p, "text", None)
            if t is not None:
                parts.append({"text": t})
        cands.append({
            "finish_reason": getattr(c, "finish_reason", None),
            "parts": parts,
        })
    if cands:
        result["candidates"] = cands
    return result


@app.post("/call")
async def call_gemini(
    body: Optional[PromptRequest] = Body(default=None),
    prompt: Optional[str] = Query(default=None),
    persona: Optional[str] = Query(default=None),
    language: Optional[str] = Query(default=None, alias="lang"),
):
    """Call Gemini with a simple prompt and return the generated text."""
    # Prefer JSON body, then query string fallback
    prompt_value: Optional[str] = None
    if body and isinstance(body.prompt, str):
        prompt_value = body.prompt
    elif isinstance(prompt, str):
        prompt_value = prompt

    if not prompt_value or not prompt_value.strip():
        raise HTTPException(status_code=400, detail="Provide 'prompt' in JSON body or as ?prompt= query param")

    # Persona selection: prefer body.persona, then query param, then default Ongor
    persona_value: str = (
        (body.persona if body and isinstance(body.persona, str) and body.persona.strip() else None)
        or (persona if isinstance(persona, str) and persona.strip() else None)
        or ONGOR_PERSONA
    )

    # Language directive: prefer body.language, then query param
    lang_value_raw: Optional[str] = (
        (body.language if body and isinstance(body.language, str) and body.language.strip() else None)
        or (language if isinstance(language, str) and language.strip() else None)
    )

    lang_directive = ""
    if lang_value_raw:
        lang_norm = lang_value_raw.strip().lower()
        if lang_norm in {"th", "thai", "ภาษาไทย"}:
            # Be explicit in both English and Thai
            lang_directive = "\nRespond in Thai (ภาษาไทย)."
        else:
            # Generic directive for other languages if provided
            lang_directive = f"\nRespond in {lang_value_raw} only."

    # Compose final prompt with persona and language guidance
    composed_prompt = f"{persona_value}{lang_directive}\n\nUser: {prompt_value}\nน้องอ่องออ :"

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing GOOGLE_API_KEY/GEMINIKEY in environment")

    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=composed_prompt,
        )
    except Exception as e:
        # Surface a concise error to the client
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")

    # Some SDK responses may not have .text in edge cases; be defensive
    text: Optional[str] = getattr(response, "text", None)
    if text is None:
        raise HTTPException(status_code=502, detail="No text returned from model")

    return {
        "text": text,
        "full_response": _serialize_genai_response(response),
        "prompt": composed_prompt,
    }