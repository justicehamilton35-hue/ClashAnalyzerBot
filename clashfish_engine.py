"""
ClashFish Analysis Engine
Evaluates Clash Royale gameplay using trained DQN model (like Stockfish for chess)
"""
import torch
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum
from dqn_agent import DQN
from video_processor import GameState, PlayerAction, Position


class MoveQuality(Enum):
    """Move quality classifications (like chess notation)"""
    BRILLIANT = "!!"      # Better than engine's best
    GOOD = "!"            # Within 5% of best
    OKAY = ""             # Within 15% of best
    INACCURACY = "?!"     # 15-30% worse
    MISTAKE = "?"         # 30-50% worse
    BLUNDER = "??"        # 50%+ worse


@dataclass
class MoveEvaluation:
    """Evaluation of a single move"""
    player_action: PlayerAction
    player_q_value: float
    best_q_value: float
    evaluation_loss: float  # Percentage loss from best move
    quality: MoveQuality
    top_alternatives: List[Tuple[str, Position, float]]  # (card, position, q_value)
    mistake_type: Optional[str] = None  # e.g., "spell_wastage", "elixir_overcap"


@dataclass
class GameAnalysis:
    """Complete game analysis report"""
    game_states: List[GameState]
    player_actions: List[PlayerAction]
    move_evaluations: List[MoveEvaluation]

    # Summary statistics
    total_moves: int
    accuracy_score: float  # 0-100
    brilliant_moves: int
    good_moves: int
    inaccuracies: int
    mistakes: int
    blunders: int

    # Performance ratings (0-10)
    elixir_management_rating: float
    card_placement_rating: float
    defensive_rating: float
    offensive_rating: float
    overall_rating: float

    # Key moments
    top_blunders: List[MoveEvaluation]
    best_moves: List[MoveEvaluation]


