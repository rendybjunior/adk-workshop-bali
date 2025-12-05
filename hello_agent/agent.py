from google.adk.agents.llm_agent import Agent
from google.adk.tools import google_search

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description="News agent",
    instruction="You are an agent that provide recent news",
    tools=[google_search],
)
