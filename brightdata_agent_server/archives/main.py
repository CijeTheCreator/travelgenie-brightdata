
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import asyncio
import os
import sys
# import os
import contextlib
import time


load_dotenv()


model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

server_params = StdioServerParameters(
    command="npx",
    env={
        "API_TOKEN": os.getenv("API_TOKEN"),
        "BROWSER_AUTH": os.getenv("BROWSER_AUTH"),
        "WEB_UNLOCKER_ZONE": os.getenv("WEB_UNLOCKER_ZONE"),
    },
    # Make sure to update to the full absolute path to your math_server.py file
    args=["@brightdata/mcp"],
)


async def initialize_bright_data_tools():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            return tools


async def chat_with_agent():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            start = time.time()
            print("Initializing Session")
            await session.initialize()
            print("Initializing tools")
            tools = await load_mcp_tools(session)
            print("Creating Agent")
            agent = create_react_agent(model, tools)

            # Start conversation history
            messages = [
                {
                    "role": "system",
                    "content": "You can use multiple tools in sequence to answer complex questions. Think step by step.",
                }
            ]

            print("Type 'exit' or 'quit' to end the chat.")
            user_input = "Go to https://www.google.com/ type \"Hello world\" into #APjFqb get all the links in the resulting page"
            # Add user message to history
            messages.append({"role": "user", "content": user_input})

            # Call the agent with the full message history

            print("Invoking Agent")
            agent_response = await agent.ainvoke({"messages": messages})

            # Extract agent's reply and add to history
            ai_message = agent_response["messages"][-1].content
            print(f"Agent: {ai_message}")
            end = time.time()
            print("\n\n Spent about:")
            print(f"Time taken: {end - start:.4f} seconds")


@contextlib.contextmanager
def suppress_stderr():
    with open(os.devnull, 'w') as devnull:
        old_stderr = sys.stderr
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stderr = old_stderr


if __name__ == "__main__":
    with suppress_stderr():
        asyncio.run(chat_with_agent())
    import gc
    gc.collect()