class ClashFishEngine:
    """AI analysis engine using DQN model"""

    def __init__(self, model_path: str, device: str = "cpu"):
        """
        Initialize ClashFish engine

        Args:
            model_path: Path to trained DQN model (.pth file)
            device: "cpu" or "cuda"
        """
        self.device = device
        self.state_size = 41  # From DQN architecture
        self.action_size = 2017  # 4 cards × 18×28 grid + 1 no-op

        # Load trained model
        self.model = DQN(self.state_size, self.action_size).to(device)
        checkpoint = torch.load(model_path, map_location=device)

        if isinstance(checkpoint, dict):
            self.model.load_state_dict(checkpoint['model_state_dict'])
        else:
            self.model.load_state_dict(checkpoint)

        self.model.eval()  # Evaluation mode
        print(f"Loaded ClashFish engine from {model_path}")

    def analyze_game(self, game_states: List[GameState],
                    player_actions: List[PlayerAction]) -> GameAnalysis:
        """
        Perform complete game analysis

        Args:
            game_states: Sequence of detected game states
            player_actions: Player's card plays

        Returns:
            Complete game analysis report
        """
        print(f"Analyzing game with {len(player_actions)} moves...")

        # Evaluate each move
        move_evaluations = []
        for i, action in enumerate(player_actions):
            evaluation = self._evaluate_move(action)
            move_evaluations.append(evaluation)

            if i % 10 == 0:
                print(f"Evaluated {i}/{len(player_actions)} moves")

        # Calculate summary statistics
        analysis = self._generate_analysis_report(
            game_states, player_actions, move_evaluations
        )

        print(f"Analysis complete. Accuracy: {analysis.accuracy_score:.1f}%")
        return analysis

    def _evaluate_move(self, action: PlayerAction) -> MoveEvaluation:
        """
        Evaluate a single player action using DQN

        Args:
            action: Player action to evaluate

        Returns:
            Move evaluation with Q-values and alternatives
        """
        # Convert game state to DQN input
        state = action.game_state_before.to_dqn_state()
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)

        # Get Q-values for all actions
        with torch.no_grad():
            q_values = self.model(state_tensor).cpu().numpy()[0]

        # Find player's action index
        player_action_idx = self._action_to_index(action)
        player_q_value = q_values[player_action_idx] if player_action_idx < len(q_values) else q_values.min()

        # Find best action and top alternatives
        best_action_idx = np.argmax(q_values)
        best_q_value = q_values[best_action_idx]

        # Get top 5 alternatives
        top_indices = np.argsort(q_values)[-5:][::-1]
        top_alternatives = []

        for idx in top_indices:
            card, position = self._index_to_action(idx, action.game_state_before)
            q_val = q_values[idx]
            top_alternatives.append((card, position, q_val))

        # Calculate evaluation loss (percentage)
        if best_q_value > 0:
            evaluation_loss = ((best_q_value - player_q_value) / abs(best_q_value)) * 100
        else:
            evaluation_loss = 0.0

        # Classify move quality
        quality = self._classify_move_quality(evaluation_loss)

        return MoveEvaluation(
            player_action=action,
            player_q_value=player_q_value,
            best_q_value=best_q_value,
            evaluation_loss=max(0, evaluation_loss),
            quality=quality,
            top_alternatives=top_alternatives
        )

    def _action_to_index(self, action: PlayerAction) -> int:
        """
        Convert PlayerAction to DQN action index

        Action space: 4 cards × 18 cols × 28 rows + 1 no-op
        """
        # Find card index in hand
        cards = action.game_state_before.cards_in_hand
        try:
            card_idx = cards.index(action.card_played)
        except ValueError:
            return self.action_size - 1  # No-op if card not found

        # Convert position to grid coordinates
        col = int(action.position.x * 18)
        row = int(action.position.y * 28)

        # Calculate linear index
        action_idx = card_idx * (18 * 28) + row * 18 + col
        return action_idx

    def _index_to_action(self, action_idx: int, state: GameState) -> Tuple[str, Position]:
        """
        Convert DQN action index back to (card, position)
        """
        if action_idx >= self.action_size - 1:
            return ("No action", Position(0, 0))

        # Decode index
        card_idx = action_idx // (18 * 28)
        remainder = action_idx % (18 * 28)
        row = remainder // 18
        col = remainder % 18

        # Get card name
        cards = state.cards_in_hand
        card = cards[card_idx] if card_idx < len(cards) else "Unknown"

        # Convert to normalized position
        position = Position(col / 18.0, row / 28.0)

        return (card, position)

    def _classify_move_quality(self, evaluation_loss: float) -> MoveQuality:
        """Classify move based on evaluation loss percentage"""
        if evaluation_loss < 0:
            return MoveQuality.BRILLIANT
        elif evaluation_loss < 5:
            return MoveQuality.GOOD
        elif evaluation_loss < 15:
            return MoveQuality.OKAY
        elif evaluation_loss < 30:
            return MoveQuality.INACCURACY
        elif evaluation_loss < 50:
            return MoveQuality.MISTAKE
        else:
            return MoveQuality.BLUNDER

    def _generate_analysis_report(self,
                                  game_states: List[GameState],
                                  player_actions: List[PlayerAction],
                                  move_evaluations: List[MoveEvaluation]) -> GameAnalysis:
        """Generate complete analysis report with statistics"""

        # Count move qualities
        brilliant = sum(1 for e in move_evaluations if e.quality == MoveQuality.BRILLIANT)
        good = sum(1 for e in move_evaluations if e.quality == MoveQuality.GOOD)
        okay = sum(1 for e in move_evaluations if e.quality == MoveQuality.OKAY)
        inaccuracies = sum(1 for e in move_evaluations if e.quality == MoveQuality.INACCURACY)
        mistakes = sum(1 for e in move_evaluations if e.quality == MoveQuality.MISTAKE)
        blunders = sum(1 for e in move_evaluations if e.quality == MoveQuality.BLUNDER)

        # Calculate accuracy score (0-100)
        # Good/brilliant moves = 100%, okay = 85%, inaccuracy = 70%, mistake = 40%, blunder = 0%
        total_moves = len(move_evaluations)
        if total_moves > 0:
            accuracy_score = (
                (brilliant * 100 + good * 100 + okay * 85 +
                 inaccuracies * 70 + mistakes * 40 + blunders * 0) / total_moves
            )
        else:
            accuracy_score = 0.0

        # Calculate performance ratings
        elixir_rating = self._calculate_elixir_rating(game_states, move_evaluations)
        placement_rating = self._calculate_placement_rating(move_evaluations)
        defensive_rating = self._calculate_defensive_rating(move_evaluations)
        offensive_rating = self._calculate_offensive_rating(move_evaluations)
        overall_rating = (elixir_rating + placement_rating +
                         defensive_rating + offensive_rating) / 4

        # Find top blunders and best moves
        top_blunders = sorted(
            [e for e in move_evaluations if e.quality in [MoveQuality.BLUNDER, MoveQuality.MISTAKE]],
            key=lambda e: e.evaluation_loss,
            reverse=True
        )[:5]

        best_moves = sorted(
            [e for e in move_evaluations if e.quality in [MoveQuality.BRILLIANT, MoveQuality.GOOD]],
            key=lambda e: e.evaluation_loss
        )[:5]

        return GameAnalysis(
            game_states=game_states,
            player_actions=player_actions,
            move_evaluations=move_evaluations,
            total_moves=total_moves,
            accuracy_score=accuracy_score,
            brilliant_moves=brilliant,
            good_moves=good,
            inaccuracies=inaccuracies,
            mistakes=mistakes,
            blunders=blunders,
            elixir_management_rating=elixir_rating,
            card_placement_rating=placement_rating,
            defensive_rating=defensive_rating,
            offensive_rating=offensive_rating,
            overall_rating=overall_rating,
            top_blunders=top_blunders,
            best_moves=best_moves
        )

    def _calculate_elixir_rating(self, game_states: List[GameState],
                                evaluations: List[MoveEvaluation]) -> float:
        """Calculate elixir management rating (0-10)"""
        # Check for overcapping (staying at 10 elixir)
        overcap_frames = sum(1 for state in game_states if state.elixir >= 10)
        overcap_ratio = overcap_frames / len(game_states) if game_states else 0

        # Penalty for overcapping
        rating = 10.0 - (overcap_ratio * 50)  # Max penalty: -5 points
        return max(0, min(10, rating))

    def _calculate_placement_rating(self, evaluations: List[MoveEvaluation]) -> float:
        """Calculate card placement rating (0-10)"""
        if not evaluations:
            return 5.0

        # Based on average evaluation loss
        avg_loss = sum(e.evaluation_loss for e in evaluations) / len(evaluations)

        # Convert to 0-10 scale (0% loss = 10, 50%+ loss = 0)
        rating = 10.0 - (avg_loss / 5)
        return max(0, min(10, rating))

    def _calculate_defensive_rating(self, evaluations: List[MoveEvaluation]) -> float:
        """Calculate defensive play rating (0-10)"""
        # Placeholder: Could analyze defensive card usage, response times, etc.
        return 5.0

    def _calculate_offensive_rating(self, evaluations: List[MoveEvaluation]) -> float:
        """Calculate offensive play rating (0-10)"""
        # Placeholder: Could analyze pressure, bridge spam, etc.
        return 5.0


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Example usage
    if len(sys.argv) < 3:
        print("Usage: python clashfish_engine.py <model_path> <video_path>")
        sys.exit(1)

    model_path = sys.argv[1]
    video_path = sys.argv[2]

    # Process video
    from video_processor import VideoProcessor
    processor = VideoProcessor(fps=2.0)
    game_states, actions = processor.process_video(video_path)

    # Analyze with engine
    engine = ClashFishEngine(model_path)
    analysis = engine.analyze_game(game_states, actions)

    # Print report
    print("\n" + "="*50)
    print("CLASHFISH ANALYSIS REPORT")
    print("="*50)
    print(f"\nTotal Moves: {analysis.total_moves}")
    print(f"Accuracy: {analysis.accuracy_score:.1f}%\n")
    print(f"Move Quality Breakdown:")
    print(f"  Brilliant (!!): {analysis.brilliant_moves}")
    print(f"  Good (!): {analysis.good_moves}")
    print(f"  Inaccuracies (?!): {analysis.inaccuracies}")
    print(f"  Mistakes (?): {analysis.mistakes}")
    print(f"  Blunders (??): {analysis.blunders}\n")
    print(f"Performance Ratings:")
    print(f"  Elixir Management: {analysis.elixir_management_rating:.1f}/10")
    print(f"  Card Placement: {analysis.card_placement_rating:.1f}/10")
    print(f"  Defensive Play: {analysis.defensive_rating:.1f}/10")
    print(f"  Offensive Play: {analysis.offensive_rating:.1f}/10")
    print(f"  Overall: {analysis.overall_rating:.1f}/10\n")
    print(f"Top Blunders:")
    for i, blunder in enumerate(analysis.top_blunders[:3], 1):
        action = blunder.player_action
        print(f"  {i}. [{action.timestamp:.1f}s] {action.card_played} - Loss: {blunder.evaluation_loss:.1f}%")
