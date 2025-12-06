import json
import os
import asyncio
import logging
from google.adk.agents.llm_agent import Agent
try:
    from google.adk.agents import SequentialAgent
except ImportError:
    try:
        from google.adk.agents.sequential_agent import SequentialAgent
    except ImportError:
        print("Could not import SequentialAgent. Please check the library version.")
        raise
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

logging.basicConfig(level=logging.ERROR)

# Ensure environment variables are set (assuming they are already set in the environment or .env)
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"
os.environ["GOOGLE_CLOUD_PROJECT"] = "workshop-adk-bali"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"

def read_posts() -> str:
    """Reads social media posts from the JSON file."""
    print("--- Tool: read_posts called ---")
    file_path = os.path.join(os.path.dirname(__file__), 'posts.json')
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return json.dumps(data, indent=2)
    except FileNotFoundError:
        return "Error: posts.json file not found."

# --- Agents ---

# 1. Summarization Agent
summarization_agent = Agent(
    name="summarization_agent",
    model="gemini-2.5-flash",
    description="Summarizes social media posts.",
    instruction="You are a social media analyst. Your goal is to read the posts using 'read_posts' tool and provide a comprehensive summary of the content, identifying key themes and trends.",
    tools=[read_posts],
    output_key="summary"
)

# 2. Creation Agent
creation_agent = Agent(
    name="creation_agent",
    model="gemini-2.5-flash",
    description="Creates new social media content.",
    instruction="You are a creative content creator. Based on the summary provided by the previous agent in {summary}, draft 3 distinct and engaging social media posts about food. Make them catchy and use emojis.",
    output_key="drafts",
    # No tools needed, relies on context/input
)

# 3. Publisher Agent
publisher_agent = Agent(
    name="publisher_agent",
    model="gemini-2.5-flash",
    description="Selects the best content for publication.",
    instruction="You are a social media manager targeting a teenager audience. Review the 3 drafts provided by the previous agent in {drafts}. Select the ONE best post that would appeal most to teenagers. Explain your reasoning and then present the final selected post clearly.",
    # No tools needed, relies on context/input
)

# --- Sequential Agent ---
root_agent = SequentialAgent(
    name="socmed_root_agent",
    description="Sequential agent for social media workflow.",
    # TODO sub_agents=[...]
)

# --- Execution Helper ---
async def call_agent_async(query: str, runner, user_id, session_id):
    """Sends a query to the agent and prints the final response."""
    content = types.Content(role='user', parts=[types.Part(text=query)])

    final_response_text = ""
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        print(f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}")

        if event.is_final_response() and event.author == 'publisher_agent':
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            else:
                final_response_text = f"No response. {event.error_message if event.error_message else ''}"
            break
    return final_response_text

async def main():
    try:
        # Session Setup
        session_service = InMemorySessionService()
        APP_NAME = "socmed_app"
        USER_ID = "user_socmed"
        SESSION_ID = "session_socmed_01"
        
        await session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
        )
        print(f"Session created: {SESSION_ID}")

        # Runner
        runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_service
        )
        print(f"Runner created for agent '{root_agent.name}'.")

        # Trigger the workflow
        query = "Please start the social media content workflow."
        print(f"\nUser: {query}\n")
        
        # In a SequentialAgent, the runner should handle the chaining. 
        # The user query goes to the first agent, its output goes to the second, etc.
        # However, ADK's SequentialAgent implementation details might vary. 
        # Usually, the 'root_agent' handles the orchestration internally when `run` is called.
        
        result = await call_agent_async(query, runner, USER_ID, SESSION_ID)
        print(f"\nFinal Result:\n{result}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
