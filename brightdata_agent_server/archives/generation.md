curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "You are a web scraping agent tasked with gathering and analyzing public sentiment about Dubai as a tourism destination, using Reddit as the primary data source.\n1. Search Reddit for the most recent and relevant posts, comments, and discussions mentioning Dubai in the context of travel, tourism, vacations, or visitor experiences.\n2. Extract the main text content from each reddit page\n3. Analyze the text to identify sentiments about:\n   - Accommodation and facilities\n   - Local culture and people\n   - Safety and accessibility\n   - Food and dining experiences\n4. Summarize the overall sentiment into a report covering:\n   - Most frequently praised aspects\n   - Common complaints or warnings\n   - General travel advice and tips shared by Reddit users\n   - Overall sentiment score or conclusion regarding Dubai as a tourism spot\nReturn the summary as the final output."
  }'
