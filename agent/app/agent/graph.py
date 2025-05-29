import operator
import os
from typing import Literal, TypedDict, Any, Annotated
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import StreamWriter, interrupt, Send
from langchain_core.messages import ToolMessage, SystemMessage
from langchain_core.tools import tool
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import ToolNode, tools_condition
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
import random
import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


system_message = """
You are a travel planning assistant.
Your primary role is to help users organize and plan their travel itineraries efficiently.

Follow these steps to assist the user:

    Ask for the origin and destination locations, along with the travel dates.

    Retrieve the location code and destination ID's of the required cities

    Use the Flight Price Tool to retrieve airfare details with the location codes.

    Use the Hotel Pricing Tool to find accommodation costs at the destination with the destination ids.

    Calculate the total estimated trip cost.

    Use the Currency Conversion Tool to convert the total into the user’s local currency.

    Get sentiment about the location for the user

    Get things to do at the location for the user

    Get Visa requirements for the user

    Generate a travel calendar using the Calendar Tool.

    Present the complete travel plan to the user, including the itinerary and calendar.

If the user is not looking for a full travel plan, assist them with specific travel-related queries using the available tools.
If a request falls outside the scope of travel planning, respond politely and decline.

When generating the travel plan, you must always include sentiment, things to do and visa requirements

"""


load_dotenv()

# MCP servers to connect to
mcp_servers = {

    "travelgenie": {
        "url": os.getenv("TRAVELGENIE_MCP_URL"),
        "transport": "sse",
    },

    # "brightdata": {
    #     "command": "npx",
    #     "args": ["@brightdata/mcp"],
    #     "env": {
    #         "API_TOKEN": os.getenv("API_TOKEN"),
    #         "BROWSER_AUTH": os.getenv("BROWSER_AUTH"),
    #         "WEB_UNLOCKER_ZONE": os.getenv("WEB_UNLOCKER_ZONE"),
    #     },
    #     "transport": "stdio",
    # }
    #
}

# Global variable to store MCP servers and their tools. Populated by initialize_mcp_tools()
mcp_servers_with_tools = {}
# Global variable to store tool name to server name mapping
tool_to_server_lookup = {}


class Weather(TypedDict):
    location: str
    search_status: str
    result: str


class State(MessagesState):
    weather_forecast: Annotated[list[Weather], operator.add]


class WeatherInput(TypedDict):
    location: str
    tool_call_id: str


class ToolNodeArgs(TypedDict):
    name: str
    args: dict[str, Any]
    id: str


class McpToolNodeArgs(TypedDict):
    server_name: str
    name: str
    args: dict[str, Any]
    id: str


@tool
async def weather_tool(query: str) -> str:
    """Call to get current weather"""
    return "Sunny"


@tool
async def create_reminder_tool(reminder_text: str) -> str:
    """Call to create a reminder"""
    return "Reminder created"


async def weather(input: WeatherInput, writer: StreamWriter):
    location = input["args"]["query"]

    # Send custom event to the client. It will update the state of the last checkpoint and all child nodes.
    # Note: if there are multiple child nodes (e.g. parallel nodes), the state will be updated for all of them.
    writer({"weather_forecast": [
           {"location": location, "search_status": f"Checking weather in {location}"}]})

    await asyncio.sleep(2)
    weather = random.choice(["Sunny", "Cloudy", "Rainy", "Snowy"])

    return {"messages": [ToolMessage(content=weather, tool_call_id=input["id"])], "weather_forecast": [{"location": location, "search_status": "", "result": weather}]}


async def reminder(input: ToolNodeArgs):
    res = interrupt(input['args']['reminder_text'])

    tool_answer = "Reminder created." if res == 'approve' else "Reminder creation cancelled by user."

    return {"messages": [ToolMessage(content=tool_answer, tool_call_id=input["id"])]}


async def mcp_tool(input: McpToolNodeArgs):
    if input["server_name"] not in mcp_servers:
        raise ValueError(
            f"Server with name {input['server_name']} not found in MCP servers list")

    protocol = mcp_servers[input["server_name"]]["transport"]

    tool_result = None
    if protocol == "sse":
        async with sse_client(mcp_servers[input["server_name"]]["url"]) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                tool_result = await session.call_tool(input["name"], input["args"])
    elif protocol == "stdio":
        server_params = StdioServerParameters(
            command=mcp_servers[input["server_name"]]["command"],
            args=mcp_servers[input["server_name"]]["args"],
            env=mcp_servers[input["server_name"]]["env"],
        )
        async with stdio_client(server_params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                tool_result = await session.call_tool(input["name"], input["args"])

    if not tool_result or tool_result.isError or not tool_result.content:
        return {"messages": [ToolMessage(content="Error calling tool", tool_call_id=input["id"])]}

    return {"messages": [ToolMessage(content=tool_result.content[0].text, tool_call_id=input["id"])]}


async def chatbot(state: State):

    tools = [tool for tools_list in mcp_servers_with_tools.values()
             for tool in tools_list]

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    ).bind_tools(tools)

    messages = state["messages"]
    messages = [SystemMessage(system_message)] + messages
    response = await llm.ainvoke(state["messages"])
    return {"messages": [response]}


# Chatbot node router. Based on tool calls, creates the list of the next parallel nodes.
def assign_tool(state: State) -> Literal["mcp_tool", "__end__"]:
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        send_list = []
        for tool in last_message.tool_calls:
            if any(tool["name"] == mcp_tool.name for mcp_tool in [tool for tools_list in mcp_servers_with_tools.values() for tool in tools_list]):
                server_name = tool_to_server_lookup.get(tool["name"], None)
                args = McpToolNodeArgs(
                    server_name=server_name,
                    name=tool["name"],
                    args=tool["args"],
                    id=tool["id"]
                )
                send_list.append(Send('mcp_tool', args))
        return send_list if len(send_list) > 0 else "__end__"
    return "__end__"


async def initialize_mcp_tools():
    global mcp_servers_with_tools, tool_to_server_lookup
    try:
        async with MultiServerMCPClient(mcp_servers) as client:
            mcp_servers_with_tools = client.server_name_to_tools
            tool_to_server_lookup = {}
            for server_name, tools in mcp_servers_with_tools.items():
                for tool in tools:
                    tool_to_server_lookup[tool.name] = server_name
    except Exception as e:
        print(f"Error initializing MCP tools: {str(e)}")


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


async def init_agent(use_mcp: bool):
    if use_mcp:
        await initialize_mcp_tools()

    builder = StateGraph(State)

    builder.add_node("chatbot", chatbot)
    builder.add_node("mcp_tool", mcp_tool)

    builder.add_edge(START, "chatbot")
    builder.add_conditional_edges("chatbot", assign_tool)
    builder.add_edge("mcp_tool", "chatbot")

    builder.add_edge("chatbot", END)

    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)
    graph.name = "LangGraph Agent"
    return graph
