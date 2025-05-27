# Flask app take 4

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
from threading import Thread
import json

load_dotenv()

app = Flask(__name__)

# Initialize model and server parameters
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


async def chat_with_agent(user_input):
    """Modified chat_with_agent function that accepts user input as parameter"""
    try:
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

                # Add user message to history
                messages.append({"role": "user", "content": user_input})

                # Call the agent with the full message history
                print("Invoking Agent")
                agent_response = await agent.ainvoke({"messages": messages})

                # Extract agent's reply and add to history
                ai_message = agent_response["messages"][-1].content
                print(f"Agent: {ai_message}")

                end = time.time()
                execution_time = end - start
                print(f"Time taken: {execution_time:.4f} seconds")

                return {
                    "response": ai_message,
                    "execution_time": execution_time
                }
    except Exception as e:
        print(f"Error in chat_with_agent: {str(e)}")
        import traceback
        traceback.print_exc()
        raise e


def run_async_chat(user_input):
    """Wrapper function to run the async chat function"""
    import threading
    import concurrent.futures

    def run_in_thread():
        """Run the async function in a separate thread with its own event loop"""
        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                with suppress_stderr():
                    result = loop.run_until_complete(
                        chat_with_agent(user_input))
                    return result
            finally:
                # Wait for all tasks to complete before closing
                pending = asyncio.all_tasks(loop)
                if pending:
                    loop.run_until_complete(asyncio.gather(
                        *pending, return_exceptions=True))
                loop.close()

        except Exception as e:
            print(f"Error in thread execution: {str(e)}")
            raise e
        finally:
            gc.collect()

    # Run in a separate thread to avoid event loop conflicts
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_in_thread)
        try:
            result = future.result(timeout=300)  # 5 minute timeout
            return result
        except concurrent.futures.TimeoutError:
            raise Exception("Chat agent execution timed out after 5 minutes")
        except Exception as e:
            raise e


@app.route('/chat', methods=['POST'])
def chat_endpoint():
    """Flask endpoint to handle chat requests"""
    try:
        # Get JSON data from request
        data = request.get_json()

        if not data or 'message' not in data:
            return jsonify({
                'error': 'Missing message in request body',
                'status': 'error'
            }), 400

        user_input = data['message']

        if not user_input.strip():
            return jsonify({
                'error': 'Message cannot be empty',
                'status': 'error'
            }), 400

        print(f"Received user input: {user_input}")

        # Run the async chat function
        try:
            result = run_async_chat(user_input)

            return jsonify({
                'status': 'success',
                'data': {
                    'response': result['response'],
                    'execution_time': result['execution_time'],
                    'user_input': user_input
                }
            })
        except Exception as async_error:
            print(f"Async error: {str(async_error)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'error': f'Agent execution failed: {str(async_error)}',
                'status': 'error'
            }), 500

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Request processing failed: {str(e)}',
            'status': 'error'
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'chat-agent-api'
    })


@app.route('/', methods=['GET'])
def home():
    """Home endpoint with usage information"""
    return jsonify({
        'message': 'Chat Agent API',
        'endpoints': {
            'POST /chat': 'Send a message to the chat agent',
            'GET /health': 'Health check',
            'GET /': 'This endpoint'
        },
        'usage': {
            'method': 'POST',
            'url': '/chat',
            'body': {
                'message': 'Your message here'
            }
        }
    })


if __name__ == '__main__':
    print("Starting Flask Chat Agent API...")
    print("Available endpoints:")
    print("- POST /chat - Send messages to the agent")
    print("- GET /health - Health check")
    print("- GET / - API information")

    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    )
