from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

# Keep /api/init_game for any future use, but frontend is now self-contained
import random, json

with open('cards.json', 'r', encoding='utf-8') as f:
    ALL_CARDS = json.load(f)

@app.get("/api/init_game")
async def init_game(count: int = 3):
    if not (3 <= count <= 11):
        count = random.randint(3, 11)
    deck = ALL_CARDS.copy()
    random.shuffle(deck)
    piles = [[] for _ in range(count)]
    for i, card in enumerate(deck):
        piles[i % count].append(card)
    return {"count": count, "piles": piles}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
