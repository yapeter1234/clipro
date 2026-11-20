import { redirect } from "next/navigation";

// Kept as a friendly redirect for bookmarks from the earlier private prototype.
export default function LoginPage(): never {
  redirect("/");
}
