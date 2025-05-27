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
import multiprocessing
import pickle
from concurrent.futures import ProcessPoolExecutor
import signal

load_dotenv()

app = Flask(__name__)

# Global configuration
SERVER_CONFIG = {
    'command': "npx",
    'env': {
        "API_TOKEN": os.getenv("API_TOKEN"),
        "BROWSER_AUTH": os.getenv("BROWSER_AUTH"),
        "WEB_UNLOCKER_ZONE": os.getenv("WEB_UNLOCKER_ZONE"),
    },
    'args': ["@brightdata/mcp"],
}

MODEL_CONFIG = {
    'model': "gemini-2.0-flash",
    'temperature': 0,
    'max_tokens': None,
    'timeout': None,
    'max_retries': 2,
}


@contextlib.contextmanager
def suppress_stderr():
    with open(os.devnull, 'w') as devnull:
        old_stderr = sys.stderr
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stderr = old_stderr


def run_chat_in_process(user_input):
    """Function to run in a separate process - must be at module level for multiprocessing"""
    import asyncio
    import os
    import sys
    import contextlib
    import time
    import gc
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from langchain_mcp_adapters.tools import load_mcp_tools
    from langgraph.prebuilt import create_react_agent
    from langchain_google_genai import ChatGoogleGenerativeAI
    from dotenv import load_dotenv

    # Reload environment in the new process
    load_dotenv()

    # Initialize model and server parameters in the new process
    model = ChatGoogleGenerativeAI(**MODEL_CONFIG)

    server_params = StdioServerParameters(
        command=SERVER_CONFIG['command'],
        env=SERVER_CONFIG['env'],
        args=SERVER_CONFIG['args'],
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
        """Chat function that runs in the separate process"""
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    start = time.time()
                    print(f"Process {os.getpid()}: Initializing Session")
                    await session.initialize()
                    print(f"Process {os.getpid()}: Initializing tools")
                    tools = await load_mcp_tools(session)
                    print(f"Process {os.getpid()}: Creating Agent")
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
                    print(f"Process {os.getpid()}: Invoking Agent")
                    agent_response = await agent.ainvoke({"messages": messages})

                    # Extract agent's reply
                    ai_message = agent_response["messages"][-1].content
                    print(f"Process {os.getpid()}: Agent response received")

                    end = time.time()
                    execution_time = end - start
                    print(
                        f"Process {os.getpid()}: Time taken: {execution_time:.4f} seconds")

                    return {
                        "response": ai_message,
                        "execution_time": execution_time,
                        "process_id": os.getpid()
                    }
        except Exception as e:
            print(f"Process {os.getpid()}: Error in chat_with_agent: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e

    # Set up signal handler for graceful shutdown
    def signal_handler(signum, frame):
        print(
            f"Process {os.getpid()}: Received signal {signum}, shutting down...")
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Create new event loop for this process
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        with suppress_stderr():
            result = loop.run_until_complete(chat_with_agent(user_input))
            return result
    except Exception as e:
        print(f"Process {os.getpid()}: Error in process execution: {str(e)}")
        raise e
    finally:
        # Clean up
        try:
            if loop and not loop.is_closed():
                loop.close()
        except:
            pass
        gc.collect()


def run_async_chat(user_input):
    """Wrapper function to run the chat in a separate process"""
    try:
        # Use process pool for complete isolation
        with ProcessPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_chat_in_process, user_input)
            try:
                result = future.result(timeout=300)  # 5 minute timeout
                return result
            except Exception as e:
                print(f"Process execution error: {str(e)}")
                raise e
    except Exception as e:
        print(f"Error in run_async_chat: {str(e)}")
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

        print(f"Main process {os.getpid()}: Received user input: {user_input}")

        # Run the chat function in a separate process
        try:
            result = run_async_chat(user_input)

            return jsonify({
                'status': 'success',
                'data': {
                    'response': result['response'],
                    'execution_time': result['execution_time'],
                    'user_input': user_input,
                    'process_id': result.get('process_id', 'unknown')
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
        'service': 'chat-agent-api',
        'process_id': os.getpid()
    })


@app.route('/', methods=['GET'])
def home():
    """Home endpoint with usage information"""
    return jsonify({
        'message': 'Chat Agent API',
        'process_id': os.getpid(),
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
    # Required for multiprocessing on some systems
    multiprocessing.set_start_method('spawn', force=True)

    print("Starting Flask Chat Agent API...")
    print(f"Main process ID: {os.getpid()}")
    print("Available endpoints:")
    print("- POST /chat - Send messages to the agent")
    print("- GET /health - Health check")
    print("- GET / - API information")

    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    )
