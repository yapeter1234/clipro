import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Clipro Studio",
  description: "AI-powered clipping and short-form video editing studio.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
