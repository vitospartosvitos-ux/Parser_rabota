import os
import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import aiosqlite

DB_PATH = "database.db"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаем базу и таблицы прямо при запуске
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("CREATE TABLE IF NOT EXISTS leads (id INTEGER PRIMARY KEY AUTOINCREMENT, source_id TEXT UNIQUE, category TEXT, title TEXT, description TEXT, metro TEXT, district TEXT, link TEXT, tags TEXT, status TEXT DEFAULT 'Новый', worker_id INTEGER, worker_name TEXT)")
        await conn.execute("CREATE TABLE IF NOT EXISTS scraped_masters (id INTEGER PRIMARY KEY AUTOINCREMENT, source_id TEXT UNIQUE, category TEXT, title TEXT, description TEXT, metro TEXT, district TEXT, link TEXT, tags TEXT, scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        await conn.execute("CREATE TABLE IF NOT EXISTS workers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")
        await conn.commit()
    yield

app = FastAPI(title="LEAD-GENERATOR PRO v3.0", lifespan=lifespan)

class ScrapeModel(BaseModel):
    source_id: str
    category: str
    title: str
    description: str
    metro: str
    district: str
    link: str
    tags: str 

@app.post("/api/add_lead")
async def add_lead(lead: ScrapeModel):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("INSERT OR IGNORE INTO leads (source_id, category, title, description, metro, district, link, tags) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                           (lead.source_id, lead.category, lead.title, lead.description, lead.metro, lead.district, lead.link, lead.tags))
        await conn.commit()
    return {"status": "success"}

@app.post("/api/assign_worker")
async def assign_worker(lead_id: int = Form(...), worker_id: int = Form(...)):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute("SELECT name FROM workers WHERE id = ?", (worker_id,))
        worker = await cursor.fetchone()
        if worker:
            await conn.execute("UPDATE leads SET status='В работе', worker_id=?, worker_name=? WHERE id=?", (worker_id, worker[0], lead_id))
            await conn.commit()
    return RedirectResponse(url="/?tab=orders", status_code=303)

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    return HTMLResponse("<h1>Сервер запущен и работает!</h1>")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)