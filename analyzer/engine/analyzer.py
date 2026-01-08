"""
Main Clash Royale Analyzer
Orchestrates video processing, game state tracking, and move analysis
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict
import json
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analyzer.utils.video_processor import VideoProcessor
from analyzer.engine.game_state_tracker import GameStateTracker
from analyzer.engine.evaluation.position_evaluator import PositionEvaluator
from analyzer.engine.analysis.move_analyzer import MoveAnalyzer


class ClashRoyaleAnalyzer:
    """
    Main analyzer class that orchestrates the entire analysis pipeline
    Similar to how Stockfish analyzes chess games
    """

    def __init__(self, roboflow_api_key: Optional[str] = None,
                 troop_workspace: Optional[str] = None,
                 card_workspace: Optional[str] = None):
        """
        Initialize the analyzer

        Args:
            roboflow_api_key: Roboflow API key (loads from env if not provided)
            troop_workspace: Workspace for troop detection
            card_workspace: Workspace for card detection
        """
        # Load environment variables
        load_dotenv()

        self.api_key = roboflow_api_key or os.getenv('ROBOFLOW_API_KEY')
        self.troop_workspace = troop_workspace or os.getenv('WORKSPACE_TROOP_DETECTION')
        self.card_workspace = card_workspace or os.getenv('WORKSPACE_CARD_DETECTION')

        if not self.api_key:
            raise ValueError("ROBOFLOW_API_KEY not provided and not found in environment")
        if not self.troop_workspace:
            raise ValueError("WORKSPACE_TROOP_DETECTION not provided and not found in environment")
        if not self.card_workspace:
            raise ValueError("WORKSPACE_CARD_DETECTION not provided and not found in environment")

        # Initialize components
        self.position_evaluator = PositionEvaluator(use_neural_net=False)
        self.move_analyzer = MoveAnalyzer(self.position_evaluator)

        # Will be initialized per-analysis
        self.video_processor = None
        self.game_state_tracker = None

    def analyze_video(self, video_path: str,
                     output_dir: Optional[str] = None,
                     fps: int = 2,
                     save_frames: bool = False) -> Dict:
        """
        Analyze a Clash Royale gameplay video

        Args:
            video_path: Path to MP4 video file
            output_dir: Directory to save analysis results
            fps: Frames per second to extract
            save_frames: Whether to save extracted frames

        Returns:
            Dictionary with complete analysis results
        """
        print(f"\n{'='*60}")
        print(f"Clash Royale Analyzer - Analyzing Video")
        print(f"{'='*60}\n")

        # Create output directory
        if not output_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"analyzer/data/analysis_results/analysis_{timestamp}"

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Initialize video processor
        print("📹 Initializing video processor...")
        self.video_processor = VideoProcessor(video_path, fps=fps)
        metadata = self.video_processor.get_metadata()
        print(f"   Video: {metadata['width']}x{metadata['height']}, "
              f"{metadata['fps']:.1f} FPS, {metadata['duration']:.1f}s")

        # Initialize game state tracker
        print("🎮 Initializing game state tracker...")
        self.game_state_tracker = GameStateTracker(
            self.api_key,
            self.troop_workspace,
            self.card_workspace
        )

        # Process video frame by frame
        print(f"🔍 Processing video at {fps} FPS...")
        frame_count = 0

        for frame, timestamp, frame_num in self.video_processor.extract_frames(
                output_dir=output_path / "frames" if save_frames else None,
                save_frames=save_frames):

            # Extract game areas
            game_area = self.video_processor.extract_game_area(frame)
            card_area = self.video_processor.extract_card_area(frame)

            # Create game state
            game_state = self.game_state_tracker.create_game_state(
                frame, game_area, card_area, timestamp, frame_num
            )

            # Evaluate position
            evaluation = self.position_evaluator.evaluate_position(game_state)
            game_state.evaluation = evaluation.total_score
            game_state.win_probability = evaluation.win_probability

            frame_count += 1

            # Progress update
            if frame_count % 10 == 0:
                print(f"   Processed {frame_count} frames "
                      f"({timestamp:.1f}s / {metadata['duration']:.1f}s)")

        print(f"✅ Processed {frame_count} frames")

        # Analyze all moves
        print("\n📊 Analyzing moves...")
        game_states = self.game_state_tracker.get_game_timeline()
        card_plays = self.game_state_tracker.get_all_card_plays()

        print(f"   Detected {len(card_plays)} card plays")

        analysis_summary = self.move_analyzer.analyze_full_game(game_states, card_plays)

        # Generate detailed report
        print("\n📝 Generating analysis report...")
        report = self._generate_report(
            video_path, metadata, game_states, card_plays, analysis_summary
        )

        # Save results
        self._save_analysis(output_path, report, game_states, card_plays, analysis_summary)

        print(f"\n✅ Analysis complete!")
        print(f"📂 Results saved to: {output_path}")

        self.video_processor.close()

        return report

    def _generate_report(self, video_path, metadata, game_states, card_plays, summary) -> Dict:
        """Generate comprehensive analysis report"""

        report = {
            "video_path": str(video_path),
            "analysis_timestamp": datetime.now().isoformat(),
            "video_metadata": metadata,

            "game_summary": {
                "duration": metadata['duration'],
                "total_frames_analyzed": len(game_states),
                "total_moves": len(card_plays),
                "your_moves": len([p for p in card_plays if p.player.value == "you"]),
                "opponent_moves": len([p for p in card_plays if p.player.value == "opponent"])
            },

            "performance": {
                "accuracy_score": summary.accuracy_score,
                "average_evaluation": summary.average_eval,
                "average_win_probability": summary.average_win_prob,

                "move_quality": {
                    "brilliant": summary.brilliant_moves,
                    "great": summary.great_moves,
                    "good": summary.good_moves,
                    "book": summary.book_moves,
                    "inaccuracies": summary.inaccuracies,
                    "mistakes": summary.mistakes,
                    "blunders": summary.blunders
                }
            },

            "playstyle": {
                "type": summary.playstyle,
                "aggression_rating": summary.aggression_rating,
                "defense_rating": summary.defense_rating,
                "elixir_efficiency": summary.elixir_efficiency
            },

            "insights": {
                "strengths": summary.strengths or [],
                "weaknesses": summary.weaknesses or [],
                "suggestions": summary.suggestions or []
            },

            "key_moments": [
                {
                    "timestamp": m.timestamp,
                    "card": m.card_name,
                    "quality": m.move_quality.value,
                    "symbol": m.move_symbol,
                    "explanation": m.explanation,
                    "eval_change": m.eval_change,
                    "win_prob_before": m.win_prob_before,
                    "win_prob_after": m.win_prob_after
                }
                for m in (summary.key_moments or [])
            ],

            "timeline": [
                {
                    "timestamp": state.timestamp,
                    "frame": state.frame_number,
                    "evaluation": state.evaluation,
                    "win_probability": state.win_probability,
                    "your_elixir": state.your_elixir,
                    "opponent_elixir": state.opponent_elixir,
                    "your_troops": len(state.your_troops),
                    "opponent_troops": len(state.opponent_troops)
                }
                for state in game_states
            ],

            "moves": [
                {
                    "timestamp": m.timestamp,
                    "card": m.card_name,
                    "player": m.player,
                    "position": m.position,
                    "quality": m.move_quality.value,
                    "symbol": m.move_symbol,
                    "explanation": m.explanation,
                    "evaluation_before": m.evaluation_before,
                    "evaluation_after": m.evaluation_after,
                    "eval_change": m.eval_change,
                    "win_prob_before": m.win_prob_before,
                    "win_prob_after": m.win_prob_after,
                    "themes": m.tactical_themes or []
                }
                for m in (summary.all_moves or [])
            ]
        }

        return report

    def _save_analysis(self, output_path, report, game_states, card_plays, summary):
        """Save analysis results to files"""

        # Save main report
        report_path = output_path / "analysis_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"   ✅ Saved report: {report_path}")

        # Save timeline
        timeline_path = output_path / "game_timeline.json"
        self.game_state_tracker.export_timeline(str(timeline_path))
        print(f"   ✅ Saved timeline: {timeline_path}")

        # Save summary stats
        summary_path = output_path / "summary.txt"
        with open(summary_path, 'w') as f:
            f.write("="*60 + "\n")
            f.write("CLASH ROYALE GAME ANALYSIS SUMMARY\n")
            f.write("="*60 + "\n\n")

            f.write(f"Accuracy Score: {summary.accuracy_score:.1f}%\n")
            f.write(f"Average Evaluation: {summary.average_eval:+.2f}\n")
            f.write(f"Average Win Probability: {summary.average_win_prob*100:.1f}%\n\n")

            f.write("Move Quality Breakdown:\n")
            f.write(f"  Brilliant (!!!): {summary.brilliant_moves}\n")
            f.write(f"  Great (!!):      {summary.great_moves}\n")
            f.write(f"  Good (!):        {summary.good_moves}\n")
            f.write(f"  Book:            {summary.book_moves}\n")
            f.write(f"  Inaccuracy (?!): {summary.inaccuracies}\n")
            f.write(f"  Mistake (?):     {summary.mistakes}\n")
            f.write(f"  Blunder (??):    {summary.blunders}\n\n")

            f.write(f"Playstyle: {summary.playstyle.upper()}\n")
            f.write(f"  Aggression: {summary.aggression_rating:.1f}/10\n")
            f.write(f"  Defense: {summary.defense_rating:.1f}/10\n")
            f.write(f"  Efficiency: {summary.elixir_efficiency:.1f}/10\n\n")

            if summary.strengths:
                f.write("Strengths:\n")
                for s in summary.strengths:
                    f.write(f"  ✅ {s}\n")
                f.write("\n")

            if summary.weaknesses:
                f.write("Weaknesses:\n")
                for w in summary.weaknesses:
                    f.write(f"  ⚠️  {w}\n")
                f.write("\n")

            if summary.suggestions:
                f.write("Suggestions:\n")
                for s in summary.suggestions:
                    f.write(f"  💡 {s}\n")

        print(f"   ✅ Saved summary: {summary_path}")

    def quick_analyze(self, video_path: str) -> Dict:
        """
        Quick analysis with default settings

        Args:
            video_path: Path to video file

        Returns:
            Analysis report dictionary
        """
        return self.analyze_video(video_path, fps=2, save_frames=False)


def main():
    """Command-line interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Clash Royale Analyzer - Stockfish for Clash Royale"
    )
    parser.add_argument("video", help="Path to Clash Royale gameplay video (MP4)")
    parser.add_argument("-o", "--output", help="Output directory for analysis results")
    parser.add_argument("--fps", type=int, default=2, help="Frames per second to analyze (default: 2)")
    parser.add_argument("--save-frames", action="store_true", help="Save extracted frames")

    args = parser.parse_args()

    try:
        analyzer = ClashRoyaleAnalyzer()
        result = analyzer.analyze_video(
            args.video,
            output_dir=args.output,
            fps=args.fps,
            save_frames=args.save_frames
        )

        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60)
        print(f"Accuracy: {result['performance']['accuracy_score']:.1f}%")
        print(f"Playstyle: {result['playstyle']['type']}")
        print(f"Brilliant moves: {result['performance']['move_quality']['brilliant']}")
        print(f"Blunders: {result['performance']['move_quality']['blunders']}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
