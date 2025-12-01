import logging
import json
import random
from pathlib import Path
from typing import Annotated

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
    function_tool,
)
from livekit.plugins import murf, google, deepgram, noise_cancellation

logger = logging.getLogger("agent")

load_dotenv(".env.local")


def load_scenarios():
    """Load improv scenarios from JSON file"""
    scenarios_path = Path("shared-data/improv_scenarios.json")
    with open(scenarios_path, "r") as f:
        data = json.load(f)
        return data['scenarios']


class ImprovHostAgent(Agent):
    """Voice Improv Battle Game Show Host"""
    
    def __init__(self, player_name=None) -> None:
        # Load scenarios
        self.all_scenarios = load_scenarios()
        
        # Game state
        self.improv_state = {
            "player_name": player_name,
            "current_round": 0,
            "max_rounds": 4,
            "rounds": [],  # [{scenario, host_reaction}]
            "phase": "intro",  # "intro" | "awaiting_improv" | "reacting" | "done"
            "current_scenario": None,
            "used_scenario_ids": set()
        }
        
        # Build instructions with player name if available
        name_instruction = ""
        if player_name:
            name_instruction = f"""
⚠️ CRITICAL - PLAYER NAME:
The player's name is: {player_name}
Greet them by name immediately! Say "Welcome to IMPROV BATTLE, {player_name}!"
DO NOT ask for their name - you already have it!
"""
        else:
            name_instruction = """
⚠️ CRITICAL - PLAYER NAME HANDLING:
The player has NOT provided their name yet.
Ask them "What's your name?" and wait for their response, then call set_player_name()
"""
        
        super().__init__(
            instructions=f"""You are the host of a high-energy TV improv show called "IMPROV BATTLE"!

🎭 YOUR ROLE:
You're a charismatic, witty game show host who guides contestants through short-form improv scenarios. Think of yourself as a mix between a comedy club MC and a game show host - supportive but honest, energetic but grounded.

{name_instruction}

🎯 SHOW STRUCTURE:

1. INTRODUCTION (Phase: "intro"):
   - Welcome the player enthusiastically!
   - Use their name if you have it, otherwise ask for it first
   - Briefly explain the game:
     * They'll get several improv scenarios
     * They act out each scene in character
     * You'll react and comment after each one
     * It's all about creativity and commitment to the bit
   - Set the energy: "Let's see what you've got!"
   - Call start_next_scenario() to begin Round 1

2. EACH ROUND (Phases: "awaiting_improv" → "reacting"):
   
   When awaiting_improv:
   - Present the scenario clearly and vividly
   - Tell them WHO they are and WHAT'S happening
   - Give them a clear cue to start: "Annnnnd... ACTION!" or "Go for it!" or "Show me what you've got!"
   - Then LISTEN - let them perform!
   
   When they finish (they'll say "end scene" or pause significantly):
   - React authentically to what they just did
   - Comment specifically on their performance:
     * What worked? What was funny/creative/unexpected?
     * What could have been stronger? (Be honest but constructive)
     * Did they commit to the character?
   - Vary your tone:
     * Sometimes: Enthusiastic praise ("That was BRILLIANT!")
     * Sometimes: Constructive critique ("I wanted more energy there")
     * Sometimes: Playful teasing ("Did you just make up a word?")
     * Sometimes: Surprised delight ("Okay, did NOT see that coming!")
   - Call end_scene() with your reaction
   - If more rounds remain, call start_next_scenario() to continue

3. FINAL WRAP-UP (Phase: "done"):
   - Summarize their improv style:
     * Are they absurdist? Character-driven? Quick-witted?
     * What moments stood out across all scenes?
   - Give them an "improviser type" label (e.g., "The Absurdist", "The Character Actor")
   - Thank them for playing and sign off with energy!

💬 HOSTING STYLE:
- HIGH ENERGY but not overwhelming
- HONEST reactions - don't fake enthusiasm
- SPECIFIC feedback - reference actual things they said/did
- VARIED tones - mix praise, critique, surprise, amusement
- KEEP IT MOVING - don't let scenes drag
- STAY POSITIVE overall but don't sugarcoat everything
- Use phrases like:
  * "Okay, okay, I see what you're doing here..."
  * "That was... interesting. Let me think about that."
  * "YES! That's exactly the commitment I'm looking for!"
  * "Hmm, I feel like you could've pushed that further."
  * "Wait, wait - did you just...? (laughs)"

🎬 SCENE MANAGEMENT:
- When they pause or say "end scene", that's your cue to react
- If a scene is going too long (more than 3-4 player turns), gently wrap it: "Annnd SCENE! Let's talk about that."
- If they're struggling, you can offer a gentle redirect: "Remember, you're a [character] who's trying to [goal]..."

🚪 EARLY EXIT:
- If player says "stop game", "I want to quit", "end show":
  * Call early_exit()
  * Thank them graciously
  * Give a quick summary even if incomplete
  * "No worries! Thanks for playing IMPROV BATTLE!"

🎯 KEY RULES:
1. Always call start_next_scenario() to begin each round
2. Always call end_scene() when they finish performing
3. Let them PERFORM - don't interrupt mid-scene
4. React to what they ACTUALLY did, not generic praise
5. Keep energy high but authentic
6. Call early_exit() if they want to stop

Remember: This is THEIR show. Your job is to set them up for success, react authentically, and keep the energy flowing!
""",
        )
    
    @function_tool
    async def start_next_scenario(self):
        """
        Start the next improv round by selecting and presenting a new scenario.
        Call this after intro and after each end_scene (if rounds remain).
        """
        logger.info("Starting next improv scenario")
        
        # Check if game is complete
        if self.improv_state["current_round"] >= self.improv_state["max_rounds"]:
            self.improv_state["phase"] = "done"
            return {
                "success": False,
                "message": "All rounds complete! Time to wrap up the show.",
                "game_complete": True
            }
        
        # Select a random unused scenario
        available_scenarios = [
            s for s in self.all_scenarios 
            if s['id'] not in self.improv_state["used_scenario_ids"]
        ]
        
        if not available_scenarios:
            # Reset if we've used all scenarios (unlikely with 15)
            self.improv_state["used_scenario_ids"].clear()
            available_scenarios = self.all_scenarios
        
        scenario = random.choice(available_scenarios)
        self.improv_state["used_scenario_ids"].add(scenario['id'])
        
        # Increment round
        self.improv_state["current_round"] += 1
        self.improv_state["current_scenario"] = scenario
        self.improv_state["phase"] = "awaiting_improv"
        
        return {
            "success": True,
            "round_number": self.improv_state["current_round"],
            "total_rounds": self.improv_state["max_rounds"],
            "scenario": scenario['description'],
            "message": f"Round {self.improv_state['current_round']} of {self.improv_state['max_rounds']}: {scenario['description']}"
        }
    
    @function_tool
    async def end_scene(
        self,
        host_reaction: Annotated[str, "Your detailed reaction and commentary on the player's performance"]
    ):
        """
        End the current improv scene and record your reaction.
        Call this after the player finishes their performance and you've given feedback.
        """
        logger.info(f"Ending scene with reaction: {host_reaction[:100]}...")
        
        if self.improv_state["phase"] != "awaiting_improv":
            return {
                "success": False,
                "message": "No active scene to end"
            }
        
        # Record the round
        round_data = {
            "round_number": self.improv_state["current_round"],
            "scenario": self.improv_state["current_scenario"]["description"],
            "host_reaction": host_reaction
        }
        self.improv_state["rounds"].append(round_data)
        
        # Move to reacting phase
        self.improv_state["phase"] = "reacting"
        
        # Check if more rounds remain
        more_rounds = self.improv_state["current_round"] < self.improv_state["max_rounds"]
        
        return {
            "success": True,
            "round_completed": self.improv_state["current_round"],
            "more_rounds": more_rounds,
            "message": "Scene ended and reaction recorded. " + 
                      ("Call start_next_scenario() to continue." if more_rounds else "All rounds complete!")
        }
    
    @function_tool
    async def early_exit(self):
        """
        Handle early exit when player wants to stop the game.
        Call this if player says they want to quit or stop.
        """
        logger.info("Player requested early exit")
        
        self.improv_state["phase"] = "done"
        
        return {
            "success": True,
            "rounds_completed": self.improv_state["current_round"],
            "message": f"Game ended early. Player completed {self.improv_state['current_round']} round(s)."
        }
    
    @function_tool
    async def set_player_name(
        self,
        name: Annotated[str, "The player's name"]
    ):
        """
        Set the player's name. Use this when they introduce themselves.
        """
        logger.info(f"Setting player name: {name}")
        
        self.improv_state["player_name"] = name
        
        return {
            "success": True,
            "player_name": name,
            "message": f"Player name set to {name}"
        }


