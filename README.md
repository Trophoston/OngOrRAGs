🧠 Ong-or AI Coach API (FastAPI + Gemini)This project implements a FastAPI backend for the Ong-or AI Coach, a virtual assistant named Nong Ong-or. This coach is specifically designed to interact with seniors (age 60+) who play the Ong-or Serious Game, which aims to improve memory and cognitive function.The core functionality involves using the Google Gemini API, combined with a specialized persona and real-time user game history, to provide personalized encouragement, instruction, and health guidance.🚀 Getting StartedPrerequisitesPython 3.8+A Google Gemini API Key.The data file: data_dashbord.json (must be present in the same directory as main.py).1. Setup and InstallationAssuming you have the complete code in a file named main.py, you can install the required dependencies using pip:pip install fastapi uvicorn pydantic python-dotenv google-genai
2. Environment ConfigurationYou must provide your Google API key to the application. Create a file named .env in the root directory and add your key. The application is configured to look for either GOOGLE_API_KEY or GEMINIKEY..env file example:# Obtain your key from Google AI Studio
GOOGLE_API_KEY="YOUR_GEMINI_API_KEY_HERE"
3. Running the ApplicationThe application is designed to be run using Uvicorn. The if __name__ == "__main__": block in main.py provides a shortcut for local development:python main.py
(Alternatively, you can use the direct Uvicorn command: uvicorn main:app --reload)The API will be available at http://127.0.0.1:8000. You can find the interactive documentation (Swagger UI) at http://127.0.0.1:8000/docs.💻 API Endpoints1. Health CheckGET /A simple endpoint to confirm the API is running.Response:{
    "Hello": "World"
}
2. Get User Game RecordsRetrieves a list of a user's recent game records from the leaderboard section of data_dashbord.json. This function returns the 25 most recent records sorted by timestamp.A. Query Parameter Style (Preferred)GET /user?email=test@example.comParameterLocationTypeDescriptionemailQuerystringThe user's email address. (Required)B. Path Parameter Style (Legacy)GET /user/{mail}ParameterLocationTypeDescriptionmailPathstringThe user's email address.Example Success Response (/user):{
    "email": "senior_player@example.com",
    "total_count": 42,
    "returned_count": 25,
    "users": [
        {
            "id": "record_1234",
            "mail": "senior_player@example.com",
            "score": 120,
            "timestamp": 1678886400000,
            "name": "Sompong",
            "username": "sompong_th"
        }
        // ... (up to 25 records)
    ]
}
3. Generate AI Response (Core Endpoint)POST /callThe main endpoint for conversational interaction. It uses the provided user prompt, custom persona (if given), language preference, and the user's game history to generate a tailored response from the gemini-2.5-flash model.Request Body (JSON)FieldTypeDescriptionpromptstringThe message/question from the user. (Required)user_mailstringThe user's email for fetching game history context.personastring(Optional) Overrides the default "Nong Ong-or" persona.languagestring(Optional) Specifies the desired response language (e.g., thai, en).Example Request:{
    "prompt": "ฉันเล่นเกมไปเมื่อเช้านี้ ฉันทำคะแนนได้ดีหรือเปล่า?",
    "user_mail": "senior_player@example.com",
    "language": "thai"
}
Example Success Response:The response includes the generated text, the full response object from the Gemini SDK for debugging/metadata, and the complete composed prompt sent to the model (including the persona and history).{
    "text": "สวัสดีค่ะคุณสมพงษ์! น้องอ่องออขอแสดงความยินดีด้วยนะคะ!...",
    "full_response": {
        // ... full metadata from the Gemini API call ...
    },
    "prompt": "Role: You are Nong Ong-or (...)\nRespond in Thai (ภาษาไทย).\nUser's Recent Game History (...)\n\nUser: ฉันเล่นเกมไปเมื่อเช้านี้ ฉันทำคะแนนได้ดีหรือเปล่า?\nน้องอ่องออ :"
}
