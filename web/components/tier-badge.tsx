import { TIER_BG } from "@/lib/constants";
import { tierLabel } from "@/lib/format";

export function TierBadge({ tier }: { tier: string }) {
  const classes = TIER_BG[tier] ?? "drose-badge-single";
  return (
    <span className={`drose-badge ${classes}`}>
      {tierLabel(tier)}
    </span>
  );
}
