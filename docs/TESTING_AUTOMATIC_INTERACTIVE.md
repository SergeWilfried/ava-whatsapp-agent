# Testing Automatic Interactive Messages

## 🧪 Test Scenarios

Test these scenarios to see automatic interactive messages in action:

### Test 1: Subject Selection (Automatic List)

**Send**: "What subjects can I learn?"
or "Show me topics"
or "I want to learn something"

**Expected**: Interactive list with Mathematics, Science, Languages, Other categories

**Why**: Keywords "subject", "topic", "learn" trigger automatic subject list

### Test 2: Subject Selection → Difficulty (Auto Flow)

**Step 1 - Send**: "What can I learn?"
**Expected**: Subject list appears

**Step 2 - Click**: Any subject (e.g., "Algebra")
**Expected**: Difficulty buttons appear (Beginner/Intermediate/Advanced)

**Why**: System detects `[List selection:]` and automatically follows up

### Test 3: Difficulty → Learning Mode (Auto Flow)

**Step 1 - Send**: "I want to learn math"
**Step 2 - Select**: Subject from list
**Step 3 - Click**: Difficulty button
**Expected**: Learning mode buttons appear (Practice/Teach Me/Quiz)

**Why**: System detects difficulty button click and continues flow

### Test 4: Yes/No Questions (Auto Detection)

**Send**: "Do you want to help me?"
or "Can you teach me?"
or "Would you like to start?"

**Expected**: AI responds + Yes/No buttons appear automatically

**Why**: System detects "Do you", "Can you", "Would you" patterns

### Test 5: Confirmation Needed

**Send**: "I need to confirm something"
or "Please verify this"
or "Are you sure about that?"

**Expected**: Confirm/Cancel buttons

**Why**: Keywords "confirm", "verify", "sure" trigger confirmation buttons

### Test 6: AI Response with Question (Auto Enhancement)

**Send**: "I'm not sure what to do"

**AI might respond**: "Would you like me to suggest some options?"

**Expected**: Yes/No buttons automatically added to AI's question

**Why**: System analyzes AI response and detects "Would you like..." pattern

### Test 7: AI Response with Options (Auto Extraction)

**Send**: "What are the best study methods?"

**AI might respond**: "There are three main methods: a) Active recall, b) Spaced repetition, c) Practice problems. Which interests you?"

**Expected**: Buttons automatically created for the three options

**Why**: System extracts "a), b), c)" pattern and creates choice buttons

## 📊 Testing Checklist

Use this checklist to verify all features work:

### Basic Features
- [ ] Keyword "subject" or "topic" shows subject list
- [ ] Keyword "menu" or "list" triggers appropriate list
- [ ] Questions with "yes or no" add Yes/No buttons
- [ ] Words like "confirm" add Confirm/Cancel buttons

### Interactive Flows
- [ ] Selecting from subject list shows difficulty buttons
- [ ] Clicking difficulty button shows learning mode buttons
- [ ] Each step remembers context from previous step

### Response Enhancement
- [ ] AI questions ending with "?" get buttons
- [ ] AI responses with options (a,b,c) get choice buttons
- [ ] Yes/no questions in AI response get Yes/No buttons
- [ ] Confirmation requests get Confirm/Cancel buttons

### Edge Cases
- [ ] Long responses still work (truncated appropriately)
- [ ] Multiple questions in one message handled correctly
- [ ] Non-interactive messages still work normally
- [ ] System falls back to text if interactive fails

## 🔍 Debugging

### Check Logs

Look for these in your logs:

```
# Intent detection
"Intent detected: list"
"Intent detected: binary"
"Intent detected: confirmation"

# Interactive component creation
"Creating tutoring subject list"
"Creating yes/no buttons"
"Creating difficulty buttons"

# Response analysis
"Analyzing response for interactive enhancement"
"Found question pattern in response"
"Extracted 3 options from response"
```

### Verify State

