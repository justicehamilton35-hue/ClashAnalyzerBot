"""
ClashFish Mistake Detection System
Identifies specific types of gameplay errors
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
from video_processor import GameState, PlayerAction, Position
from clashfish_engine import MoveEvaluation, MoveQuality
import numpy as np


@dataclass
class Mistake:
    """Represents a specific gameplay mistake"""
    timestamp: float
    mistake_type: str
    description: str
    severity: str  # "minor", "moderate", "critical"
    suggestion: str
    evaluation: Optional[MoveEvaluation] = None


class MistakeDetector:
    """Detects and classifies gameplay mistakes"""

    # Spell cards that should have targets
    SPELL_CARDS = ['Arrows', 'Fireball', 'Zap', 'Lightning', 'Rocket', 'Freeze', 'Tornado', 'Poison']

    # Defensive/reactive cards
    DEFENSIVE_CARDS = ['Arrows', 'Zap', 'Knight', 'Musketeer', 'Skeleton Army', 'Barbarians', 'Inferno Tower']

    def __init__(self):
        pass

    def detect_all_mistakes(self,
                          game_states: List[GameState],
                          player_actions: List[PlayerAction],
                          evaluations: List[MoveEvaluation]) -> List[Mistake]:
        """
        Detect all types of mistakes in a game

        Args:
            game_states: Sequence of game states
            player_actions: Player's actions
            evaluations: Move evaluations from engine

        Returns:
            List of detected mistakes
        """
        mistakes = []

        # Elixir management mistakes
        mistakes.extend(self._detect_elixir_mistakes(game_states, player_actions))

        # Spell wastage
        mistakes.extend(self._detect_spell_mistakes(player_actions, evaluations))

        # Placement errors
        mistakes.extend(self._detect_placement_mistakes(player_actions, evaluations))

        # Timing errors
        mistakes.extend(self._detect_timing_mistakes(game_states, player_actions))

        # Strategic errors (from engine evaluations)
        mistakes.extend(self._detect_strategic_mistakes(evaluations))

        # Sort by severity and timestamp
        mistakes.sort(key=lambda m: (
            {'critical': 0, 'moderate': 1, 'minor': 2}[m.severity],
            m.timestamp
        ))

        return mistakes

    def _detect_elixir_mistakes(self,
                               game_states: List[GameState],
                               actions: List[PlayerAction]) -> List[Mistake]:
        """Detect elixir management errors"""
        mistakes = []

        # Check for overcapping (staying at 10 elixir)
        overcap_start = None
        for i, state in enumerate(game_states):
            if state.elixir >= 10:
                if overcap_start is None:
                    overcap_start = i
            else:
                if overcap_start is not None:
                    # Calculate overcap duration
                    overcap_duration = (i - overcap_start) * 0.5  # 0.5s per frame
                    if overcap_duration >= 3.0:  # Overcapped for 3+ seconds
                        mistakes.append(Mistake(
                            timestamp=game_states[overcap_start].timestamp,
                            mistake_type="elixir_overcap",
                            description=f"Overcapped at 10 elixir for {overcap_duration:.1f}s",
                            severity="moderate" if overcap_duration < 5 else "critical",
                            suggestion="Play cards faster to avoid wasting elixir generation"
                        ))
                    overcap_start = None

        # Check for poor elixir trades
        for i, action in enumerate(actions):
            # Find corresponding state
            state_before = action.game_state_before

            # Check if player spent a lot of elixir when enemy had few units
            if action.elixir_cost >= 5 and len(state_before.enemy_units) == 0:
                mistakes.append(Mistake(
                    timestamp=action.timestamp,
                    mistake_type="poor_elixir_trade",
                    description=f"Played expensive {action.card_played} ({action.elixir_cost} elixir) with no enemies on field",
                    severity="moderate",
                    suggestion="Build elixir advantage by playing cheaper cards or wait for enemy to commit"
                ))

        return mistakes

    def _detect_spell_mistakes(self,
                              actions: List[PlayerAction],
                              evaluations: List[MoveEvaluation]) -> List[Mistake]:
        """Detect spell wastage"""
        mistakes = []

        for action, evaluation in zip(actions, evaluations):
            if action.card_played in self.SPELL_CARDS:
                # Check if there were enemies near the spell location
                state = action.game_state_before
                spell_pos = action.position

                # Count enemies within spell range (approximate radius)
                enemies_in_range = 0
                for enemy in state.enemy_units:
                    distance = np.sqrt((enemy.x - spell_pos.x)**2 +
                                     (enemy.y - spell_pos.y)**2)
                    if distance < 0.15:  # ~15% of screen = spell radius
                        enemies_in_range += 1

                if enemies_in_range == 0:
                    mistakes.append(Mistake(
                        timestamp=action.timestamp,
                        mistake_type="spell_wastage",
                        description=f"Used {action.card_played} with no enemies in range",
                        severity="critical",
                        suggestion=f"Save {action.card_played} for enemy swarms or key targets",
                        evaluation=evaluation
                    ))

        return mistakes

    def _detect_placement_mistakes(self,
                                  actions: List[PlayerAction],
                                  evaluations: List[MoveEvaluation]) -> List[Mistake]:
        """Detect poor card placement"""
        mistakes = []

        for action, evaluation in zip(actions, evaluations):
            # Check if unit was placed far from any action
            state = action.game_state_before
            placement = action.position

            # Calculate distance to nearest enemy
            min_distance = float('inf')
            for enemy in state.enemy_units:
                distance = np.sqrt((enemy.x - placement.x)**2 +
                                 (enemy.y - placement.y)**2)
                min_distance = min(min_distance, distance)

            # If placed very far from enemies (and not a defensive position)
            if min_distance > 0.4 and placement.y > 0.5:  # Lower half of screen
                if action.card_played not in self.DEFENSIVE_CARDS:
                    mistakes.append(Mistake(
                        timestamp=action.timestamp,
                        mistake_type="poor_placement",
                        description=f"Placed {action.card_played} far from enemies",
                        severity="minor",
                        suggestion="Place offensive cards closer to bridge or enemy units",
                        evaluation=evaluation
                    ))

        return mistakes

    def _detect_timing_mistakes(self,
                               game_states: List[GameState],
                               actions: List[PlayerAction]) -> List[Mistake]:
        """Detect timing errors"""
        mistakes = []

        for i, action in enumerate(actions):
            state = action.game_state_before

            # Check for slow reactions to enemy pushes
            # If many enemies on field and player has low elixir
            if len(state.enemy_units) >= 3 and action.elixir_cost > state.elixir:
                mistakes.append(Mistake(
                    timestamp=action.timestamp,
                    mistake_type="slow_reaction",
                    description=f"Tried to play {action.card_played} ({action.elixir_cost} elixir) but only had {state.elixir}",
                    severity="moderate",
                    suggestion="React faster to enemy pushes to have enough elixir"
                ))

        return mistakes

    def _detect_strategic_mistakes(self,
                                  evaluations: List[MoveEvaluation]) -> List[Mistake]:
        """Detect strategic errors from engine evaluations"""
        mistakes = []

        for evaluation in evaluations:
            # Major blunders and mistakes
            if evaluation.quality in [MoveQuality.BLUNDER, MoveQuality.MISTAKE]:
                action = evaluation.player_action

                # Get best alternative
                if evaluation.top_alternatives:
                    best_card, best_pos, best_q = evaluation.top_alternatives[0]
                    suggestion = f"Consider {best_card} at ({best_pos.x:.2f}, {best_pos.y:.2f}) instead"
                else:
                    suggestion = "See engine recommendations for better options"

                severity = "critical" if evaluation.quality == MoveQuality.BLUNDER else "moderate"

                mistakes.append(Mistake(
                    timestamp=action.timestamp,
                    mistake_type="strategic_error",
                    description=f"Poor choice: {action.card_played} (evaluation loss: {evaluation.evaluation_loss:.1f}%)",
                    severity=severity,
                    suggestion=suggestion,
                    evaluation=evaluation
                ))

        return mistakes

    def get_improvement_summary(self, mistakes: List[Mistake]) -> Dict[str, str]:
        """
        Generate improvement suggestions based on recurring mistakes

        Args:
            mistakes: List of detected mistakes

        Returns:
            Dictionary of improvement areas and suggestions
        """
        # Count mistake types
        mistake_counts = {}
        for mistake in mistakes:
            mistake_counts[mistake.mistake_type] = mistake_counts.get(mistake.mistake_type, 0) + 1

        # Generate suggestions for top issues
        improvements = {}

        if mistake_counts.get('elixir_overcap', 0) >= 2:
            improvements['Elixir Management'] = (
                "You frequently overcap at 10 elixir. Try to play cards faster "
                "to maintain constant pressure and avoid wasting elixir generation."
            )

        if mistake_counts.get('spell_wastage', 0) >= 2:
            improvements['Spell Usage'] = (
                f"You wasted {mistake_counts['spell_wastage']} spells. "
                "Save spells for when enemies are grouped or for key targets. "
                "Don't panic-spell!"
            )

        if mistake_counts.get('poor_placement', 0) >= 3:
            improvements['Card Placement'] = (
                "Improve your card placement. Place units closer to the bridge "
                "for offense, and behind towers for defense. Position matters!"
            )

        if mistake_counts.get('strategic_error', 0) >= 5:
            improvements['Decision Making'] = (
                f"You made {mistake_counts['strategic_error']} strategic errors. "
                "Think more carefully about each play. What is your win condition? "
                "Are you defending efficiently?"
            )

        if mistake_counts.get('slow_reaction', 0) >= 2:
            improvements['Reaction Time'] = (
                "You reacted slowly to enemy pushes. Watch your opponent's elixir "
                "and anticipate their moves. Start defending earlier."
            )

        return improvements


if __name__ == "__main__":
    # Test mistake detection
    print("Mistake Detector Module")
    print("Run clashfish_engine.py to see full analysis with mistake detection")
