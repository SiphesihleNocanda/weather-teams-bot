import os
import aiohttp
from datetime import datetime
import sys
import traceback
import json
from typing import Any, Dict, Optional
from dataclasses import asdict

from botbuilder.core import MemoryStorage, TurnContext
from teams import Application, ApplicationOptions, TeamsAdapter
from teams.ai import AIOptions
from teams.ai.planners import AssistantsPlanner, OpenAIAssistantsOptions, AzureOpenAIAssistantsOptions
from teams.state import TurnState
from teams.feedback_loop_data import FeedbackLoopData

from config import Config

config = Config()

planner = AssistantsPlanner[TurnState](
    OpenAIAssistantsOptions(api_key=config.OPENAI_API_KEY, assistant_id=config.OPENAI_ASSISTANT_ID)
)

# Define storage and application
storage = MemoryStorage()
bot_app = Application[TurnState](
    ApplicationOptions(
        bot_app_id=config.APP_ID,
        storage=storage,
        adapter=TeamsAdapter(config),
        ai=AIOptions(planner=planner, enable_feedback_loop=True),
    )
)
    
@bot_app.ai.action("getCurrentWeather")
async def get_current_weather(context: TurnContext, state: TurnState):
    loc  = context.data.get("location")
    unit = context.data.get("unit", "c").lower()
    units = "metric" if unit == "c" else "imperial"
    key  = os.getenv("OPENWEATHER_API_KEY")

    async with aiohttp.ClientSession() as session:
        resp = await session.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": loc, "units": units, "appid": key}
        )
    if resp.status != 200:
        return json.dumps({"error": f"Could not fetch weather for {loc}"})

    data = await resp.json()

    # grab raw UNIX times
    sr_ts = data["sys"]["sunrise"]
    ss_ts = data["sys"]["sunset"]
    # format into hh:mm (server local time)
    sr_str = datetime.fromtimestamp(sr_ts).strftime("%H:%M")
    ss_str = datetime.fromtimestamp(ss_ts).strftime("%H:%M")
    payload = {
        "location":    loc,
        "temperature": data["main"]["temp"],
        "condition":   data["weather"][0]["description"],
        "wind_speed":  data["wind"]["speed"],
        "sunrise_time": sr_str,
        "sunset_time":  ss_str
    }
    return json.dumps(payload)
    

@bot_app.ai.action("getQuoteOfTheDay")
async def get_quote_of_the_day(context: TurnContext, state: TurnState):
    key = config.API_NINJAS_API_KEY
    url = "https://api.api-ninjas.com/v1/quotes"
    headers = {"X-Api-Key": key}

    async with aiohttp.ClientSession() as session:
        resp = await session.get(url, headers=headers)
    if resp.status != 200:
        return json.dumps({"error": "Couldn’t fetch a quote right now."})

    data = await resp.json()
    # API returns a list of quote objects; pick the first one
    # e.g. [ { "quote":"…", "author":"…", "category":"…" } ]
    quote_obj = data[0] if isinstance(data, list) and data else {}
    return json.dumps({
        "quote":  quote_obj.get("quote", "No quote found."),
        "author": quote_obj.get("author", "Unknown")
    })


from datetime import datetime
# … other imports …

@bot_app.ai.action("get5DayForecast")
async def get_5day_forecast(context: TurnContext, state: TurnState):
    loc = context.data.get("location")
    key = os.getenv("OPENWEATHER_API_KEY")
    async with aiohttp.ClientSession() as session:
        resp = await session.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={"q": loc, "units": "metric", "appid": key}
        )
    if resp.status != 200:
        return json.dumps({"error": f"Could not fetch 5-day forecast for {loc}"})

    data = await resp.json()

    # 1) Pick the daily 12:00 snapshot, up to 5 days
    midday_items = [
        item for item in data.get("list", [])
        if item.get("dt_txt", "").endswith("12:00:00")
    ][:5]

    # 2) Build labeled forecast
    today = datetime.utcnow().date()
    forecast = []
    for item in midday_items:
        # parse the timestamp string
        dt = datetime.strptime(item["dt_txt"], "%Y-%m-%d %H:%M:%S")
        label = "Today" if dt.date() == today else dt.strftime("%A")
        forecast.append({
            "day":        label,
            "temp":       item["main"]["temp"],
            "condition":  item["weather"][0]["description"],
            "pop":        item.get("pop", 0),
            "wind_speed": item["wind"]["speed"]
        })

    return json.dumps({"location": loc, "forecast": forecast})


@bot_app.error
async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")

@bot_app.feedback_loop()
async def feedback_loop(_context: TurnContext, _state: TurnState, feedback_loop_data: FeedbackLoopData):
    # Add custom feedback process logic here.
    print(f"Your feedback is:\n{json.dumps(asdict(feedback_loop_data), indent=4)}")