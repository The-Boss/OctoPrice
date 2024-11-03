
from contextlib import asynccontextmanager
from fastapi import FastAPI
from datetime import datetime, timedelta
from pytz import utc
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


# API settings - replace with your specific details
OCTOPUS_API_URL = "https://api.octopus.energy/v1/products/AGILE-24-10-01/electricity-tariffs/E-1R-AGILE-24-10-01-A/standard-unit-rates/"
threshold_high = 22.0
threshold_medium = 15.0

# Store for the fetched data



# class PricePoint(BaseModel):
#     value_exc_vat: float
#     value_inc_vat: float
#     valid_from: datetime
#     valid_to: datetime
#     payment_method: str | None

# class EnergyData(BaseModel):
#     energy_data: List[PricePoint]

energy_data: List = []


def fetch_energy_data():
    """Gets Octo data from now through to the latest available in the future."""    
    print("fetching data...")
    global energy_data
    # params = {"period_from": datetime.now().isoformat()}
    params = {"period_from": "2024-11-02T21:00:00Z"}
    try:
        response = requests.get(OCTOPUS_API_URL, params=params)
        response.raise_for_status()
        energy_data = response.json()["results"]
        print("success!...")
        # print(energy_data)

    except requests.RequestException as e:
        print("Failed to fetch data:", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    fetch_energy_data()
    scheduler = BackgroundScheduler()
    trigger = CronTrigger(minute="0,30")
    scheduler.add_job(fetch_energy_data, trigger)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

@app.get("/")
async def read_root():
    time = datetime.now()
    
    while True:
        if ((datetime.strptime(energy_data[-1]["valid_from"].replace("Z",""), "%Y-%m-%dT%H:%M:%S") < time) and datetime.strptime(energy_data[-1]["valid_to"].replace("Z",""), "%Y-%m-%dT%H:%M:%S") > time):
        # Have the right prive point - return it
            return energy_data[-1]
        elif (datetime.strptime(energy_data[-1]["valid_to"].replace("Z",""), "%Y-%m-%dT%H:%M:%S") < time):
            energy_data.pop()
            print("removed value")
        else:
            return {"key":"Error"}

    # return energy_data[-1]
    # return {"colour":"blue"}

@app.get("/defaultprice")
async def read_root():
    return {"colour":"red"}





