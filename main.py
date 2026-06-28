import os
import random
import json
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from google import genai

# 加载环境变量
load_dotenv()

# --- 初始化 Gemini 客户端 ---
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# 加载塔罗牌数据
with open('cards.json', 'r', encoding='utf-8') as f:
    ALL_CARDS = json.load(f)

# --- Pydantic Models ---
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
        # 构建卡牌描述
        cards_desc = "\n".join(
            [f"- {c.name} ({'Reversed' if c.isReversed else 'Upright'}): {c.meaning}" for c in request.cards]
        )
        
        # 具体的解牌任务 Prompt
        prompt = f"""
        The user has asked the following question: 
        "{request.question}"
        
        They drew the following cards:
        {cards_desc}
        
        Provide a cohesive, insightful, and beautifully written tarot reading. 
        Synthesize the meanings of the cards as they relate to the user's specific question. 
        Keep the tone elegant, slightly poetic, but grounded and helpful. 
        Output the reading in clean paragraphs (do not use markdown headers, just plain text with line breaks).
        """

        # 调用 Gemini (使用新版 SDK)
        # system_instruction 用于设置模型的人格和语言规则
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt,
            config={
                "system_instruction": "You are a mystical, wise, and empathetic Tarot reader. "
                                      "You must always respond in the same language as the user's question."
            }
        )
        
        return {"reading": response.text}
        
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        raise HTTPException(status_code=500, detail="The Oracle is currently resting. Please try again later.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)