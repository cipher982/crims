import { notFound, redirect } from "next/navigation";
import { getRandomHighRepeatId } from "@/lib/queries";

export const metadata = { title: "Random Person — NYC CJ Explorer" };
export const dynamic = "force-dynamic";

export default async function RandomPersonPage() {
  const id = await getRandomHighRepeatId();
  if (!id) {
    notFound();
  }
  redirect(`/person/${id}`);
}
