from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq
import os
from dotenv import load_dotenv

#GROQ_API_KEY="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"


app = FastAPI()
load_dotenv()


# --- System & Reason-Specific Prompts (editable) ---
SYSTEM_PROMPT = "You are an expert in medical RCM documentation."
REASON_PROMPTS = {
    "timely_filing_wrong_payer": (
        "You are summarizing a paragraph that explains a claim denial due to timely filing. "
        "Ensure the summary clearly includes the CPT code (make sure to show the CPT code as 'CPT: ', the initial submission date (even if to the wrong payer), "
        "and corrected resubmission date. The goal is to present a brief but complete justification that the claim "
        "was originally filed on time but incorrectly submitted, and then corrected. Limit the summary to {count} characters."
    ),
    "timely_filing_primary_payer_delay": (
        "You are summarizing a paragraph that explains a claim denial due to timely filing. "
        "Ensure the summary clearly includes the CPT code (make sure to show the CPT code as 'CPT: ', the initial submission date ((Submission Date (to be marked as Date of COB)), "
        "and the Date of EOB. The goal is to present a brief but complete justification that the claim "
        "was originally filed on time but incorrectly submitted, and then corrected. Limit the summary to {count} characters."
    ),
    "timely_filing_credential delay": (
        "You are summarizing a paragraph that explains a claim denial due to timely filing. "
        "Ensure the summary clearly includes the CPT code (make sure to show the CPT code as 'CPT: ', the initial submission date ((Credentialing Submission Date (to be marked as Credentialling submission date)), "
        "and the Credentialing Approval Date. Also if {count} characters allow provide data for provider name and insurance company name The goal is to present a brief but complete justification that the claim "
        "was originally filed on time but incorrectly submitted, and then corrected. Limit the summary to {count} characters."
    )
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


# --- Groq Client Initialization ---
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
print(client)

GROQ_MODEL = "llama-3.3-70b-versatile"  # Adjust if needed


# --- Helper Function to Query Groq API ---
def generate_summary(paragraph: str, reason: str, char_count: int) -> str:
    reason_prompt = REASON_PROMPTS.get(reason.lower(), "Summarize the paragraph in {count} characters.")
    user_prompt = reason_prompt.format(count=char_count) + f"\n\nText: {paragraph}"

    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Endpoint ---
@app.post("/summarise", response_model=OutputData)
def summarise_text(data: InputData):
    summary = generate_summary(data.paragraph, data.Reason, data.Character_count)
    return OutputData(ID=data.ID, summarise_text=summary)
