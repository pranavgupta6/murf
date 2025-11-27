# Fraud Alert Voice Agent - SecureBank India

## 🎯 Challenge: Day 6 - Fraud Alert Voice Agent

### Status: ✅ PRIMARY GOAL COMPLETE

This is a fully functional fraud detection voice agent for **SecureBank India** that handles suspicious transaction verification calls.

---

## 📋 MVP Completion Checklist

- ✅ **Sample fraud cases database created** - 5 detailed fraud cases with all required fields
- ✅ **Fraud agent persona implemented** - Professional, calm, reassuring bank fraud representative
- ✅ **Load fraud case at call start** - Agent asks for customer name and loads their case from database
- ✅ **Simple call flow implemented**:
  - ✅ Greets and explains purpose
  - ✅ Asks for customer name
  - ✅ Performs identity verification (security question only - no sensitive data)
  - ✅ Reads transaction details clearly
  - ✅ Asks if customer authorized transaction
  - ✅ Takes appropriate action based on response
  - ✅ Ends call professionally
- ✅ **Update fraud case in database** - Status and outcome notes saved after call completion

---

## 🏗️ Architecture

### Files Created/Modified

1. **`backend/src/agent.py`** - Main fraud alert agent (replaced SDR agent)
   - `FraudAlertAgent` class with fraud detection logic
   - 6 function tools for case management and verification
   
2. **`backend/shared-data/fraud_cases_database.json`** - Fraud cases database
   - 5 sample fraud cases
   - All fake data (no real information)
   
3. **`backend/src/agent_sdr_backup.py`** - Backup of previous SDR agent

---

## 🗂️ Database Structure

**File**: `backend/shared-data/fraud_cases_database.json`

### Fraud Case Schema:
```json
{
  "userName": "John Smith",
  "securityIdentifier": "12345",
  "cardEnding": "4242",
  "securityQuestion": "What is your mother's maiden name?",
  "securityAnswer": "Johnson",
  "transactionAmount": "$1,247.50",
  "transactionName": "ABC Electronics Industry",
  "transactionTime": "November 26, 2025 at 3:42 PM",
  "transactionCategory": "e-commerce",
  "transactionSource": "alibaba.com",
  "transactionLocation": "Shanghai, China",
  "status": "pending_review",
  "case": "pending",
  "outcome_note": ""
}
```

### Sample Cases Included:

1. **John Smith** - $1,247.50 at ABC Electronics (alibaba.com from China)
   - Security Q: Mother's maiden name? A: Johnson
   
2. **Sarah Johnson** - $3,899.00 at Luxury Watches (Dubai)
   - Security Q: Birth city? A: Mumbai
   
3. **Raj Kumar** - $567.25 at GameStop Digital (Los Angeles)
   - Security Q: Favorite color? A: Blue
   
4. **Priya Sharma** - $2,150.00 at Crypto Exchange (Singapore)
   - Security Q: Pet's name? A: Max
   
5. **Michael Chen** - $450.00 at Premium Streaming (London)
   - Security Q: First car? A: Honda Civic

---

## 🎭 Agent Behavior

### Call Flow

1. **Introduction**
   - "This is the Fraud Prevention Department from SecureBank India"
   - Explains calling about suspicious transaction
   - Maintains calm, professional tone

2. **Customer Identification**
   - Asks: "May I have your full name please?"
   - Uses `get_fraud_case()` tool to load their case
   - If not found, apologizes and suggests contacting main line

3. **Identity Verification** (SAFE - NO SENSITIVE DATA)
   - Asks security question from their profile
   - ⚠️ **Never asks for**: Card numbers, CVV, PIN, passwords
   - ✅ **Only asks**: Pre-stored security question
   - Uses `verify_security_answer()` tool
   - 2 attempts allowed
   - Fails gracefully with `mark_verification_failed()` if needed

4. **Transaction Details**
   - Once verified, reads suspicious transaction:
     - Merchant name
     - Amount
     - Date/time
     - Location
     - Card ending (last 4 digits only)
   - Can use `read_transaction_details()` tool

5. **Confirmation**
   - "Did you make or authorize this transaction?"
   - Listens for yes/no
   - **If YES**: `mark_case_safe()` - confirms legitimate
   - **If NO**: `mark_case_fraudulent()` - blocks card, initiates dispute

6. **Closing**
   - Thanks customer
   - Summarizes action taken
   - Reassures account security
   - Professional goodbye

