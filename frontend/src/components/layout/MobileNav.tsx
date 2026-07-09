"use client";

import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

const TUTOR_LINKS = [
  { href: "/dashboard", icon: "📊", label: "Главная" },
  { href: "/content", icon: "📚", label: "Контент" },
  { href: "/tests", icon: "📝", label: "Тесты" },
  { href: "/review", icon: "✅", label: "Проверка" },
];

const STUDENT_LINKS = [
  { href: "/dashboard", icon: "📊", label: "Главная" },
];

export default function MobileNav() {
  const pathname = usePathname();
  const router = useRouter();
  const { auth } = useAuth();
  const links = auth.role === "TUTOR" ? TUTOR_LINKS : STUDENT_LINKS;

  return (
    <nav className="mobile-nav">
      {links.map((link) => (
        <button
          key={link.href}
          className={`mobile-nav-item ${pathname === link.href ? "active" : ""}`}
          onClick={() => router.push(link.href)}
        >
          <span className="mobile-nav-icon">{link.icon}</span>
          <span className="mobile-nav-label">{link.label}</span>
        </button>
      ))}
    </nav>
  );
}
