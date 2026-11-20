"use client";

import { useRouter } from "next/navigation";

export default function LogoutButton() {
  const router = useRouter();
  async function logout() {
    await fetch("/api/auth/logout", { method: "POST", cache: "no-store" });
    router.replace("/login");
    router.refresh();
  }
  return <button className="logout-button" onClick={logout} aria-label="Sign out" title="Sign out">↗</button>;
}
