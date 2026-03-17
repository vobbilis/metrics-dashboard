import { AreaChart, Area, ResponsiveContainer, YAxis } from 'recharts'

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#8b5cf6', '#06b6d4', '#ef4444']

interface SparklineChartProps {
  data: { value: number }[]
  width?: number
  height?: number
  color?: string
  colorIndex?: number
}

export function SparklineChart({ data, height = 80, color, colorIndex = 0 }: SparklineChartProps) {
  if (data.length === 0) {
    return null
  }

  const chartData = data.length === 1 ? [data[0], data[0]] : data
  const strokeColor = color ?? COLORS[colorIndex % COLORS.length]

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
        <defs>
          <linearGradient id={`grad-${colorIndex}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={strokeColor} stopOpacity={0.3} />
            <stop offset="100%" stopColor={strokeColor} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <YAxis hide domain={['dataMin', 'dataMax']} />
        <Area
          type="monotone"
          dataKey="value"
          stroke={strokeColor}
          strokeWidth={1.5}
          fill={`url(#grad-${colorIndex})`}
          dot={false}
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
