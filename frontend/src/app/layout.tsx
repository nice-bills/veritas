import type { Metadata } from "next";
import { Toaster } from "sonner";
import "./globals.css";

export const metadata: Metadata = {
  title: "Veritas OS | Crypto Agent Platform",
  description: "The easiest way to build, test, and audit crypto AI agents on Base.",
  themeColor: "#09090b",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" style={{ colorScheme: "dark" }}>
      <body className="bg-zinc-950 text-white antialiased min-h-screen">
        {children}
        <Toaster position="bottom-right" theme="dark" />
      </body>
    </html>
  );
}
