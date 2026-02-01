import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Veritas | Crypto AI Agent Platform",
  description: "Deploy AI agents on Base with cryptographic proof. The easiest way to build, test, and audit autonomous crypto agents.",
  keywords: ["AI agents", "crypto", "Base", "blockchain", "DeFi", "automation"],
  authors: [{ name: "Veritas" }],
};

export const viewport: Viewport = {
  themeColor: "#0a0a0a",
  colorScheme: "dark",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="bg-[#0a0a0a] text-white antialiased min-h-screen overflow-x-hidden">
        {children}
      </body>
    </html>
  );
}
