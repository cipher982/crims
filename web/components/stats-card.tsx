interface StatsCardProps {
  label: string;
  value: string;
}

export function StatsCard({ label, value }: StatsCardProps) {
  return (
    <div className="drose-stat-card">
      <div className="drose-stat-label">{label}</div>
      <div className="drose-stat-value">{value}</div>
    </div>
  );
}
