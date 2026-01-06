#!/usr/bin/env python3
"""
ClashFish CLI - AI Clash Royale Coach
Command-line interface for analyzing Clash Royale games
"""
import argparse
import sys
from pathlib import Path
from video_processor import VideoProcessor
from clashfish_engine import ClashFishEngine
from mistake_detector import MistakeDetector
from report_generator import ReportGenerator


def analyze_game(video_path: str, model_path: str, output_path: str = None,
                format: str = "text", fps: float = 2.0):
    """
    Analyze a Clash Royale game recording

    Args:
        video_path: Path to video file
        model_path: Path to trained DQN model
        output_path: Optional output file path
        format: Report format (text, json, html)
        fps: Frames per second to extract
    """
    print("=" * 60)
    print("CLASHFISH - AI CLASH ROYALE COACH")
    print("=" * 60)
    print()

    # Validate inputs
    video_file = Path(video_path)
    if not video_file.exists():
        print(f"❌ Error: Video file not found: {video_path}")
        sys.exit(1)

    model_file = Path(model_path)
    if not model_file.exists():
        print(f"❌ Error: Model file not found: {model_path}")
        sys.exit(1)

    print(f"📹 Video: {video_file.name}")
    print(f"🤖 Model: {model_file.name}")
    print(f"⚙️  FPS: {fps}")
    print()

    # Step 1: Process video
    print("📊 Step 1/4: Processing video...")
    processor = VideoProcessor(fps=fps)
    game_states, actions = processor.process_video(video_path)

    if not actions:
        print("❌ Error: No player actions detected in video")
        sys.exit(1)

    print(f"✅ Detected {len(game_states)} game states and {len(actions)} actions")
    print()

    # Step 2: Analyze with engine
    print("🧠 Step 2/4: Analyzing with AI engine...")
    engine = ClashFishEngine(model_path)
    analysis = engine.analyze_game(game_states, actions)

    print(f"✅ Accuracy: {analysis.accuracy_score:.1f}%")
    print(f"   Blunders: {analysis.blunders}, Mistakes: {analysis.mistakes}")
    print()

    # Step 3: Detect mistakes
    print("🔍 Step 3/4: Detecting mistakes...")
    detector = MistakeDetector()
    mistakes = detector.detect_all_mistakes(game_states, actions, analysis.move_evaluations)

    critical = len([m for m in mistakes if m.severity == "critical"])
    moderate = len([m for m in mistakes if m.severity == "moderate"])
    minor = len([m for m in mistakes if m.severity == "minor"])

    print(f"✅ Found {len(mistakes)} mistakes")
    print(f"   Critical: {critical}, Moderate: {moderate}, Minor: {minor}")
    print()

    # Step 4: Generate report
    print("📝 Step 4/4: Generating report...")
    generator = ReportGenerator()

    if format == "text":
        report = generator.generate_text_report(analysis, mistakes)
    elif format == "json":
        report = generator.generate_json_report(analysis, mistakes)
    elif format == "html":
        report = generator.generate_html_report(analysis, mistakes)
    else:
        print(f"❌ Error: Unknown format '{format}'")
        sys.exit(1)

    # Output report
    if output_path:
        output_file = Path(output_path)
        with open(output_file, "w") as f:
            f.write(report)
        print(f"✅ Report saved to: {output_file}")
    else:
        print("✅ Report generated")
        print()
        print(report)

    print()
    print("=" * 60)
    print("Analysis complete! 🎉")
    print("=" * 60)


def get_latest_model():
    """Find the latest trained model"""
    models_dir = Path("models")
    if not models_dir.exists():
        return None

    model_files = list(models_dir.glob("model_*.pth"))
    if not model_files:
        return None

    latest = max(model_files, key=lambda p: p.stat().st_mtime)
    return str(latest)


def batch_analyze(video_dir: str, model_path: str, output_dir: str = None,
                 format: str = "text", fps: float = 2.0):
    """
    Analyze multiple videos in a directory

    Args:
        video_dir: Directory containing video files
        model_path: Path to trained DQN model
        output_dir: Optional output directory for reports
        format: Report format
        fps: Frames per second
    """
    video_path = Path(video_dir)
    if not video_path.exists():
        print(f"❌ Error: Directory not found: {video_dir}")
        sys.exit(1)

    # Find all video files
    video_files = []
    for ext in ["*.mp4", "*.mov", "*.avi", "*.mkv"]:
        video_files.extend(video_path.glob(ext))

    if not video_files:
        print(f"❌ Error: No video files found in {video_dir}")
        sys.exit(1)

    print(f"Found {len(video_files)} videos to analyze")
    print()

    # Create output directory
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)
    else:
        output_path = None

    # Analyze each video
    for i, video_file in enumerate(video_files, 1):
        print(f"\n{'='*60}")
        print(f"Analyzing {i}/{len(video_files)}: {video_file.name}")
        print(f"{'='*60}\n")

        # Determine output path
        if output_path:
            ext = {"text": ".txt", "json": ".json", "html": ".html"}[format]
            out_file = output_path / f"{video_file.stem}_report{ext}"
        else:
            out_file = None

        try:
            analyze_game(str(video_file), model_path, str(out_file) if out_file else None,
                        format, fps)
        except Exception as e:
            print(f"❌ Error analyzing {video_file.name}: {e}")
            continue

    print(f"\n✅ Batch analysis complete! Analyzed {len(video_files)} videos")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="ClashFish - AI Clash Royale Coach",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a single video
  python clashfish.py analyze my_game.mp4

  # Specify model and output
  python clashfish.py analyze game.mp4 --model models/best.pth --output report.html --format html

  # Batch analyze multiple videos
  python clashfish.py batch ./replays/ --output ./reports/

  # Use custom FPS
  python clashfish.py analyze game.mp4 --fps 1.0
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a single video")
    analyze_parser.add_argument("video", help="Path to video file")
    analyze_parser.add_argument("--model", "-m", help="Path to DQN model (default: latest)")
    analyze_parser.add_argument("--output", "-o", help="Output file path")
    analyze_parser.add_argument("--format", "-f", choices=["text", "json", "html"],
                               default="text", help="Report format (default: text)")
    analyze_parser.add_argument("--fps", type=float, default=2.0,
                               help="Frames per second to extract (default: 2.0)")

    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Analyze multiple videos")
    batch_parser.add_argument("directory", help="Directory containing videos")
    batch_parser.add_argument("--model", "-m", help="Path to DQN model (default: latest)")
    batch_parser.add_argument("--output", "-o", help="Output directory for reports")
    batch_parser.add_argument("--format", "-f", choices=["text", "json", "html"],
                             default="text", help="Report format (default: text)")
    batch_parser.add_argument("--fps", type=float, default=2.0,
                             help="Frames per second (default: 2.0)")

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Get model path
    if hasattr(args, 'model') and args.model:
        model_path = args.model
    else:
        model_path = get_latest_model()
        if not model_path:
            print("❌ Error: No trained model found in models/ directory")
            print("   Please specify a model with --model or train a model first")
            sys.exit(1)

    # Execute command
    try:
        if args.command == "analyze":
            analyze_game(args.video, model_path, args.output, args.format, args.fps)
        elif args.command == "batch":
            batch_analyze(args.directory, model_path, args.output, args.format, args.fps)
    except KeyboardInterrupt:
        print("\n\n❌ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
