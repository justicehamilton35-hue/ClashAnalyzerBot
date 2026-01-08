"""
Move Analysis Engine for Clash Royale Analyzer
Analyzes moves, identifies blunders and brilliant plays
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np


class MoveQuality(Enum):
    """Move quality classification"""
    BRILLIANT = "brilliant"  # !!!
    GREAT = "great"  # !!
    GOOD = "good"  # !
    BOOK = "book"  # Standard move
    INACCURACY = "inaccuracy"  # ?!
    MISTAKE = "mistake"  # ?
    BLUNDER = "blunder"  # ??


@dataclass
class MoveAnalysis:
    """Detailed analysis of a single move"""
    # Move information
    card_name: str
    player: str
    position: Tuple[float, float]
    timestamp: float
    frame_number: int

    # Evaluation
    evaluation_before: float  # Position eval before move
    evaluation_after: float  # Position eval after move
    eval_change: float  # Change in evaluation

    # Classification
    move_quality: MoveQuality
    move_symbol: str  # !, ??, etc.

    # Alternative moves
    best_move: Optional[str] = None  # What should have been played
    best_move_eval: Optional[float] = None  # Eval of best move
    alternatives: List[Dict] = None  # Other good moves

    # Detailed explanation
    explanation: str = ""
    tactical_themes: List[str] = None  # e.g., ["tempo", "defense", "counter"]

    # Context
    elixir_before: int = 0
    elixir_after: int = 0
    win_prob_before: float = 0.5
    win_prob_after: float = 0.5


@dataclass
class GameAnalysisSummary:
    """Summary of entire game analysis"""
    # Move counts by quality
    brilliant_moves: int = 0
    great_moves: int = 0
    good_moves: int = 0
    book_moves: int = 0
    inaccuracies: int = 0
    mistakes: int = 0
    blunders: int = 0

    # Average metrics
    average_eval: float = 0.0
    average_win_prob: float = 0.5
    accuracy_score: float = 0.0  # 0-100%

    # Detailed analysis
    all_moves: List[MoveAnalysis] = None
    key_moments: List[MoveAnalysis] = None  # Critical moves

    # Playstyle
    playstyle: str = "balanced"
    aggression_rating: float = 5.0  # 0-10
    defense_rating: float = 5.0  # 0-10
    elixir_efficiency: float = 5.0  # 0-10

    # Recommendations
    strengths: List[str] = None
    weaknesses: List[str] = None
    suggestions: List[str] = None


class MoveAnalyzer:
    """Analyzes moves and generates insights"""

    def __init__(self, position_evaluator):
        """
        Initialize move analyzer

        Args:
            position_evaluator: PositionEvaluator instance
        """
        self.evaluator = position_evaluator

    def analyze_move(self,
                    card_play,
                    state_before,
                    state_after) -> MoveAnalysis:
        """
        Analyze a single card play

        Args:
            card_play: CardPlay object
            state_before: GameState before the move
            state_after: GameState after the move

        Returns:
            MoveAnalysis with detailed evaluation
        """
        # Evaluate positions
        eval_before = self.evaluator.evaluate_position(state_before)
        eval_after = self.evaluator.evaluate_position(state_after)

        eval_change = eval_after.total_score - eval_before.total_score

        # Classify move quality
        quality = self._classify_move(eval_change, eval_before.total_score)
        symbol = self._get_move_symbol(quality)

        # Generate explanation
        explanation = self._generate_explanation(
            card_play, state_before, state_after,
            eval_before, eval_after, quality
        )

        # Identify tactical themes
        themes = self._identify_tactical_themes(card_play, state_before, state_after)

        # TODO: Calculate best alternative moves (requires move generation)
        best_move = None
        best_move_eval = None

        return MoveAnalysis(
            card_name=card_play.card.name,
            player=card_play.player.value,
            position=card_play.position,
            timestamp=card_play.timestamp,
            frame_number=card_play.frame_number,
            evaluation_before=eval_before.total_score,
            evaluation_after=eval_after.total_score,
            eval_change=eval_change,
            move_quality=quality,
            move_symbol=symbol,
            best_move=best_move,
            best_move_eval=best_move_eval,
            explanation=explanation,
            tactical_themes=themes,
            elixir_before=card_play.elixir_before,
            elixir_after=card_play.elixir_after,
            win_prob_before=eval_before.win_probability,
            win_prob_after=eval_after.win_probability
        )

    def _classify_move(self, eval_change: float, current_eval: float) -> MoveQuality:
        """
        Classify move quality based on evaluation change

        Args:
            eval_change: Change in evaluation after move
            current_eval: Current position evaluation

        Returns:
            MoveQuality enum
        """
        # More lenient thresholds in losing positions
        if current_eval < -3.0:
            # In bad positions, finding any improvement is great
            if eval_change >= 2.0:
                return MoveQuality.BRILLIANT
            elif eval_change >= 1.0:
                return MoveQuality.GREAT
            elif eval_change >= 0.3:
                return MoveQuality.GOOD
            elif eval_change >= -0.3:
                return MoveQuality.BOOK
            elif eval_change >= -1.0:
                return MoveQuality.INACCURACY
            elif eval_change >= -2.0:
                return MoveQuality.MISTAKE
            else:
                return MoveQuality.BLUNDER
        else:
            # Standard thresholds
            if eval_change >= 3.0:
                return MoveQuality.BRILLIANT
            elif eval_change >= 1.5:
                return MoveQuality.GREAT
            elif eval_change >= 0.5:
                return MoveQuality.GOOD
            elif eval_change >= -0.5:
                return MoveQuality.BOOK
            elif eval_change >= -1.5:
                return MoveQuality.INACCURACY
            elif eval_change >= -3.0:
                return MoveQuality.MISTAKE
            else:
                return MoveQuality.BLUNDER

    def _get_move_symbol(self, quality: MoveQuality) -> str:
        """Get chess-style symbol for move quality"""
        symbols = {
            MoveQuality.BRILLIANT: "!!!",
            MoveQuality.GREAT: "!!",
            MoveQuality.GOOD: "!",
            MoveQuality.BOOK: "",
            MoveQuality.INACCURACY: "?!",
            MoveQuality.MISTAKE: "?",
            MoveQuality.BLUNDER: "??"
        }
        return symbols.get(quality, "")

    def _generate_explanation(self,
                             card_play,
                             state_before,
                             state_after,
                             eval_before,
                             eval_after,
                             quality) -> str:
        """
        Generate human-readable explanation of move

        Returns:
            Explanation string
        """
        card_name = card_play.card.name
        eval_change = eval_after.total_score - eval_before.total_score

        if quality == MoveQuality.BRILLIANT:
            return (f"Brilliant move! Playing {card_name} significantly improved your position "
                   f"(+{eval_change:.1f} evaluation). This created strong offensive pressure "
                   f"and gained a decisive advantage.")

        elif quality == MoveQuality.GREAT:
            return (f"Great move! {card_name} was very effective here "
                   f"(+{eval_change:.1f} evaluation). This gave you a significant advantage.")

        elif quality == MoveQuality.GOOD:
            return (f"Good move. {card_name} improved your position "
                   f"(+{eval_change:.1f} evaluation).")

        elif quality == MoveQuality.BOOK:
            return f"Standard move. {card_name} maintained your position."

        elif quality == MoveQuality.INACCURACY:
            return (f"Inaccuracy. {card_name} slightly weakened your position "
                   f"({eval_change:.1f} evaluation). Consider placing it differently "
                   f"or playing a different card.")

        elif quality == MoveQuality.MISTAKE:
            return (f"Mistake. Playing {card_name} here significantly weakened your position "
                   f"({eval_change:.1f} evaluation). You should have played defensively "
                   f"or built a better push.")

        elif quality == MoveQuality.BLUNDER:
            return (f"Blunder! {card_name} was a severe mistake "
                   f"({eval_change:.1f} evaluation). This likely cost you the game. "
                   f"You needed to defend or manage elixir better.")

        return ""

    def _identify_tactical_themes(self, card_play, state_before, state_after) -> List[str]:
        """
        Identify tactical themes in the move

        Returns:
            List of theme strings
        """
        themes = []

        # Check if defensive play
        if len(state_after.opponent_troops) < len(state_before.opponent_troops):
            themes.append("defense")

        # Check if offensive play
        your_troops_forward = sum(1 for t in state_after.your_troops if t.y < 0.4)
        if your_troops_forward > 2:
            themes.append("offense")
            themes.append("pressure")

        # Check elixir efficiency
        elixir_spent = state_before.your_elixir - state_after.your_elixir
        if elixir_spent <= 2:
            themes.append("cycle")
        elif elixir_spent >= 5:
            themes.append("heavy_push")

        # Check counter play
        if len(state_after.opponent_troops) < len(state_before.opponent_troops) and elixir_spent <= 3:
            themes.append("counter")
            themes.append("elixir_advantage")

        # Check tempo
        if len(state_after.your_troops) > len(state_before.your_troops) + 2:
            themes.append("tempo")

        return themes

    def analyze_full_game(self,
                         game_states: List,
                         card_plays: List) -> GameAnalysisSummary:
        """
        Analyze entire game and generate summary

        Args:
            game_states: List of GameState objects
            card_plays: List of CardPlay objects

        Returns:
            GameAnalysisSummary with complete analysis
        """
        all_moves = []
        move_quality_counts = {
            MoveQuality.BRILLIANT: 0,
            MoveQuality.GREAT: 0,
            MoveQuality.GOOD: 0,
            MoveQuality.BOOK: 0,
            MoveQuality.INACCURACY: 0,
            MoveQuality.MISTAKE: 0,
            MoveQuality.BLUNDER: 0
        }

        # Analyze each move
        for i, play in enumerate(card_plays):
            # Find corresponding states
            state_before = None
            state_after = None

            for j, state in enumerate(game_states):
                if state.timestamp <= play.timestamp:
                    state_before = state
                if state.timestamp > play.timestamp:
                    state_after = state
                    break

            if state_before and state_after:
                analysis = self.analyze_move(play, state_before, state_after)
                all_moves.append(analysis)
                move_quality_counts[analysis.move_quality] += 1

        # Calculate summary statistics
        total_moves = len(all_moves)
        if total_moves == 0:
            return GameAnalysisSummary()

        # Accuracy score (percentage of good moves)
        good_moves = (move_quality_counts[MoveQuality.BRILLIANT] +
                     move_quality_counts[MoveQuality.GREAT] +
                     move_quality_counts[MoveQuality.GOOD] +
                     move_quality_counts[MoveQuality.BOOK])

        accuracy = (good_moves / total_moves) * 100 if total_moves > 0 else 0

        # Average evaluation and win probability
        avg_eval = np.mean([m.evaluation_after for m in all_moves])
        avg_win_prob = np.mean([m.win_prob_after for m in all_moves])

        # Identify key moments (brilliant moves and blunders)
        key_moments = [m for m in all_moves if m.move_quality in
                      [MoveQuality.BRILLIANT, MoveQuality.BLUNDER]]

        # Analyze playstyle
        playstyle_analysis = self._analyze_playstyle(all_moves)

        # Generate recommendations
        strengths, weaknesses, suggestions = self._generate_recommendations(
            all_moves, move_quality_counts, playstyle_analysis
        )

        return GameAnalysisSummary(
            brilliant_moves=move_quality_counts[MoveQuality.BRILLIANT],
            great_moves=move_quality_counts[MoveQuality.GREAT],
            good_moves=move_quality_counts[MoveQuality.GOOD],
            book_moves=move_quality_counts[MoveQuality.BOOK],
            inaccuracies=move_quality_counts[MoveQuality.INACCURACY],
            mistakes=move_quality_counts[MoveQuality.MISTAKE],
            blunders=move_quality_counts[MoveQuality.BLUNDER],
            average_eval=avg_eval,
            average_win_prob=avg_win_prob,
            accuracy_score=accuracy,
            all_moves=all_moves,
            key_moments=key_moments,
            playstyle=playstyle_analysis["playstyle"],
            aggression_rating=playstyle_analysis["aggression"],
            defense_rating=playstyle_analysis["defense"],
            elixir_efficiency=playstyle_analysis["efficiency"],
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions
        )

    def _analyze_playstyle(self, moves: List[MoveAnalysis]) -> Dict:
        """
        Analyze overall playstyle from moves

        Returns:
            Dictionary with playstyle metrics
        """
        if not moves:
            return {
                "playstyle": "balanced",
                "aggression": 5.0,
                "defense": 5.0,
                "efficiency": 5.0
            }

        # Count tactical themes
        offense_count = sum(1 for m in moves if m.tactical_themes and "offense" in m.tactical_themes)
        defense_count = sum(1 for m in moves if m.tactical_themes and "defense" in m.tactical_themes)
        cycle_count = sum(1 for m in moves if m.tactical_themes and "cycle" in m.tactical_themes)
        heavy_count = sum(1 for m in moves if m.tactical_themes and "heavy_push" in m.tactical_themes)

        total = len(moves)

        # Calculate ratings
        aggression = ((offense_count + heavy_count) / total) * 10 if total > 0 else 5.0
        defense = (defense_count / total) * 10 if total > 0 else 5.0
        efficiency = (cycle_count / total) * 10 if total > 0 else 5.0

        # Determine playstyle
        if aggression > 7:
            if cycle_count > heavy_count:
                playstyle = "bridge_spam"
            else:
                playstyle = "beatdown"
        elif defense > 7:
            playstyle = "control"
        elif efficiency > 7:
            playstyle = "cycle"
        else:
            playstyle = "balanced"

        return {
            "playstyle": playstyle,
            "aggression": min(aggression, 10.0),
            "defense": min(defense, 10.0),
            "efficiency": min(efficiency, 10.0)
        }

    def _generate_recommendations(self,
                                 moves: List[MoveAnalysis],
                                 quality_counts: Dict,
                                 playstyle: Dict) -> Tuple[List[str], List[str], List[str]]:
        """
        Generate strengths, weaknesses, and suggestions

        Returns:
            Tuple of (strengths, weaknesses, suggestions)
        """
        strengths = []
        weaknesses = []
        suggestions = []

        # Analyze strengths
        if quality_counts[MoveQuality.BRILLIANT] > 0:
            strengths.append(f"Made {quality_counts[MoveQuality.BRILLIANT]} brilliant moves showing strong tactical awareness")

        if playstyle["aggression"] > 7:
            strengths.append("Strong aggressive playstyle with constant pressure")
        elif playstyle["defense"] > 7:
            strengths.append("Excellent defensive play and counterpush timing")

        # Analyze weaknesses
        if quality_counts[MoveQuality.BLUNDER] > 2:
            weaknesses.append(f"Made {quality_counts[MoveQuality.BLUNDER]} blunders - review positioning and timing")

        if quality_counts[MoveQuality.MISTAKE] > 3:
            weaknesses.append("Several mistakes in card placement - work on optimal positioning")

        if playstyle["efficiency"] < 3:
            weaknesses.append("Low elixir efficiency - consider faster cycle strategies")

        # Generate suggestions
        if quality_counts[MoveQuality.BLUNDER] > 0:
            suggestions.append("Review blundered moves carefully - these cost you the most advantage")

        if playstyle["aggression"] < 3 and playstyle["defense"] < 3:
            suggestions.append("Play more decisively - commit to either offense or defense")

        if playstyle["efficiency"] > 8:
            suggestions.append("Good cycle play, but mix in heavier pushes for surprise factor")

        suggestions.append("Watch replays of brilliant moves to reinforce good patterns")

        return strengths, weaknesses, suggestions
