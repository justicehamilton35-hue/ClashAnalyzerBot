# ClashFish - AI Clash Royale Coach Design Document

## Overview
ClashFish transforms the existing DQN bot into an AI coaching system similar to Stockfish for chess. Instead of playing in real-time, it analyzes recorded games and provides detailed feedback.

## Architecture

### 1. Video Processing Module (`video_processor.py`)
**Purpose**: Extract game state from screen recordings

**Features**:
- Accept video uploads (MP4, MOV, AVI)
- Extract frames at configurable FPS (e.g., 1 frame per second)
- Use existing Roboflow models for:
  - Card detection (what cards in hand)
  - Troop detection (unit positions)
  - Elixir detection (current elixir level)
  - Tower HP detection (match progression)
- Output: Timeline of game states

**Input**: Screen recording file
**Output**: List of `GameState` objects with timestamps

### 2. Game State Reconstructor (`game_reconstructor.py`)
**Purpose**: Build coherent game timeline from detected frames

**Features**:
- Identify player actions (when/where cards were played)
- Track elixir spending and generation
- Detect key moments: tower destruction, game end
- Filter noise from detection errors
- Interpolate missing frames

**Data Structure**:
```python
@dataclass
class GameState:
    timestamp: float
    elixir: int
    cards_in_hand: List[str]
    allied_units: List[Position]
    enemy_units: List[Position]
    tower_hp: Dict[str, int]

@dataclass
class PlayerAction:
    timestamp: float
    card_played: str
    position: Tuple[float, float]
    elixir_cost: int
    game_state_before: GameState
```

### 3. Analysis Engine (`clashfish_engine.py`)
**Purpose**: Evaluate gameplay using DQN model (like Stockfish engine)

**Features**:
- Load trained DQN model
- For each player action:
  - Get Q-values for all possible actions
  - Find top 5 alternatives
  - Calculate "evaluation loss" (Q-value difference)
- Classify move quality:
  - **Brilliant (!!)**: Better than AI's best move
  - **Good (!)**: Within 5% of best Q-value
  - **Inaccuracy (?!)**: 5-15% worse than best
  - **Mistake (?)**: 15-30% worse than best
  - **Blunder (??)**: 30%+ worse than best

**Metrics**:
- Move accuracy: % of moves within top 3 AI choices
- Average evaluation loss per move
- Critical blunders: Moves that led to tower loss

### 4. Mistake Detection System (`mistake_detector.py`)
**Purpose**: Identify specific types of errors

**Categories**:
- **Elixir Management**:
  - Overcapping (staying at 10 elixir)
  - Poor elixir trades (spending 6 to counter 2)

- **Card Placement**:
  - Spell wastage (no targets in range)
  - Misplaced units (too far from action)
  - Poor defensive placement (wrong lane)

- **Timing**:
  - Missed counter opportunities
  - Overcommitment (entire elixir on one push)
  - Late reactions to threats

- **Strategic**:
  - No spell for enemy swarm
  - Weak defense composition
  - No win condition cards played

### 5. Report Generator (`report_generator.py`)
**Purpose**: Create detailed analysis report

**Report Sections**:
1. **Game Summary**
   - Result (Win/Loss)
   - Duration
   - Overall accuracy score (0-100)
   - Key statistics

2. **Move-by-Move Analysis**
   - Timeline with each card played
   - Evaluation for each move
   - Alternative suggestions
   - Annotations for mistakes/good plays

3. **Mistake Summary**
   - Top 5 blunders with timestamps
   - Recurring error patterns
   - Specific improvement areas

4. **Performance Ratings**
   - Elixir management: 0-10
   - Card placement: 0-10
   - Defensive play: 0-10
   - Offensive pressure: 0-10
   - Overall: 0-10

5. **Improvement Suggestions**
   - Specific actionable advice
   - Card usage recommendations
   - Timing tips

### 6. Web API (`app.py`)
**Purpose**: Flask/FastAPI server for mobile uploads

**Endpoints**:
- `POST /upload` - Accept screen recording
- `GET /analysis/{job_id}` - Check analysis status
- `GET /report/{job_id}` - Get full analysis report
- `GET /report/{job_id}/summary` - Get quick summary

**Features**:
- Async processing (Celery/RQ for background jobs)
- Progress updates during analysis
- Store reports in database
- User authentication (optional)

### 7. Mobile Frontend (`frontend/`)
**Purpose**: User-friendly interface for mobile devices

