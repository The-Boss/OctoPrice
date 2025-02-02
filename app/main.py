
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, status
from datetime import datetime
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import List, Dict, Optional
from pydantic import BaseModel
import os

# Retrieve the API key from environment variables
API_KEY = os.getenv("OCTO_KEY")
# API_KEY ="password"

# Fallback to a default value if the variable is not set
if API_KEY is None:
    raise ValueError("API_KEY environment variable not set.")
else:
    print("API_KEY found")


# API URLs
OCTOPUS_API_URL = "https://api.octopus.energy/v1/products/AGILE-24-10-01/electricity-tariffs/E-1R-AGILE-24-10-01-A/standard-unit-rates/"
WHATSAPPSENDER_API_URL = "https://whatsappsender-2782.twil.io/WhatsappSender"

# Default price thresholds
threshold_high = 22.0
threshold_medium = 17.0
threshold_low = 12.0


# Define Pydantic Models
class ThresholdUpdate(BaseModel):
    high: float
    medium: float
    low: float

class StatusPing(BaseModel):
    time: datetime
    from_device_id: str

class SupportRequest(BaseModel):
    time: datetime
    from_device_id: str
    tel: str

class PricePoint(BaseModel):
    value_exc_vat: float
    value_inc_vat: float
    valid_from: datetime
    valid_to: datetime
    payment_method: Optional[str] = None

class ColourResponse(BaseModel):
    colour: str

class EnergyData(BaseModel):
    energy_data: List[PricePoint]

# In-memory energy data
energy_data: List[dict] = []

# Dependency for API key authentication
def api_key_auth(api_key: str):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )


def fetch_energy_data():
    """Gets Octo data from now through to the latest available in the future."""    
    print("fetching data...")
    global energy_data
    params = {"period_from": datetime.now().isoformat()}
    # params = {"period_from": "2024-11-02T21:00:00Z"}
    try:
        response = requests.get(OCTOPUS_API_URL, params=params)
        response.raise_for_status()
        energy_data = response.json()["results"]
        print("Data fetched successfully!...")
    except requests.RequestException as e:
        print("Failed to fetch data:", e)


def retrieve_current_data() -> Optional[dict]:
    """Retrieve the current price point based on the current time."""
    if not energy_data:
        print("Energy data is empty")
        return None
    
    current_time = datetime.now()
    while energy_data:
        last_price = energy_data[-1]
        # Think I might need to consider the below as datetimes, not strings
        valid_from = datetime.strptime(last_price["valid_from"].replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
        valid_to = datetime.strptime(last_price["valid_to"].replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
        
        if valid_from <= current_time < valid_to:
            return last_price
        elif valid_to < current_time:
            energy_data.pop()  # Remove outdated price points
            print("Removed outdated value.")
        else:
            break
    return None


def determine_colour(price_data) -> dict:
    """Determine the color based on the price value."""
    if not price_data:
        return None
    
    price = price_data["value_exc_vat"]
    if price >= threshold_high:
        return ColourResponse(colour="red")
    elif threshold_medium <= price < threshold_high:
        return ColourResponse(colour="yellow")
    elif threshold_low <= price < threshold_medium:
        return ColourResponse(colour="green")
    else:
        return ColourResponse(colour="blue")


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

@app.get("/", response_model=Optional[PricePoint])
async def get_current_price():
    """Endpoint to retrieve the current price point data."""
    price_data = retrieve_current_data()
    if price_data:
        return PricePoint(**price_data)
    raise HTTPException(status_code=404, detail="No current price data available.")


@app.get("/colour", response_model=Optional[ColourResponse])
async def get_colour():
    """Endpoint to retrieve the current price color based on thresholds."""
    price_data = retrieve_current_data()
    colour = determine_colour(price_data)
    if colour:
        return colour
    raise HTTPException(status_code=404, detail="No colour data available.")        



@app.get("/thresholds")
async def get_thresholds():
    """Endpoint to retrieve the current thresholds"""
    global threshold_high, threshold_medium, threshold_low
    return {"message": "Thresholds", "high": threshold_high, "medium": threshold_medium, "low": threshold_low}



# Endpoint to update threshold values
@app.put("/thresholds", dependencies=[Depends(api_key_auth)])
async def update_thresholds(thresholds: ThresholdUpdate):
    global threshold_high, threshold_medium, threshold_low
    
    if thresholds.high <= thresholds.medium or thresholds.medium <= thresholds.low:
        raise HTTPException(
            status_code=400, detail="Threshold values must follow high > medium > low."
        )
    threshold_high = thresholds.high
    threshold_medium = thresholds.medium
    threshold_low = thresholds.low
    return {"message": "Thresholds updated successfully", "high": threshold_high, "medium": threshold_medium, "low": threshold_low}


# Endpoint to receive status pings
@app.put("/providestatus")
async def provide_status(status_msg: StatusPing):
    return {"message": f"Status Received at {status_msg.time}"}


# Endpoint to receive help calls 
@app.put("/requesthelp") #TODO include an api key here
async def provide_status(request: SupportRequest):

    price_data = retrieve_current_data()
    
    if not price_data:
        price_data = "Could not retrieve price data"

    payload = {
        "To": request.tel,
        "Price": price_data["value_exc_vat"]
    }

    try:
        # Make the PUT request to the external API
        response = requests.put(WHATSAPPSENDER_API_URL, json=payload)
        response.raise_for_status()  # Raise error if the request failed
        return {"message": "Help request processed successfully", "code": response.status_code}
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to send help request: {str(e)}")

#    return {"message": f"Request received at {request.time}"}
