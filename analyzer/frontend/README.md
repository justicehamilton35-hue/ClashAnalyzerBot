# Clash Royale Analyzer - Frontend

Chess.com-style interface for analyzing Clash Royale gameplay videos.

## Features

- **Video Upload**: Drag-and-drop MP4 upload
- **Real-time Analysis**: Progress tracking during analysis
- **Interactive Timeline**: Click through game states with evaluation graph
- **Move List**: Detailed move-by-move breakdown with classifications
- **Evaluation Board**: Visual game state with troop positions
- **Win Probability Graph**: Timeline showing win% throughout the game
- **Analysis Dashboard**: Summary stats, playstyle, and recommendations

## Tech Stack

- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Recharts**: Data visualization
- **Video.js**: Video playback
- **Axios**: API client

## Setup

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Open browser to http://localhost:3000
```

## Project Structure

```
src/
├── app/                    # Next.js app router
│   ├── page.tsx           # Home page
│   ├── analyze/[id]/      # Analysis page
│   └── layout.tsx         # Root layout
├── components/            # React components
│   ├── Upload/           # Video upload
│   ├── Analysis/         # Analysis display
│   ├── Timeline/         # Game timeline
│   ├── MoveList/         # Move-by-move list
│   ├── EvaluationGraph/  # Evaluation chart
│   └── GameBoard/        # Visual board
├── lib/                  # Utilities
│   ├── api.ts           # API client
│   └── types.ts         # TypeScript types
└── styles/              # Global styles
```

## Configuration

Update API URL in `src/lib/api.ts`:

```typescript
const API_BASE_URL = 'http://localhost:8000';
```

## Building for Production

```bash
npm run build
npm start
```

## Environment Variables

Create `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```
