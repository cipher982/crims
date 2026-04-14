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
    "text-white/80",
  candidate:
    "text-white/80",
  mixed:
    "text-white/80",
  unsupported:
    "text-white/80",
};

export function MethodBadge({ status }: MethodBadgeProps) {
  return (
    <span
      className={`inline text-[10px] font-semibold uppercase tracking-[0.12em] ${CLASSES[status]}`}
    >
      {LABELS[status]}
    </span>
  );
}
