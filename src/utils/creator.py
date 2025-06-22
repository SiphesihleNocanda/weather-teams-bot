import asyncio, os, argparse
from teams.ai.planners import AssistantsPlanner
from openai.types.beta import AssistantCreateParams
from openai.types.beta.function_tool_param import FunctionToolParam
from openai.types.shared_params import FunctionDefinition
from dotenv import load_dotenv

load_dotenv(f'{os.getcwd()}/env/.env.local.user', override=True)

def load_keys_from_args():
    parser = argparse.ArgumentParser(description='Load keys from command input parameters.')
    parser.add_argument('--api-key', type=str, required=True)
    return parser.parse_args()

async def main():
    args = load_keys_from_args()

    assistant_params = AssistantCreateParams(
        name="Weatheragent_sphe",
        instructions=("""
You are a delightful assistant/meteorologist. \

When you receive weather data from getCurrentWeather, format it like this but still be creative and punny:  
    "The current weather in {location} is {adjective}, with a temperature of about {temperature}°C.
The sky shows {condition}, and winds are around {wind_speed} m/s.
🌅 Sunrise was at {sunrise_time}, and 🌇 sunset will be at {sunset_time}.
Enjoy your day in {location} and stay safe!!”

                      
When you have a 5-day forecast from get5DayForecast format it like this:
     “Here’s the forecast for the next 5 days in {location}:  
 • {day}: Around {temp}°C with {condition}, {pop}% chance of precipitation, and winds at {wind_speed} m/s.  
 • {nextDay}: …  
 (and so on for all five days)  
> It looks like a {overall_summary}. Have a great week and stay safe!” 

Always include the **precipitation chance** (`pop`) after the condition. \
                      
Use synonyms and friendly adjectives ("pleasant", "brisk", "balmy","sunny", "cold", etc) to describe the temperature. \
Use emojis to describe the temperature for the specific location, can use {condition} to determine which emojis to use. \
Suggest how the user should approach the weather for that given location. \

• Call **getCurrentWeather** for live conditions \
• Call **get5DayForecast** for a 5-day outlook \
• Call **getQuoteOfTheDay** to fetch a random quote \

When the user says “hi”, “hello” or “hey”, respond exactly with:  
    “Hi there! What can I do for you today?  
     • A motivational quote for some food-for-thought
     • Current weather for any city  
     • A 5-day forecast” \

If the user asks for anything else, reply:  
  “Sorry, I can only provide current weather, a 5-day forecast, or a motivational quote.” \

Keep it punny, upbeat and creative! \
"""),
        tools=[
            {
                "type": "code_interpreter",
            },
            FunctionToolParam(
                type="function",
                function=FunctionDefinition(
                    name="getCurrentWeather",
                    description="Determine weather in a given location",
                    parameters={
                        "type": "object",
                        "properties": {
                            "location": {
                            "type": "string",
                            "description": "Return live weather for location eg. Johannesburg, South Africa : temperature, condition, wind_speed, sunrise_time, sunset_time"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["c", "f"],
                            "default": "c"
                        }
                    },
                    "required": ["location"]
                }),
            ),
            FunctionToolParam(
                type="function",
                function=FunctionDefinition(
                    name="get5DayForecast",
                    description="Get a 5 day forecast for a given location",
                    parameters={
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "Return 5 day forecast for location eg. Johannesburg, South Africa : temperature, condition, pop(chance of precipitation) wind_speed"
                            }
                        },
                        "required": ["location"]
                    }
                )
            ),
            FunctionToolParam(
                type="function",
                function=FunctionDefinition(
                    name="getQuoteOfTheDay",
                    description="Return a random motivational quote and its author",
                    parameters={
                        "type": "object",
                        "properties": {},
                        "required": []
                }),
            ),
        ],
        model="gpt-4.1-mini",
    )

    assistant = await AssistantsPlanner.create_assistant(
        api_key=args.api_key,
        azure_ad_token_provider=None, 
        api_version="",
        organization="",       
        endpoint="",
        request=assistant_params
    )
    print(assistant.tools)
    print(f"Created assistant with ID: {assistant.id}")

asyncio.run(main())