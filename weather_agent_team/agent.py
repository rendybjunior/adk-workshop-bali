from google.adk.agents.llm_agent import Agent
from google.genai import types # For creating message Content/Parts
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from typing import Optional

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

def say_hello(name: Optional[str] = None) -> str: # MODIFIED SIGNATURE
    """Provides a simple greeting. If a name is provided, it will be used."""
    if name:
        print(f"--- Tool: say_hello called with name: {name} ---")
        return f"Hello, {name}!"
    else:
        print(f"--- Tool: say_hello called without a specific name (name_arg_value: {name}) ---")
        return "Hello there!"

def say_goodbye() -> str:
    """Provides a simple farewell message to conclude the conversation."""
    print(f"--- Tool: say_goodbye called ---")
    return "Goodbye! Have a great day."


async def main():
    try:
        # Create agent
        greeting_agent = Agent(
            name="greeting_agent",
            model="gemini-2.5-flash",
            description="Handles simple greetings and hellos using the 'say_hello' tool.",
            tools=[say_hello],
        )

        farewell_agent = Agent(
            name="farewell_agent",
            model="gemini-2.5-flash",
            description="Handles simple farewells and goodbyes using the 'say_goodbye' tool.",
            tools=[say_goodbye],
        )

        weather_agent_team = Agent(
            name="weather_agent_team", # Give it a new version name
            model="gemini-2.5-flash",
            description="The main coordinator agent. Handles weather requests and delegates greetings/farewells to specialists.",
            instruction="You are the main Weather Agent coordinating a team. Your primary responsibility is to provide weather information. "
                        "Use the 'get_weather' tool ONLY for specific weather requests (e.g., 'weather in London'). "
                        "You have specialized sub-agents: "
                        "1. 'greeting_agent': Handles simple greetings like 'Hi', 'Hello'. Delegate to it for these. "
                        "2. 'farewell_agent': Handles simple farewells like 'Bye', 'See you'. Delegate to it for these. "
                        "Analyze the user's query. If it's a greeting, delegate to 'greeting_agent'. If it's a farewell, delegate to 'farewell_agent'. "
                        "If it's a weather request, handle it yourself using 'get_weather'. "
                        "For anything else, respond appropriately or state you cannot handle it.",
            tools=[get_weather], # Root agent still needs the weather tool for its core task
            # Key change: Link the sub-agents here!
            sub_agents=[greeting_agent, farewell_agent]
        )

        # Create chat session
        session_service = InMemorySessionService()
        APP_NAME = "weather_tutorial_agent_team"
        USER_ID = "user_1_agent_team"
        SESSION_ID = "session_001_agent_team"
        session = await session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
        )
        print(f"Session created: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'")

        runner_agent_team = Runner(
            agent=weather_agent_team,
            app_name=APP_NAME,
            session_service=session_service
        )
        print(f"Runner created for agent '{weather_agent_team.name}'.")

        # --- Interactions using await (correct within async def) ---
        result = await call_agent_async(query = "Hello there!",
                               runner=runner_agent_team, user_id=USER_ID, session_id=SESSION_ID)
        print(result)

        result = await call_agent_async(query = "What is the weather in New York?",
                               runner=runner_agent_team, user_id=USER_ID, session_id=SESSION_ID)
        print(result)

        result = await call_agent_async(query = "Thanks, bye!",
                               runner=runner_agent_team, user_id=USER_ID, session_id=SESSION_ID)
        print(result)
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
