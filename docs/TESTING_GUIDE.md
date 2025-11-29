# Testing the Agent-Based Search Integration

This guide shows you how to test the new agent-based conversation system with automatic search capabilities.

## 🔧 Setup

### 1. Install Dependencies

First, install the required packages:

```bash
pip install -e .
```

Or install just the new dependency:

```bash
pip install duckduckgo-search
```

### 2. Verify Installation

Check that duckduckgo-search is installed:

```bash
python -c "from duckduckgo_search import DDGS; print('✓ DuckDuckGo Search installed')"
```

Check that langchain agents are available:

```bash
python -c "from langchain.agents import create_tool_calling_agent, AgentExecutor; print('✓ LangChain agents available')"
```

## 🧪 Test Cases

### Test 1: Current Events (Should Use Search)

Send a message asking about recent news:

```
User: "What's the latest news about AI developments?"
```

**Expected Behavior**:
- Agent recognizes need for current information
- Calls `search_news` tool
- Returns response with recent news
- Check logs for: `Action: search_news`

### Test 2: General Knowledge (May Not Search)

Ask about well-established facts:

```
User: "Explain how photosynthesis works"
```

**Expected Behavior**:
- Agent recognizes this as general knowledge
- May respond without searching
- Provides accurate explanation
- Check logs for: Direct response or minimal tool use

### Test 3: Fact Checking (Should Use Search)

Ask about something that may need verification:

```
User: "What's the current world population?"
```

**Expected Behavior**:
- Agent recognizes need for up-to-date statistics
- Calls `get_current_information` or `search_web`
- Returns current data
- Check logs for: Tool call with population query

### Test 4: Time-Sensitive Information (Should Use Search)

Ask about something that changes:

```
User: "Who is the current president of France?"
```

**Expected Behavior**:
- Agent may search to verify current information
- Returns accurate current answer
- Check logs for: Possible tool call

### Test 5: Historical Facts (May Not Search)

Ask about established historical information:

```
User: "When did World War II end?"
```

**Expected Behavior**:
- Agent likely responds from training data
- No search needed for well-known historical facts
- Check logs for: Direct response

### Test 6: Trending Topics (Should Use Search)

Ask about current trends:

```
User: "What are the trending topics on social media today?"
```

**Expected Behavior**:
- Agent recognizes this requires real-time data
- Calls `search_news` or `search_web`
- Returns current trending information
- Check logs for: Tool call with trends query

### Test 7: Mixed Query (Intelligent Decision)

Ask a question that combines general knowledge with current info:

```
User: "How does solar energy work and what are the latest developments?"
```

**Expected Behavior**:
- Agent explains solar energy from knowledge
- May search for "latest developments"
- Combines both in response
- Check logs for: Possible tool call for recent developments

## 📊 Monitoring Agent Behavior

### Check Verbose Logs

The agent has `verbose=True` enabled, so you'll see detailed logs:

```
> Entering new AgentExecutor chain...

Thought: The user is asking about current news. I should search for recent information.

Action: search_news
Action Input: "AI developments latest"

Observation: [Search results showing recent AI news articles...]

Thought: I now have current information to provide an accurate answer.

Final Answer: Based on recent news, here's what's happening with AI...

> Finished chain.
```

### What to Look For

1. **Thought**: Agent's reasoning about what to do
2. **Action**: Which tool was chosen (search_web, search_news, get_current_information)
3. **Action Input**: The search query used
4. **Observation**: Results returned from the tool
5. **Final Answer**: The response sent to user

### Log Levels

If verbose logs are too much, you can disable them in [nodes.py](src/ai_companion/graph/nodes.py):

```python
agent_executor = AgentExecutor(
    agent=agent,
    tools=SEARCH_TOOLS,
    verbose=False,  # Change to False
    max_iterations=3,
    handle_parsing_errors=True
)
```

## 🔍 Testing Search Tools Directly

### Test search_web

```python
from ai_companion.graph.tools import search_web

result = search_web.invoke("artificial intelligence news")
print(result)
```

**Expected Output**:
```
Search Results:

1. Latest AI Developments 2024
   Recent advances in artificial intelligence include...
   https://example.com/ai-news

2. AI Industry Trends
   The AI industry is experiencing rapid growth...
   https://example.com/ai-trends

3. Machine Learning Breakthroughs
   Researchers have achieved new milestones...
   https://example.com/ml-news
```

### Test search_news

```python
from ai_companion.graph.tools import search_news

result = search_news.invoke("technology 2024")
print(result)
```

**Expected Output**:
```
Search Results:

1. Tech Trends 2024
   This year's technology landscape is defined by...
   https://news.example.com/tech-2024

2. Innovation Report
   New innovations are transforming industries...
   https://news.example.com/innovation

3. Digital Transformation
   Companies are accelerating their digital strategies...
   https://news.example.com/digital
```

### Test get_current_information

```python
from ai_companion.graph.tools import get_current_information

result = get_current_information.invoke("capital of France")
print(result)
```

