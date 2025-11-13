"""LangChain tool for web search functionality."""
from typing import Optional
from langchain_core.tools import tool
from ai_companion.modules.search import WebSearch


# Initialize search module
web_search = WebSearch(max_results=3)


@tool
def search_web(query: str) -> str:
    """Search the web for current information using DuckDuckGo.

    Useful for finding:
    - Current events and news
    - Factual information and definitions
    - How-to guides and tutorials
    - Recent statistics and data
    - Historical facts
    - Scientific information
    - Any topic requiring up-to-date information

    Args:
        query: The search query string

    Returns:
        Formatted search results with titles, snippets, and links

    Example:
        search_web("what is photosynthesis")
        search_web("current population of Japan")
        search_web("how to solve quadratic equations")
    """
    results = web_search.search(query)
    return web_search.format_results(results)


@tool
def search_news(query: str) -> str:
    """Search for recent news articles using DuckDuckGo News.

    Useful for finding:
    - Breaking news and current events
    - Recent developments in any field
    - Latest research and discoveries
    - Recent policy changes
    - Current trends and topics

    Args:
        query: The search query string

    Returns:
        Formatted news results with titles, snippets, dates, and sources

    Example:
        search_news("climate change 2024")
        search_news("latest AI developments")
        search_news("space exploration news")
    """
    results = web_search.search_news(query)
    return web_search.format_results(results)


@tool
def get_current_information(topic: str) -> str:
    """Get current, factual information about any topic.

    Use this when you need:
    - Up-to-date facts and statistics
    - Current definitions or explanations
    - Recent changes to well-known information
    - Verification of information you're uncertain about

    Args:
        topic: The topic or question to research

    Returns:
        Current information from reliable web sources

    Example:
        get_current_information("capital of France")
        get_current_information("speed of light in meters per second")
        get_current_information("who won the 2024 Olympics")
    """
    results = web_search.search(topic)
    return web_search.format_results(results, max_length=400)


# List of available search tools for the agent
SEARCH_TOOLS = [
    search_web,
    search_news,
    get_current_information,
]
