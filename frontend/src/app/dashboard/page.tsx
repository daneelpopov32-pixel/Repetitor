"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import Link from "next/link";

export default function DashboardPage() {
  const { auth, hydrated, logout } = useAuth();
  const router = useRouter();
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    if (!hydrated) return;
    if (!auth.token) {
      router.replace("/auth/login");
      return;
    }
    if (auth.role === "TUTOR") {
      loadTutorDashboard();
    } else {
      loadStudentDashboard();
    }
  }, [auth.token, hydrated]);

  const loadTutorDashboard = async () => {
    try {
      const students = await api.getTutorStudents(auth.token!);
      setData({ students });
    } catch {}
  };

  const loadStudentDashboard = async () => {
    try {
      const [dash, assignedTests] = await Promise.all([
        api.getDashboard(auth.userId!, auth.token!),
        api.getStudentTests(auth.token!),
      ]);
      setData({ dashboard: dash, assignedTests });
    } catch {}
  };

  if (!hydrated || !data) return <div className="container" style={{ padding: "2rem" }}>Загрузка...</div>;

  return (
    <>
      <header className="header">
        <h1>Репетитор</h1>
        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          <span style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
            {auth.email} ({auth.role})
          </span>
          {auth.role === "TUTOR" && (
            <>
              <Link href="/content" className="btn btn-primary" style={{ background: "var(--success)" }}>
                Контент
              </Link>
              <Link href="/tests" className="btn btn-primary">
                Мои тесты
              </Link>
              <Link href="/tests/new" className="btn btn-primary">
                Создать тест
              </Link>
            </>
          )}
          <button className="btn btn-danger" onClick={logout}>
            Выйти
          </button>
        </div>
      </header>
      <main className="container" style={{ padding: "2rem" }}>
        {auth.role === "TUTOR" ? (
          <TutorDashboard data={data} token={auth.token!} />
        ) : (
          <StudentDashboard data={data} token={auth.token!} />
        )}
      </main>
    </>
  );
}

function TutorDashboard({ data, token }: { data: any; token: string }) {
  const [inviteCode, setInviteCode] = useState("");
  const [showCode, setShowCode] = useState(false);

  const generateCode = async () => {
    try {
      const res = await api.generateInvitationCode(7, token);
      setInviteCode(res.code);
      setShowCode(true);
    } catch {}
  };

  return (
    <div>
      <h2 style={{ marginBottom: "1rem" }}>Мои ученики</h2>
      <div style={{ marginBottom: "1rem" }}>
        <button className="btn btn-primary" onClick={generateCode}>
          Сгенерировать код приглашения
        </button>
        {showCode && (
          <span style={{ marginLeft: "1rem", fontFamily: "monospace", fontSize: "1.1rem" }}>
            {inviteCode}
          </span>
        )}
      </div>
      {!data.students?.length ? (
        <div className="card" style={{ textAlign: "center", padding: "2rem" }}>
          <p style={{ color: "var(--text-secondary)", marginBottom: "0.5rem" }}>Пока нет учеников</p>
          <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
            Сгенерируйте код приглашения и передайте его ученику для регистрации.
          </p>
        </div>
      ) : (
        <div className="grid">
          {data.students.map((s: any) => (
            <div key={s.student_id} className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <strong>Ученик</strong>
                  <div style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
                    Тестов: {s.total_tests} | Средний балл: {s.average_score}%
                  </div>
                </div>
                <Link href={`/dashboard?view=student&id=${s.student_id}`} className="btn btn-primary">
                  Подробнее
                </Link>
              </div>
              {s.weak_themes?.length > 0 && (
                <div style={{ marginTop: "0.5rem" }}>
                  <span style={{ fontSize: "0.75rem", color: "var(--danger)" }}>Слабые темы: </span>
                  {s.weak_themes.map((t: any) => (
                    <span key={t.theme_id} className="badge badge-warning" style={{ marginRight: "0.25rem" }}>
                      {t.name} ({t.success_rate}%)
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function StudentDashboard({ data, token }: { data: any; token: string }) {
  const router = useRouter();
  const [starting, setStarting] = useState<string | null>(null);
  const dash = data.dashboard;
  const assignedTests = data.assignedTests || [];

  const startTest = async (testId: string) => {
    setStarting(testId);
    try {
      const res = await api.startAttempt(testId, token);
      router.push(`/tests/${testId}/attempt`);
    } catch (e: any) {
      alert(e.message || "Ошибка при запуске теста");
    }
    setStarting(null);
  };

  return (
    <div>
      {/* Assigned Tests */}
      {assignedTests.length > 0 && (
        <div style={{ marginBottom: "2rem" }}>
          <h2 style={{ marginBottom: "1rem" }}>Назначенные тесты</h2>
          {assignedTests.map((t: any) => (
            <div key={t.test_id} className="card" style={{ marginBottom: "0.75rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <strong>{t.title}</strong>
                  <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: "0.25rem" }}>
                    {t.tasks_count} заданий
                    {t.time_limit_minutes ? ` | ${t.time_limit_minutes} мин` : ""}
                  </div>
                </div>
                <div>
                  {t.attempt_status ? (
                    <span className={`badge ${t.attempt_status === "COMPLETED" ? "badge-success" : "badge-warning"}`}>
                      {t.attempt_status === "COMPLETED" ? "Пройден" : "В процессе"}
                    </span>
                  ) : (
                    <button
                      className="btn btn-primary"
                      disabled={starting === t.test_id}
                      onClick={() => startTest(t.test_id)}
                    >
                      {starting === t.test_id ? "Запуск..." : "Начать тест"}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Statistics */}
      <h2 style={{ marginBottom: "1rem" }}>Мой прогресс</h2>
      <div className="grid grid-2">
        <div className="card">
          <h3>Общая статистика</h3>
          <p>Тестов пройдено: <strong>{dash.total_tests}</strong></p>
          <p>Средний балл: <strong>{dash.average_score}%</strong></p>
        </div>
        <div className="card">
          <h3>Динамика</h3>
          {dash.dynamics.length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
              {dash.dynamics.slice(-5).map((d: any, i: number) => (
                <div key={i} style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>{d.date}</span>
                  <span className={`badge ${d.score >= 70 ? "badge-success" : "badge-warning"}`}>
                    {d.score}%
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: "var(--text-secondary)" }}>Нет данных</p>
          )}
        </div>
      </div>
      {dash.weak_themes?.length > 0 && (
        <div className="card" style={{ marginTop: "1rem" }}>
          <h3 style={{ color: "var(--danger)" }}>Слабые темы (менее 50%)</h3>
          {dash.weak_themes.map((t: any) => (
            <div key={t.theme_id} style={{ display: "flex", justifyContent: "space-between", padding: "0.5rem 0" }}>
              <span>{t.name}</span>
              <span className="badge badge-warning">{t.success_rate}%</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
