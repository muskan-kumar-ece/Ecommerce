type TimelineItem = {
  label: string;
  completed: boolean;
  timestamp?: string | null;
};

type TimelineProps = {
  items: TimelineItem[];
  formatTimestamp: (value: string) => string;
};

export function Timeline({ items, formatTimestamp }: TimelineProps) {
  return (
    <ol className="space-y-4">
      {items.map((step) => (
        <li key={step.label} className="flex items-start gap-3">
          <span
            className={`mt-1 h-2.5 w-2.5 rounded-full ${step.completed ? "bg-emerald-600" : "bg-neutral-300 dark:bg-neutral-700"}`}
          />
          <div>
            <p className={`text-sm font-medium ${step.completed ? "text-neutral-900 dark:text-neutral-100" : "text-neutral-500 dark:text-neutral-400"}`}>
              {step.label}
            </p>
            {step.timestamp ? (
              <p className="text-xs text-neutral-500 dark:text-neutral-400">{formatTimestamp(step.timestamp)}</p>
            ) : null}
          </div>
        </li>
      ))}
    </ol>
  );
}
