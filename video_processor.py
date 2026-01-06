"""
ClashFish Video Processor
Extracts game state from Clash Royale screen recordings
"""
import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from PIL import Image
import io
from pathlib import Path
from inference_sdk import InferenceHTTPClient


@dataclass
class Position:
    """Represents a position on the game field"""
    x: float
    y: float

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)


@dataclass
class GameState:
    """Represents the game state at a specific timestamp"""
    timestamp: float  # seconds from start
    frame_number: int
    elixir: int
    cards_in_hand: List[str]
    allied_units: List[Position]
    enemy_units: List[Position]
    tower_count: Dict[str, int]  # {'allied': 3, 'enemy': 3}

    def to_dqn_state(self) -> np.ndarray:
        """Convert to DQN state format (41-dim vector)"""
        state = np.zeros(41)
        state[0] = self.elixir / 10.0  # Normalized elixir

        # Allied units (max 10)
        for i, unit in enumerate(self.allied_units[:10]):
            state[1 + i*2] = unit.x
            state[2 + i*2] = unit.y

        # Enemy units (max 10)
        for i, unit in enumerate(self.enemy_units[:10]):
            state[21 + i*2] = unit.x
            state[22 + i*2] = unit.y

        return state


@dataclass
class PlayerAction:
    """Represents a player's card play"""
    timestamp: float
    frame_number: int
    card_played: str
    position: Position
    elixir_cost: int
    game_state_before: GameState


