import clsx from 'clsx';

interface MetricCardProps {
  label: string;
  value: string;
  positive?: boolean;
  negative?: boolean;
}

export default function MetricCard({ label, value, positive, negative }: MetricCardProps) {
  return (
    <div className="card">
      <div className="label">{label}</div>
      <div
        className={clsx('text-xl font-semibold', {
          'metric-value-positive': positive,
          'metric-value-negative': negative,
        })}
      >
        {value}
      </div>
    </div>
  );
}
