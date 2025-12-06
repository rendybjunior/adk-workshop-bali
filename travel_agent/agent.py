from google.adk.agents.llm_agent import Agent

def search_train(origin: str, dest: str, date: str, day_part: str, pax: int) -> dict:
    """Search train schedule berdasarkan parameter pencarian."""
    return {"code": "Argo Semeru 6", "departure": "6:20", "price": 585000}

def book_train(code: str, name: str) -> dict:
    """Booking tiket kereta lalu mengembalikan pranala pembayaran."""
    return {"status": "booked", "name": name, "payment_link":"http://sample.bayar.id"}

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description="Travel agent",
    instruction="You are a helpful travel agent for search and booking train.",
    # TODO tools=[...],
)
