export const maxDuration = 300
export const runtime = 'nodejs';
// This is required to enable streaming
export const dynamic = 'force-dynamic';

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

    const stream = new TransformStream();
    const writer = stream.writable.getWriter();

    (async () => {
      try {
        const reader = response.body?.getReader();
        if (!reader) throw new Error('No reader available');

        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            await writer.close();
            break;
          }

          // Just forward the raw chunks
          await writer.write(value);
        }
      } catch (error) {
        console.error('Stream processing error:', error);

        // Write an error message to the stream before closing
        const errorData = JSON.stringify({ error: "Error in agent" });
        await writer.write(new TextEncoder().encode(`event: error\ndata: ${errorData}\n\n`));
        await writer.close();
      }
    })();

    return new Response(stream.readable, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });

  } catch (error) {
    console.error('Error in agent route', error);
    return NextResponse.json(
      { error: 'Failed to process /agent request' },
      { status: 500 }
    );
  }
} 
