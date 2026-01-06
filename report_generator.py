"""
ClashFish Report Generator
Creates formatted analysis reports (text, JSON, HTML)
"""
import json
from typing import Dict, List
from datetime import datetime
from clashfish_engine import GameAnalysis, MoveQuality
from mistake_detector import Mistake, MistakeDetector


class ReportGenerator:
    """Generates analysis reports in various formats"""

    def __init__(self):
        pass

    def generate_text_report(self, analysis: GameAnalysis, mistakes: List[Mistake]) -> str:
        """Generate plain text report"""
        report = []
        report.append("=" * 60)
        report.append("CLASHFISH ANALYSIS REPORT")
        report.append("=" * 60)
        report.append("")

        # Game summary
        report.append("GAME SUMMARY")
        report.append("-" * 60)
        if analysis.game_states:
            duration = analysis.game_states[-1].timestamp
            report.append(f"Duration: {int(duration // 60)}:{int(duration % 60):02d}")

        report.append(f"Total Moves: {analysis.total_moves}")
        report.append(f"Overall Accuracy: {analysis.accuracy_score:.1f}% ({self._get_rating_label(analysis.accuracy_score)})")
        report.append("")

        # Move quality breakdown
        report.append("MOVE QUALITY BREAKDOWN")
        report.append("-" * 60)
        report.append(f"  Brilliant (!!): {analysis.brilliant_moves:3d}")
        report.append(f"  Good (!):       {analysis.good_moves:3d}")
        report.append(f"  Inaccuracies (?!): {analysis.inaccuracies:3d}")
        report.append(f"  Mistakes (?):   {analysis.mistakes:3d}")
        report.append(f"  Blunders (??):  {analysis.blunders:3d}")
        report.append("")

        # Performance ratings
        report.append("PERFORMANCE RATINGS")
        report.append("-" * 60)
        report.append(f"  Elixir Management: {analysis.elixir_management_rating:.1f}/10 {self._get_bar(analysis.elixir_management_rating)}")
        report.append(f"  Card Placement:    {analysis.card_placement_rating:.1f}/10 {self._get_bar(analysis.card_placement_rating)}")
        report.append(f"  Defensive Play:    {analysis.defensive_rating:.1f}/10 {self._get_bar(analysis.defensive_rating)}")
        report.append(f"  Offensive Play:    {analysis.offensive_rating:.1f}/10 {self._get_bar(analysis.offensive_rating)}")
        report.append(f"  Overall:           {analysis.overall_rating:.1f}/10 {self._get_bar(analysis.overall_rating)}")
        report.append("")

        # Top blunders
        if analysis.top_blunders:
            report.append("TOP BLUNDERS")
            report.append("-" * 60)
            for i, blunder in enumerate(analysis.top_blunders[:5], 1):
                action = blunder.player_action
                report.append(
                    f"{i}. [{self._format_time(action.timestamp)}] "
                    f"{action.card_played} at ({action.position.x:.2f}, {action.position.y:.2f}) "
                    f"- Loss: {blunder.evaluation_loss:.1f}%"
                )
                if blunder.top_alternatives:
                    best_card, best_pos, _ = blunder.top_alternatives[0]
                    report.append(f"   → Should have played: {best_card} at ({best_pos.x:.2f}, {best_pos.y:.2f})")
            report.append("")

        # Best moves
        if analysis.best_moves:
            report.append("BEST MOVES")
            report.append("-" * 60)
            for i, good_move in enumerate(analysis.best_moves[:5], 1):
                action = good_move.player_action
                report.append(
                    f"{i}. [{self._format_time(action.timestamp)}] "
                    f"{action.card_played} at ({action.position.x:.2f}, {action.position.y:.2f}) "
                    f"{good_move.quality.value}"
                )
            report.append("")

        # Mistake summary
        if mistakes:
            report.append("MISTAKES SUMMARY")
            report.append("-" * 60)

            # Group by severity
            critical = [m for m in mistakes if m.severity == "critical"]
            moderate = [m for m in mistakes if m.severity == "moderate"]
            minor = [m for m in mistakes if m.severity == "minor"]

            if critical:
                report.append(f"🔴 {len(critical)} Critical Mistakes:")
                for mistake in critical[:3]:
                    report.append(f"  [{self._format_time(mistake.timestamp)}] {mistake.description}")

            if moderate:
                report.append(f"🟡 {len(moderate)} Moderate Mistakes:")
                for mistake in moderate[:3]:
                    report.append(f"  [{self._format_time(mistake.timestamp)}] {mistake.description}")

            if minor:
                report.append(f"🔵 {len(minor)} Minor Mistakes")

            report.append("")

        # Improvement suggestions
        detector = MistakeDetector()
        improvements = detector.get_improvement_summary(mistakes)

        if improvements:
            report.append("IMPROVEMENT TIPS")
            report.append("-" * 60)
            for area, suggestion in improvements.items():
                report.append(f"📚 {area}:")
                report.append(f"   {suggestion}")
                report.append("")

        report.append("=" * 60)
        report.append(f"Report generated by ClashFish v1.0 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("=" * 60)

        return "\n".join(report)

    def generate_json_report(self, analysis: GameAnalysis, mistakes: List[Mistake]) -> str:
        """Generate JSON report for API consumption"""
        # Build move-by-move timeline
        moves = []
        for i, (action, evaluation) in enumerate(zip(analysis.player_actions, analysis.move_evaluations)):
            move_data = {
                "move_number": i + 1,
                "timestamp": action.timestamp,
                "card_played": action.card_played,
                "position": {"x": action.position.x, "y": action.position.y},
                "elixir_cost": action.elixir_cost,
                "q_value": float(evaluation.player_q_value),
                "best_q_value": float(evaluation.best_q_value),
                "evaluation_loss": float(evaluation.evaluation_loss),
                "quality": evaluation.quality.name,
                "quality_symbol": evaluation.quality.value,
                "alternatives": [
                    {
                        "card": card,
                        "position": {"x": pos.x, "y": pos.y},
                        "q_value": float(q_val)
                    }
                    for card, pos, q_val in evaluation.top_alternatives[:3]
                ]
            }
            moves.append(move_data)

        # Build mistakes list
        mistakes_data = [
            {
                "timestamp": m.timestamp,
                "type": m.mistake_type,
                "description": m.description,
                "severity": m.severity,
                "suggestion": m.suggestion
            }
            for m in mistakes
        ]

        # Build full report
        report = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_moves": analysis.total_moves,
                "accuracy_score": round(analysis.accuracy_score, 2),
                "move_quality": {
                    "brilliant": analysis.brilliant_moves,
                    "good": analysis.good_moves,
                    "inaccuracies": analysis.inaccuracies,
                    "mistakes": analysis.mistakes,
                    "blunders": analysis.blunders
                },
                "ratings": {
                    "elixir_management": round(analysis.elixir_management_rating, 2),
                    "card_placement": round(analysis.card_placement_rating, 2),
                    "defensive_play": round(analysis.defensive_rating, 2),
                    "offensive_play": round(analysis.offensive_rating, 2),
                    "overall": round(analysis.overall_rating, 2)
                }
            },
            "moves": moves,
            "mistakes": mistakes_data,
            "improvements": MistakeDetector().get_improvement_summary(mistakes)
        }

        return json.dumps(report, indent=2)

    def generate_html_report(self, analysis: GameAnalysis, mistakes: List[Mistake]) -> str:
        """Generate HTML report for web viewing"""
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ClashFish Analysis Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .summary {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .accuracy {{
            font-size: 3em;
            font-weight: bold;
            color: {self._get_color_for_score(analysis.accuracy_score)};
            text-align: center;
        }}
        .moves-breakdown {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin: 20px 0;
        }}
        .move-stat {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .move-stat .number {{
            font-size: 2em;
            font-weight: bold;
        }}
        .rating-bar {{
            background: #e0e0e0;
            height: 30px;
            border-radius: 15px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .rating-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            padding-left: 10px;
            color: white;
            font-weight: bold;
        }}
        .mistake {{
            background: white;
            padding: 15px;
            border-left: 4px solid #ff6b6b;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .mistake.moderate {{
            border-left-color: #ffd93d;
        }}
        .mistake.minor {{
            border-left-color: #6bcf7f;
        }}
        .improvement {{
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }}
        .timestamp {{
            color: #666;
            font-family: monospace;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>⚔️ ClashFish Analysis</h1>
        <p>AI-Powered Clash Royale Coach</p>
    </div>

    <div class="summary">
        <h2>Overall Performance</h2>
        <div class="accuracy">{analysis.accuracy_score:.1f}%</div>
        <p style="text-align: center; color: #666;">{self._get_rating_label(analysis.accuracy_score)}</p>
    </div>

    <div class="summary">
        <h2>Move Quality Breakdown</h2>
        <div class="moves-breakdown">
            <div class="move-stat">
                <div class="number" style="color: #4caf50;">{analysis.brilliant_moves}</div>
                <div>Brilliant (!!)</div>
            </div>
            <div class="move-stat">
                <div class="number" style="color: #8bc34a;">{analysis.good_moves}</div>
                <div>Good (!)</div>
            </div>
            <div class="move-stat">
                <div class="number" style="color: #ffc107;">{analysis.inaccuracies}</div>
                <div>Inaccuracies (?!)</div>
            </div>
            <div class="move-stat">
                <div class="number" style="color: #ff9800;">{analysis.mistakes}</div>
                <div>Mistakes (?)</div>
            </div>
            <div class="move-stat">
                <div class="number" style="color: #f44336;">{analysis.blunders}</div>
                <div>Blunders (??)</div>
            </div>
        </div>
    </div>

    <div class="summary">
        <h2>Performance Ratings</h2>
        <div>
            <strong>Elixir Management</strong>
            <div class="rating-bar">
                <div class="rating-fill" style="width: {analysis.elixir_management_rating * 10}%">
                    {analysis.elixir_management_rating:.1f}/10
                </div>
            </div>
        </div>
        <div>
            <strong>Card Placement</strong>
            <div class="rating-bar">
                <div class="rating-fill" style="width: {analysis.card_placement_rating * 10}%">
                    {analysis.card_placement_rating:.1f}/10
                </div>
            </div>
        </div>
        <div>
            <strong>Defensive Play</strong>
            <div class="rating-bar">
                <div class="rating-fill" style="width: {analysis.defensive_rating * 10}%">
                    {analysis.defensive_rating:.1f}/10
                </div>
            </div>
        </div>
        <div>
            <strong>Offensive Play</strong>
            <div class="rating-bar">
                <div class="rating-fill" style="width: {analysis.offensive_rating * 10}%">
                    {analysis.offensive_rating:.1f}/10
                </div>
            </div>
        </div>
    </div>

    <div class="summary">
        <h2>Top Mistakes</h2>
        {"".join(f'''
        <div class="mistake {m.severity}">
            <strong class="timestamp">[{self._format_time(m.timestamp)}]</strong> {m.description}
            <br><small>💡 {m.suggestion}</small>
        </div>
        ''' for m in mistakes[:10])}
    </div>

    <div class="summary">
        <h2>Improvement Tips</h2>
        {"".join(f'''
        <div class="improvement">
            <strong>📚 {area}</strong>
            <p>{suggestion}</p>
        </div>
        ''' for area, suggestion in MistakeDetector().get_improvement_summary(mistakes).items())}
    </div>

    <footer style="text-align: center; color: #999; margin-top: 40px;">
        <p>Generated by ClashFish v1.0 - {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </footer>
</body>
</html>
"""
        return html

    def _format_time(self, seconds: float) -> str:
        """Format timestamp as MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"

    def _get_bar(self, rating: float, width: int = 10) -> str:
        """Generate ASCII progress bar"""
        filled = int(rating)
        return "█" * filled + "░" * (width - filled)

    def _get_rating_label(self, score: float) -> str:
        """Get rating label for accuracy score"""
        if score >= 90:
            return "EXCELLENT"
        elif score >= 80:
            return "VERY GOOD"
        elif score >= 70:
            return "GOOD"
        elif score >= 60:
            return "FAIR"
        elif score >= 50:
            return "NEEDS IMPROVEMENT"
        else:
            return "WEAK"

    def _get_color_for_score(self, score: float) -> str:
        """Get color for accuracy score"""
        if score >= 80:
            return "#4caf50"  # Green
        elif score >= 60:
            return "#ffc107"  # Yellow
        else:
            return "#f44336"  # Red


if __name__ == "__main__":
    print("Report Generator Module")
    print("Use with clashfish_engine.py to generate reports")
