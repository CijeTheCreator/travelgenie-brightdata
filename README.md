# Travel Genie

An AI-powered agent designed to help tourists plan smarter and cut down trip costs effortlessly

## Features

- Real-time flight pricing  
- Real-time hotel pricing  
- Sentiment analysis on destination (updated live)  
- Reddit-powered itinerary planning based on recent tourist experiences  
- Easy calendar integration (Google Calendar, Spplr, etc.)  

## Installation

### LangGraph server
```bash
cd agent/
poetry install
poetry run server
````

### MCP Servers

```bash
cd mcp-servers/calandar-mcp
uv sync
uv run python calendar-mcp-server.py sse
```

### Next.js client

```bash
cd client/
npm install
npm run dev
```

Application will start at [http://localhost:3000](http://localhost:3000) by default

A Docker Build is coming very soon

## How it works

1. User inputs destination and trip dates.
2. Travel Genie fetches real-time flight and hotel prices.
3. Prices are converted to the user’s local currency and summed for total trip cost.
4. The agent scrapes live sentiment data from platforms like Reddit.
5. It identifies trending activities and safety insights based on user content.
6. A personalized itinerary is generated using this data.
7. The itinerary is formatted as a calendar.
8. Users can export it to Google Calendar, Spplr, or others.
9. Visa requirements are checked via real-time scraping from visaindex.com.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

