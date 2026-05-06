import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ReRush — Find That Episode",
  description: "AI-powered semantic search for sitcom episodes. Describe what you remember, we'll find it.",
  keywords: ["TV episodes", "sitcom search", "Friends", "Seinfeld", "The Office", "semantic search"],
  openGraph: {
    title: "ReRush — Find That Episode",
    description: "Describe any episode in natural language and find it instantly.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased">{children}</body>
    </html>
  );
}
