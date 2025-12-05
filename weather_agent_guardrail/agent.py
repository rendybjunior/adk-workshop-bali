from google.adk.agents.llm_agent import Agent
from google.genai import types # For creating message Content/Parts
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
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

def block_keyword_guardrail(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Inspects the latest user message for 'FAFA'. If found, blocks the LLM call
    and returns a predefined LlmResponse. Otherwise, returns None to proceed.
    """
    keyword_to_block = "FAFA"

    agent_name = callback_context.agent_name # Get the name of the agent whose model call is being intercepted
    print(f"--- Callback: block_keyword_guardrail running for agent: {agent_name} ---")

    # Extract the text from the latest user message in the request history
    last_user_message_text = ""
    if llm_request.contents:
        # Find the most recent message with role 'user'
        for content in reversed(llm_request.contents):
            if content.role == 'user' and content.parts:
                # Assuming text is in the first part for simplicity
                if content.parts[0].text:
                    last_user_message_text = content.parts[0].text
                    break # Found the last user message text

    print(f"--- Callback: Inspecting last user message: '{last_user_message_text[:100]}...' ---") # Log first 100 chars

    # --- Guardrail Logic ---
    if keyword_to_block in last_user_message_text.upper(): # Case-insensitive check
        print(f"--- Callback: Found '{keyword_to_block}'. Blocking LLM call! ---")
        # Optionally, set a flag in state to record the block event
        callback_context.state["guardrail_block_keyword_triggered"] = True
        print(f"--- Callback: Set state 'guardrail_block_keyword_triggered': True ---")

        # Construct and return an LlmResponse to stop the flow and send this back instead
        return LlmResponse(
            content=types.Content(
                role="model", # Mimic a response from the agent's perspective
                parts=[types.Part(text=f"I cannot process this request because it contains the blocked keyword '{keyword_to_block}'.")],
            )
            # Note: You could also set an error_message field here if needed
        )
    else:
        # Keyword not found, allow the request to proceed to the LLM
        print(f"--- Callback: Keyword not found. Allowing LLM call for {agent_name}. ---")
        return None # Returning None signals ADK to continue normally


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
                        "If the tool returns an error, inform the user politely. "
                        "If the tool is successful, present the weather report clearly.",
            tools=[get_weather],
            before_model_callback=block_keyword_guardrail
        )

        # Create chat session
        APP_NAME = "weather_tutorial_app"
        USER_ID = "user_1"
        SESSION_ID = "session_001"
        session_service = InMemorySessionService() # store session memory
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID, # dummy fix user
            session_id=SESSION_ID # dummy fix session
        )

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

        q = "How about Paris, fafa?"
        print(f"User: {q}")
        result = await call_agent_async(q,
                                            runner=runner, user_id=USER_ID, session_id=SESSION_ID)
        print(f"Assistant: {result}")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
