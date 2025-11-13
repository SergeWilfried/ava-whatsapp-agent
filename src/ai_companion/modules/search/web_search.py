"""Web search functionality using DuckDuckGo."""
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class WebSearch:
    """Web search using DuckDuckGo Search API."""

    def __init__(self, max_results: int = 5):
        """Initialize web search.

        Args:
            max_results: Maximum number of search results to return
        """
        self.max_results = max_results
        self._init_search_tool()

    def _init_search_tool(self):
        """Initialize DuckDuckGo search tool."""
        try:
            from langchain_community.tools import DuckDuckGoSearchResults
            from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

            wrapper = DuckDuckGoSearchAPIWrapper(
                max_results=self.max_results,
                region="us-en",  # Can be changed based on restaurant location
            )

            self.search_tool = DuckDuckGoSearchResults(
                api_wrapper=wrapper,
                output_format="list"  # Returns structured list of results
            )
            logger.info("DuckDuckGo search initialized successfully")

        except ImportError:
            logger.warning(
                "duckduckgo-search not installed. Install with: "
                "pip install duckduckgo-search langchain-community"
            )
            self.search_tool = None

    def search(self, query: str) -> List[Dict[str, str]]:
        """Perform web search.

        Args:
            query: Search query string

        Returns:
            List of search results with title, snippet, and link

        Example:
            >>> search = WebSearch()
            >>> results = search.search("best pizza toppings 2024")
            >>> for result in results:
            ...     print(result['title'], result['link'])
        """
        if not self.search_tool:
            logger.error("Search tool not available")
            return []

        try:
            results = self.search_tool.invoke(query)
            logger.info(f"Search completed: {len(results)} results for '{query}'")
            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def search_news(self, query: str) -> List[Dict[str, str]]:
        """Search for news articles.

        Args:
            query: Search query string

        Returns:
            List of news results with title, snippet, link, date, and source
        """
        if not self.search_tool:
            logger.error("Search tool not available")
            return []

        try:
            from langchain_community.tools import DuckDuckGoSearchResults
            from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

            wrapper = DuckDuckGoSearchAPIWrapper(
                max_results=self.max_results,
                region="us-en",
            )

            news_search = DuckDuckGoSearchResults(
                api_wrapper=wrapper,
                backend="news",
                output_format="list"
            )

            results = news_search.invoke(query)
            logger.info(f"News search completed: {len(results)} results for '{query}'")
            return results

        except Exception as e:
            logger.error(f"News search failed: {e}")
            return []

    def format_results(self, results: List[Dict[str, str]], max_length: int = 500) -> str:
        """Format search results into a readable string.

        Args:
            results: List of search result dictionaries
            max_length: Maximum length of formatted output

        Returns:
            Formatted string with search results
        """
        if not results:
            return "No results found."

        formatted = "Search Results:\n\n"

        for i, result in enumerate(results[:3], 1):  # Limit to top 3 results
            title = result.get('title', 'No title')
            snippet = result.get('snippet', 'No description')
            link = result.get('link', '')

            formatted += f"{i}. {title}\n"
            formatted += f"   {snippet[:150]}...\n"
            if link:
                formatted += f"   {link}\n"
            formatted += "\n"

            # Check if we're approaching max length
            if len(formatted) > max_length:
                formatted = formatted[:max_length] + "..."
                break

        return formatted.strip()


# Example usage for restaurant-specific searches
class RestaurantSearch(WebSearch):
    """Specialized search for restaurant-related queries."""

    def search_competitor_prices(self, item_name: str, location: str = "") -> List[Dict]:
        """Search for competitor pricing on menu items.

        Args:
            item_name: Menu item name (e.g., "Margherita pizza")
            location: Optional location for local results

        Returns:
            List of search results
        """
        query = f"{item_name} price {location} restaurant menu"
        return self.search(query)

    def search_food_trends(self, cuisine: str = "fast food") -> List[Dict]:
        """Search for current food trends.

        Args:
            cuisine: Type of cuisine to search for

        Returns:
            List of news results about food trends
        """
        query = f"{cuisine} trends 2024"
        return self.search_news(query)

    def search_recipe_inspiration(self, dish_type: str) -> List[Dict]:
        """Search for recipe ideas and inspiration.

        Args:
            dish_type: Type of dish (e.g., "pizza", "burger")

        Returns:
            List of search results
        """
        query = f"best {dish_type} recipe variations"
        return self.search(query)

    def search_dietary_info(self, ingredient: str, restriction: str) -> List[Dict]:
        """Search for dietary restriction information.

        Args:
            ingredient: Ingredient name
            restriction: Dietary restriction (e.g., "vegan", "gluten-free")

        Returns:
            List of search results
        """
        query = f"is {ingredient} {restriction}"
        return self.search(query)
