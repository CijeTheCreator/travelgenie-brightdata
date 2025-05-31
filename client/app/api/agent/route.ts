export const maxDuration = 300;
import { NextRequest, NextResponse } from 'next/server';

const AGENT_URL = process.env.NEXT_PUBLIC_AGENT_URL;

export async function POST(request: NextRequest) {
  const body = await request.json();

  try {
    const response = await fetch(`${AGENT_URL}/agent`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to call agent');
    }

    // Create a ReadableStream that handles SSE buffering
    const stream = new ReadableStream({
      async start(controller) {
        let buffer = '';

        try {
          const reader = response.body?.getReader();
          if (!reader) throw new Error('No reader available');

          while (true) {
            const { done, value } = await reader.read();

            if (done) {
              // Handle any remaining buffer content
              if (buffer.trim()) {
                const finalEvent = buffer.endsWith('\n\n') ? buffer : buffer + '\n\n';
                controller.enqueue(new TextEncoder().encode(finalEvent));
              }
              controller.close();
              break;
            }

            // Convert chunk to string and add to buffer
            const text = new TextDecoder().decode(value);
            buffer += text;

            // Process complete SSE events (separated by double newlines)
            const events = buffer.split('\n\n');

            // Keep the last (potentially incomplete) event in buffer
            buffer = events.pop() || '';

            // Send complete events
            for (const event of events) {
              if (event.trim()) {
                const formattedEvent = event + '\n\n';
                controller.enqueue(new TextEncoder().encode(formattedEvent));
              }
            }
          }
        } catch (error) {
          console.error('Stream processing error:', error);

          // Send error event in proper SSE format
          const errorEvent = `event: error\ndata: ${JSON.stringify({
            error: "Error in agent stream",
            details: error instanceof Error ? error.message : String(error)
          })}\n\n`;

          controller.enqueue(new TextEncoder().encode(errorEvent));
          controller.close();
        }
      }
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Cache-Control',
        // Prevent response buffering in some environments
        'X-Accel-Buffering': 'no',
      },
    });

  } catch (error) {
    console.error('Error in agent route:', error);
    return NextResponse.json(
      { error: 'Failed to process /agent request' },
      { status: 500 }
    );
  }
}