**Pages**:
- Upload screen recording
- View analysis progress
- Interactive report view
  - Timeline scrubber
  - Click on moves to see details
  - Highlight mistakes in red, good plays in green
- Learning resources based on detected mistakes

## Technology Stack

### Backend
- **FastAPI**: Modern async web framework
- **OpenCV**: Video frame extraction
- **PyTorch**: DQN model inference
- **Celery + Redis**: Background job processing
- **SQLite/PostgreSQL**: Store analysis results

### Frontend
- **React/Next.js**: Modern web framework
- **TailwindCSS**: Mobile-responsive styling
- **Video.js**: Video playback with annotations
- **Chart.js**: Visualization of metrics

## Implementation Phases

### Phase 1: Core Analysis (Week 1)
- [ ] Video frame extraction
- [ ] Game state reconstruction
- [ ] Basic DQN evaluation
- [ ] Simple text report generation

### Phase 2: Advanced Analysis (Week 2)
- [ ] Mistake detection system
- [ ] Move classification
- [ ] Detailed metrics calculation
- [ ] JSON report format

### Phase 3: Web API (Week 3)
- [ ] FastAPI server setup
- [ ] Upload endpoint
- [ ] Background processing
- [ ] Report retrieval API

### Phase 4: Mobile Frontend (Week 4)
- [ ] Upload interface
- [ ] Progress tracking
- [ ] Interactive report viewer
- [ ] Mobile optimization

### Phase 5: Polish & Deploy (Week 5)
- [ ] Error handling
- [ ] Performance optimization
- [ ] Mobile app wrapper (optional)
- [ ] Deployment (AWS/GCP/Heroku)

## Example Analysis Output

```
ClashFish Analysis Report
========================

Game Result: DEFEAT
Duration: 3:42
Overall Accuracy: 64% (Fair)

Move-by-Move Analysis:
----------------------
1. [0:15] Knight at bridge (7,15) - Good (!)
   AI would play: Knight at bridge (7,15)

2. [0:23] Arrows on empty space (9,10) - BLUNDER (??)
   AI would play: Save elixir (wait)
   Evaluation loss: -45% (wasted 3 elixir)

3. [0:35] Hog Rider at bridge (6,14) - Inaccuracy (?!)
   AI would play: Musketeer for defense (4,22)
   Evaluation loss: -12% (ignored enemy push)

Mistakes Summary:
-----------------
🔴 3 Blunders - Average loss: 38%
🟡 5 Mistakes - Average loss: 22%
🔵 7 Inaccuracies - Average loss: 10%

Top Blunders:
1. [0:23] Arrows on empty space - Wasted spell
2. [1:45] Overcapped at 10 elixir for 8 seconds
3. [2:30] Placed Wizard behind tower (no targets)

Performance Ratings:
-------------------
Elixir Management: 4/10 - Overcapped 3 times
Card Placement: 6/10 - Several wasted spells
Defensive Play: 5/10 - Slow reactions to pushes
Offensive Pressure: 7/10 - Good aggression
Overall: 5.5/10 - FAIR

Improvement Tips:
----------------
1. Avoid using spells when no enemies are in range
2. Watch your elixir - don't let it reach 10
3. Respond faster to enemy pushes (avg reaction: 4s)
4. Consider saving Arrows for enemy Minion Horde
```

## Mobile Upload Workflow

1. User finishes Clash Royale match
2. Records screen or uses built-in replay
3. Opens ClashFish mobile site
4. Uploads video (auto-detect phone resolution)
5. Processing starts (shows progress: "Extracting frames... 45%")
6. Analysis complete (notification sent)
7. Views interactive report with video playback
8. Can share report link with friends/clan

## Differences from Current Bot

| Current Bot | ClashFish |
|-------------|-----------|
| Real-time play | Offline analysis |
| Learns from gameplay | Teaches from gameplay |
| BlueStacks required | Any device with browser |
| Windows only | Cross-platform |
| Screenshot capture | Video processing |
| Epsilon-greedy exploration | Deterministic evaluation |
| Training mode | Inference mode only |

## Future Enhancements

- **Deck analysis**: Suggest better card compositions
- **Meta comparison**: Compare performance vs top players
- **Replay database**: Learn from uploaded games
- **Live analysis**: Real-time overlay during play (advanced)
- **Coaching modes**: Beginner, Intermediate, Advanced
- **Multi-language support**: Localization
- **Clan analytics**: Compare clan members' games
