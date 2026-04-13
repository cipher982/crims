import { TIER_BG } from "@/lib/constants";
import { tierLabel } from "@/lib/format";

export function TierBadge({ tier }: { tier: string }) {
  const classes = TIER_BG[tier] ?? "bg-gray-100 text-gray-700";
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${classes}`}
    >
      {tierLabel(tier)}
    </span>
  );
}
