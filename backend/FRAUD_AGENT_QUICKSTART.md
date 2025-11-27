# Quick Start - Fraud Alert Agent Testing

## 🚀 5-Minute Test Guide

### Step 1: Start the Agent

```bash
cd backend
uv run python src/agent.py console
```

### Step 2: Test with Sample Customer

**Available Test Customers:**

| Name | Security Question | Answer | Transaction |
|------|-------------------|--------|-------------|
| John Smith | Mother's maiden name? | Johnson | $1,247.50 - ABC Electronics |
| Sarah Johnson | Birth city? | Mumbai | $3,899.00 - Luxury Watches |
| Raj Kumar | Favorite color? | Blue | $567.25 - GameStop |
| Priya Sharma | Pet's name? | Max | $2,150.00 - Crypto Exchange |
| Michael Chen | First car? | Honda Civic | $450.00 - Streaming Service |

---

## 📋 Test Scenarios

### ✅ Scenario 1: Legitimate Transaction (SAFE)

**What to say:**

```
Agent: "May I have your full name please?"
You: "John Smith"

Agent: "What is your mother's maiden name?"
You: "Johnson"

Agent: [Reads transaction details]
      "Did you make or authorize this transaction?"
You: "Yes, I did"

Agent: "Perfect! Your account remains secure..."
```

**Expected Result:**
- ✅ Case marked as "confirmed_safe"
- ✅ Database updated with safe status
- ✅ No card blocking action

**Verify:**
```bash
cat backend/shared-data/fraud_cases_database.json | grep -A 15 "John Smith"
```
Should show `"case": "safe"`

---

### ❌ Scenario 2: Fraudulent Transaction (FRAUD)

**What to say:**

```
You: "Priya Sharma"

Agent: "What is your pet's name?"
You: "Max"

Agent: [Reads transaction details about $2,150 crypto purchase]
You: "No! I didn't make that transaction!"

Agent: "I understand. For your protection, I have:
       1. Blocked your card ending in 3456
       2. Initiated a fraud dispute..."
```

**Expected Result:**
- ✅ Case marked as "confirmed_fraud"
- ✅ Card blocking message
- ✅ Dispute initiated message
- ✅ New card promised in 5-7 days

**Verify:**
```bash
cat backend/shared-data/fraud_cases_database.json | grep -A 15 "Priya Sharma"
```
Should show `"case": "fraudulent"`

---

### 🚫 Scenario 3: Failed Verification

**What to say:**

```
You: "Raj Kumar"

Agent: "What is your favorite color?"
You: "Red"  # WRONG (correct is Blue)

Agent: "That doesn't match. You have 1 more attempt."
You: "Green"  # WRONG AGAIN

Agent: "I cannot verify your identity. Please visit your nearest branch. Goodbye."
```

**Expected Result:**
- ✅ Call terminated after 2 failed attempts
- ✅ Case marked as "verification_failed"
- ✅ No transaction details revealed

**Verify:**
```bash
cat backend/shared-data/fraud_cases_database.json | grep -A 15 "Raj Kumar"
```
Should show `"status": "verification_failed"`

---

### 🔍 Scenario 4: Customer Not Found

**What to say:**

```
You: "Random Person"

Agent: "I apologize, but I cannot find a fraud case for Random Person 
       in our system. There may have been an error."
```

**Expected Result:**
- ✅ Polite error message
- ✅ No case loaded
- ✅ Suggests contacting fraud department directly

---

## 🎯 Success Criteria

Your agent is working correctly if:

1. ✅ Introduces itself as SecureBank fraud department
2. ✅ Asks for customer name and loads their case
3. ✅ Asks security question (NOT sensitive data)
4. ✅ Verifies answer before proceeding
5. ✅ Reads transaction details after verification
6. ✅ Asks if customer authorized transaction
7. ✅ Marks safe when customer says "yes"
8. ✅ Marks fraudulent when customer says "no"
9. ✅ Updates database file correctly
10. ✅ Handles verification failures gracefully

---

## 📊 Check Database Updates

After each test, check the database was updated:

```bash
# View the entire database
cat backend/shared-data/fraud_cases_database.json

# Or open in VS Code
code backend/shared-data/fraud_cases_database.json
```

Look for these fields being updated:
- `"status"`: Should change from "pending_review" to "confirmed_safe", "confirmed_fraud", or "verification_failed"
- `"case"`: Should change from "pending" to "safe" or "fraudulent"
- `"outcome_note"`: Should contain details about what happened

---

## 🔄 Reset Database

To reset all cases back to pending for fresh testing:

```bash
# The database resets each time you restart the agent since we reload it fresh
# Or manually edit the JSON file and set:
"status": "pending_review",
"case": "pending",
"outcome_note": ""
```

---

## 🐛 Common Issues

### Agent doesn't ask security question
- Make sure the case loaded successfully (check console logs)
- Verify customer name matches exactly in database

### Verification always fails
- Check your answer matches the database exactly
- Answers are case-insensitive ("Johnson" = "johnson")

### Database not updating
- Check file permissions on fraud_cases_database.json
- Look for error messages in console

### Agent asks for card number or PIN
- **This should NEVER happen!** 
- If it does, there's a bug - agent should only ask security question

---

## 💡 Pro Tips

1. **Console Logs**: Watch the terminal output - it shows all tool calls and data updates
2. **Natural Speech**: Talk naturally - don't just say "yes" or "no", say "Yes, I made that purchase"
3. **Test All Cases**: Try all 5 customers to ensure database lookup works correctly
4. **Check Updates**: After EVERY call, verify the database was updated
5. **Security Focus**: Notice the agent NEVER asks for sensitive data

---

## 🎉 You're Done!

Once you've tested all scenarios and verified:
- Agent behavior is professional and clear
- Security questions work correctly
- Database updates properly
- No sensitive data is requested

**You've completed the Fraud Alert Voice Agent challenge!** 🚀

---

## 📚 Next Steps

1. Try the advanced goals (telephony, multiple cases, DTMF)
2. Add more fraud cases to the database
3. Customize the security questions
4. Add SMS notifications
5. Integrate with a real CRM system

---

**Need Help?** Check the full documentation in `FRAUD_AGENT_README.md`