class VideoProcessor:
    """Processes Clash Royale screen recordings and extracts game state"""

    # Card elixir costs (default values)
    CARD_COSTS = {
        'Arrows': 3, 'Fireball': 4, 'Zap': 2, 'Lightning': 6, 'Rocket': 6,
        'Freeze': 4, 'Tornado': 3, 'Knight': 3, 'Musketeer': 4, 'Wizard': 5,
        'Hog Rider': 4, 'Giant': 5, 'Pekka': 7, 'Golem': 8, 'Balloon': 5,
        'Minions': 3, 'Minion Horde': 5, 'Goblins': 2, 'Skeleton Army': 3,
        'Barbarians': 5, 'Elite Barbarians': 6, 'Valkyrie': 4, 'Prince': 5,
        'Baby Dragon': 4, 'Inferno Dragon': 4, 'Mega Knight': 7, 'Sparky': 6
    }

    def __init__(self,
                 fps: float = 2.0,
                 roboflow_workspace_card: str = None,
                 roboflow_workspace_troop: str = None,
                 roboflow_api_key: str = None):
        """
        Initialize video processor

        Args:
            fps: Frames per second to extract (default 2 = analyze every 0.5s)
            roboflow_workspace_card: Roboflow workspace for card detection
            roboflow_workspace_troop: Roboflow workspace for troop detection
            roboflow_api_key: Roboflow API key
        """
        self.fps = fps
        self.workspace_card = roboflow_workspace_card
        self.workspace_troop = roboflow_workspace_troop

        # Initialize Roboflow client
        if roboflow_api_key:
            self.client = InferenceHTTPClient(
                api_url="http://localhost:9001",
                api_key=roboflow_api_key
            )
        else:
            self.client = None
            print("Warning: No Roboflow API key provided. Using mock detection.")

    def process_video(self, video_path: str) -> Tuple[List[GameState], List[PlayerAction]]:
        """
        Process a screen recording and extract game states

        Args:
            video_path: Path to video file

        Returns:
            Tuple of (game_states, player_actions)
        """
        print(f"Processing video: {video_path}")

        # Extract frames
        frames = self._extract_frames(video_path)
        print(f"Extracted {len(frames)} frames")

        # Detect game state from each frame
        game_states = []
        for i, (frame, timestamp) in enumerate(frames):
            state = self._detect_game_state(frame, timestamp, i)
            if state:
                game_states.append(state)
                if i % 10 == 0:
                    print(f"Processed frame {i}/{len(frames)}")

        print(f"Detected {len(game_states)} valid game states")

        # Reconstruct player actions from state changes
        player_actions = self._reconstruct_actions(game_states)
        print(f"Reconstructed {len(player_actions)} player actions")

        return game_states, player_actions

    def _extract_frames(self, video_path: str) -> List[Tuple[np.ndarray, float]]:
        """
        Extract frames from video at specified FPS

        Returns:
            List of (frame, timestamp) tuples
        """
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")

        video_fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(video_fps / self.fps)  # Extract every Nth frame

        frames = []
        frame_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval == 0:
                timestamp = frame_count / video_fps
                frames.append((frame, timestamp))

            frame_count += 1

        cap.release()
        return frames

    def _detect_game_state(self, frame: np.ndarray, timestamp: float, frame_number: int) -> Optional[GameState]:
        """
        Detect game state from a single frame

        Args:
            frame: Video frame (BGR format from OpenCV)
            timestamp: Timestamp in seconds
            frame_number: Frame index

        Returns:
            GameState object or None if detection fails
        """
        try:
            # Detect cards in hand
            cards = self._detect_cards(frame)

            # Detect elixir level
            elixir = self._detect_elixir(frame)

            # Detect troops and towers
            allied_units, enemy_units, towers = self._detect_troops_and_towers(frame)

            return GameState(
                timestamp=timestamp,
                frame_number=frame_number,
                elixir=elixir,
                cards_in_hand=cards,
                allied_units=allied_units,
                enemy_units=enemy_units,
                tower_count=towers
            )
        except Exception as e:
            print(f"Error detecting state at frame {frame_number}: {e}")
            return None

    def _detect_cards(self, frame: np.ndarray) -> List[str]:
        """Detect cards in hand using Roboflow"""
        if not self.client:
            return ["Knight", "Musketeer", "Fireball", "Zap"]  # Mock

        # Extract card bar region (bottom of screen)
        height, width = frame.shape[:2]
        card_region = frame[int(height*0.85):height, int(width*0.3):int(width*0.7)]

        # Convert to PIL Image
        card_image = Image.fromarray(cv2.cvtColor(card_region, cv2.COLOR_BGR2RGB))

        # Save to bytes
        img_bytes = io.BytesIO()
        card_image.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        try:
            # Call Roboflow
            result = self.client.infer(img_bytes.read(), model_id=self.workspace_card)

            # Parse predictions
            cards = []
            if 'predictions' in result:
                for pred in result['predictions']:
                    if 'class' in pred:
                        cards.append(pred['class'])

            return cards[:4]  # Max 4 cards
        except Exception as e:
            print(f"Card detection error: {e}")
            return []

    def _detect_elixir(self, frame: np.ndarray) -> int:
        """Detect elixir level from frame"""
        # Simple color-based detection (purple pixels)
        height, width = frame.shape[:2]
        elixir_region = frame[int(height*0.9):height, int(width*0.4):int(width*0.6)]

        # Count purple pixels (approximate)
        purple_mask = cv2.inRange(elixir_region,
                                   np.array([180, 80, 180]),  # Lower purple
                                   np.array([255, 180, 255]))  # Upper purple

        purple_count = cv2.countNonZero(purple_mask)

        # Map to elixir level (0-10)
        elixir = min(10, purple_count // 100)  # Rough approximation
        return elixir

    def _detect_troops_and_towers(self, frame: np.ndarray) -> Tuple[List[Position], List[Position], Dict[str, int]]:
        """Detect troop positions and tower counts using Roboflow"""
        if not self.client:
            # Mock data
            return (
                [Position(0.5, 0.7), Position(0.3, 0.6)],  # Allied
                [Position(0.6, 0.3), Position(0.4, 0.2)],  # Enemy
                {'allied': 3, 'enemy': 3}  # Towers
            )

        # Convert frame to PIL
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)

        # Save to bytes
        img_bytes = io.BytesIO()
        pil_image.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        try:
            # Call Roboflow troop detection
            result = self.client.infer(img_bytes.read(), model_id=self.workspace_troop)

            allied_units = []
            enemy_units = []
            tower_count = {'allied': 0, 'enemy': 0}

            if 'predictions' in result:
                height, width = frame.shape[:2]

                for pred in result['predictions']:
                    class_name = pred.get('class', '').lower()
                    x = pred.get('x', 0) / width  # Normalize
                    y = pred.get('y', 0) / height

                    if 'ally' in class_name and 'tower' not in class_name:
                        allied_units.append(Position(x, y))
                    elif 'enemy' in class_name and 'tower' not in class_name:
                        enemy_units.append(Position(x, y))
                    elif 'tower' in class_name:
                        if 'ally' in class_name:
                            tower_count['allied'] += 1
                        elif 'enemy' in class_name:
                            tower_count['enemy'] += 1

            return allied_units, enemy_units, tower_count
        except Exception as e:
            print(f"Troop detection error: {e}")
            return [], [], {'allied': 3, 'enemy': 3}

    def _reconstruct_actions(self, game_states: List[GameState]) -> List[PlayerAction]:
        """
        Reconstruct player actions from sequence of game states

        Detects when new cards are played by:
        1. Detecting elixir decrease
        2. Detecting new allied units appearing
        3. Matching cards that disappeared from hand
        """
        actions = []

        for i in range(1, len(game_states)):
            prev_state = game_states[i-1]
            curr_state = game_states[i]

            # Check for elixir decrease (card was played)
            elixir_diff = prev_state.elixir - curr_state.elixir

            if elixir_diff > 0:  # Elixir decreased = card played
                # Find which card was played
                prev_cards = set(prev_state.cards_in_hand)
                curr_cards = set(curr_state.cards_in_hand)
                played_cards = prev_cards - curr_cards

                if played_cards:
                    card_played = played_cards.pop()

                    # Find new unit position (approximate)
                    new_units = self._find_new_units(prev_state.allied_units,
                                                     curr_state.allied_units)

                    position = new_units[0] if new_units else Position(0.5, 0.5)

                    action = PlayerAction(
                        timestamp=curr_state.timestamp,
                        frame_number=curr_state.frame_number,
                        card_played=card_played,
                        position=position,
                        elixir_cost=self.CARD_COSTS.get(card_played, elixir_diff),
                        game_state_before=prev_state
                    )
                    actions.append(action)

        return actions

    def _find_new_units(self, prev_units: List[Position], curr_units: List[Position]) -> List[Position]:
        """Find newly appeared units"""
        new_units = []

        for curr_unit in curr_units:
            # Check if this unit existed before (within small distance)
            is_new = True
            for prev_unit in prev_units:
                distance = np.sqrt((curr_unit.x - prev_unit.x)**2 +
                                 (curr_unit.y - prev_unit.y)**2)
                if distance < 0.05:  # Same unit (moved slightly)
                    is_new = False
                    break

            if is_new:
                new_units.append(curr_unit)

        return new_units


if __name__ == "__main__":
    # Test with a sample video
    import sys

    if len(sys.argv) < 2:
        print("Usage: python video_processor.py <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]

    processor = VideoProcessor(fps=2.0)
    game_states, actions = processor.process_video(video_path)

    print(f"\n=== Processing Complete ===")
    print(f"Total game states: {len(game_states)}")
    print(f"Total actions: {len(actions)}")

    print(f"\n=== Sample Actions ===")
    for action in actions[:5]:
        print(f"[{action.timestamp:.1f}s] {action.card_played} at ({action.position.x:.2f}, {action.position.y:.2f})")