---

## 🔧 Function Tools (6 Total)

### 1. `get_fraud_case(customer_name)`
**Purpose**: Load fraud case from database by customer name

**Input**: Customer's full name (e.g., "John Smith")

**Returns**: 
- Success: Case loaded message with security identifier
- Failure: Apology message if case not found

**Action**: Sets `self.current_case` with customer's fraud data

---

### 2. `verify_security_answer(customer_answer)`
**Purpose**: Verify customer identity using security answer

**Input**: Customer's answer to security question

**Returns**:
- Success: Confirmation message, sets `self.is_verified = True`
- Failure: Error message with remaining attempts
- Max attempts: "Cannot verify identity" message

**Tracking**: Increments `self.verification_attempts` (max: 2)

---

### 3. `mark_verification_failed()`
**Purpose**: Mark case when customer fails identity verification

**Returns**: Call termination message

**Action**: 
- Updates database: `status = 'verification_failed'`
- Adds outcome note
- Saves database

---

### 4. `read_transaction_details()`
**Purpose**: Read suspicious transaction details to customer

**Pre-condition**: Customer must be verified

**Returns**: Formatted transaction details (amount, merchant, location, time, card)

**Action**: Logs transaction read event

---

### 5. `mark_case_safe()`
**Purpose**: Mark case as safe when customer confirms transaction

**Pre-condition**: Customer must be verified

**Returns**: Confirmation message with reassurance

**Action**:
- Updates database: `status = 'confirmed_safe'`, `case = 'safe'`
- Adds outcome note with customer confirmation
- Saves database

---

### 6. `mark_case_fraudulent()`
**Purpose**: Mark case as fraud when customer denies transaction

**Pre-condition**: Customer must be verified

**Returns**: Detailed message with actions taken (card blocked, dispute initiated)

**Action**:
- Updates database: `status = 'confirmed_fraud'`, `case = 'fraudulent'`
- Adds outcome note with fraud confirmation
- Saves database

---

## 🚀 How to Use

### Start the Agent

```bash
cd backend

# Install dependencies (if not already done)
uv sync

# Download required models
uv run python src/agent.py download-files

# Run in console mode (test directly)
uv run python src/agent.py console
```

### Test Conversation Examples

#### Example 1: Transaction Confirmed Safe

```
Agent: "Good day! This is the Fraud Prevention Department from SecureBank India. 
        We're calling about a suspicious transaction on your account. May I have 
        your full name please?"

You: "John Smith"

Agent: [Uses get_fraud_case tool]
       "Thank you, Mr. Smith. For security purposes, I need to verify your identity. 
        What is your mother's maiden name?"

You: "Johnson"

Agent: [Uses verify_security_answer tool]
       "Thank you for verifying your identity. We detected a transaction of $1,247.50 
        at ABC Electronics Industry on alibaba.com from Shanghai, China on November 26th 
        at 3:42 PM using your card ending in 4242. Did you make or authorize this transaction?"

You: "Yes, I did. I ordered some electronics."

Agent: [Uses mark_case_safe tool]
       "Perfect! I've updated our records to show this transaction was authorized by you. 
        Your account remains secure. Thank you for confirming this with us."
```

#### Example 2: Fraudulent Transaction Detected

```
Agent: "Good day! This is the Fraud Prevention Department from SecureBank India..."

You: "Priya Sharma"

Agent: "For security, what is your pet's name?"

You: "Max"

Agent: [Verified] "We detected a transaction of $2,150.00 at Crypto Exchange Pro 
        on cryptoexchangepro.io from Singapore on November 26th at 9:30 PM 
        using your card ending in 3456. Did you make this transaction?"

You: "No! I didn't make that purchase!"

Agent: [Uses mark_case_fraudulent tool]
       "I understand. For your protection, I have immediately:
        1. Blocked your card ending in 3456
        2. Initiated a fraud dispute for the $2,150.00 transaction
        3. Flagged this for investigation
        4. Prevented any further charges
        
        You'll receive a new card within 5-7 business days. The fraudulent 
        charge will be reversed within 7-10 business days."
```

#### Example 3: Failed Verification

```
Agent: "What is your mother's maiden name?"

You: "Williams"

Agent: [Wrong answer] "I'm sorry, that doesn't match our records. 
        You have 1 more attempt."

You: "Smith"

Agent: [Wrong again] "I'm sorry, but I cannot verify your identity. 
        For your security, I cannot proceed. Please visit your nearest 
        branch or call our main customer service line. Goodbye."

[Uses mark_verification_failed tool - case updated in database]
```

