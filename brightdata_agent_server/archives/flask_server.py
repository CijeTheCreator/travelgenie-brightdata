from flask import Flask, request, jsonify
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import asyncio
import os
import sys
import contextlib
import time
import gc
from concurrent.futures import ThreadPoolExecutor
import nest_asyncio

# Allow nested event loops (required for Flask + asyncio)
nest_asyncio.apply()

load_dotenv()

app = Flask(__name__)

# Global variables to store initialized components
agent = None
session = None
read_stream = None
write_stream = None
stdio_context = None
session_context = None

# Initialize model
model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# Server parameters
server_params = StdioServerParameters(
    command="npx",
    env={
        "API_TOKEN": os.getenv("API_TOKEN"),
        "BROWSER_AUTH": os.getenv("BROWSER_AUTH"),
        "WEB_UNLOCKER_ZONE": os.getenv("WEB_UNLOCKER_ZONE"),
    },
    args=["@brightdata/mcp"],
)


@contextlib.contextmanager
def suppress_stderr():
    with open(os.devnull, 'w') as devnull:
        old_stderr = sys.stderr
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stderr = old_stderr


async def initialize_service():
    """Initialize the MCP session and agent once at startup"""
    global agent, session, stdio_context, session_context, read_stream, write_stream

    try:
        print("Initializing MCP service...")

        # Create stdio client context
        stdio_context = stdio_client(server_params)
        read_stream, write_stream = await stdio_context.__aenter__()

        # Create session context
        session_context = ClientSession(read_stream, write_stream)
        session = await session_context.__aenter__()

        print("Initializing Session...")
        await session.initialize()

        print("Loading tools...")
        tools = await load_mcp_tools(session)

        print("Creating Agent...")
        agent = create_react_agent(model, tools)

        print("MCP service initialized successfully!")
        return True

    except Exception as e:
        print(f"Failed to initialize service: {str(e)}")
        return False


def run_async_in_thread(coro):
    """Run async function in a thread with its own event loop"""
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    with ThreadPoolExecutor() as executor:
        future = executor.submit(run_in_thread)
        return future.result()


async def invoke_agent_async(user_input):
    """Async function to invoke the agent"""
    global agent

    if agent is None:
        raise Exception("Service not initialized")

    try:
        start = time.time()

        # Create message history
        messages = [
            {
                "role": "system",
                "content": "You can use multiple tools in sequence to answer complex questions. Think step by step.",
            },
            {"role": "user", "content": user_input}
        ]

        print(f"Invoking Agent with input: {user_input[:100]}...")

        # Call the agent
        agent_response = await agent.ainvoke({"messages": messages})

        # Extract agent's reply
        ai_message = agent_response["messages"][-1].content

        end = time.time()
        processing_time = end - start

        print(f"Agent response completed in {processing_time:.4f} seconds")

        return {
            "success": True,
            "response": ai_message,
            "processing_time": processing_time,
            "user_input": user_input
        }

    except Exception as e:
        print(f"Error invoking agent: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "user_input": user_input
        }


@app.route('/invoke', methods=['POST'])
def invoke_agent():
    """Flask endpoint to invoke the agent"""
    try:
        # Get user input from request body
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        user_input = data.get('user_input', '')

        if not user_input:
            return jsonify({"error": "user_input is required"}), 400

        # Check if service is initialized
        if agent is None:
            return jsonify({"error": "Service not initialized"}), 500

        print("Request received and validated")
        # Run the async function in a thread
        result = run_async_in_thread(invoke_agent_async(user_input))

        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 500

    except Exception as e:
        print(f"Error in invoke endpoint: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy" if agent is not None else "not_initialized",
        "service": "MCP Agent API"
    })


@app.route('/status', methods=['GET'])
def status():
    """Status endpoint"""
    return jsonify({
        "initialized": agent is not None,
        "model": "gemini-2.0-flash",
        "service": "MCP Agent API"
    })


def cleanup_service():
    """Cleanup function to properly close connections"""
    global session_context, stdio_context, session

    try:
        if session_context:
            asyncio.run(session_context.__aexit__(None, None, None))
        if stdio_context:
            asyncio.run(stdio_context.__aexit__(None, None, None))
        print("Service cleanup completed")
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")


if __name__ == "__main__":
    print("Starting MCP Agent Flask API...")

    # Initialize the service
    with suppress_stderr():
        success = run_async_in_thread(initialize_service())

    if not success:
        print("Failed to initialize service. Exiting.")
        sys.exit(1)

    try:
        # Start Flask app
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except Exception as e:
        print(f"\nCAUGHT:    {str(e)}")
    finally:
        cleanup_service()
        gc.collect()
