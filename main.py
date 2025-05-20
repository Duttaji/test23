from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import os

# Replace with your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")  # Or set it directly for testing

app = FastAPI()

# --- System & Reason-Specific Prompts (editable) ---
SYSTEM_PROMPT = "You are an expert in medical RCM documentation."
REASON_PROMPTS = {
    "timely filing": "Summarize the paragraph including CPT, initial submission date, resubmission date in {count} characters.",
    # Add more reasons as needed
}

# --- Request and Response Models ---
class InputData(BaseModel):
    ID: str
    Payer: str
    paragraph: str
    Reason: str
    Character_count: int

class OutputData(BaseModel):
    ID: str
    summarise_text: str

# --- Helper Function to Query OpenAI ---
def generate_summary(paragraph: str, reason: str, char_count: int) -> str:
    reason_prompt = REASON_PROMPTS.get(reason.lower(), "Summarize the paragraph in {count} characters.")
    user_prompt = reason_prompt.format(count=char_count) + f"\n\nText: {paragraph}"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # or gpt-3.5-turbo if using that
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Endpoint ---
@app.post("/summarise", response_model=OutputData)
def summarise_text(data: InputData):
    summary = generate_summary(data.paragraph, data.Reason, data.Character_count)
    return OutputData(ID=data.ID, summarise_text=summary)
