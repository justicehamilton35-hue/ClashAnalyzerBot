"""
Position Evaluation Engine for Clash Royale Analyzer
Similar to Stockfish's evaluation function for chess
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import torch
import torch.nn as nn


@dataclass
class EvaluationMetrics:
    """Detailed evaluation metrics"""
    material_score: float  # Troop/tower value on board
    board_control: float  # Territory control
    elixir_advantage: float  # Elixir difference
    tower_health: float  # Tower health differential
    positioning_score: float  # Quality of troop positioning
    pressure_score: float  # Offensive pressure
    defense_score: float  # Defensive strength
    tempo_score: float  # Pace of play

    # Combined scores
    total_score: float  # Overall position evaluation (-10 to +10)
    win_probability: float  # 0.0 to 1.0


class PositionEvaluator:
    """
    Evaluates Clash Royale positions similar to how Stockfish evaluates chess positions
    """

    # Card elixir costs (comprehensive database)
    CARD_COSTS = {
        # Troops
        "Knight": 3, "Archers": 3, "Arrows": 3, "Fireball": 4, "Mini P.E.K.K.A": 4,
        "Musketeer": 4, "Giant": 5, "Prince": 5, "Baby Dragon": 4, "Skeleton Army": 3,
        "Witch": 5, "Barbarians": 5, "Hog Rider": 4, "Valkyrie": 4, "Golem": 8,
        "Pekka": 7, "Balloon": 5, "Miner": 3, "Sparky": 6, "Bowler": 5,
        "Lumberjack": 4, "Ice Wizard": 3, "Princess": 3, "Lava Hound": 7,
        "Electro Wizard": 4, "Mega Knight": 7, "Royal Ghost": 3, "Bandit": 3,
        "Night Witch": 4, "Inferno Dragon": 4, "Graveyard": 5, "Clone": 3,
        "Goblin Gang": 3, "Elite Barbarians": 6, "Ice Golem": 2, "Mega Minion": 3,
        "Dart Goblin": 3, "Goblins": 2, "Skeletons": 1, "Ice Spirit": 1,
        "Fire Spirit": 1, "Zap": 2, "Freeze": 4, "Poison": 4, "Tornado": 3,
        "Log": 2, "Rocket": 6, "Lightning": 6, "Rage": 2, "Mirror": 0,
        "Earthquake": 3, "Barbarian Barrel": 2, "Royal Hogs": 5, "Snowball": 2,
        "Goblin Barrel": 3, "X-Bow": 6, "Mortar": 4, "Cannon": 3, "Tesla": 4,
        "Inferno Tower": 5, "Bomb Tower": 4, "Elixir Collector": 6, "Furnace": 4,
        "Goblin Hut": 5, "Barbarian Hut": 7, "Tombstone": 3,
        # Add more cards as needed
    }

    # Tower values
    KING_TOWER_VALUE = 100.0
    PRINCESS_TOWER_VALUE = 50.0

    # Board zones (y-coordinate normalized)
    ZONE_YOUR_BASE = (0.7, 1.0)  # Your side
    ZONE_MIDDLE = (0.3, 0.7)  # Middle
    ZONE_ENEMY_BASE = (0.0, 0.3)  # Enemy side

    def __init__(self, use_neural_net: bool = True):
        """
        Initialize position evaluator

        Args:
            use_neural_net: Whether to use neural network evaluation (when available)
        """
        self.use_neural_net = use_neural_net
        self.neural_evaluator = None

        if use_neural_net:
            self._load_neural_evaluator()

    def _load_neural_evaluator(self):
        """Load pre-trained neural network for position evaluation"""
        # Placeholder - implement when model is trained
        # self.neural_evaluator = torch.load('models/position_evaluator.pth')
        pass

    def evaluate_position(self, game_state) -> EvaluationMetrics:
        """
        Evaluate a game position

        Args:
            game_state: GameState object

        Returns:
            EvaluationMetrics with detailed evaluation
        """
        # Calculate individual metrics
        material = self._evaluate_material(game_state)
        board_control = self._evaluate_board_control(game_state)
        elixir = self._evaluate_elixir(game_state)
        towers = self._evaluate_towers(game_state)
        positioning = self._evaluate_positioning(game_state)
        pressure = self._evaluate_pressure(game_state)
        defense = self._evaluate_defense(game_state)
        tempo = self._evaluate_tempo(game_state)

        # Weighted combination (tuned weights)
        total_score = (
            material * 0.25 +
            board_control * 0.15 +
            elixir * 0.10 +
            towers * 0.30 +
            positioning * 0.10 +
            pressure * 0.05 +
            defense * 0.05 +
            tempo * 0.00  # Tempo is informational, not scored directly
        )

        # Clamp to -10 to +10 range
        total_score = np.clip(total_score, -10.0, 10.0)

        # Convert to win probability using sigmoid
        win_prob = self._score_to_probability(total_score)

        return EvaluationMetrics(
            material_score=material,
            board_control=board_control,
            elixir_advantage=elixir,
            tower_health=towers,
            positioning_score=positioning,
            pressure_score=pressure,
            defense_score=defense,
            tempo_score=tempo,
            total_score=total_score,
            win_probability=win_prob
        )

    def _evaluate_material(self, game_state) -> float:
        """
        Evaluate material advantage (troops on board)

        Returns:
            Score from -10 to +10
        """
        your_value = 0.0
        opponent_value = 0.0

        # Calculate your troop value
        for troop in game_state.your_troops:
            card_name = troop.class_name.replace("ally ", "").replace("enemy ", "")
            cost = self.CARD_COSTS.get(card_name, 3)  # Default 3 elixir
            your_value += cost

        # Calculate opponent troop value
        for troop in game_state.opponent_troops:
            card_name = troop.class_name.replace("ally ", "").replace("enemy ", "")
            cost = self.CARD_COSTS.get(card_name, 3)
            opponent_value += cost

        # Material difference
        material_diff = your_value - opponent_value

        # Normalize to -10 to +10 range (assuming max ~30 elixir on board)
        return np.clip(material_diff / 3.0, -10.0, 10.0)

    def _evaluate_board_control(self, game_state) -> float:
        """
        Evaluate board control and territory

        Returns:
            Score from -10 to +10
        """
        your_control = 0.0
        opponent_control = 0.0

        # Zone-based control evaluation
        def count_troops_in_zone(troops, zone_min, zone_max):
            count = 0
            for troop in troops:
                if zone_min <= troop.y <= zone_max:
                    count += 1
            return count

        # Enemy base control (most valuable)
        your_enemy_base = count_troops_in_zone(game_state.your_troops, *self.ZONE_ENEMY_BASE)
        opponent_your_base = count_troops_in_zone(game_state.opponent_troops, *self.ZONE_YOUR_BASE)

        # Middle control
        your_middle = count_troops_in_zone(game_state.your_troops, *self.ZONE_MIDDLE)
        opponent_middle = count_troops_in_zone(game_state.opponent_troops, *self.ZONE_MIDDLE)

        # Weighted control score
        your_control = your_enemy_base * 3 + your_middle * 1
        opponent_control = opponent_your_base * 3 + opponent_middle * 1

        control_diff = your_control - opponent_control

        return np.clip(control_diff, -10.0, 10.0)

    def _evaluate_elixir(self, game_state) -> float:
        """
        Evaluate elixir advantage

        Returns:
            Score from -10 to +10
        """
        elixir_diff = game_state.your_elixir - game_state.opponent_elixir

        # Normalize (max difference is 10 elixir)
        return np.clip(elixir_diff, -10.0, 10.0)

    def _evaluate_towers(self, game_state) -> float:
        """
        Evaluate tower health advantage

        Returns:
            Score from -10 to +10
        """
        your_towers = game_state.your_towers
        opponent_towers = game_state.opponent_towers

        if not your_towers or not opponent_towers:
            return 0.0

        # Count towers
        your_count = (
            int(your_towers.king_tower) * self.KING_TOWER_VALUE +
            int(your_towers.left_princess) * self.PRINCESS_TOWER_VALUE +
            int(your_towers.right_princess) * self.PRINCESS_TOWER_VALUE
        )

        opponent_count = (
            int(opponent_towers.king_tower) * self.KING_TOWER_VALUE +
            int(opponent_towers.left_princess) * self.PRINCESS_TOWER_VALUE +
            int(opponent_towers.right_princess) * self.PRINCESS_TOWER_VALUE
        )

        tower_diff = your_count - opponent_count

        # Normalize
        max_towers = self.KING_TOWER_VALUE + 2 * self.PRINCESS_TOWER_VALUE
        return np.clip((tower_diff / max_towers) * 10.0, -10.0, 10.0)

    def _evaluate_positioning(self, game_state) -> float:
        """
        Evaluate quality of troop positioning

        Returns:
            Score from -10 to +10
        """
        your_positioning = 0.0
        opponent_positioning = 0.0

        # Reward spread-out positioning (not clumped)
        def calculate_spread(troops):
            if len(troops) < 2:
                return 0.0

            spread = 0.0
            for i, troop1 in enumerate(troops):
                for troop2 in troops[i+1:]:
                    distance = np.sqrt((troop1.x - troop2.x)**2 + (troop1.y - troop2.y)**2)
                    spread += distance

            return spread / (len(troops) * (len(troops) - 1) / 2) if len(troops) > 1 else 0.0

        your_spread = calculate_spread(game_state.your_troops)
        opponent_spread = calculate_spread(game_state.opponent_troops)

        # Good spread is around 0.3-0.5 (normalized coordinates)
        your_positioning = 10 * (1 - abs(your_spread - 0.4) / 0.4) if your_spread > 0 else 0
        opponent_positioning = 10 * (1 - abs(opponent_spread - 0.4) / 0.4) if opponent_spread > 0 else 0

        return np.clip(your_positioning - opponent_positioning, -10.0, 10.0)

    def _evaluate_pressure(self, game_state) -> float:
        """
        Evaluate offensive pressure

        Returns:
            Score from -10 to +10
        """
        # Pressure is based on troops near enemy towers
        your_pressure = 0
        opponent_pressure = 0

        for troop in game_state.your_troops:
            if troop.y < 0.3:  # Near enemy base
                your_pressure += 1

        for troop in game_state.opponent_troops:
            if troop.y > 0.7:  # Near your base
                opponent_pressure += 1

        pressure_diff = your_pressure - opponent_pressure

        return np.clip(pressure_diff * 2, -10.0, 10.0)

    def _evaluate_defense(self, game_state) -> float:
        """
        Evaluate defensive strength

        Returns:
            Score from -10 to +10
        """
        # Defense is based on troops in your base defending
        your_defenders = 0
        opponent_defenders = 0

        for troop in game_state.your_troops:
            if troop.y > 0.7:  # In your base
                your_defenders += 1

        for troop in game_state.opponent_troops:
            if troop.y < 0.3:  # In opponent base
                opponent_defenders += 1

        # Compare defense vs opponent's offense
        your_defense_score = your_defenders - len([t for t in game_state.opponent_troops if t.y > 0.7])
        opponent_defense_score = opponent_defenders - len([t for t in game_state.your_troops if t.y < 0.3])

        defense_diff = your_defense_score - opponent_defense_score

        return np.clip(defense_diff * 2, -10.0, 10.0)

    def _evaluate_tempo(self, game_state) -> float:
        """
        Evaluate tempo/pace of play

        Returns:
            Tempo score (higher = faster pace)
        """
        # Tempo based on total troops and elixir spent
        total_troops = len(game_state.your_troops) + len(game_state.opponent_troops)

        # Normalize tempo (typical game might have 5-15 troops on board)
        tempo = (total_troops / 10.0) * 10.0

        return np.clip(tempo, 0.0, 10.0)

    def _score_to_probability(self, score: float) -> float:
        """
        Convert evaluation score to win probability using sigmoid

        Args:
            score: Evaluation score (-10 to +10)

        Returns:
            Win probability (0.0 to 1.0)
        """
        # Sigmoid transformation
        # At score=0, prob=0.5; at score=10, prob~0.99; at score=-10, prob~0.01
        return 1.0 / (1.0 + np.exp(-score / 2.0))

    def compare_moves(self, current_state, move_states: List[Tuple[str, any]]) -> List[Tuple[str, float]]:
        """
        Compare multiple possible moves from a position

        Args:
            current_state: Current game state
            move_states: List of (move_name, resulting_state) tuples

        Returns:
            List of (move_name, evaluation_score) sorted by score
        """
        move_evaluations = []

        for move_name, state in move_states:
            eval_metrics = self.evaluate_position(state)
            move_evaluations.append((move_name, eval_metrics.total_score))

        # Sort by score (best first)
        move_evaluations.sort(key=lambda x: x[1], reverse=True)

        return move_evaluations

    def classify_move_quality(self, prev_eval: float, curr_eval: float) -> str:
        """
        Classify move quality based on evaluation change

        Args:
            prev_eval: Previous position evaluation
            curr_eval: Current position evaluation after move

        Returns:
            Move classification: "brilliant", "great", "good", "book",
                                "inaccuracy", "mistake", "blunder"
        """
        # Positive change is good for you
        eval_change = curr_eval - prev_eval

        if eval_change >= 3.0:
            return "brilliant"
        elif eval_change >= 1.5:
            return "great"
        elif eval_change >= 0.5:
            return "good"
        elif eval_change >= -0.5:
            return "book"
        elif eval_change >= -1.5:
            return "inaccuracy"
        elif eval_change >= -3.0:
            return "mistake"
        else:
            return "blunder"

    def get_move_symbol(self, classification: str) -> str:
        """Get chess-style symbol for move classification"""
        symbols = {
            "brilliant": "!!!",
            "great": "!!",
            "good": "!",
            "book": "",
            "inaccuracy": "?!",
            "mistake": "?",
            "blunder": "??"
        }
        return symbols.get(classification, "")
