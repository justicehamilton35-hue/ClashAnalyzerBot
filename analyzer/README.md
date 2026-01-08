# Clash Royale Analyzer - Stockfish for Clash Royale

A comprehensive gameplay analyzer that watches Clash Royale videos, detects every card played, evaluates positions, identifies blunders and brilliant moves, and provides in-depth analysis similar to how Stockfish analyzes chess games.

## Features

### Core Analysis
- **Video Processing**: Upload MP4 gameplay videos for analysis
- **Card Detection**: Detect every card played by you and your opponent
- **Position Evaluation**: Advanced AI evaluates each game state
- **Move Classification**: Identifies brilliant moves, good moves, inaccuracies, mistakes, and blunders
- **Win Probability**: Real-time win percentage throughout the game timeline
- **Playstyle Analysis**: Determines optimal playstyles based on your deck and opponent

### Analysis Features
- **Optimal Placement Suggestions**: Shows best possible card placements
- **Blunder Detection**: Identifies poor placements with detailed explanations
- **Brilliant Move Recognition**: Highlights exceptional plays
- **Timeline Replay**: Replay games with full analysis overlay
- **Side-by-Side Comparison**: Compare your moves vs optimal moves

### Interface
- **Chess.com-style Layout**: Familiar, intuitive interface
- **Interactive Timeline**: Click through game states
- **Analysis Dashboard**: Comprehensive statistics and insights
- **Move-by-Move Breakdown**: Detailed analysis for each play

## Architecture

```
analyzer/
├── backend/              # FastAPI backend
│   ├── api/             # REST API endpoints
│   ├── database/        # Database models and connections
│   └── schemas/         # Pydantic schemas
├── frontend/            # React/Next.js frontend
│   ├── src/            # Source code
│   └── public/         # Static assets
├── engine/              # Analysis engine
│   ├── evaluation/     # Position evaluation
│   ├── analysis/       # Move analysis
│   └── prediction/     # Win probability prediction
├── models/              # Trained models
│   ├── trained_models/ # Saved model weights
│   └── configs/        # Model configurations
└── data/               # Data storage
    ├── videos/         # Uploaded videos
    ├── replays/        # Game replay data
    └── analysis_results/ # Analysis outputs
```

## Technology Stack

### Backend
- **FastAPI**: High-performance API framework
- **PostgreSQL**: Database for storing games and analysis
- **Celery**: Asynchronous video processing
- **Redis**: Caching and task queue

### Machine Learning
- **PyTorch**: Deep learning framework
- **OpenCV**: Video processing
- **Roboflow**: Computer vision for card detection
- **MCTS**: Monte Carlo Tree Search for position evaluation

### Frontend
- **Next.js**: React framework
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Styling
- **Recharts**: Data visualization
- **Video.js**: Video playback

## Getting Started

See individual component READMEs for setup instructions:
- [Backend Setup](backend/README.md)
- [Frontend Setup](frontend/README.md)
- [Engine Documentation](engine/README.md)

## How It Works

1. **Upload Video**: Upload MP4 of your Clash Royale gameplay
2. **Frame Extraction**: Video is processed frame-by-frame
3. **State Detection**: Each frame is analyzed to detect cards, elixir, troops, towers
4. **Position Evaluation**: AI evaluates the strength of each position
5. **Move Analysis**: Each card play is analyzed and classified
6. **Report Generation**: Comprehensive analysis report is generated
7. **Interactive Replay**: Review the game with analysis overlay

## Analysis Metrics

### Move Classification
- **Brilliant (!!!)**: Exceptional move, best or only winning move
- **Great (!!)**: Very strong move, significantly better than alternatives
- **Good (!)**: Solid move, above average
- **Book**: Standard, expected move
- **Inaccuracy (?!)**: Suboptimal, loses slight advantage
- **Mistake (?)**: Clear error, loses significant advantage
- **Blunder (??)**: Severe mistake, game-losing move

### Evaluation Metrics
- **Position Score**: -10 (losing) to +10 (winning)
- **Win Probability**: 0% to 100%
- **Elixir Efficiency**: Value generated per elixir spent
- **Tempo Rating**: Speed and pressure of your plays
- **Defense Rating**: Effectiveness of defensive plays

### Playstyle Categories
- **Beatdown**: Heavy, expensive pushes
- **Cycle**: Fast, cheap card cycling
- **Control**: Board control and defense
- **Siege**: Tower damage from your side
- **Bridge Spam**: Aggressive, constant pressure
- **Bait**: Spell baiting strategy

## License

MIT License - See LICENSE file for details
