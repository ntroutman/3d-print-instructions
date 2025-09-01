"""Gemini client for generating instructions."""

import os
from google import genai
from google.auth import default

PROJECT_ID = "personalization-rec-ai-9261362"
LOCATION = "us-central1"
MODEL_ID = "gemini-2.5-flash"


class GeminiClient:
    def __init__(self):
        # Set service account credentials
        service_account_path = os.path.join(os.path.dirname(__file__), "service_account.json")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_path
        
        self.client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    
    def generate(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=MODEL_ID,
            contents=prompt
        )
        return response.candidates[0].content.parts[0].text


if __name__ == "__main__":
    client = GeminiClient()
    result = client.generate("Say hello world")
    print(result)