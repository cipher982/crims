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
    "border border-white/10 bg-white/4 text-white/80",
  candidate:
    "border border-white/10 bg-white/4 text-white/80",
  mixed:
    "border border-white/10 bg-white/4 text-white/80",
  unsupported:
    "border border-white/10 bg-white/4 text-white/80",
};

export function MethodBadge({ status }: MethodBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] ${CLASSES[status]}`}
    >
      {LABELS[status]}
    </span>
  );
}