async def prewarm(proc: JobProcess):
    """Prewarm the model and resources before handling requests"""
    await proc.userdata


async def entrypoint(ctx: JobContext):
    """Main entry point for the agent"""
    logger.info("Starting Improv Battle game show host")
    
    # Join the room and connect to the user
    await ctx.connect()
    
    # Wait a moment for participant metadata to be available
    import asyncio
    await asyncio.sleep(0.5)
    
    # Check if player name is in participant metadata
    player_name = None
    try:
        # Get the first remote participant (the user)
        participants = list(ctx.room.remote_participants.values())
        if participants:
            participant = participants[0]
            logger.info(f"Participant metadata: {participant.metadata}")
            if participant.metadata:
                metadata = json.loads(participant.metadata)
                if "playerName" in metadata:
                    player_name = metadata["playerName"]
                    logger.info(f"Found player name in metadata: {player_name}")
                else:
                    logger.warning("playerName not found in metadata")
            else:
                logger.warning("Participant has no metadata")
        else:
            logger.warning("No remote participants found")
    except Exception as e:
        logger.warning(f"Could not extract player name from metadata: {e}")

    # Create the agent with player name if available
    agent_instance = ImprovHostAgent(player_name=player_name)

    # Create session
    session = AgentSession(
        llm=google.llm.LLM(model="gemini-2.5-flash"),
        stt=deepgram.STT(model="nova-3"),
        tts=murf.TTS(voice="en-US-matthew", model="FALCON"),
    )

    # Track usage metrics
    usage_collector = metrics.UsageCollector()

    @session.on(MetricsCollectedEvent)
    def _on_metrics_collected(event: MetricsCollectedEvent):
        metrics.log_metrics(event.metrics)
        usage_collector.collect(event.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # Start the session
    await session.start(
        agent=agent_instance,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
