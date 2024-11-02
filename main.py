
from contextlib import asynccontextmanager

from fastapi import FastAPI
from datetime import datetime, timedelta
from pytz import utc
import requests
# from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing import List, Dict
import uvicorn
# import asyncio

# API settings - replace with your specific details
OCTOPUS_API_URL = "https://api.octopus.energy/v1/products/AGILE-24-10-01/electricity-tariffs/E-1R-AGILE-24-10-01-A/standard-unit-rates/"
threshold_high = 22.0
threshold_medium = 15.0

# Store for the fetched data
energy_data: List = [{"price":"null"}]

scheduler = AsyncIOScheduler(timezone=utc)

@scheduler.scheduled_job('cron', minute="0,35")
async def fetch_energy_data():
    """Gets Octo data from now through to the latest available in the future."""    
    print("fetching data...")
    global energy_data
    params = {"period_from": datetime.now().isoformat()}
    try:
        response = requests.get(OCTOPUS_API_URL, params=params)
        response.raise_for_status()
        energy_data = response.json()["results"]
        print("success!...")

    except requests.RequestException as e:
        print("Failed to fetch data:", e)
        


@asynccontextmanager
async def lifespan(app: FastAPI):
    # fetch_energy_data()
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

@app.get("/")
async def read_root():
    return energy_data[-1]
    # return {"colour":"blue"}

@app.get("/defaultprice")
async def read_root():
    return {"colour":"red"}





