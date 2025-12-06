from google.adk.agents.llm_agent import Agent

# --- Train Tools ---
def search_train(origin: str, dest: str, date: str, day_part: str, pax: int) -> dict:
    """Search train schedule based on search parameters."""
    print(f"--- Tool: search_train called with origin={origin}, dest={dest}, date={date} ---")
    return {"code": "Argo Semeru 6", "departure": "6:20", "price": 585000}

def book_train(code: str, name: str) -> dict:
    """Book train ticket and return payment link."""
    print(f"--- Tool: book_train called with code={code}, name={name} ---")
    return {"status": "booked", "name": name, "payment_link": "http://sample.bayar.id"}

# --- Hotel Tools ---
def search_hotel(location: str, date: str, nights: int, guests: int) -> dict:
    """Search hotel availability based on location and dates."""
    print(f"--- Tool: search_hotel called with location={location}, date={date} ---")
    return {
        "hotels": [
            {"name": "Bali Resort & Spa", "price_per_night": 1500000, "rating": 4.5},
            {"name": "City Center Hotel", "price_per_night": 800000, "rating": 4.0}
        ]
    }

def book_hotel(hotel_name: str, room_type: str) -> dict:
    """Book a hotel room and return confirmation."""
    print(f"--- Tool: book_hotel called with hotel_name={hotel_name}, room_type={room_type} ---")
    return {"status": "booked", "hotel_name": hotel_name, "confirmation_code": "HTL-12345"}

# Create sub-agents
train_agent = Agent(
    name="train_agent",
    model="gemini-2.5-flash",
    description="Specialist for searching and booking trains.",
    instruction="You are a train travel specialist. Use 'search_train' to find schedules and 'book_train' to make bookings.",
    tools=[search_train, book_train],
)

hotel_agent = Agent(
    name="hotel_agent",
    model="gemini-2.5-flash",
    description="Specialist for searching and booking hotels.",
    instruction="You are a hotel booking specialist. Use 'search_hotel' to find accommodation and 'book_hotel' to make reservations.",
    tools=[search_hotel, book_hotel],
)

# Create root agent
root_agent = Agent(
    name="travel_agent_team",
    model="gemini-2.5-flash",
    description="Main travel coordinator. Delegates train tasks to train_agent and hotel tasks to hotel_agent.",
    instruction="You are a helpful travel agent team leader. "
                "You have two specialized sub-agents: "
                "1. 'train_agent': Handles train searches and bookings. "
                "2. 'hotel_agent': Handles hotel searches and bookings. "
                "Delegate user requests to the appropriate specialist. "
                "If the user asks for both, you can coordinate between them.",
    sub_agents=[train_agent, hotel_agent]
)
