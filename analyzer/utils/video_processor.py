"""
Video Processing Module for Clash Royale Analyzer
Extracts frames from MP4 videos and prepares them for analysis
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Generator, Tuple, List, Optional
import json
from datetime import timedelta


class VideoProcessor:
    """Processes Clash Royale gameplay videos for analysis"""

    def __init__(self, video_path: str, fps: int = 2):
        """
        Initialize video processor

        Args:
            video_path: Path to the MP4 video file
            fps: Frames per second to extract (default: 2 for analysis efficiency)
        """
        self.video_path = Path(video_path)
        self.fps = fps
        self.cap = None
        self.total_frames = 0
        self.video_fps = 0
        self.duration = 0
        self.width = 0
        self.height = 0

        self._initialize_video()

    def _initialize_video(self):
        """Initialize video capture and extract metadata"""
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {self.video_path}")

        self.cap = cv2.VideoCapture(str(self.video_path))

        if not self.cap.isOpened():
            raise ValueError(f"Could not open video file: {self.video_path}")

        # Extract video metadata
        self.video_fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.duration = self.total_frames / self.video_fps if self.video_fps > 0 else 0

        print(f"Video initialized: {self.width}x{self.height}, "
              f"{self.video_fps:.2f} FPS, {self.duration:.2f}s duration")

    def get_metadata(self) -> dict:
        """Get video metadata"""
        return {
            "width": self.width,
            "height": self.height,
            "fps": self.video_fps,
            "total_frames": self.total_frames,
            "duration": self.duration,
            "extract_fps": self.fps
        }

    def extract_frames(self,
                      output_dir: Optional[str] = None,
                      save_frames: bool = False) -> Generator[Tuple[np.ndarray, float, int], None, None]:
        """
        Extract frames from video at specified FPS

        Args:
            output_dir: Directory to save frames (if save_frames=True)
            save_frames: Whether to save frames to disk

        Yields:
            Tuple of (frame, timestamp, frame_number)
        """
        if output_dir and save_frames:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

        # Calculate frame interval
        frame_interval = int(self.video_fps / self.fps)

        frame_count = 0
        extracted_count = 0

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to beginning

        while True:
            ret, frame = self.cap.read()

            if not ret:
                break

            # Extract frame at specified interval
            if frame_count % frame_interval == 0:
                timestamp = frame_count / self.video_fps

                if save_frames and output_dir:
                    frame_path = output_path / f"frame_{extracted_count:06d}.jpg"
                    cv2.imwrite(str(frame_path), frame)

                yield frame, timestamp, extracted_count
                extracted_count += 1

            frame_count += 1

        print(f"Extracted {extracted_count} frames from {frame_count} total frames")

    def extract_game_area(self, frame: np.ndarray) -> np.ndarray:
        """
        Extract the game play area from a frame
        This should match the coordinates from Actions.py

        Args:
            frame: Full video frame

        Returns:
            Cropped game area
        """
        # Default coordinates for Windows (adjust based on your setup)
        # These match the coordinates in Actions.py
        top_left_x = 1376
        top_left_y = 120
        bottom_right_x = 1838
        bottom_right_y = 769

        # Ensure coordinates are within frame bounds
        h, w = frame.shape[:2]
        top_left_x = min(top_left_x, w)
        top_left_y = min(top_left_y, h)
        bottom_right_x = min(bottom_right_x, w)
        bottom_right_y = min(bottom_right_y, h)

        game_area = frame[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
        return game_area

    def extract_card_area(self, frame: np.ndarray) -> np.ndarray:
        """
        Extract the card bar area from a frame

        Args:
            frame: Full video frame

        Returns:
            Cropped card bar area
        """
        # Card bar coordinates (Windows)
        card_bar_x = 1450
        card_bar_y = 847
        card_bar_width = 1862 - 1450
        card_bar_height = 971 - 847

        h, w = frame.shape[:2]
        y1 = min(card_bar_y, h)
        y2 = min(card_bar_y + card_bar_height, h)
        x1 = min(card_bar_x, w)
        x2 = min(card_bar_x + card_bar_width, w)

        card_area = frame[y1:y2, x1:x2]
        return card_area

    def split_card_bar(self, card_area: np.ndarray) -> List[np.ndarray]:
        """
        Split card bar into individual card images

        Args:
            card_area: Card bar image

        Returns:
            List of 4 individual card images
        """
        width = card_area.shape[1]
        card_width = width // 4

        cards = []
        for i in range(4):
            left = i * card_width
            right = (i + 1) * card_width
            card = card_area[:, left:right]
            cards.append(card)

        return cards

    def process_full_video(self, output_dir: str) -> dict:
        """
        Process entire video and save extracted data

        Args:
            output_dir: Directory to save processed data

        Returns:
            Processing summary
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        frames_dir = output_path / "frames"
        game_area_dir = output_path / "game_areas"
        card_area_dir = output_path / "card_areas"

        frames_dir.mkdir(exist_ok=True)
        game_area_dir.mkdir(exist_ok=True)
        card_area_dir.mkdir(exist_ok=True)

        metadata = {
            "video_path": str(self.video_path),
            "metadata": self.get_metadata(),
            "frames": []
        }

        for frame, timestamp, frame_num in self.extract_frames():
            # Save full frame
            frame_path = frames_dir / f"frame_{frame_num:06d}.jpg"
            cv2.imwrite(str(frame_path), frame)

            # Extract and save game area
            game_area = self.extract_game_area(frame)
            game_path = game_area_dir / f"game_{frame_num:06d}.jpg"
            cv2.imwrite(str(game_path), game_area)

            # Extract and save card area
            card_area = self.extract_card_area(frame)
            card_path = card_area_dir / f"cards_{frame_num:06d}.jpg"
            cv2.imwrite(str(card_path), card_area)

            metadata["frames"].append({
                "frame_number": frame_num,
                "timestamp": timestamp,
                "frame_path": str(frame_path),
                "game_area_path": str(game_path),
                "card_area_path": str(card_path)
            })

        # Save metadata
        metadata_path = output_path / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        return metadata

    def get_frame_at_timestamp(self, timestamp: float) -> Optional[np.ndarray]:
        """
        Get frame at specific timestamp

        Args:
            timestamp: Time in seconds

        Returns:
            Frame at that timestamp, or None if invalid
        """
        if timestamp < 0 or timestamp > self.duration:
            return None

        frame_number = int(timestamp * self.video_fps)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()

        return frame if ret else None

    def close(self):
        """Release video capture resources"""
        if self.cap:
            self.cap.release()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def format_timestamp(seconds: float) -> str:
    """Format seconds as MM:SS.mmm"""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    milliseconds = int((seconds - total_seconds) * 1000)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: python video_processor.py <video_path> [output_dir]")
        sys.exit(1)

    video_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"

    with VideoProcessor(video_path, fps=2) as processor:
        print(f"Processing video: {video_path}")
        print(f"Metadata: {processor.get_metadata()}")

        result = processor.process_full_video(output_dir)
        print(f"Processed {len(result['frames'])} frames")
        print(f"Output saved to: {output_dir}")
