import logging
import json
from pathlib import Path
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


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a supportive and grounded health & wellness voice companion. The user is interacting with you via voice for their daily check-in.
            
            Your role is to conduct a brief, supportive daily wellness check-in. You need to gather:
            1. Mood & Energy - How they're feeling today, their energy level, any stress or concerns
            2. Daily Intentions - 1-3 practical things they want to accomplish today
            3. Self-care Goals - Any activities for themselves (exercise, rest, hobbies, etc.)
            
            Your approach:
            - Start by greeting them warmly and asking how they're feeling today
            - Ask about their energy level and if anything is stressing them out
            - Ask what 1-3 things they'd like to get done today
            - Ask if there's anything they want to do for themselves
            - Offer simple, realistic, non-medical advice:
              * Break large goals into smaller steps
              * Encourage short breaks or walks
              * Suggest grounding activities (5-minute walk, deep breathing, stretching)
            - At the end, recap their mood, energy, and main objectives
            - Confirm: "Does this sound right?"
            - Once confirmed, use the save_checkin tool to store the session
            
            IMPORTANT BOUNDARIES:
            - You are NOT a medical professional or therapist
            - Never diagnose conditions or provide medical advice
            - Keep suggestions practical, small, and actionable
            - If someone mentions serious distress, gently suggest they speak with a healthcare provider
            
            If there are previous check-ins available, reference them naturally:
            - Compare today's mood/energy to last time
            - Ask about progress on previous goals
            - Acknowledge patterns you notice
            
            Keep responses conversational, warm, and concise. No complex formatting or emojis.""",
        )
        
        # Load previous check-ins
        self.previous_checkins = self._load_previous_checkins()

    def _load_previous_checkins(self) -> list:
        """Load previous check-in data from JSON files"""
        checkins_dir = Path("checkins")
        if not checkins_dir.exists():
            return []
        
        checkins = []
        for file in sorted(checkins_dir.glob("checkin_*.json")):
            try:
                with open(file, "r") as f:
                    checkins.append(json.load(f))
            except Exception as e:
                logger.error(f"Error loading {file}: {e}")
        
        # Return the 5 most recent check-ins
        return checkins[-5:] if checkins else []

    @function_tool
    async def save_checkin(
        self, 
        context: RunContext, 
        mood: str, 
        energy_level: str, 
        stress_factors: str, 
        daily_goals: str, 
        selfcare_activities: str,
        advice_given: str
    ):
        """Use this tool to save a completed wellness check-in to a JSON file. Call this ONLY after confirming all details with the user.
        
        Args:
            mood: Description of the user's current mood (e.g., positive, neutral, low, anxious, calm)
            energy_level: The user's energy level (e.g., high, medium, low, exhausted, energized)
            stress_factors: Any stress or concerns mentioned (or "none" if not applicable)
            daily_goals: Comma-separated list of 1-3 things they want to accomplish today
            selfcare_activities: Self-care or personal activities they plan to do (or "none" if not mentioned)
            advice_given: Brief summary of the advice or suggestions you provided
        """
        
        logger.info(f"Saving wellness check-in")
        
        # Parse goals and activities into lists
        goals_list = [goal.strip() for goal in daily_goals.split(",") if goal.strip()]
        activities_list = [activity.strip() for activity in selfcare_activities.split(",") if activity.strip()] if selfcare_activities.lower() != "none" else []
        
        # Create check-in object
        checkin = {
            "mood": mood,
            "energyLevel": energy_level,
            "stressFactors": stress_factors,
            "dailyGoals": goals_list,
            "selfcareActivities": activities_list,
            "adviceGiven": advice_given,
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        
        # Save to JSON file
        checkins_dir = Path("checkins")
        checkins_dir.mkdir(exist_ok=True)
        
        checkin_filename = f"checkin_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        checkin_path = checkins_dir / checkin_filename
        
        with open(checkin_path, "w") as f:
            json.dump(checkin, f, indent=2)
        
        logger.info(f"Check-in saved to {checkin_path}")
        
        return f"Check-in saved successfully! I've recorded your mood, energy level, and goals for today. Take care and remember to be kind to yourself!"

    async def get_context(self) -> str:
        """Get context from previous check-ins to inform the conversation"""
        if not self.previous_checkins:
            return "This is the first check-in session."
        
        last_checkin = self.previous_checkins[-1]
        context = f"Previous check-in from {last_checkin.get('date', 'recently')}: "
        context += f"Mood was {last_checkin.get('mood', 'not recorded')}, "
        context += f"energy was {last_checkin.get('energyLevel', 'not recorded')}. "
        
        if last_checkin.get('dailyGoals'):
            context += f"Goals included: {', '.join(last_checkin['dailyGoals'][:2])}."
        
        return context


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
        agent=Assistant(),
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