---

## 📊 Database Updates

### After Each Call, Database is Updated:

**Safe Transaction:**
```json
{
  "status": "confirmed_safe",
  "case": "safe",
  "outcome_note": "Customer John Smith confirmed they authorized this transaction. No fraud detected."
}
```

**Fraudulent Transaction:**
```json
{
  "status": "confirmed_fraud",
  "case": "fraudulent",
  "outcome_note": "Customer Priya Sharma denied making this transaction. Fraud confirmed. Card blocked and dispute initiated."
}
```

**Verification Failed:**
```json
{
  "status": "verification_failed",
  "case": "pending",
  "outcome_note": "Customer failed identity verification. Call terminated for security."
}
```

---

## 🔒 Security Features

### What Agent NEVER Asks For:
- ❌ Full card numbers
- ❌ CVV/CVC codes
- ❌ PINs
- ❌ Passwords
- ❌ Social Security Numbers
- ❌ Account numbers

### What Agent DOES Use:
- ✅ Pre-stored security questions only
- ✅ Non-sensitive verification
- ✅ Limited attempt verification (2 max)
- ✅ Graceful failure handling

---

## 🎯 Key Features

1. **Safe Identity Verification** - Uses security questions, not sensitive data
2. **Clear Transaction Details** - Reads all relevant info clearly
3. **Professional Tone** - Calm, reassuring, empathetic
4. **Database Integration** - Loads and updates cases automatically
5. **Fraud Protection Actions** - Blocks cards, initiates disputes
6. **Verification Failure Handling** - Terminates safely if identity unverified
7. **Comprehensive Logging** - All actions logged for audit trail

---

## 🧪 Testing Checklist

Test these scenarios:

- [ ] Agent introduces itself as SecureBank fraud department
- [ ] Agent asks for customer name
- [ ] Agent loads correct fraud case from database
- [ ] Agent asks security question (not sensitive data)
- [ ] Correct answer → proceeds to transaction details
- [ ] Wrong answer → gives second chance
- [ ] 2 wrong answers → terminates call, marks verification_failed
- [ ] Agent reads transaction details clearly
- [ ] Customer says "Yes" → marks case safe, updates database
- [ ] Customer says "No" → marks case fraudulent, blocks card, updates database
- [ ] Database file is updated with correct status and outcome_note
- [ ] Agent never asks for card numbers, PINs, or passwords

---

## 📈 Next Steps (Advanced Goals - Optional)

Beyond the MVP, you could add:

1. **LiveKit Telephony Integration** - Make it work with real phone calls
2. **Multiple Fraud Cases** - Handle customers with multiple suspicious transactions
3. **DTMF Input** - Allow keypad input (press 1 for yes, 2 for no)
4. **SMS Notifications** - Send confirmation SMS after call
5. **Email Reports** - Email detailed fraud report to customer
6. **Escalation** - Transfer to human agent if needed
7. **Multi-language Support** - Hindi, Tamil, Telugu, etc.
8. **Voice Biometrics** - Additional voice-based verification

---

## 🐛 Troubleshooting

### Issue: Agent can't find customer
- Check customer name spelling matches exactly in database
- Names are case-insensitive but must match full name

### Issue: Verification always fails
- Check security answers in database are correct
- Answers are case-insensitive

### Issue: Database not updating
- Check file permissions on `fraud_cases_database.json`
- Verify `save_fraud_database()` function is called
- Check logs for errors

---

## 📝 Important Notes

⚠️ **ALL DATA IS FAKE** ⚠️

- This is a demo/sandbox implementation
- No real card numbers, PINs, or personal information
- All transactions are fictional
- All names and details are made up

**Do not use this with real customer data without proper security measures!**

---

## 🎉 Challenge Complete!

You've successfully built a fraud alert voice agent that:
- ✅ Loads fraud cases from a database
- ✅ Verifies customer identity safely
- ✅ Reads transaction details clearly
- ✅ Handles customer responses appropriately
- ✅ Updates case status in database
- ✅ Never asks for sensitive information

**Primary Goal: COMPLETE** 🚀

---

**Built for the Ten Days of Voice Agents Challenge by murf.ai**

*Implementation Date: November 27, 2025*
