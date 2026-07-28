import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Curato AI — Social Media Intelligence System",
  description:
    "Enterprise-grade multi-agent AI platform for intelligent social media content generation.",
  keywords: ["AI", "social media", "content generation", "multi-agent"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${jetbrainsMono.variable} h-full antialiased dark`}
    >
      <body className="min-h-full bg-zinc-950 text-zinc-100 font-[family-name:var(--font-inter)]">
        {children}
      </body>
    </html>
  );
}
