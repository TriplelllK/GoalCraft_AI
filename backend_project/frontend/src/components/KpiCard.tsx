interface KpiCardProps {
  label: string;
  value: string;
  hint?: string;
  color?: string;
}

export function KpiCard({ label, value, hint, color }: KpiCardProps) {
  return (
    <div className="kpi-card">
      <div className="kpi-value" style={color ? { color } : undefined}>{value}</div>
      <div className="kpi-label">{label}</div>
      {hint ? <div className="kpi-hint">{hint}</div> : null}
    </div>
  );
}
