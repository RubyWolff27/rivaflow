interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  strokeWidth?: number;
  className?: string;
}

export default function Sparkline({
  data,
  width = 120,
  height = 40,
  strokeWidth = 2,
  className = '',
}: SparklineProps) {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return null;
  }

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * width;
    const y = height - ((value - min) / range) * height;
    return `${x},${y}`;
  });

  const pathData = `M ${points.join(' L ')}`;

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className={className}
      style={{ display: 'block' }}
    >
      <path
        d={pathData}
        fill="none"
        stroke="var(--accent)"
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
