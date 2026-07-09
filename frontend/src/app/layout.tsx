import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";
import MobileNav from "@/components/layout/MobileNav";

const inter = Inter({ subsets: ["latin", "cyrillic"] });

export const metadata: Metadata = {
  title: "Репетитор — Тесты ФИПИ",
  description: "Комбинатор тестов ФИПИ + Аналитика прогресса",
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body className={inter.className}>
        <AuthProvider>
          {children}
          <MobileNav />
        </AuthProvider>
      </body>
    </html>
  );
}
