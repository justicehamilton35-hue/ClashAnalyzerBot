'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

interface TimelinePoint {
  timestamp: number;
  evaluation: number;
  win_probability: number;
  your_elixir: number;
  opponent_elixir: number;
}

interface Props {
  timeline: TimelinePoint[];
  selectedTimestamp: number;
  onTimestampSelect: (timestamp: number) => void;
}

export default function EvaluationGraph({ timeline, selectedTimestamp, onTimestampSelect }: Props) {
  // Transform data for recharts
  const chartData = timeline.map((point) => ({
    time: point.timestamp,
    evaluation: point.evaluation,
    winProb: point.win_probability * 100, // Convert to percentage
    elixir: point.your_elixir,
  }));

  return (
    <div className="space-y-6">
      {/* Evaluation Chart */}
      <div>
        <h3 className="text-sm font-semibold text-slate-400 mb-2">Position Evaluation</h3>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart
            data={chartData}
            onClick={(e: any) => {
              if (e?.activeLabel !== undefined) {
                onTimestampSelect(e.activeLabel);
              }
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="time"
              stroke="#94a3b8"
              fontSize={12}
              tickFormatter={(value) => `${value.toFixed(0)}s`}
            />
            <YAxis
              stroke="#94a3b8"
              fontSize={12}
              domain={[-10, 10]}
              ticks={[-10, -5, 0, 5, 10]}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#94a3b8' }}
              itemStyle={{ color: '#fff' }}
              formatter={(value: any) => [`${value.toFixed(2)}`, 'Evaluation']}
              labelFormatter={(label) => `Time: ${label.toFixed(1)}s`}
            />
            <ReferenceLine y={0} stroke="#64748b" strokeDasharray="3 3" />
            <ReferenceLine
              x={selectedTimestamp}
              stroke="#3b82f6"
              strokeWidth={2}
              label={{ value: '▼', position: 'top', fill: '#3b82f6' }}
            />
            <Line
              type="monotone"
              dataKey="evaluation"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
        <div className="flex items-center justify-center gap-8 mt-2 text-sm text-slate-400">
          <span>+10 = Winning</span>
          <span>0 = Equal</span>
          <span>-10 = Losing</span>
        </div>
      </div>

      {/* Win Probability Chart */}
      <div>
        <h3 className="text-sm font-semibold text-slate-400 mb-2">Win Probability</h3>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart
            data={chartData}
            onClick={(e: any) => {
              if (e?.activeLabel !== undefined) {
                onTimestampSelect(e.activeLabel);
              }
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="time"
              stroke="#94a3b8"
              fontSize={12}
              tickFormatter={(value) => `${value.toFixed(0)}s`}
            />
            <YAxis
              stroke="#94a3b8"
              fontSize={12}
              domain={[0, 100]}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#94a3b8' }}
              itemStyle={{ color: '#fff' }}
              formatter={(value: any) => [`${value.toFixed(1)}%`, 'Win Probability']}
              labelFormatter={(label) => `Time: ${label.toFixed(1)}s`}
            />
            <ReferenceLine y={50} stroke="#64748b" strokeDasharray="3 3" />
            <ReferenceLine
              x={selectedTimestamp}
              stroke="#3b82f6"
              strokeWidth={2}
              label={{ value: '▼', position: 'top', fill: '#3b82f6' }}
            />
            <Line
              type="monotone"
              dataKey="winProb"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Elixir Chart */}
      <div>
        <h3 className="text-sm font-semibold text-slate-400 mb-2">Elixir</h3>
        <ResponsiveContainer width="100%" height={150}>
          <LineChart
            data={chartData}
            onClick={(e: any) => {
              if (e?.activeLabel !== undefined) {
                onTimestampSelect(e.activeLabel);
              }
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="time"
              stroke="#94a3b8"
              fontSize={12}
              tickFormatter={(value) => `${value.toFixed(0)}s`}
            />
            <YAxis stroke="#94a3b8" fontSize={12} domain={[0, 10]} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#94a3b8' }}
              itemStyle={{ color: '#fff' }}
              labelFormatter={(label) => `Time: ${label.toFixed(1)}s`}
            />
            <ReferenceLine
              x={selectedTimestamp}
              stroke="#3b82f6"
              strokeWidth={2}
            />
            <Line
              type="stepAfter"
              dataKey="elixir"
              stroke="#a855f7"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
