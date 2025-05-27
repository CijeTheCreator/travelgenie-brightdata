Rewrite this curl command to use the text below as user_input

curl -X POST http://localhost:5000/chat   -H "Content-Type: application/json"   -d '{"message": "Go to https://www.google.com/ type \"Hello world\" into #APjFqb get all the links in the resulting page"}'


"""
You are a web scraping agent tasked with gathering and analyzing public sentiment about Dubai as a tourism destination, using Reddit as the primary data source.

1. Search Reddit for the most recent and relevant posts, comments, and discussions mentioning Dubai in the context of travel, tourism, vacations, or visitor experiences.

2. Extract the main text content from each reddit page

3. Analyze the text to identify sentiments about:
   - Accommodation and facilities
   - Local culture and people
   - Safety and accessibility
   - Food and dining experiences

4. Summarize the overall sentiment into a report covering:
   - Most frequently praised aspects
   - Common complaints or warnings
   - General travel advice and tips shared by Reddit users
   - Overall sentiment score or conclusion regarding [LOCATION] as a tourism spot

Return the summary as the final output.
"""

