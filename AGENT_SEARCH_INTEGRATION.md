# Agent-Based Search Integration

Your AI companion now operates as an **intelligent agent** that can automatically decide when to use web search tools! 🤖🔍

## 🎯 What Changed

### From Simple Chain to Intelligent Agent

Previously, the conversation node used a simple LangChain chain that could only respond with its training data. Now it's been upgraded to an **agent-based system** that can:

- **Automatically decide** when to search the web for current information
- **Use multiple tools** (web search, news search, fact-checking)
- **Combine search results** with its knowledge to provide comprehensive answers
- **Operate autonomously** - no manual tool invocation needed

## 🏗️ Architecture Changes

### conversation_node (nodes.py)

The conversation node has been completely refactored to use LangChain's agent framework:

```python
from langchain.agents import create_tool_calling_agent, AgentExecutor
from ai_companion.graph.tools import SEARCH_TOOLS

async def conversation_node(state: AICompanionState, config: RunnableConfig):
    """Conversation node with agent capabilities for automatic tool use."""

    # 1. Build system message with character card and context
    system_message = get_character_card_prompt("en").format(
        memory_context=memory_context or "No previous memories available.",
        current_activity=current_activity
    )

    # 2. Add tool usage guidance
    system_message += """
    ## Tool Usage:
    You have access to web search tools. Use them when:
    - You need current, up-to-date information
    - You're unsure about facts, statistics, or recent events
    - The user asks about current events, news, or trends
    - You need to verify information
    - The user asks questions requiring real-time data
    """

    # 3. Create agent with tools
    agent = create_tool_calling_agent(model, SEARCH_TOOLS, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=SEARCH_TOOLS,
        verbose=True,
        max_iterations=3,
        handle_parsing_errors=True
    )

    # 4. Execute agent - it will decide when to use tools
    response = await agent_executor.ainvoke({"messages": state["messages"]})

    return {"messages": AIMessage(content=response["output"])}
```

### Key Components

1. **create_tool_calling_agent**: Creates an agent that can call tools
2. **AgentExecutor**: Manages the agent's execution loop
3. **SEARCH_TOOLS**: List of available tools (search_web, search_news, get_current_information)
4. **max_iterations=3**: Prevents infinite loops
5. **handle_parsing_errors=True**: Gracefully handles tool call errors
6. **Fallback mechanism**: Falls back to regular chain if agent fails

## 🔧 Available Search Tools

The agent has access to three search tools defined in [search_tool.py](src/ai_companion/graph/tools/search_tool.py):

### 1. search_web
General web search for any topic
```python
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
    """
```

### 2. search_news
Specialized news search
```python
@tool
def search_news(query: str) -> str:
    """Search for recent news articles using DuckDuckGo News.

    Useful for finding:
    - Breaking news and current events
    - Recent developments in any field
    - Latest research and discoveries
    - Recent policy changes
    - Current trends and topics
    """
```

### 3. get_current_information
Quick fact-checking
```python
@tool
def get_current_information(topic: str) -> str:
    """Get current, factual information about any topic.

    Use this when you need:
    - Up-to-date facts and statistics
    - Current definitions or explanations
    - Recent changes to well-known information
    - Verification of information you're uncertain about
    """
```

## 🎭 How the Agent Works

### Decision-Making Process

1. **User sends message** → Agent receives conversation context
2. **Agent analyzes** → Determines if current information is needed
3. **Agent decides**:
   - If knowledge is sufficient → Respond directly
   - If search is needed → Call appropriate tool
4. **Tool execution** → Search is performed
5. **Result processing** → Agent receives search results
6. **Response generation** → Agent combines results with knowledge
7. **Final answer** → Natural, conversational response to user

### Example Flow

**User**: "What's the weather like in Tokyo today?"

**Agent's Internal Process**:
1. Recognizes need for current information (weather is time-sensitive)
2. Decides to call `search_web` tool
3. Executes: `search_web("Tokyo weather today")`
4. Receives search results with current weather data
5. Formulates natural response incorporating the data
6. Sends: "Based on current data, Tokyo is experiencing..."

## 🚀 Benefits of Agent-Based Approach

### 1. **Autonomous Decision Making**
- Agent decides when to search without explicit instructions
- No need to pre-program search triggers
- Adapts to different types of queries automatically

### 2. **Multi-Tool Capability**
- Can use different tools for different needs
- Can chain multiple tool calls if needed
- Flexible and extensible

### 3. **Natural Conversations**
- Search results integrated seamlessly
- Maintains conversational flow
- No awkward "let me search that" responses

### 4. **Graceful Degradation**
- Fallback to regular chain if agent fails
- Error handling built-in
- Robust and reliable

### 5. **General Purpose**
- Not restricted to specific domains (restaurant, tutoring, etc.)
- Can answer questions on any topic
- True general-purpose AI assistant

## 📦 Installation

The agent requires these dependencies (already added to [pyproject.toml](pyproject.toml)):

