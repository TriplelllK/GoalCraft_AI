interface ProgressBarProps {
  label: string;
  value: number;           // 0.0 – 1.0
}

const colorForValue = (v: number) => {
  if (v >= 0.8) return 'var(--color-success)';
  if (v >= 0.6) return 'var(--color-warning)';
  return 'var(--color-danger)';
};

export function ProgressBar({ label, value }: ProgressBarProps) {
  const pct = Math.round(value * 100);
  return (
    <div className="progress-row">
      <span className="progress-label">{label}</span>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${pct}%`, background: colorForValue(value) }} />
      </div>
      <span className="progress-pct">{pct}%</span>
    </div>
  );
}
