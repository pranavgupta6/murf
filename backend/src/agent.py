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
            instructions="""You are a friendly and enthusiastic barista working at Murf Coffee Shop, the best coffee shop in town powered by AI. The user is interacting with you via voice.
            
            Your job is to take coffee orders from customers. You need to gather the following information for each order:
            1. Drink type (e.g., latte, cappuccino, espresso, americano, mocha, flat white, etc.)
            2. Size (small, medium, or large)
            3. Milk preference (whole milk, skim milk, oat milk, almond milk, soy milk, or no milk)
            4. Extras (e.g., extra shot, whipped cream, caramel drizzle, vanilla syrup, chocolate syrup, cinnamon, etc.)
            5. Customer name for the order
            
            Start by greeting the customer warmly and asking what they would like to order.
            Ask clarifying questions one at a time to gather all the information needed.
            Be conversational and friendly, making suggestions when appropriate.
            Once you have all the information, confirm the complete order with the customer.
            After confirmation, use the save_order tool to finalize the order.
            
            Keep your responses concise and natural, without complex formatting, emojis, or asterisks.
            Be enthusiastic about coffee and make the customer feel welcome.""",
        )
        
        # Initialize order state
        self.current_order = {
            "drinkType": None,
            "size": None,
            "milk": None,
            "extras": [],
            "name": None
        }

    @function_tool
    async def save_order(self, context: RunContext, drink_type: str, size: str, milk: str, extras: str, customer_name: str):
        """Use this tool to save a completed coffee order to a JSON file. Call this ONLY after confirming all order details with the customer.
        
        Args:
            drink_type: The type of drink ordered (e.g., latte, cappuccino, espresso)
            size: The size of the drink (small, medium, or large)
            milk: The type of milk (whole, skim, oat, almond, soy, or none)
            extras: Comma-separated list of extras (e.g., extra shot, whipped cream, vanilla syrup)
            customer_name: The customer's name for the order
        """
        
        logger.info(f"Saving order for {customer_name}")
        
        # Parse extras into a list
        extras_list = [extra.strip() for extra in extras.split(",") if extra.strip()] if extras else []
        
        # Create order object
        order = {
            "drinkType": drink_type,
            "size": size,
            "milk": milk,
            "extras": extras_list,
            "name": customer_name,
            "timestamp": datetime.now().isoformat(),
            "status": "confirmed"
        }
        
        # Save to JSON file
        orders_dir = Path("orders")
        orders_dir.mkdir(exist_ok=True)
        
        order_filename = f"order_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{customer_name.replace(' ', '_')}.json"
        order_path = orders_dir / order_filename
        
        with open(order_path, "w") as f:
            json.dump(order, f, indent=2)
        
        logger.info(f"Order saved to {order_path}")
        
        return f"Order saved successfully! Your {size} {drink_type} with {milk} will be ready soon, {customer_name}. Order ID: {order_filename}"


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
