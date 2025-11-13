# DuckDuckGo Search Integration Guide

Your restaurant assistant now has **web search capabilities** powered by DuckDuckGo! 🔍

## 🎯 What's Been Added

### 1. **Web Search Module**
- [web_search.py](src/ai_companion/modules/search/web_search.py) - Core search functionality
- [search_tool.py](src/ai_companion/graph/tools/search_tool.py) - LangChain tool integration

### 2. **Search Capabilities**
- ✅ General web search
- ✅ News search for food trends
- ✅ Dietary restriction checks
- ✅ Competitor pricing research
- ✅ Recipe inspiration

---

## 📦 Installation

First, install the required package:

```bash
pip install duckduckgo-search langchain-community
```

Or add to your `requirements.txt`:
```
duckduckgo-search>=5.0.0
langchain-community>=0.2.0
```

---

## 🚀 How to Use

### Basic Search

```python
from ai_companion.modules.search import WebSearch

# Initialize search
search = WebSearch(max_results=5)

# Perform search
results = search.search("best pizza toppings 2024")

# Format results for display
formatted = search.format_results(results)
print(formatted)
```

### News Search

```python
# Search for food industry news
news_results = search.search_news("fast food trends 2024")
formatted_news = search.format_results(news_results)
```

### Restaurant-Specific Search

```python
from ai_companion.modules.search.web_search import RestaurantSearch

restaurant_search = RestaurantSearch()

# Check competitor prices
pricing = restaurant_search.search_competitor_prices(
    "Margherita pizza",
    location="Seattle"
)

# Find food trends
trends = restaurant_search.search_food_trends("italian cuisine")

# Check dietary info
dietary_info = restaurant_search.search_dietary_info(
    "mozzarella",
    "vegan"
)
```

---

## 🛠️ LangChain Tool Integration

The search functionality is exposed as LangChain tools that can be used by agents:

```python
from ai_companion.graph.tools import SEARCH_TOOLS, search_web

# Use as a standalone tool
result = search_web.invoke("best burger toppings")
print(result)

# Available tools:
# - search_web: General web search
# - search_news: News article search
# - check_ingredient_dietary_info: Dietary restriction checks
```

---

## 🎨 Use Cases for Restaurant Assistant

### 1. **Answer Customer Questions**

**Customer**: "Is mozzarella vegan?"

**System**: Uses `check_ingredient_dietary_info` tool
```python
check_ingredient_dietary_info("mozzarella", "vegan")
```

**Response**: "Based on current information, traditional mozzarella is not vegan as it's made from dairy milk. However, we can recommend vegan cheese alternatives!"

---

### 2. **Stay Updated on Food Trends**

```python
# Daily automated search for trends
trends = search_news("pizza trends 2024")

# Update menu recommendations based on results
# "Try our new truffle pizza - it's trending in 2024!"
```

---

### 3. **Competitive Analysis**

```python
# Research competitor pricing
competitor_search = RestaurantSearch()
results = competitor_search.search_competitor_prices(
    "Pepperoni pizza",
    "downtown Seattle"
)

# Adjust your pricing strategy accordingly
```

---

### 4. **Recipe Inspiration**

```python
# Find new recipe ideas
inspiration = competitor_search.search_recipe_inspiration("gourmet burger")

# "We just added a new Korean BBQ burger based on trending flavors!"
```

---

## 🔧 Integration with Existing Nodes

### Option 1: Add Search to Conversation Node

Update [nodes.py](src/ai_companion/graph/nodes.py) to allow search when needed:

```python
from ai_companion.modules.search import WebSearch

async def conversation_node(state: AICompanionState, config: RunnableConfig):
    # ... existing code ...

    # Check if search is needed based on message content
    user_message = state["messages"][-1].content

    search_keywords = ["is", "vegan", "gluten-free", "trend", "popular"]
    needs_search = any(keyword in user_message.lower() for keyword in search_keywords)

    if needs_search:
        search = WebSearch()
        search_results = search.search(user_message)
        search_context = search.format_results(search_results, max_length=200)

        # Add search results to context
        system_message += f"\n\nWeb Search Results:\n{search_context}"

    # ... rest of code ...
```

---

### Option 2: Create Dedicated Search Node

Add a new `search_node` to the workflow:

```python
async def search_node(state: AICompanionState, config: RunnableConfig):
    """Perform web search and return results."""
    user_query = state["messages"][-1].content

    search = WebSearch(max_results=3)
    results = search.search(user_query)
    formatted_results = search.format_results(results)

    return {"messages": AIMessage(content=formatted_results)}
```

Then update the router to detect search intent:

```python
# In router_prompt
ROUTER_PROMPT = """
...
Route to 'search' when:
- Customer asks factual questions requiring current information
- Customer asks about food trends or popular items
- Customer asks about dietary restrictions or ingredient information
...
"""
```

