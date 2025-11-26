import logging
import json
from pathlib import Path
from typing import Annotated
from datetime import datetime

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    WorkerOptions,
    cli,
    metrics,
    tokenize,
    function_tool,
    RunContext
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Load company data for SDR
def load_company_data():
    """Load the company FAQ and information from JSON file"""
    content_path = Path("shared-data/razorpay_company_data.json")
    with open(content_path, "r") as f:
        return json.load(f)

COMPANY_DATA = load_company_data()


class SDRAgent(Agent):
    """Sales Development Representative agent that answers FAQ and captures leads"""
    
    def __init__(self) -> None:
        # Build FAQ reference for the agent
        faq_list = "\n".join([
            f"Q: {faq['question']}\nA: {faq['answer']}" 
            for faq in COMPANY_DATA['faqs']
        ])
        
        company_name = COMPANY_DATA['company']['name']
        company_desc = COMPANY_DATA['company']['description']
        
        super().__init__(
            instructions=f"""You are Arjun, a friendly and professional Sales Development Representative (SDR) for {company_name}.

ABOUT {company_name.upper()}:
{company_desc}

YOUR ROLE:
1. **Warm Greeting**: Start with a warm, professional greeting. Introduce yourself as Arjun from {company_name}. Example: "Hi! I'm Arjun from Razorpay. How are you doing today?"

2. **Discovery**: Ask open-ended questions to understand:
   - What brought them here today?
   - What they're currently working on or what challenges they face
   - Their business needs and goals

3. **Answer Questions**: Use the FAQ knowledge below to answer their questions accurately. If asked about something not in the FAQ, politely say you'll need to connect them with a specialist.

FAQ KNOWLEDGE BASE:
{faq_list}

4. **Lead Qualification**: Throughout the conversation, naturally gather:
   - Their name
   - Company name
   - Email address
   - Their role/position
   - What they want to use {company_name} for (use case)
   - Their team size
   - Their timeline (are they looking to start now, soon, or just exploring?)

Use the function tools to save each piece of information as you collect it.

5. **Closing**: When they indicate they're done (e.g., "That's all", "I'm done", "Thanks, bye"), use the end_call_with_summary tool to:
   - Thank them for their time
   - Provide a brief verbal summary of what you learned
   - Let them know someone will follow up
   - Save the complete lead information

CONVERSATION STYLE:
- Be conversational and natural, not robotic
- Listen actively and show genuine interest
- Don't ask all questions at once - weave them naturally into the conversation
- Be helpful and focus on understanding their needs
- Stay professional but friendly

Remember: You're here to help them understand {company_name} and determine if it's a good fit for their needs.""",
        )
        
        # Initialize lead data storage
        self.lead_data = {
            "name": None,
            "company": None,
            "email": None,
            "role": None,
            "use_case": None,
            "team_size": None,
            "timeline": None,
            "timestamp": None,
            "conversation_notes": []
        }

    @function_tool
    async def save_lead_name(
        self, 
        name: Annotated[str, "The lead's full name"],
        context: RunContext
    ):
        """Save the lead's name"""
        self.lead_data["name"] = name
        logger.info(f"Saved lead name: {name}")
        return f"Saved name: {name}"

    @function_tool
    async def save_lead_company(
        self, 
        company: Annotated[str, "The lead's company name"],
        context: RunContext
    ):
        """Save the lead's company name"""
        self.lead_data["company"] = company
        logger.info(f"Saved lead company: {company}")
        return f"Saved company: {company}"

    @function_tool
    async def save_lead_email(
        self, 
        email: Annotated[str, "The lead's email address"],
        context: RunContext
    ):
        """Save the lead's email address"""
        self.lead_data["email"] = email
        logger.info(f"Saved lead email: {email}")
        return f"Saved email: {email}"

    @function_tool
    async def save_lead_role(
        self, 
        role: Annotated[str, "The lead's job title or role"],
        context: RunContext
    ):
        """Save the lead's role or job title"""
        self.lead_data["role"] = role
        logger.info(f"Saved lead role: {role}")
        return f"Saved role: {role}"

    @function_tool
    async def save_lead_use_case(
        self, 
        use_case: Annotated[str, "What the lead wants to use the product for"],
        context: RunContext
    ):
        """Save the lead's use case or what they want to use the product for"""
        self.lead_data["use_case"] = use_case
        logger.info(f"Saved lead use case: {use_case}")
        return f"Saved use case: {use_case}"

    @function_tool
    async def save_lead_team_size(
        self, 
        team_size: Annotated[str, "The size of the lead's team or company"],
        context: RunContext
    ):
        """Save the lead's team size"""
        self.lead_data["team_size"] = team_size
        logger.info(f"Saved lead team size: {team_size}")
        return f"Saved team size: {team_size}"

    @function_tool
    async def save_lead_timeline(
        self, 
        timeline: Annotated[str, "When the lead wants to get started (now/soon/later/exploring)"],
        context: RunContext
    ):
        """Save the lead's timeline for getting started"""
        self.lead_data["timeline"] = timeline
        logger.info(f"Saved lead timeline: {timeline}")
        return f"Saved timeline: {timeline}"

    @function_tool
    async def add_conversation_note(
        self, 
        note: Annotated[str, "Important point or insight from the conversation"],
        context: RunContext
    ):
        """Add a note about something important mentioned in the conversation"""
        self.lead_data["conversation_notes"].append(note)
        logger.info(f"Added conversation note: {note}")
        return f"Note saved"

    @function_tool
    async def search_faq(
        self, 
        question: Annotated[str, "The user's question to search for in the FAQ"],
        context: RunContext
    ):
        """Search the FAQ knowledge base for relevant answers"""
        # Simple keyword search
        question_lower = question.lower()
        relevant_faqs = []
        
        for faq in COMPANY_DATA['faqs']:
            if (question_lower in faq['question'].lower() or 
                question_lower in faq['answer'].lower() or
                any(word in faq['question'].lower() or word in faq['answer'].lower() 
                    for word in question_lower.split() if len(word) > 3)):
                relevant_faqs.append(f"Q: {faq['question']}\nA: {faq['answer']}")
        
        if relevant_faqs:
            return "\n\n".join(relevant_faqs[:3])  # Return top 3 matches
        else:
            return "No specific FAQ found for this question. Use general knowledge from the instructions."

    @function_tool
    async def end_call_with_summary(self, context: RunContext):
        """End the call and save the complete lead summary. Use this when the user indicates they're done."""
        # Add timestamp
        self.lead_data["timestamp"] = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save lead to JSON file
        lead_filename = f"lead_{self.lead_data['timestamp']}_{self.lead_data.get('name', 'Unknown').replace(' ', '_')}.json"
        lead_path = Path("leads") / lead_filename
        
        with open(lead_path, "w") as f:
            json.dump(self.lead_data, f, indent=2)
        
        logger.info(f"Lead saved to {lead_path}")
        
        # Create verbal summary
        name = self.lead_data.get('name', 'the prospect')
        company = self.lead_data.get('company', 'their company')
        use_case = self.lead_data.get('use_case', 'their needs')
        timeline = self.lead_data.get('timeline', 'their timeline')
        
        summary = f"""Thank you so much for your time today, {name}! Let me quickly recap what we discussed:

You're from {company}, and you're interested in using Razorpay for {use_case}. Based on our conversation, your timeline is {timeline}.

I've captured all your details, and someone from our team will reach out to you shortly at the email address you provided. We're excited about the possibility of working with you!

Is there anything else I can help you with before we wrap up?"""
        
        return summary


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using OpenAI, Cartesia, AssemblyAI, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
                model="gemini-2.5-flash",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
                voice="en-US-matthew", 
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # Metrics collection, to measure pipeline performance
    # For more information, see https://docs.livekit.io/agents/build/metrics/
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=SDRAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
