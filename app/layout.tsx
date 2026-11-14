import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Nav from "@/components/nav";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "FwdMD",
  description: "Check health WhatsApp forwards against WHO, ICMR, MoHFW and PIB sources.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background min-h-screen flex flex-col`}>
        <Nav />
        <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-6 pb-24">{children}</main>
        <footer
          role="note"
          className="fixed inset-x-0 bottom-0 z-10 border-t border-amber-300 bg-amber-50 px-4 py-2 text-center text-sm font-medium text-amber-900"
        >
          Not medical advice. In an emergency, see a doctor.
        </footer>
      </body>
    </html>
  );
}
