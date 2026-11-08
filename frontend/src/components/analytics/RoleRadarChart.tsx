import React, { useState } from 'react';
import type { DimensionScore } from '../../api/types';

export interface RoleRadarChartProps {
  dimensions: Record<string, DimensionScore> | DimensionScore[];
  playerName?: string;
  className?: string;
}

export const RoleRadarChart: React.FC<RoleRadarChartProps> = ({
  dimensions,
  playerName = 'Player',
  className = '',
}) => {
  const [activeDimension, setActiveDimension] = useState<DimensionScore | null>(null);

  // Normalize dimensions into an array
  const dimList: DimensionScore[] = Array.isArray(dimensions)
    ? dimensions
    : dimensions
    ? Object.values(dimensions)
    : [];

  if (dimList.length < 3) {
    return (
      <div className="p-6 bg-surface-card border border-surface-border rounded text-center text-xs text-text-tertiary">
        Insufficient dimensions ({dimList.length}) to plot radar polygon.
      </div>
    );
  }

  const size = 320;
  const center = size / 2;
  const radius = center - 50;
  const numAxes = dimList.length;
  const angleStep = (Math.PI * 2) / numAxes;

  // Compute point for a given axis and value (0-100)
  const getCoordinates = (index: number, value: number) => {
    const angle = index * angleStep - Math.PI / 2; // start from 12 o'clock
    const r = (value / 100) * radius;
    const x = center + r * Math.cos(angle);
    const y = center + r * Math.sin(angle);
    return { x, y, angle };
  };

  // Polygon path string
  const polygonPoints = dimList
    .map((d, i) => {
      const score = d.dimension_score ?? (d as unknown as { score?: number }).score ?? 0;
      const { x, y } = getCoordinates(i, Math.min(100, Math.max(0, score)));
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');

  const gridLevels = [25, 50, 75, 100];

  return (
    <div className={`flex flex-col items-center ${className}`}>
      {/* SVG Canvas */}
      <div className="relative">
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          className="overflow-visible"
          role="img"
          aria-label={`Role-adaptive performance radar chart for ${playerName}`}
        >
          {/* Concentric Grid Rings */}
          {gridLevels.map((level) => {
            const levelPoints = dimList
              .map((_, i) => {
                const { x, y } = getCoordinates(i, level);
                return `${x.toFixed(1)},${y.toFixed(1)}`;
              })
              .join(' ');

            return (
              <polygon
                key={level}
                points={levelPoints}
                fill="none"
                stroke="#2D323E"
                strokeWidth={level === 50 ? '1.5' : '1'}
                strokeDasharray={level === 50 ? '3 3' : undefined}
                className="transition-colors"
              />
            );
          })}

          {/* Radial Axis Spokes */}
          {dimList.map((_, i) => {
            const outer = getCoordinates(i, 100);
            return (
              <line
                key={i}
                x1={center}
                y1={center}
                x2={outer.x}
                y2={outer.y}
                stroke="#2D323E"
                strokeWidth="1"
              />
            );
          })}

          {/* Data Polygon */}
          <polygon
            points={polygonPoints}
            fill="#D62978"
            fillOpacity="0.22"
            stroke="#D62978"
            strokeWidth="2.5"
            strokeLinejoin="round"
            className="filter drop-shadow-[0_2px_8px_rgba(214,41,120,0.35)]"
          />

          {/* Data Points */}
          {dimList.map((d, i) => {
            const { x, y } = getCoordinates(i, Math.min(100, Math.max(0, d.dimension_score)));
            const isHovered = activeDimension?.dimension_id === d.dimension_id;

            return (
              <circle
                key={d.dimension_id}
                cx={x}
                cy={y}
                r={isHovered ? 5.5 : 3.5}
                fill="#F1EFEA"
                stroke="#D62978"
                strokeWidth="2"
                className="cursor-pointer transition-all duration-150"
                onMouseEnter={() => setActiveDimension(d)}
                onMouseLeave={() => setActiveDimension(null)}
              />
            );
          })}

          {/* Axis Labels */}
          {dimList.map((d, i) => {
            const labelCoord = getCoordinates(i, 118);
            const isHovered = activeDimension?.dimension_id === d.dimension_id;

            // Anchor alignment based on position
            let textAnchor: 'middle' | 'start' | 'end' = 'middle';
            if (labelCoord.x > center + 10) textAnchor = 'start';
            else if (labelCoord.x < center - 10) textAnchor = 'end';

            return (
              <text
                key={d.dimension_id}
                x={labelCoord.x}
                y={labelCoord.y + 4}
                textAnchor={textAnchor}
                className={`text-[10px] font-medium transition-colors cursor-pointer select-none ${
                  isHovered ? 'fill-accent-magenta font-semibold' : 'fill-text-secondary'
                }`}
                onMouseEnter={() => setActiveDimension(d)}
                onMouseLeave={() => setActiveDimension(null)}
              >
                {d.dimension_name}
              </text>
            );
          })}
        </svg>

        {/* Center/Hover Metric Tooltip */}
        {activeDimension && (
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-surface-elevated/95 border border-accent-magenta/40 rounded px-2.5 py-1 text-center pointer-events-none shadow-elevated">
            <div className="text-[10px] text-text-secondary font-medium">
              {activeDimension.dimension_name}
            </div>
            <div className="text-xs font-display font-bold text-accent-magenta tabular-nums">
              {activeDimension.dimension_score.toFixed(1)}th pct
            </div>
          </div>
        )}
      </div>

      {/* Accessible Tabular Representation */}
      <div className="w-full mt-4 pt-3 border-t border-surface-border">
        <div className="flex items-center justify-between text-[11px] font-semibold text-text-secondary uppercase tracking-wider mb-2">
          <span>Dimension Breakdown</span>
          <span>Percentile / Weight</span>
        </div>
        <div className="space-y-1.5">
          {dimList.map((d) => (
            <div
              key={d.dimension_id}
              className={`flex items-center justify-between text-xs px-2.5 py-1.5 rounded transition-colors ${
                activeDimension?.dimension_id === d.dimension_id
                  ? 'bg-accent-magenta/10 text-text-primary'
                  : 'hover:bg-surface-elevated text-text-secondary'
              }`}
              onMouseEnter={() => setActiveDimension(d)}
              onMouseLeave={() => setActiveDimension(null)}
            >
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-accent-magenta" />
                <span className="font-medium text-text-primary">
                  {d.dimension_name || (d as unknown as { name?: string }).name || d.dimension_id}
                </span>
              </div>
              <div className="flex items-center gap-3 tabular-nums">
                <span className="text-text-tertiary text-[11px]">
                  (w={(d.weight ?? 0).toFixed(2)})
                </span>
                <span className="font-bold text-text-primary">
                  {(d.dimension_score ?? (d as unknown as { score?: number }).score ?? 0).toFixed(1)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
