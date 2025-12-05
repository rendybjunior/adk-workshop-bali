from google.adk.agents.llm_agent import Agent
from google.genai import types # For creating message Content/Parts
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools.tool_context import ToolContext

import asyncio
import logging
import os

logging.basicConfig(level=logging.ERROR)

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"
os.environ["GOOGLE_CLOUD_PROJECT"] = "workshop-adk-bali"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"


def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city."""
    print(f"--- Tool: get_weather called for city: {city} ---")
    city_normalized = city.lower().replace(" ", "")

    # Mock weather data
    mock_weather_db = {
        "newyork": {"status": "success", "report": "The weather in New York is sunny with a temperature of 25°C."},
        "london": {"status": "success", "report": "It's cloudy in London with a temperature of 15°C."},
        "tokyo": {"status": "success", "report": "Tokyo is experiencing light rain and a temperature of 18°C."},
    }

    if city_normalized in mock_weather_db:
        return mock_weather_db[city_normalized]
    else:
        return {"status": "error", "error_message": f"Sorry, I don't have weather information for '{city}'."}


def get_weather_stateful(city: str, tool_context: ToolContext) -> dict:
    """Retrieves weather, converts temp unit based on session state."""
    print(f"--- Tool: get_weather_stateful called for {city} ---")

    # --- Read preference from state ---
    preferred_unit = tool_context.state.get("user_preference_temperature_unit", "Celsius") # Default to Celsius
    print(f"--- Tool: Reading state 'user_preference_temperature_unit': {preferred_unit} ---")

    city_normalized = city.lower().replace(" ", "")

    # Mock weather data (always stored in Celsius internally)
    mock_weather_db = {
        "newyork": {"temp_c": 25, "condition": "sunny"},
        "london": {"temp_c": 15, "condition": "cloudy"},
        "tokyo": {"temp_c": 18, "condition": "light rain"},
    }

    if city_normalized in mock_weather_db:
        data = mock_weather_db[city_normalized]
        temp_c = data["temp_c"]
        condition = data["condition"]

        # Format temperature based on state preference
        if preferred_unit == "Fahrenheit":
            temp_value = (temp_c * 9/5) + 32 # Calculate Fahrenheit
            temp_unit = "°F"
        else: # Default to Celsius
            temp_value = temp_c
            temp_unit = "°C"

        report = f"The weather in {city.capitalize()} is {condition} with a temperature of {temp_value:.0f}{temp_unit}."
        result = {"status": "success", "report": report}
        print(f"--- Tool: Generated report in {preferred_unit}. Result: {result} ---")

        # Example of writing back to state (optional for this tool)
        tool_context.state["last_city_checked_stateful"] = city
        print(f"--- Tool: Updated state 'last_city_checked_stateful': {city} ---")

        return result
    else:
        # Handle city not found
        error_msg = f"Sorry, I don't have weather information for '{city}'."
        print(f"--- Tool: City '{city}' not found. ---")
        return {"status": "error", "error_message": error_msg}


# Create function that execute events in runner
async def call_agent_async(query: str, runner, user_id, session_id):
    """Sends a query to the agent and prints the final response."""
    content = types.Content(role='user', parts=[types.Part(text=query)])

    # RUNNER MAIN LOGIC: loop through events
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        # Key Concept: is_final_response() marks the concluding message for the turn.
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            else:
                final_response_text = f"No response. {event.error_message if event.error_message else ''}"
            break # Stop processing events once the final response is found

    return final_response_text


async def main():
    try:
        # Create agent
        weather_agent = Agent(
            name="weather_agent_v1",
            model="gemini-2.5-flash",
            description="Provides weather information for specific cities.",
            instruction="You are a helpful weather assistant. "
                        "When the user asks for the weather in a specific city, "
                        "use the 'get_weather' tool to find the information. "
                        "If the user asks for the weather without specifying a city, you assume they mean the last checked city"
                        "If the tool returns an error, inform the user politely. "
                        "If the tool is successful, present the weather report clearly.",
            tools=[get_weather_stateful],
        )

        # Create chat session
        APP_NAME = "weather_tutorial_app"
        USER_ID = "user_1"
        SESSION_ID = "session_001"
        session_service = InMemorySessionService() # store session memory
        initial_state = {
            "user_preference_temperature_unit": "Celsius"
        }
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID, # dummy fix user
            session_id=SESSION_ID, # dummy fix session
            state=initial_state
        )
        retrieved_session = await session_service.get_session(app_name=APP_NAME,
                                                         user_id=USER_ID,
                                                         session_id = SESSION_ID)
        print(f"Session retrieved: {retrieved_session}")

        # Create a runner that orchestrates the agent execution loop.
        runner = Runner(
            agent=weather_agent, # The agent we want to run
            app_name=APP_NAME,
            session_service=session_service
        )

        # Ask to the agent
        q = "What is the weather like in London?"
        print(f"User: {q}")
        result = await call_agent_async(q,
                                            runner=runner, user_id=USER_ID, session_id=SESSION_ID)
        print(f"Assistant: {result}")

        # Manually update state
        stored_session = session_service.sessions[APP_NAME][USER_ID][SESSION_ID]
        stored_session.state["user_preference_temperature_unit"] = "Fahrenheit"

        q = "How about New York?"
        print(f"User: {q}")
        result = await call_agent_async(q,
                                            runner=runner, user_id=USER_ID, session_id=SESSION_ID)
        print(f"Assistant: {result}")

        q = "How's the weather?"
        print(f"User: {q}")
        result = await call_agent_async(q,
                                            runner=runner, user_id=USER_ID, session_id=SESSION_ID)
        print(f"Assistant: {result}")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
