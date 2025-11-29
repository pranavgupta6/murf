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

# Load game world and state for D&D-style adventure
def load_game_world():
    """Load the game world configuration from JSON file"""
    content_path = Path("shared-data/game_state.json")
    with open(content_path, "r") as f:
        return json.load(f)

def save_game_state(game_data):
    """Save the current game state to JSON file"""
    content_path = Path("shared-data/game_state.json")
    with open(content_path, "w") as f:
        json.dump(game_data, f, indent=2)


class GameMasterAgent(Agent):
    """D&D-style Game Master for interactive voice adventures in The Forgotten Realm"""
    
    def __init__(self) -> None:
        # Load game world when agent initializes
        self.game_data = load_game_world()
        self.world = self.game_data['world']
        self.session = self.game_data['current_session']
        
        # Initialize new session
        self.session['session_id'] = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session['turn_count'] = 0
        self.session['location'] = 'village_square'
        self.session['inventory'] = []
        self.session['health'] = 100
        self.session['story_progress'] = 'intro'
        
        super().__init__(
            instructions=f"""You are the Game Master running an epic fantasy D&D-style adventure in {self.world['name']}.

🎭 YOUR ROLE AS GAME MASTER:
You are a dramatic storyteller who brings the world to life through vivid descriptions and engaging NPCs. You narrate scenes, embody characters, and respond to player choices.

🌍 THE WORLD - {self.world['name']}:
A medieval fantasy realm where dragons soar, magic flows, and heroes rise. The village of Eldergrove is threatened by an ancient dragon, but not everything is as it seems...

📖 STORY STRUCTURE:
ACT 1 - INTRODUCTION (Turns 1-3):
- Player arrives in the village square of Eldergrove
- Elder Thornwick urgently seeks a hero
- The village is in panic - a dragon has been spotted near the forest
- Set the scene: peaceful village disrupted by fear

ACT 2 - INVESTIGATION (Turns 4-8):
- Player explores: tavern, blacksmith, or forest path
- NPCs reveal clues: innkeeper knows rumors, blacksmith offers gear, old warrior gives advice
- The twist: mysterious stranger in forest knows the truth
- Build tension: dragon isn't the villain, treasure was stolen FROM the dragon

ACT 3 - DRAGON ENCOUNTER (Turns 9-12):
- Player reaches dragon's lair
- Vorthax the Ancient is intelligent, not mindlessly evil
- Revelation: village thieves stole his precious Crimson Dragon's Eye
- Choice: fight dragon (hard), help recover treasure (quest), or negotiate (diplomacy)

ACT 4 - RESOLUTION (Turns 13-15):
- Based on player's choice:
  * Combat: epic battle with dragon
  * Quest: find thieves in village, recover gem
  * Diplomacy: broker peace between dragon and village
- Satisfying conclusion with reward

🎲 GM RULES - FOLLOW THESE EXACTLY:

1. **Narration Style**:
   - Use vivid, sensory details (sights, sounds, smells)
   - Speak in second person: "You see...", "You hear...", "Before you..."
   - Be dramatic but not overly verbose
   - Create atmosphere: tense in danger, peaceful in safety

2. **Scene Structure** (EVERY RESPONSE):
   - Describe the current scene (2-3 sentences)
   - If NPC present, have them speak directly in character
   - Present the situation/challenge
   - END with clear question: "What do you do?" or "How do you respond?"

3. **Player Agency**:
   - Accept creative solutions
   - Don't force a specific path
   - Let player be heroic, clever, or diplomatic
   - Consequences should feel fair

4. **Dice Rolls** (Simulate internally):
   - For risky actions, mentally decide success/failure
   - Describe outcome dramatically: "Your blade strikes true!" vs "You miss!"
   - Keep combat quick: 2-3 exchanges max

5. **Pacing**:
   - Keep responses concise (3-5 sentences)
   - Move story forward each turn
   - Don't get stuck in one location too long
   - Build toward dragon encounter by turn 9

6. **NPCs** (Be these characters):
   - Elder Thornwick: "Please, brave adventurer, our village needs you!"
   - Vorthax the Dragon: Deep, rumbling voice - "You dare enter my lair, little mortal?"
   - Shadowcloak: Whispers mysteriously - "Not all monsters are evil..."
   - Innkeeper Bella: Chatty and warm - "Oh honey, let me tell you what I heard..."
   - Blacksmith Grimgar: Gruff but helpful - "Need a weapon? I've got just the thing."

7. **Use Function Tools**:
   - Call update_location when player moves
   - Call add_to_inventory when player gets item
   - Call record_npc_interaction when meeting characters
   - Call progress_story when advancing to new act
   - Call check_victory_condition when story might end

8. **Victory Conditions**:
   - Fight dragon and win
   - Recover stolen gem and return to dragon
   - Broker peace deal between dragon and village
   All lead to satisfying conclusion!

🎬 OPENING SCENE:
Start with: "Welcome, brave adventurer, to The Forgotten Realm! You find yourself standing in the village square of Eldergrove on a crisp autumn morning. The fountain bubbles peacefully at the center, but the villagers seem anxious, whispering among themselves. 

An elderly man in robes hurries toward you - Elder Thornwick, by the look of his ceremonial staff. 'Thank the gods you've arrived!' he says breathlessly. 'A great dragon has been spotted in the northern forest. Our village lives in fear. Will you help us?'

What do you do?"

REMEMBER: 
- Keep it moving and exciting
- End EVERY response with "What do you do?" or similar
- Use function tools to track progress
- Make player feel like a hero
- This is cooperative storytelling - have fun!""",
        )
        
    @function_tool
    async def update_location(
        self,
        new_location: Annotated[str, "The key of the new location (e.g., 'forest_path', 'dragon_cave', 'tavern')"]
    ):
        """Update the player's current location in the game world"""
        logger.info(f"Player moving to: {new_location}")
        
        if new_location not in self.world['locations']:
            return f"Error: Location '{new_location}' does not exist."
        
        old_location = self.session['location']
        self.session['location'] = new_location
        self.session['turn_count'] += 1
        
        location_data = self.world['locations'][new_location]
        save_game_state(self.game_data)
        
        logger.info(f"Moved from {old_location} to {new_location}")
        return f"Location updated to {location_data['name']}. {location_data['description']}"
    
    @function_tool
    async def add_to_inventory(
        self,
        item_key: Annotated[str, "The key of the item to add (e.g., 'rusty_sword', 'healing_potion')"]
    ):
        """Add an item to the player's inventory"""
        logger.info(f"Adding item to inventory: {item_key}")
        
        if item_key not in self.world['items']:
            return f"Error: Item '{item_key}' does not exist."
        
        if item_key in self.session['inventory']:
            return f"Player already has {self.world['items'][item_key]['name']}."
        
        self.session['inventory'].append(item_key)
        item = self.world['items'][item_key]
        save_game_state(self.game_data)
        
        logger.info(f"Added {item['name']} to inventory")
        return f"Added {item['name']} to inventory: {item['description']}"
    
    @function_tool
    async def record_npc_interaction(
        self,
        npc_key: Annotated[str, "The key of the NPC (e.g., 'village_elder', 'ancient_dragon')"]
    ):
        """Record that the player has interacted with an NPC"""
        logger.info(f"Recording interaction with: {npc_key}")
        
        if npc_key not in self.world['npcs']:
            return f"Error: NPC '{npc_key}' does not exist."
        
        npc = self.world['npcs'][npc_key]
        logger.info(f"Player met {npc['name']}")
        
        return f"Interaction recorded with {npc['name']} ({npc['personality']}). Quest: {npc['quest']}"
    
    @function_tool
    async def progress_story(
        self,
        new_phase: Annotated[str, "The new story phase (intro/investigation/forest_encounter/dragon_confrontation/resolution)"]
    ):
        """Progress the story to a new phase"""
        logger.info(f"Advancing story to: {new_phase}")
        
        old_phase = self.session['story_progress']
        self.session['story_progress'] = new_phase
        save_game_state(self.game_data)
        
        logger.info(f"Story progressed from {old_phase} to {new_phase}")
        return f"Story phase updated to: {new_phase}. {self.game_data['story_arcs'].get(new_phase, '')}"
    
    @function_tool
    async def check_victory_condition(
        self,
        outcome: Annotated[str, "The outcome achieved (dragon_defeated/treasure_recovered/peace_brokered)"]
    ):
        """Check if the player has achieved a victory condition"""
        logger.info(f"Checking victory condition: {outcome}")
        
        victories = {
            "dragon_defeated": "You have slain Vorthax the Ancient in glorious combat! The village celebrates your heroism.",
            "treasure_recovered": "You recovered the Crimson Dragon's Eye and returned it to Vorthax. The dragon thanks you and vows to protect the village.",
            "peace_brokered": "Your diplomacy has brought peace! The dragon and village now trade knowledge and protection."
        }
        
        if outcome in victories:
            self.session['story_progress'] = 'completed'
            save_game_state(self.game_data)
            return f"VICTORY! {victories[outcome]} Total turns: {self.session['turn_count']}. Adventure complete!"
        
        return "Condition not met yet."
    
    @function_tool
    async def update_health(
        self,
        change: Annotated[int, "Health change amount (positive for healing, negative for damage)"]
    ):
        """Update the player's health"""
        logger.info(f"Updating health by: {change}")
        
        self.session['health'] += change
        if self.session['health'] > 100:
            self.session['health'] = 100
        
        save_game_state(self.game_data)
        
        if self.session['health'] <= 0:
            return f"Your health has fallen to 0! You collapse... But brave heroes never truly die. You awaken back at the village, determined to try again."
        
        return f"Health updated to {self.session['health']}/100."
    
    @function_tool
    async def view_status(self):
        """View current player status and game state"""
        logger.info("Viewing player status")
        
        location = self.world['locations'][self.session['location']]
        inventory_list = [self.world['items'][item]['name'] for item in self.session['inventory']]
        inventory_str = ", ".join(inventory_list) if inventory_list else "Empty"
        
        status = f"""Current Status:
Location: {location['name']}
Health: {self.session['health']}/100
Inventory: {inventory_str}
Story Progress: {self.session['story_progress']}
Turn: {self.session['turn_count']}"""
        
        return status


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

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=GameMasterAgent(),
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
