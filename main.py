import os
import random
import json
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Initialize OpenAI Client
load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

with open('cards.json', 'r', encoding='utf-8') as f:
    ALL_CARDS = json.load(f)

# --- Pydantic Models for AI Endpoint ---
class CardDraw(BaseModel):
    name: str
    isReversed: bool
    meaning: str

class ReadingRequest(BaseModel):
    question: str
    cards: List[CardDraw]

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/api/init_game")
async def init_game(count: int = 3):
    if not (1 <= count <= 11):
        count = random.randint(1, 11)
    deck = ALL_CARDS.copy()
    random.shuffle(deck)
    piles = [[] for _ in range(count)]
    for i, card in enumerate(deck):
        piles[i % count].append(card)
    return {"count": count, "piles": piles}

@app.post("/api/interpret")
async def interpret_reading(request: ReadingRequest):
    try:
        # Construct a prompt describing the draw
        cards_desc = "\n".join(
            [f"- {c.name} ({'Reversed' if c.isReversed else 'Upright'}): {c.meaning}" for c in request.cards]
        )
        
        prompt = f"""
        You are a mystical, wise, and empathetic Tarot reader. The user has asked the following question: 
        "{request.question}"
        
        They drew the following cards:
        {cards_desc}
        
        Provide a cohesive, insightful, and beautifully written tarot reading. 
        Synthesize the meanings of the cards as they relate to the user's specific question. 
        Keep the tone elegant, slightly poetic, but grounded and helpful. 
        Output the reading in clean paragraphs (do not use markdown headers, just plain text with line breaks).
        """

        # Call the OpenAI API (Using gpt-4o or your intended gpt-5 model name)
        response = await client.chat.completions.create(
            model="gpt-4o", # Replace with "gpt-5" when available
            messages=[
                {"role": "system", "content": "You are a professional, intuitive Tarot reader."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        return {"reading": response.choices[0].message.content}
        
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        raise HTTPException(status_code=500, detail="The Oracle is currently resting. Please try again later.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)