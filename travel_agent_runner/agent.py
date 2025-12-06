from google.adk.agents.llm_agent import Agent
from google.genai import types
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

import asyncio
import logging
import os

logging.basicConfig(level=logging.ERROR)

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"
os.environ["GOOGLE_CLOUD_PROJECT"] = "workshop-adk-bali"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"


def search_train(origin: str, dest: str, date: str, day_part: str, pax: int) -> dict:
    """Search train schedule berdasarkan parameter pencarian."""
    print(f"--- Tool: search_train called for {origin} to {dest} on {date} ---")
    return {"code": "Argo Semeru 6", "departure": "6:20", "price": 585000}

def book_train(code: str, name: str) -> dict:
    """Booking tiket kereta lalu mengembalikan pranala pembayaran."""
    print(f"--- Tool: book_train called for {code} by {name} ---")
    return {"status": "booked", "name": name, "payment_link":"http://sample.bayar.id"}


async def call_agent_async(query: str, runner, user_id, session_id):
    """Sends a query to the agent and prints the final response."""
    content = types.Content(role='user', parts=[types.Part(text=query)])

    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            else:
                final_response_text = f"No response. {event.error_message if event.error_message else ''}"
            break

    return final_response_text


async def main():
    try:
        # Create agent
        root_agent = Agent(
            model='gemini-2.5-flash',
            name='root_agent',
            description="Travel agent",
            instruction="You are a helpful travel agent for search and booking train.",
            tools=[search_train, book_train],
        )

        # Create chat session
        APP_NAME = "travel_agent_app"
        USER_ID = "user_1"
        SESSION_ID = "session_001"
        session_service = InMemorySessionService()
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID
        )

        # Create runner
        runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_service
        )

        # Ask to the agent
        q = "Saya mau cari kereta dari Gambir ke Bandung untuk 1 jan 2026 pagi buat 2 orang"
        print(f"User: {q}")
        result = await call_agent_async(q, runner=runner, user_id=USER_ID, session_id=SESSION_ID)
        print(f"Assistant: {result}")

        q = "Tolong booking ya atas nama Zulkifli dan Verrell"
        print(f"User: {q}")
        result = await call_agent_async(q, runner=runner, user_id=USER_ID, session_id=SESSION_ID)
        print(f"Assistant: {result}")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
