"use client";

import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import Avatar from "@/components/ui/Avatar";

const TUTOR_LINKS = [
  { href: "/dashboard", icon: "📊", label: "Главная" },
  { href: "/content", icon: "📚", label: "Контент" },
  { href: "/tests", icon: "📝", label: "Тесты" },
  { href: "/review", icon: "✅", label: "Проверка" },
];

const STUDENT_LINKS = [
  { href: "/dashboard", icon: "📊", label: "Главная" },
  { href: "/tests", icon: "📋", label: "Мои тесты" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { auth, logout } = useAuth();
  const links = auth.role === "TUTOR" ? TUTOR_LINKS : STUDENT_LINKS;

  const handleLogout = () => {
    logout();
    router.push("/auth/login");
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">🎓 Репетитор</div>

      <nav className="sidebar-nav">
        {links.map((link) => (
          <a
            key={link.href}
            className={`sidebar-link ${pathname === link.href ? "active" : ""}`}
            onClick={() => router.push(link.href)}
          >
            <span className="icon">{link.icon}</span>
            {link.label}
          </a>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <Avatar name={auth.email || "U"} />
          <div>
            <div className="sidebar-user-name">
              {auth.role === "TUTOR" ? "Репетитор" : "Ученик"}
            </div>
            <div className="sidebar-user-email truncate">{auth.email}</div>
          </div>
        </div>
        <button className="btn btn-ghost btn-sm" style={{ width: "100%" }} onClick={handleLogout}>
          Выход
        </button>
      </div>
    </aside>
  );
}
