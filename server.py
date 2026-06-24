import os
import uvicorn
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from database_v2 import DatabaseManager # Импортируем из корня

db = DatabaseManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_pool()
    # ... тут твой код создания таблиц (оставь как было) ...
    yield
    if db.pool: await db.pool.close()

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
    async with db.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO leads (source_id, category, title, description, metro, district, link, tags)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8) ON CONFLICT (source_id) DO NOTHING
        """, lead.source_id, lead.category, lead.title, lead.description, lead.metro, lead.district, lead.link, lead.tags)
    return {"status": "success"}

# ... остальные эндпоинты (add_master, assign_worker) оставляй как есть ...

if __name__ == "__main__":
    # Для локального теста 8000, для Render будет переопределено
    uvicorn.run("server:app", host="0.0.0.0", port=10000, reload=True)