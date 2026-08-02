from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def tavily_search(query: str):
    """Search for information using Tavily."""
    response = tavily_client.search(query=query , max_results=5)

    results = []

    for i , r in enumerate(response['results']):
        title = r.get('title' , 'No Title')
        url = r.get('url' , 'No URL')
        snippet = r.get('content' , '').strip()

        if len(snippet) > 300:
            snippet = snippet[:300].rsplit(' ', 1)[0] + "..."
        
        results.append(f"{i}. **{title}**\n {url}\n  {snippet}")

    return "\n\n".join(results)
        
        