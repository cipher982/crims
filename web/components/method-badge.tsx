interface MethodBadgeProps {
  status: "exact" | "candidate" | "mixed" | "unsupported";
}

const LABELS: Record<MethodBadgeProps["status"], string> = {
  exact: "Exact",
  candidate: "Candidate",
  mixed: "Mixed",
  unsupported: "Unsupported",
};

const CLASSES: Record<MethodBadgeProps["status"], string> = {
  exact:
    "border border-cyan-400/25 bg-cyan-400/10 text-cyan-200",
  candidate:
    "border border-amber-400/25 bg-amber-400/10 text-amber-200",
  mixed:
    "border border-indigo-400/25 bg-indigo-400/10 text-indigo-200",
  unsupported:
    "border border-rose-400/25 bg-rose-400/10 text-rose-200",
};

export function MethodBadge({ status }: MethodBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.14em] ${CLASSES[status]}`}
    >
      {LABELS[status]}
    </span>
  );
}