**Expected Output**:
```
Search Results:

1. Paris - Capital of France
   Paris is the capital and most populous city of France...
   https://example.com/paris

2. France Geography
   France's capital city is Paris, located in the north...
   https://example.com/france-info
```

## 🐛 Common Issues and Solutions

### Issue 1: Agent Never Uses Tools

**Problem**: Agent always responds without searching

**Possible Causes**:
- Model doesn't support tool calling
- Tool descriptions not clear enough
- System prompt guidance insufficient

**Solutions**:
1. Verify model supports function calling (Groq models should)
2. Update tool descriptions to be more explicit
3. Adjust system prompt tool usage guidance
4. Try asking more explicit current-event questions

### Issue 2: Search Returns Empty Results

**Problem**: Search tools return "No results found"

**Possible Causes**:
- DuckDuckGo rate limiting
- Network connectivity issues
- Search query too specific

**Solutions**:
1. Wait a few minutes (rate limiting)
2. Check internet connection
3. Test with simpler queries
4. Add retry logic with backoff

### Issue 3: Agent Gets Stuck

**Problem**: Agent keeps searching without providing answer

**Possible Causes**:
- Search results not helpful
- Parsing errors
- Iteration limit too high

**Solutions**:
1. Lower `max_iterations` (currently 3)
2. Improve error handling
3. Check search result formatting
4. Review agent scratchpad in logs

### Issue 4: Errors in Tool Calls

**Problem**: Agent calls tools with wrong parameters

**Possible Causes**:
- Tool schema unclear
- Model hallucinating parameters
- Prompt confusion

**Solutions**:
1. Simplify tool descriptions
2. Add parameter examples
3. Enable `handle_parsing_errors=True` (already enabled)
4. Review tool call logs

### Issue 5: Fallback Always Triggered

**Problem**: Agent always falls back to regular chain

**Possible Causes**:
- Agent executor failing
- Tool import errors
- Model compatibility issues

**Solutions**:
1. Check error logs for specific issues
2. Verify all imports work
3. Test tools independently first
4. Ensure model supports function calling

## 🎯 Success Metrics

### What "Success" Looks Like

✅ **Appropriate Tool Use**
- Agent searches when information is current/time-sensitive
- Agent doesn't search for well-known facts
- Right tool chosen for the query type

✅ **Natural Responses**
- Search results integrated smoothly
- Conversational tone maintained
- No awkward "I searched and found..." phrasing

✅ **Reliability**
- Handles search errors gracefully
- Falls back when needed
- Doesn't get stuck in loops

✅ **Performance**
- Responses within reasonable time
- Not searching excessively
- Efficient tool usage

## 📝 Test Checklist

Use this checklist when testing:

- [ ] Agent responds to greetings without searching
- [ ] Agent searches for current news when asked
- [ ] Agent searches for time-sensitive information
- [ ] Agent doesn't search for historical facts
- [ ] Agent handles search errors gracefully
- [ ] Agent provides natural, conversational responses
- [ ] Agent doesn't get stuck in loops
- [ ] Agent chooses appropriate tools
- [ ] Search results are relevant
- [ ] Responses incorporate search data naturally
- [ ] Fallback works when agent fails
- [ ] Verbose logs show agent reasoning
- [ ] No syntax or import errors
- [ ] Performance is acceptable

## 🚀 Advanced Testing

### Test with Different Scenarios

1. **Educational Questions**
```
"Explain quantum mechanics"
"Who discovered penicillin?"
"What's the latest research on climate change?"
```

2. **Current Events**
```
"What's happening in the news today?"
"Latest developments in space exploration"
"Recent sports results"
```

3. **Fact Checking**
```
"Is the Earth flat?" (should verify with search)
"What's the speed of light?" (may not need search)
"Current COVID-19 statistics" (should search)
```

4. **Conversational**
```
"Hello, how are you?"
"Tell me a joke"
"What can you help me with?"
```

### Load Testing

Test with multiple rapid queries:
```python
queries = [
    "What's the weather?",
    "Latest AI news",
    "Explain photosynthesis",
    "Current world population",
    "Who won the World Cup?"
]

for query in queries:
    # Send query and measure response time
    # Check if agent behavior is consistent
```

### Edge Cases

Test unusual scenarios:
- Very long queries
- Queries in different languages
- Ambiguous questions
- Multiple questions at once
- Queries with typos

## 📊 Measuring Performance

### Response Time

Track how long agent takes:
- Without tools: Should be fast
- With one tool call: Moderate
- With multiple tools: Slower but acceptable

### Tool Call Accuracy

Measure:
- % of queries where tool use was appropriate
- % of queries where right tool was chosen
- % of successful tool executions

### User Satisfaction

Consider:
- Response quality
- Information accuracy
- Conversational naturalness
- Overall helpfulness

## 📚 Next Steps After Testing

Once testing is complete:

1. **Optimize** - Adjust parameters based on results
2. **Monitor** - Watch production usage patterns
3. **Improve** - Refine prompts and tool descriptions
4. **Expand** - Add more tools as needed
5. **Scale** - Enable caching for common queries

---

**Ready to test your intelligent agent!** 🚀🧪