---

### Option 3: Agent with Tools (Advanced)

Make the conversation node an agent that can use search tools:

```python
from langchain.agents import create_tool_calling_agent, AgentExecutor
from ai_companion.graph.tools import SEARCH_TOOLS

async def agent_conversation_node(state: AICompanionState, config: RunnableConfig):
    """Conversation node with search tool access."""

    # Create agent with search tools
    model = get_chat_model().bind_tools(SEARCH_TOOLS)

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(model, SEARCH_TOOLS, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=SEARCH_TOOLS)

    response = await agent_executor.ainvoke({
        "messages": state["messages"],
        "agent_scratchpad": []
    })

    return {"messages": AIMessage(content=response["output"])}
```

---

## 📊 Search Result Format

Results are returned as a list of dictionaries:

```python
[
    {
        'title': 'Best Pizza Toppings in 2024',
        'snippet': 'The trending toppings include truffle, burrata...',
        'link': 'https://example.com/pizza-trends'
    },
    {
        'title': 'Gourmet Pizza Guide',
        'snippet': 'Discover unique combinations like fig and prosciutto...',
        'link': 'https://example.com/gourmet-pizza'
    }
]
```

Formatted output:
```
Search Results:

1. Best Pizza Toppings in 2024
   The trending toppings include truffle, burrata...
   https://example.com/pizza-trends

2. Gourmet Pizza Guide
   Discover unique combinations like fig and prosciutto...
   https://example.com/gourmet-pizza
```

---

## ⚙️ Configuration

Customize search behavior in `WebSearch`:

```python
search = WebSearch(
    max_results=5,          # Number of results to return
)

# For region-specific results
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

wrapper = DuckDuckGoSearchAPIWrapper(
    region="us-en",         # Region code (us-en, uk-en, de-de, etc.)
    time="d",               # Time filter (d=day, w=week, m=month)
    max_results=5
)
```

---

## 🎯 Example Customer Interactions

### Example 1: Dietary Question
**Customer**: "Is your marinara sauce vegan?"

**AI**: *Uses search if uncertain*
```python
results = check_ingredient_dietary_info("marinara sauce", "vegan")
```

**Response**: "Yes! Traditional marinara sauce is vegan - it's made from tomatoes, garlic, herbs, and olive oil. Our marinara is 100% plant-based! 🌱"

---

### Example 2: Trend Query
**Customer**: "What's popular right now?"

**AI**: *Searches for trends*
```python
results = search_news("pizza trends 2024")
```

**Response**: "Right now, truffle pizzas and Detroit-style thick crust are super popular! Want to try our new Truffle Mushroom Pizza? 🍕"

---

### Example 3: Competitor Check
**Staff Use**: Check competitor pricing

```python
search = RestaurantSearch()
results = search.search_competitor_prices("large pepperoni pizza", "Seattle")
```

Analyze results to stay competitive.

---

## 🚨 Important Notes

### Rate Limiting
- DuckDuckGo has rate limits
- Cache search results when possible
- Don't search on every message

### Privacy
- DuckDuckGo doesn't track searches
- No API key required
- Safe for customer queries

### Error Handling
```python
try:
    results = search.search(query)
    if not results:
        return "I couldn't find current information on that."
except Exception as e:
    logger.error(f"Search failed: {e}")
    return "I'm having trouble searching right now. Let me answer from what I know..."
```

---

## 📈 Performance Tips

1. **Cache Common Searches**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(query: str):
    search = WebSearch()
    return search.search(query)
```

2. **Async Execution**
```python
import asyncio

async def async_search(query: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, search.search, query)
```

3. **Limit Search Frequency**
```python
# Only search if last search was > 5 minutes ago
from datetime import datetime, timedelta

last_search_time = {}

def should_search(query: str) -> bool:
    if query in last_search_time:
        if datetime.now() - last_search_time[query] < timedelta(minutes=5):
            return False
    last_search_time[query] = datetime.now()
    return True
```

---

## 🎉 Benefits

✅ **Real-time Information** - Get current food trends and news
✅ **Better Customer Service** - Answer dietary questions accurately
✅ **Competitive Intelligence** - Monitor competitor pricing
✅ **Menu Innovation** - Discover new recipe ideas
✅ **No API Keys Needed** - DuckDuckGo is free
✅ **Privacy-Focused** - No tracking of searches

---

## 📚 Resources

- [DuckDuckGo Search GitHub](https://github.com/deedy5/duckduckgo_search)
- [LangChain Tools Documentation](https://python.langchain.com/docs/modules/agents/tools/)
- [LangChain Community Tools](https://python.langchain.com/docs/integrations/tools/)

---

**Your restaurant assistant now has the power of web search!** 🚀🔍
