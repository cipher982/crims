import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { Nav } from "@/components/nav";
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
  title: "NYC Criminal Justice Explorer",
  description: "Person-centric exploration of NYC DOC jail recidivism data",
};

export const viewport: Viewport = {
  themeColor: "#030305",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${jetbrainsMono.variable} h-full antialiased`}
    >
      <body className="min-h-full">
        <div className="drose-particle-bg" aria-hidden="true" />
        <Nav />
        <main className="drose-shell">
          {children}
        </main>
      </body>
    </html>
  );
}
