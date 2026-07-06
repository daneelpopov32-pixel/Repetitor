"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { motion } from "framer-motion";
import { slideUp, stagger } from "@/lib/motion";
import Sidebar from "@/components/layout/Sidebar";
import PageWrapper from "@/components/layout/PageWrapper";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Avatar from "@/components/ui/Avatar";
import ProgressBar from "@/components/ui/ProgressBar";
import EmptyState from "@/components/ui/EmptyState";
import Spinner from "@/components/ui/Spinner";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function TutorDashboard({ token }: { token: string }) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [students, setStudents] = useState<any[]>([]);
  const [inviteCode, setInviteCode] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getTutorStudents(token).then(setStudents).catch(() => {}).finally(() => setLoading(false));
  }, [token]);

  const generateCode = async () => {
    const res = await api.generateInvitationCode(30, token);
    setInviteCode(res.code);
  };

  if (loading) return <div style={{ display: "flex", justifyContent: "center", padding: "3rem" }}><Spinner size="lg" /></div>;

  return (
    <PageWrapper
      title="Главная"
      actions={
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          {inviteCode && (
            <code style={{ padding: "0.25rem 0.75rem", background: "var(--c-hover)", borderRadius: "var(--r-md)", fontSize: "var(--text-sm)" }}>
              {inviteCode}
            </code>
          )}
          <Button variant="secondary" onClick={generateCode}>Пригласить ученика</Button>
        </div>
      }
    >
      {/* Stats */}
      <motion.div className="grid grid-3" style={{ marginBottom: "1.5rem" }} {...stagger}>
        <motion.div {...slideUp}>
          <Card>
            <div style={{ color: "var(--c-text-secondary)", fontSize: "var(--text-sm)", marginBottom: "0.25rem" }}>Учеников</div>
            <div style={{ fontSize: "var(--text-3xl)", fontWeight: 700 }}>{students.length}</div>
          </Card>
        </motion.div>
        <motion.div {...slideUp}>
          <Card>
            <div style={{ color: "var(--c-text-secondary)", fontSize: "var(--text-sm)", marginBottom: "0.25rem" }}>Средний балл</div>
            <div style={{ fontSize: "var(--text-3xl)", fontWeight: 700 }}>
              {students.length > 0
                ? Math.round(students.reduce((s: number, st: Record<string, unknown>) => s + ((st.average_score as number) || 0), 0) / students.length)
                : "—"}
            </div>
          </Card>
        </motion.div>
        <motion.div {...slideUp}>
          <Card>
            <div style={{ color: "var(--c-text-secondary)", fontSize: "var(--text-sm)", marginBottom: "0.25rem" }}>Всего тестов</div>
            <div style={{ fontSize: "var(--text-3xl)", fontWeight: 700 }}>
              {students.reduce((s: number, st: Record<string, unknown>) => s + ((st.test_count as number) || 0), 0)}
            </div>
          </Card>
        </motion.div>
      </motion.div>

      {/* Students */}
      {students.length === 0 ? (
        <EmptyState icon="👥" title="Пока нет учеников" text="Пригласите ученика по коду или создайте тест" />
      ) : (
        <motion.div className="grid grid-2" {...stagger}>
          {students.map((s: Record<string, unknown>, idx: number) => (
            <motion.div key={String(s.id || idx)} {...slideUp}>
              <Card hover>
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.75rem" }}>
                  <Avatar name={`${s.first_name || ""} ${s.last_name || ""}`.trim() || "У"} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600 }}>{String(s.first_name || "")} {String(s.last_name || "")}</div>
                    <div style={{ fontSize: "var(--text-xs)", color: "var(--c-text-secondary)" }}>{String(s.email || "")}</div>
                  </div>
                  <Badge variant={((s.average_score as number) || 0) >= 70 ? "success" : ((s.average_score as number) || 0) >= 40 ? "warning" : "danger"}>
                    {String(s.average_score || 0)}%
                  </Badge>
                </div>
                <ProgressBar value={((s.average_score as number) || 0)} variant={((s.average_score as number) || 0) >= 70 ? "success" : "default"} />
                <div style={{ fontSize: "var(--text-xs)", color: "var(--c-text-secondary)", marginTop: "0.5rem" }}>
                  {String(s.test_count || 0)} тестов
                </div>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      )}
    </PageWrapper>
  );
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function StudentDashboard({ token }: { token: string }) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [tests, setTests] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    api.getStudentTests(token).then(setTests).catch(() => {}).finally(() => setLoading(false));
  }, [token]);

  if (loading) return <div style={{ display: "flex", justifyContent: "center", padding: "3rem" }}><Spinner size="lg" /></div>;

  const startTest = async (testId: string) => {
    try {
      const res = await api.startAttempt(testId, token);
      router.push(`/tests/${res.attempt_id}/attempt`);
    } catch {}
  };

  return (
    <PageWrapper title="Мои тесты">
      {tests.length === 0 ? (
        <EmptyState icon="📋" title="Пока нет тестов" text="Репетитор назначит вам тест — он появится здесь" />
      ) : (
        <motion.div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }} {...stagger}>
          {tests.map((t: Record<string, unknown>, idx: number) => {
            const status = t.status as string;
            const score = t.score as number | null;
            return (
              <motion.div key={String(t.test_id || idx)} {...slideUp}>
                <Card hover onClick={status !== "COMPLETED" ? () => startTest(t.test_id as string) : undefined}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, marginBottom: "0.25rem" }}>{String(t.title || "Тест")}</div>
                      <div style={{ fontSize: "var(--text-xs)", color: "var(--c-text-secondary)" }}>
                        {String(t.task_count || 0)} заданий{t.time_limit ? ` • ${t.time_limit} мин` : ""}
                      </div>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                      {score !== null && score !== undefined && (
                        <span style={{ fontWeight: 600, fontSize: "var(--text-lg)" }}>{String(score)}%</span>
                      )}
                      <Badge variant={
                        status === "COMPLETED" ? "success" :
                        status === "IN_PROGRESS" ? "warning" : "info"
                      }>
                        {status === "COMPLETED" ? "Пройден" :
                         status === "IN_PROGRESS" ? "В процессе" : "Начать"}
                      </Badge>
                    </div>
                  </div>
                </Card>
              </motion.div>
            );
          })}
        </motion.div>
      )}
    </PageWrapper>
  );
}

export default function DashboardPage() {
  const { auth, hydrated, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (hydrated && !auth.token) router.replace("/auth/login");
  }, [hydrated, auth.token, router]);

  if (!hydrated || !auth.token) return <div className="layout-auth"><Spinner size="lg" /></div>;

  return (
    <div className="layout">
      <Sidebar />
      {auth.role === "TUTOR"
        ? <TutorDashboard token={auth.token} />
        : <StudentDashboard token={auth.token} />
      }
    </div>
  );
}
