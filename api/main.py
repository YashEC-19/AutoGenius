from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
import requests
import os
import sys
import uuid
import time
import json
from dotenv import load_dotenv
from asyncio import sleep as asyncio_sleep

load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

outputs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'outputs'))
os.makedirs(outputs_path, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=outputs_path), name="outputs")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")
UNSPLASH_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

class CarQuery(BaseModel):
    query: str

def research_car(query: str) -> str:
    llm = ChatGroq(api_key=GROQ_API_KEY, model="llama-3.3-70b-versatile")
    messages = [
        SystemMessage(content="You are an expert automotive researcher. Research the given car and provide detailed specs, performance data, features and analysis."),
        HumanMessage(content=f"Research this car thoroughly: {query}")
    ]
    response = llm.invoke(messages)
    return response.content

def write_report(query: str, research: str) -> str:
    llm = ChatGroq(api_key=GROQ_API_KEY, model="llama-3.3-70b-versatile")
    messages = [
        SystemMessage(content="You are an expert automotive journalist. Write a compelling, detailed report based on the research provided."),
        HumanMessage(content=f"Write a detailed report for {query} based on this research:\n\n{research}")
    ]
    response = llm.invoke(messages)
    return response.content

def generate_image(query: str) -> str:
    try:
        search_query = query.replace(" ", "+")
        url = f"https://api.unsplash.com/search/photos?query={search_query}&per_page=1&orientation=landscape&client_id={UNSPLASH_KEY}"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                return data['results'][0]['urls']['regular']
        return None
    except Exception as e:
        print(f"Image generation error: {e}")
        return None

async def research_stream(query: str):
    run_id = uuid.uuid4().hex[:8]
    start = time.time()

    def send(step, message, data=None):
        payload = {"step": step, "message": message, "run_id": run_id}
        if data:
            payload.update(data)
        return f"data: {json.dumps(payload)}\n\n"

    yield send(1, "🔍 Initializing Research Agent...")
    await asyncio_sleep(0.5)

    yield send(2, "📡 Researching car specs and data...")
    research = research_car(query)
    await asyncio_sleep(0.3)

    yield send(3, "✅ Research complete!", {"research": research})
    await asyncio_sleep(0.3)

    yield send(4, "✍️ Writer Agent crafting report...")
    report = write_report(query, research)
    await asyncio_sleep(0.3)

    yield send(5, "✅ Report complete!", {"report": report})
    await asyncio_sleep(0.3)

    yield send(6, "🎨 Fetching car image...")
    image_url = generate_image(query)
    await asyncio_sleep(0.3)

    duration = round(time.time() - start, 1)
    yield send(7, "🏁 All done!", {
        "image_url": image_url,
        "duration": duration,
        "status": "COMPLETE"
    })

@app.post("/research/stream")
async def research_stream_endpoint(car_query: CarQuery):
    return StreamingResponse(
        research_stream(car_query.query),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/research")
async def research_endpoint(car_query: CarQuery):
    run_id = uuid.uuid4().hex[:8]
    start = time.time()
    research = research_car(car_query.query)
    report = write_report(car_query.query, research)
    image_url = generate_image(car_query.query)
    duration = round(time.time() - start, 1)
    return {
        "run_id": run_id,
        "query": car_query.query,
        "research": research,
        "report": report,
        "image_url": image_url,
        "duration": duration,
        "status": "COMPLETE"
    }

@app.get("/vision/generate")
async def vision_generate(prompt: str):
    try:
        encoded = requests.utils.quote(prompt + ", automotive photography, ultra detailed, cinematic lighting, 4k")
        seed = int(time.time()) % 99999
        pollinations_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&seed={seed}&nologo=true&model=flux"
        response = requests.get(pollinations_url, timeout=60)
        if response.status_code == 200:
            return Response(content=response.content, media_type="image/jpeg")
        else:
            return {"error": "Image generation failed"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health():
    return {"status": "ok"}