```toml
dependencies = [
    # ... other dependencies ...
    "langchain>=0.3.13",
    "langchain-community>=0.3.13",
    "duckduckgo-search>=5.0.0",
]
```

Install with:
```bash
pip install -e .
```

Or just the search package:
```bash
pip install duckduckgo-search
```

## 🎯 Use Cases

### 1. Educational Tutoring
**Student**: "Who won the Nobel Prize in Physics this year?"
- Agent searches for current Nobel Prize winners
- Provides accurate, up-to-date information
- Explains the research if asked

### 2. Current Events
**User**: "What's happening with AI regulation in Europe?"
- Agent searches for recent news
- Summarizes latest developments
- Provides context and implications

### 3. Fact Checking
**User**: "Is coffee good for your health?"
- Agent searches for current medical research
- Presents evidence-based information
- Acknowledges complexity and nuance

### 4. General Knowledge
**User**: "Explain quantum computing"
- Agent may or may not search depending on query specificity
- Provides clear explanation
- Can search for specific details if needed

### 5. Real-Time Information
**User**: "What time is sunrise tomorrow in New York?"
- Agent recognizes need for location/time-specific data
- Searches for current information
- Provides accurate answer

## 🔍 Monitoring and Debugging

### Verbose Mode

The agent executor has `verbose=True` enabled, so you can see the agent's reasoning:

```
> Entering new AgentExecutor chain...

Thought: The user is asking about current events. I need to search for recent news.

Action: search_news
Action Input: "AI developments 2024"

Observation: [Search results...]

Thought: I now have current information to answer the question.

Final Answer: Based on recent news, here's what's happening with AI...

> Finished chain.
```

### Log Analysis

Check logs to see:
- Which tools were called
- Search queries used
- Number of iterations
- Any errors encountered

## ⚙️ Configuration

### Agent Parameters

Customize the agent behavior in [nodes.py](src/ai_companion/graph/nodes.py):

```python
agent_executor = AgentExecutor(
    agent=agent,
    tools=SEARCH_TOOLS,
    verbose=True,              # Set to False to reduce logging
    max_iterations=3,          # Increase for more complex reasoning
    handle_parsing_errors=True # Keep True for robustness
)
```

### Search Configuration

Customize search behavior in [web_search.py](src/ai_companion/modules/search/web_search.py):

```python
web_search = WebSearch(
    max_results=3  # Number of search results to return
)
```

## 🎓 Tool Usage Guidance

The system prompt includes guidance on when to use tools:

```
## Tool Usage:
You have access to web search tools. Use them when:
- You need current, up-to-date information
- You're unsure about facts, statistics, or recent events
- The user asks about current events, news, or trends
- You need to verify information
- The user asks questions requiring real-time data

Always provide natural, conversational responses that incorporate search results seamlessly.
```

This guidance helps the agent make smart decisions about when to search.

## 🔐 Privacy and Safety

### DuckDuckGo Benefits
- No user tracking
- No search history stored
- No API keys required
- Privacy-focused search

### Rate Limiting
- Built into DuckDuckGo API
- Agent respects rate limits automatically
- Falls back gracefully if rate limited

## 🐛 Troubleshooting

### Agent Not Using Tools

**Problem**: Agent responds without searching when it should

**Solution**:
- Adjust tool descriptions to be more specific
- Update system prompt guidance
- Lower the agent's confidence threshold

### Search Errors

**Problem**: Search tool returns errors

**Solution**:
- Check internet connection
- Verify duckduckgo-search is installed
- Check for rate limiting
- Review error logs

### Performance Issues

**Problem**: Agent takes too long to respond

**Solution**:
- Reduce `max_iterations`
- Decrease `max_results` in WebSearch
- Use faster model if available
- Enable caching for common queries

## 📊 Performance Optimization

### Caching

Add caching for common queries:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(query: str):
    return web_search.search(query)
```

### Async Execution

The agent already uses async execution for performance:

```python
response = await agent_executor.ainvoke(...)
```

### Smart Tool Selection

The agent learns to use the most appropriate tool:
- `get_current_information` for quick facts
- `search_web` for general queries
- `search_news` for current events

## 🎉 What's Next

### Potential Enhancements

1. **Additional Tools**
   - Calculator tool for math
   - Weather API tool
   - Translation tool
   - Code execution tool

2. **Memory Integration**
   - Remember previous searches
   - Learn user preferences
   - Personalize search strategies

3. **Multi-Step Reasoning**
   - Chain multiple searches
   - Combine information from multiple sources
   - Deeper analysis capabilities

4. **Custom Search Sources**
   - Academic paper search
   - Specific website search
   - Domain-specific databases

## 📚 Resources

- [LangChain Agents Documentation](https://python.langchain.com/docs/modules/agents/)
- [DuckDuckGo Search API](https://github.com/deedy5/duckduckgo_search)
- [Tool Calling Guide](https://python.langchain.com/docs/modules/agents/tools/)
- [Agent Executor Reference](https://python.langchain.com/docs/modules/agents/agent_executor/)

---

**Your AI is now a true autonomous agent with web search capabilities!** 🚀🤖
