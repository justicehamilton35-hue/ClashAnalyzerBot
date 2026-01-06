"""
ClashFish Video Annotator
Creates annotated video replays with mistake analysis overlaid
"""
import cv2
import numpy as np
from typing import List, Tuple, Dict
from pathlib import Path
from dataclasses import dataclass

from video_processor import GameState, PlayerAction, Position
from clashfish_engine import GameAnalysis, MoveEvaluation, MoveQuality


class VideoAnnotator:
    """Annotates Clash Royale videos with AI analysis"""

    # Colors (BGR format for OpenCV)
    COLOR_BRILLIANT = (0, 255, 0)      # Green
    COLOR_GOOD = (0, 200, 100)         # Light green
    COLOR_OKAY = (0, 165, 255)         # Orange
    COLOR_INACCURACY = (0, 100, 255)   # Dark orange
    COLOR_MISTAKE = (0, 50, 200)       # Red-orange
    COLOR_BLUNDER = (0, 0, 255)        # Red
    COLOR_BEST_MOVE = (255, 0, 255)    # Magenta (AI suggestion)
    COLOR_TEXT_BG = (0, 0, 0)          # Black
    COLOR_TEXT = (255, 255, 255)       # White

    def __init__(self):
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.6
        self.font_thickness = 2

    def annotate_video(self,
                      input_video_path: str,
                      output_video_path: str,
                      analysis: GameAnalysis,
                      progress_callback=None) -> str:
        """
        Create annotated video with analysis overlaid

        Args:
            input_video_path: Original video file
            output_video_path: Where to save annotated video
            analysis: ClashFish analysis results
            progress_callback: Optional callback(progress_pct, message)

        Returns:
            Path to annotated video
        """
        print(f"🎬 Creating annotated replay: {output_video_path}")

        # Open input video
        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {input_video_path}")

        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"Video: {width}x{height} @ {fps}fps, {total_frames} frames")

        # Create output video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

        # Build frame -> evaluation mapping
        move_map = self._build_move_map(analysis.move_evaluations, fps)

        # Process each frame
        frame_num = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            timestamp = frame_num / fps

            # Annotate frame
            annotated = self._annotate_frame(
                frame, timestamp, frame_num, move_map, analysis, width, height
            )

            # Write annotated frame
            out.write(annotated)

            # Progress update
            if frame_num % 100 == 0:
                progress = int((frame_num / total_frames) * 100)
                if progress_callback:
                    progress_callback(progress, f"Annotating frame {frame_num}/{total_frames}")
                print(f"Annotated {frame_num}/{total_frames} frames ({progress}%)")

            frame_num += 1

        # Cleanup
        cap.release()
        out.release()

        print(f"✅ Annotated video saved: {output_video_path}")
        return output_video_path

    def _build_move_map(self, evaluations: List[MoveEvaluation], fps: int) -> Dict[int, MoveEvaluation]:
        """Map frame numbers to move evaluations"""
        move_map = {}
        for eval in evaluations:
            frame_num = int(eval.player_action.timestamp * fps)
            # Show annotation for 3 seconds after the move
            for f in range(frame_num, frame_num + fps * 3):
                move_map[f] = eval
        return move_map

    def _annotate_frame(self,
                       frame: np.ndarray,
                       timestamp: float,
                       frame_num: int,
                       move_map: Dict[int, MoveEvaluation],
                       analysis: GameAnalysis,
                       width: int,
                       height: int) -> np.ndarray:
        """Annotate a single frame"""
        annotated = frame.copy()

        # Draw overall stats (top-left corner)
        self._draw_stats_panel(annotated, analysis, width, height)

        # If there's a move at this frame, annotate it
        if frame_num in move_map:
            eval = move_map[frame_num]
            self._draw_move_annotation(annotated, eval, width, height, timestamp)

        return annotated

    def _draw_stats_panel(self, frame: np.ndarray, analysis: GameAnalysis, width: int, height: int):
        """Draw overall stats panel"""
        # Semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (300, 150), self.COLOR_TEXT_BG, -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # Stats text
        y_offset = 35
        cv2.putText(frame, "CLASHFISH ANALYSIS", (20, y_offset),
                   self.font, 0.7, self.COLOR_TEXT, 2)
        y_offset += 30
        cv2.putText(frame, f"Accuracy: {analysis.accuracy_score:.1f}%", (20, y_offset),
                   self.font, self.font_scale, self.COLOR_TEXT, self.font_thickness)
        y_offset += 25
        cv2.putText(frame, f"Rating: {analysis.overall_rating:.1f}/10", (20, y_offset),
                   self.font, self.font_scale, self.COLOR_TEXT, self.font_thickness)
        y_offset += 25
        cv2.putText(frame, f"Blunders: {analysis.blunders} | Mistakes: {analysis.mistakes}", (20, y_offset),
                   self.font, 0.5, self.COLOR_TEXT, 1)

    def _draw_move_annotation(self,
                             frame: np.ndarray,
                             eval: MoveEvaluation,
                             width: int,
                             height: int,
                             timestamp: float):
        """Draw annotation for a specific move"""
        action = eval.player_action

        # Convert normalized position to pixel coordinates
        player_x = int(action.position.x * width)
        player_y = int(action.position.y * height)

        # Choose color based on move quality
        color = self._get_quality_color(eval.quality)

        # Draw player's move
        cv2.circle(frame, (player_x, player_y), 30, color, 3)
        cv2.circle(frame, (player_x, player_y), 5, color, -1)

        # Add move label
        label = f"{action.card_played} {eval.quality.value}"
        self._draw_label(frame, label, player_x, player_y - 40, color)

        # For mistakes/blunders, show optimal position
        if eval.quality in [MoveQuality.MISTAKE, MoveQuality.BLUNDER, MoveQuality.INACCURACY]:
            if eval.top_alternatives:
                best_card, best_pos, best_q = eval.top_alternatives[0]

                # Draw AI's suggested position
                ai_x = int(best_pos.x * width)
                ai_y = int(best_pos.y * height)

                cv2.circle(frame, (ai_x, ai_y), 30, self.COLOR_BEST_MOVE, 3)
                cv2.circle(frame, (ai_x, ai_y), 5, self.COLOR_BEST_MOVE, -1)

                # AI suggestion label
                ai_label = f"AI: {best_card}"
                self._draw_label(frame, ai_label, ai_x, ai_y - 40, self.COLOR_BEST_MOVE)

                # Draw arrow from player move to AI suggestion
                cv2.arrowedLine(frame, (player_x, player_y), (ai_x, ai_y),
                              self.COLOR_BEST_MOVE, 2, tipLength=0.3)

                # Show evaluation loss
                loss_text = f"-{eval.evaluation_loss:.0f}% better"
                self._draw_label(frame, loss_text,
                               (player_x + ai_x) // 2,
                               (player_y + ai_y) // 2 - 10,
                               self.COLOR_BEST_MOVE)

        # Show move info panel at bottom
        time_since = timestamp - action.timestamp
        if 0 <= time_since <= 3:  # Show for 3 seconds
            self._draw_move_info_panel(frame, eval, width, height)

    def _draw_label(self, frame: np.ndarray, text: str, x: int, y: int, color: Tuple[int, int, int]):
        """Draw text label with background"""
        # Get text size
        (text_width, text_height), _ = cv2.getTextSize(text, self.font, self.font_scale, self.font_thickness)

        # Draw background rectangle
        cv2.rectangle(frame,
                     (x - 5, y - text_height - 5),
                     (x + text_width + 5, y + 5),
                     self.COLOR_TEXT_BG, -1)

        # Draw text
        cv2.putText(frame, text, (x, y), self.font, self.font_scale, color, self.font_thickness)

    def _draw_move_info_panel(self, frame: np.ndarray, eval: MoveEvaluation, width: int, height: int):
        """Draw detailed move info panel at bottom"""
        panel_height = 120
        y_start = height - panel_height

        # Semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, y_start), (width, height), self.COLOR_TEXT_BG, -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)

        # Move details
        action = eval.player_action
        y_offset = y_start + 25

        # Card played
        cv2.putText(frame, f"Played: {action.card_played} ({action.elixir_cost} elixir)",
                   (20, y_offset), self.font, 0.7, self.COLOR_TEXT, 2)
        y_offset += 30

        # Move quality
        quality_text = f"Quality: {eval.quality.name} {eval.quality.value}"
        color = self._get_quality_color(eval.quality)
        cv2.putText(frame, quality_text, (20, y_offset), self.font, 0.7, color, 2)
        y_offset += 30

        # Evaluation loss (if applicable)
        if eval.evaluation_loss > 0:
            loss_text = f"Evaluation Loss: {eval.evaluation_loss:.1f}%"
            cv2.putText(frame, loss_text, (20, y_offset), self.font, 0.6, self.COLOR_MISTAKE, 2)

        # AI suggestion (right side)
        if eval.top_alternatives and eval.quality != MoveQuality.BRILLIANT:
            best_card, best_pos, _ = eval.top_alternatives[0]
            suggestion = f"AI suggests: {best_card}"
            cv2.putText(frame, suggestion, (width - 350, y_start + 25),
                       self.font, 0.7, self.COLOR_BEST_MOVE, 2)

    def _get_quality_color(self, quality: MoveQuality) -> Tuple[int, int, int]:
        """Get color for move quality"""
        quality_colors = {
            MoveQuality.BRILLIANT: self.COLOR_BRILLIANT,
            MoveQuality.GOOD: self.COLOR_GOOD,
            MoveQuality.OKAY: self.COLOR_OKAY,
            MoveQuality.INACCURACY: self.COLOR_INACCURACY,
            MoveQuality.MISTAKE: self.COLOR_MISTAKE,
            MoveQuality.BLUNDER: self.COLOR_BLUNDER,
        }
        return quality_colors.get(quality, self.COLOR_TEXT)


if __name__ == "__main__":
    print("Video Annotator Module")
    print("Use with ClashFish analysis to create annotated replays")
