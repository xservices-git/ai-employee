import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Employee",
  description: "Local AI Employee V3.0",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