After sending a message, check the state contains:

```python
{
    "messages": [AIMessage(content="...")],
    "interactive_component": {
        "type": "button" or "list",
        "body": {...},
        "action": {...}
    }
}
```

### Test API Calls

Use WhatsApp API test tool or check network tab to see:

```json
{
    "messaging_product": "whatsapp",
    "to": "+1234567890",
    "type": "interactive",
    "interactive": {
        "type": "button",
        "body": {"text": "Question?"},
        "action": {
            "buttons": [
                {"type": "reply", "reply": {"id": "yes", "title": "Yes"}},
                {"type": "reply", "reply": {"id": "no", "title": "No"}}
            ]
        }
    }
}
```

## 🎯 Expected Behaviors

### Scenario: Subject Learning Flow

```
You: "What can I learn?"
→ System shows subject list

You: Click "Algebra"
→ System shows difficulty buttons

You: Click "Beginner"
→ System shows learning mode buttons

You: Click "Teach Me"
→ System starts teaching
```

### Scenario: Yes/No Question

```
You: "Can you help me with homework?"
→ AI responds with answer + Yes/No buttons

You: Click "Yes"
→ AI continues with help
```

### Scenario: Multiple Choice from AI

```
You: "What's the best way to study?"
→ AI lists: "a) Active recall, b) Spaced repetition, c) Practice"
→ System automatically creates buttons for a, b, c

You: Click "Active recall"
→ AI explains active recall method
```

## ⚠️ Common Issues

### Issue: Interactive Message Not Appearing

**Check**:
1. User message contains trigger keywords?
2. Syntax errors in interactive_logic.py or nodes.py?
3. State has interactive_component field?
4. WhatsApp API credentials correct?

**Debug**:
```python
# Add print statements in conversation_node
print(f"Intent detected: {intent}")
print(f"Interactive component: {interactive}")
```

### Issue: Wrong Type of Interactive Message

**Check**:
1. Intent detection working correctly?
2. Keyword lists need adjustment?
3. Multiple intents conflicting?

**Fix**: Adjust keyword priorities or add more specific conditions

### Issue: Interactive Message in Wrong Context

**Check**:
1. Too broad keywords triggering?
2. Need more context checking?

**Fix**: Add context validation before creating interactive message

## 📈 Success Metrics

Track these to measure success:

1. **Interactive Message Usage**
   - How many conversations use interactive messages?
   - Which types are most common?

2. **User Engagement**
   - Do users click buttons/select from lists?
   - Do they complete multi-step flows?

3. **Conversation Efficiency**
   - Faster task completion with interactive messages?
   - Fewer clarifying questions needed?

4. **User Satisfaction**
   - Positive feedback about buttons/lists?
   - Users prefer interactive vs text?

## 🚀 Advanced Testing

### Load Testing

Send multiple messages rapidly:
```python
messages = [
    "What can I learn?",
    "Show me subjects",
    "Can you help?",
    "I need to confirm"
]

for msg in messages:
    send_message(msg)
    time.sleep(1)
```

### Edge Case Testing

Test unusual inputs:
```
- Very long messages (>1000 chars)
- Messages with special characters
- Multiple questions in one message
- Mixed languages
- Only emojis
```

### Integration Testing

Test full flows end-to-end:
```
1. Start conversation
2. Request subjects (get list)
3. Select subject (get difficulty)
4. Choose difficulty (get learning mode)
5. Pick learning mode (start lesson)
6. Verify entire flow completed
```

## 📊 Test Results Template

Document your tests:

```markdown
### Test: [Test Name]
**Date**: YYYY-MM-DD
**Tester**: [Name]

**Input**: "User message here"
**Expected**: Interactive list with subjects
**Actual**: [What actually happened]
**Status**: ✅ Pass / ❌ Fail

**Notes**: [Any observations]
```

---

**Start testing and see automatic interactive messages in action!** 🧪✨
