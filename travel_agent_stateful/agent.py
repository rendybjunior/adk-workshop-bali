from google.adk.agents.llm_agent import Agent
from google.genai import types
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


def search_train(dest: str, date: str, day_part: str, pax: int, tool_context: ToolContext, origin: str = None) -> dict:
    """Search train schedule berdasarkan parameter pencarian.
    
    Args:
        dest: Kota tujuan.
        date: Tanggal keberangkatan.
        day_part: Waktu keberangkatan (pagi/siang/sore/malam).
        pax: Jumlah penumpang.
        tool_context: Context tool untuk akses state.
        origin: Kota asal (opsional). Jika tidak diisi, akan menggunakan data dari history perjalanan terakhir.
    """
    
    # Logic: If origin is missing, retrieve last_traveled_city from tool_context.state
    if not origin:
        origin = tool_context.state.get("last_traveled_city")
        print(f"--- Tool: Using default origin from state: {origin} ---")
    
    print(f"--- Tool: search_train called for {origin} to {dest} on {date} ---")
    
    if not origin:
         return {"error": "Origin city is missing and no history found."}

    return {"code": "Argo Semeru 6", "departure": "6:20", "price": 585000, "origin": origin, "destination": dest}

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
            instruction="You are a helpful travel agent for search and booking train. "
                        "If the user does not specify the origin city, assume they are traveling from their last traveled city in {last_traveled_city}.",
            tools=[search_train, book_train],
        )

        # Create chat session
        APP_NAME = "travel_agent_stateful_app"
        USER_ID = "user_1"
        SESSION_ID = "session_001"
        session_service = InMemorySessionService()
        
        # Initialize state with Jakarta as the last_traveled_city
        # initial_state = {"...": "..."}
        
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID,
            # TODO state=...
        )

        # Create runner
        runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_service
        )

        # Ask to the agent - omitting origin to test state usage
        q = "Saya mau cari kereta ke Bandung untuk 1 jan 2026 pagi buat 2 orang"
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
