"""
Game State Tracker for Clash Royale Analyzer
Tracks complete game state including cards, troops, towers, elixir
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import cv2
from inference_sdk import InferenceHTTPClient
import os


class CardType(Enum):
    """Card type classification"""
    TROOP = "troop"
    SPELL = "spell"
    BUILDING = "building"


class Player(Enum):
    """Player identification"""
    YOU = "you"
    OPPONENT = "opponent"


@dataclass
class Card:
    """Represents a Clash Royale card"""
    name: str
    type: CardType
    elixir_cost: int
    description: str = ""


@dataclass
class TroopPosition:
    """Represents a troop on the battlefield"""
    x: float  # Normalized 0-1
    y: float  # Normalized 0-1
    class_name: str
    player: Player
    confidence: float
    timestamp: float


@dataclass
class CardPlay:
    """Represents a card being played"""
    card: Card
    player: Player
    position: Tuple[float, float]  # Normalized (x, y)
    timestamp: float
    elixir_before: int
    elixir_after: int
    frame_number: int


@dataclass
class TowerState:
    """Represents tower health state"""
    king_tower: bool
    left_princess: bool
    right_princess: bool
    player: Player


@dataclass
class GameState:
    """Complete game state at a specific moment"""
    timestamp: float
    frame_number: int

    # Elixir
    your_elixir: int
    opponent_elixir: int  # Estimated

    # Cards in hand
    your_cards: List[Card] = field(default_factory=list)

    # Troops on field
    your_troops: List[TroopPosition] = field(default_factory=list)
    opponent_troops: List[TroopPosition] = field(default_factory=list)

    # Tower states
    your_towers: Optional[TowerState] = None
    opponent_towers: Optional[TowerState] = None

    # Recent card plays
    recent_plays: List[CardPlay] = field(default_factory=list)

    # Position evaluation (set by evaluation engine)
    evaluation: Optional[float] = None
    win_probability: Optional[float] = None


class GameStateTracker:
    """Tracks complete game state from video frames"""

    def __init__(self, roboflow_api_key: str,
                 troop_workspace: str,
                 card_workspace: str):
        """
        Initialize game state tracker

        Args:
            roboflow_api_key: Roboflow API key
            troop_workspace: Workspace name for troop detection
            card_workspace: Workspace name for card detection
        """
        self.api_key = roboflow_api_key
        self.troop_workspace = troop_workspace
        self.card_workspace = card_workspace

        # Initialize Roboflow clients
        self.troop_model = InferenceHTTPClient(
            api_url="http://localhost:9001",
            api_key=roboflow_api_key
        )
        self.card_model = InferenceHTTPClient(
            api_url="http://localhost:9001",
            api_key=roboflow_api_key
        )

        # Game state history
        self.states: List[GameState] = []
        self.card_plays: List[CardPlay] = []

        # Card database (expanded from env.py)
        self.spell_cards = {
            "Fireball", "Zap", "Arrows", "Tornado", "Rocket",
            "Lightning", "Freeze", "Poison", "Earthquake", "Log",
            "Snowball", "Giant Snowball", "Barbarian Barrel", "Graveyard"
        }

        # Previous state for tracking changes
        self.prev_state: Optional[GameState] = None

    def detect_cards_in_hand(self, card_area: np.ndarray) -> List[str]:
        """
        Detect cards in hand from card bar image

        Args:
            card_area: Cropped card bar image

        Returns:
            List of detected card names
        """
        # Split into 4 individual cards
        width = card_area.shape[1]
        card_width = width // 4

        detected_cards = []

        for i in range(4):
            left = i * card_width
            right = (i + 1) * card_width
            single_card = card_area[:, left:right]

            # Save temporarily for detection
            temp_path = f"/tmp/temp_card_{i}.png"
            cv2.imwrite(temp_path, single_card)

            try:
                results = self.card_model.run_workflow(
                    workspace_name=self.card_workspace,
                    workflow_id="custom-workflow",
                    images={"image": temp_path}
                )

                # Parse results
                predictions = []
                if isinstance(results, list) and results:
                    preds_dict = results[0].get("predictions", {})
                    if isinstance(preds_dict, dict):
                        predictions = preds_dict.get("predictions", [])

                if predictions:
                    card_name = predictions[0]["class"]
                    detected_cards.append(card_name)
                else:
                    detected_cards.append("Unknown")

            except Exception as e:
                print(f"Error detecting card {i}: {e}")
                detected_cards.append("Unknown")

            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

        return detected_cards

    def detect_troops(self, game_area: np.ndarray) -> Tuple[List[TroopPosition], List[TroopPosition]]:
        """
        Detect troops on the battlefield

        Args:
            game_area: Cropped game area image

        Returns:
            Tuple of (your_troops, opponent_troops)
        """
        # Save temporarily for detection
        temp_path = "/tmp/temp_game_area.png"
        cv2.imwrite(temp_path, game_area)

        try:
            results = self.troop_model.run_workflow(
                workspace_name=self.troop_workspace,
                workflow_id="detect-count-and-visualize",
                images={"image": temp_path}
            )

            # Parse results
            predictions = []
            if isinstance(results, dict) and "predictions" in results:
                predictions = results["predictions"]
            elif isinstance(results, list) and results:
                first = results[0]
                if isinstance(first, dict) and "predictions" in first:
                    predictions = first["predictions"]

            if isinstance(predictions, dict) and "predictions" in predictions:
                predictions = predictions["predictions"]

            # Define tower classes to exclude from troop detection
            TOWER_CLASSES = {
                "ally king tower",
                "ally princess tower",
                "enemy king tower",
                "enemy princess tower"
            }

            # Separate ally and enemy troops
            your_troops = []
            opponent_troops = []

            height, width = game_area.shape[:2]

            for pred in predictions:
                if not isinstance(pred, dict):
                    continue

                class_name = pred.get("class", "").strip().lower()

                # Skip towers
                if class_name in TOWER_CLASSES:
                    continue

                x = pred.get("x", 0)
                y = pred.get("y", 0)
                confidence = pred.get("confidence", 0.0)

                # Normalize coordinates
                norm_x = x / width if width > 0 else 0
                norm_y = y / height if height > 0 else 0

                troop = TroopPosition(
                    x=norm_x,
                    y=norm_y,
                    class_name=class_name,
                    player=Player.YOU if class_name.startswith("ally") else Player.OPPONENT,
                    confidence=confidence,
                    timestamp=0.0  # Set by caller
                )

                if class_name.startswith("ally"):
                    your_troops.append(troop)
                elif class_name.startswith("enemy"):
                    opponent_troops.append(troop)

        except Exception as e:
            print(f"Error detecting troops: {e}")
            your_troops = []
            opponent_troops = []

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        return your_troops, opponent_troops

    def detect_towers(self, game_area: np.ndarray) -> Tuple[TowerState, TowerState]:
        """
        Detect tower states

        Args:
            game_area: Cropped game area image

        Returns:
            Tuple of (your_towers, opponent_towers)
        """
        temp_path = "/tmp/temp_tower_detect.png"
        cv2.imwrite(temp_path, game_area)

        your_towers = TowerState(
            king_tower=True,
            left_princess=True,
            right_princess=True,
            player=Player.YOU
        )

        opponent_towers = TowerState(
            king_tower=True,
            left_princess=True,
            right_princess=True,
            player=Player.OPPONENT
        )

        try:
            results = self.troop_model.run_workflow(
                workspace_name=self.troop_workspace,
                workflow_id="detect-count-and-visualize",
                images={"image": temp_path}
            )

            predictions = []
            if isinstance(results, dict) and "predictions" in results:
                predictions = results["predictions"]
            elif isinstance(results, list) and results:
                first = results[0]
                if isinstance(first, dict) and "predictions" in first:
                    predictions = first["predictions"]

            if isinstance(predictions, dict) and "predictions" in predictions:
                predictions = predictions["predictions"]

            # Count towers
            ally_king = 0
            ally_princess = 0
            enemy_king = 0
            enemy_princess = 0

            for pred in predictions:
                if not isinstance(pred, dict):
                    continue

                class_name = pred.get("class", "").strip().lower()

                if class_name == "ally king tower":
                    ally_king += 1
                elif class_name == "ally princess tower":
                    ally_princess += 1
                elif class_name == "enemy king tower":
                    enemy_king += 1
                elif class_name == "enemy princess tower":
                    enemy_princess += 1

            # Assume 2 princess towers if both detected
            your_towers.king_tower = ally_king > 0
            your_towers.left_princess = ally_princess >= 1
            your_towers.right_princess = ally_princess >= 2

            opponent_towers.king_tower = enemy_king > 0
            opponent_towers.left_princess = enemy_princess >= 1
            opponent_towers.right_princess = enemy_princess >= 2

        except Exception as e:
            print(f"Error detecting towers: {e}")

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        return your_towers, opponent_towers

    def count_elixir(self, frame: np.ndarray) -> int:
        """
        Count elixir from frame using pixel detection

        Args:
            frame: Full video frame

        Returns:
            Elixir count (0-10)
        """
        # Elixir bar coordinates (Windows)
        target = (225, 128, 229)
        tolerance = 80
        count = 0

        for x in range(1512, 1892, 38):
            try:
                # Ensure coordinates are within bounds
                if x < frame.shape[1] and 989 < frame.shape[0]:
                    b, g, r = frame[989, x]  # OpenCV uses BGR
                    if (abs(r - target[0]) <= tolerance and
                        abs(g - target[1]) <= tolerance and
                        abs(b - target[2]) <= tolerance):
                        count += 1
            except:
                pass

        return count

    def estimate_opponent_elixir(self, game_state: GameState) -> int:
        """
        Estimate opponent's elixir based on their plays

        Args:
            game_state: Current game state

        Returns:
            Estimated elixir (0-10)
        """
        # Simple estimation: assume elixir regenerates at same rate
        # and opponent spends elixir when troops appear
        # This is a placeholder - can be improved with ML
        return 5  # Default estimate

    def create_game_state(self,
                         frame: np.ndarray,
                         game_area: np.ndarray,
                         card_area: np.ndarray,
                         timestamp: float,
                         frame_number: int) -> GameState:
        """
        Create complete game state from frame

        Args:
            frame: Full video frame
            game_area: Cropped game area
            card_area: Cropped card bar
            timestamp: Video timestamp
            frame_number: Frame number

        Returns:
            Complete GameState object
        """
        # Detect components
        your_cards = self.detect_cards_in_hand(card_area)
        your_troops, opponent_troops = self.detect_troops(game_area)
        your_towers, opponent_towers = self.detect_towers(game_area)
        your_elixir = self.count_elixir(frame)

        # Set timestamps for troops
        for troop in your_troops + opponent_troops:
            troop.timestamp = timestamp

        # Create game state
        state = GameState(
            timestamp=timestamp,
            frame_number=frame_number,
            your_elixir=your_elixir,
            opponent_elixir=5,  # Estimated
            your_cards=[Card(name=c, type=CardType.TROOP, elixir_cost=0) for c in your_cards],
            your_troops=your_troops,
            opponent_troops=opponent_troops,
            your_towers=your_towers,
            opponent_towers=opponent_towers
        )

        # Detect card plays by comparing with previous state
        if self.prev_state:
            self._detect_card_plays(self.prev_state, state)

        self.prev_state = state
        self.states.append(state)

        return state

    def _detect_card_plays(self, prev_state: GameState, curr_state: GameState):
        """
        Detect card plays by comparing states

        Args:
            prev_state: Previous game state
            curr_state: Current game state
        """
        # Detect new troops (simple heuristic)
        prev_troop_count = len(prev_state.your_troops)
        curr_troop_count = len(curr_state.your_troops)

        # If more troops appeared, a card was likely played
        if curr_troop_count > prev_troop_count:
            # Try to identify which card was played
            # This is simplified - real implementation would track specific troops
            new_troops = curr_troop_count - prev_troop_count

            if new_troops > 0 and curr_state.your_troops:
                # Get newest troop (last in list)
                newest_troop = curr_state.your_troops[-1]

                # Create card play record
                card_play = CardPlay(
                    card=Card(name=newest_troop.class_name, type=CardType.TROOP, elixir_cost=0),
                    player=Player.YOU,
                    position=(newest_troop.x, newest_troop.y),
                    timestamp=curr_state.timestamp,
                    elixir_before=prev_state.your_elixir,
                    elixir_after=curr_state.your_elixir,
                    frame_number=curr_state.frame_number
                )

                self.card_plays.append(card_play)
                curr_state.recent_plays.append(card_play)

    def get_game_timeline(self) -> List[GameState]:
        """Get complete game state timeline"""
        return self.states

    def get_all_card_plays(self) -> List[CardPlay]:
        """Get all detected card plays"""
        return self.card_plays

    def export_timeline(self, output_path: str):
        """Export game timeline to JSON"""
        import json

        timeline_data = {
            "total_states": len(self.states),
            "total_plays": len(self.card_plays),
            "states": [
                {
                    "timestamp": state.timestamp,
                    "frame": state.frame_number,
                    "your_elixir": state.your_elixir,
                    "opponent_elixir": state.opponent_elixir,
                    "your_troops": len(state.your_troops),
                    "opponent_troops": len(state.opponent_troops),
                    "evaluation": state.evaluation,
                    "win_probability": state.win_probability
                }
                for state in self.states
            ],
            "plays": [
                {
                    "card": play.card.name,
                    "player": play.player.value,
                    "timestamp": play.timestamp,
                    "position": play.position,
                    "elixir_before": play.elixir_before,
                    "elixir_after": play.elixir_after
                }
                for play in self.card_plays
            ]
        }

        with open(output_path, 'w') as f:
            json.dump(timeline_data, f, indent=2)

        print(f"Timeline exported to {output_path}")
