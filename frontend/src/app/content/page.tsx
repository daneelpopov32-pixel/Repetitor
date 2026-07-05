"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import Link from "next/link";

interface ThemeNode {
  id: string;
  name: string;
  fipi_code?: string;
  children: ThemeNode[];
}

interface Task {
  id: string;
  type: string;
  theme_id: string;
  text_preview: string;
  source_url?: string;
}

export default function ContentPage() {
  const { auth, hydrated, logout } = useAuth();
  const router = useRouter();
  const [subjects, setSubjects] = useState<any[]>([]);
  const [selectedSubject, setSelectedSubject] = useState<string>("");
  const [themeTree, setThemeTree] = useState<ThemeNode[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [taskTotal, setTaskTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showAddSubject, setShowAddSubject] = useState(false);
  const [newSubjectName, setNewSubjectName] = useState("");
  const [showAddTask, setShowAddTask] = useState(false);
  const [selectedTheme, setSelectedTheme] = useState<string>("");
  const [expandedThemes, setExpandedThemes] = useState<Set<string>>(new Set());
  const [filterType, setFilterType] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    if (!hydrated) return;
    if (!auth.token || auth.role !== "TUTOR") {
      router.replace("/auth/login");
      return;
    }
    loadSubjects();
  }, [auth.token, hydrated]);

  const loadSubjects = async () => {
    try {
      const data = await api.getSubjects(auth.token!);
      setSubjects(data);
      if (data.length > 0 && !selectedSubject) {
        setSelectedSubject(data[0].id);
      }
    } catch {}
    setLoading(false);
  };

  const loadThemeTree = async (subjectId: string) => {
    try {
      const data = await api.getThemeTree(subjectId, auth.token!);
      setThemeTree(data.themes || []);
    } catch {}
  };

  const loadTasks = async (subjectId: string) => {
    try {
      const data = await api.listTasks({ subject_id: subjectId }, auth.token!);
      setTasks(data.tasks || []);
      setTaskTotal(data.total || 0);
    } catch {}
  };

  useEffect(() => {
    if (selectedSubject) {
      loadThemeTree(selectedSubject);
      loadTasksForSubject(selectedSubject);
    }
  }, [selectedSubject]);

  const loadTasksForSubject = async (subjectId: string) => {
    try {
      const data = await api.listTasks({ subject_id: subjectId }, auth.token!);
      setTasks(data.tasks || []);
      setTaskTotal(data.total || 0);
    } catch {}
  };

  const loadTasksForTheme = async (themeId: string) => {
    try {
      const data = await api.listTasks({ theme_id: themeId }, auth.token!);
      setTasks(data.tasks || []);
      setTaskTotal(data.total || 0);
    } catch {}
  };

  const handleThemeClick = (themeId: string) => {
    setSelectedTheme(themeId);
    loadTasksForTheme(themeId);
  };

  const handleAddSubject = async () => {
    if (!newSubjectName.trim()) {
      setError("Введите название предмета");
      return;
    }
    try {
      await api.createSubject(newSubjectName.trim(), auth.token!);
      setNewSubjectName("");
      setShowAddSubject(false);
      setSuccess("Предмет добавлен");
      loadSubjects();
      setTimeout(() => setSuccess(""), 3000);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const renderThemeTree = (nodes: ThemeNode[], depth = 0) => {
    return nodes.map((node) => {
      const hasChildren = node.children?.length > 0;
      const isExpanded = expandedThemes.has(node.id);
      const isSelected = selectedTheme === node.id;

      return (
        <div key={node.id} style={{ paddingLeft: depth * 1.25 + "rem" }}>
          <div
            onClick={() => handleThemeClick(node.id)}
            style={{
              padding: "0.4rem 0.5rem",
              borderRadius: "var(--radius)",
              cursor: "pointer",
              background: isSelected ? "var(--primary)" : "transparent",
              color: isSelected ? "white" : "var(--text)",
              display: "flex",
              alignItems: "center",
              gap: "0.35rem",
              fontSize: "0.85rem",
              transition: "background 0.15s",
            }}
            onMouseEnter={(e) => { if (!isSelected) e.currentTarget.style.background = "var(--bg)"; }}
            onMouseLeave={(e) => { if (!isSelected) e.currentTarget.style.background = "transparent"; }}
          >
            {hasChildren && (
              <span
                onClick={(e) => { e.stopPropagation(); toggleExpand(node.id); }}
                style={{ fontSize: "0.7rem", width: "1rem", textAlign: "center", userSelect: "none" }}
              >
                {isExpanded ? "▼" : "▶"}
              </span>
            )}
            {!hasChildren && <span style={{ width: "1rem" }} />}
            <span>
              {node.fipi_code ? `${node.fipi_code} ` : ""}{node.name}
            </span>
          </div>
          {hasChildren && isExpanded && renderThemeTree(node.children, depth + 1)}
        </div>
      );
    });
  };

  const toggleExpand = (id: string) => {
    setExpandedThemes((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  if (loading || !hydrated) return <div className="container" style={{ padding: "2rem" }}>Загрузка...</div>;

  return (
    <>
      <header className="header">
        <h1>Управление контентом</h1>
        <div style={{ display: "flex", gap: "1rem", alignItems: "center", flexWrap: "wrap" }}>
          <button
            className="btn btn-primary"
            style={{ background: "var(--success)" }}
            onClick={async () => {
              try {
                const res = await api.syncCodifier("История", auth.token!);
                setSuccess(`Синхронизация запущена (задача: ${res.task_id.slice(0, 8)}...)`);
              } catch (e: any) {
                setError(e.message);
              }
            }}
          >
            Синхронизировать кодификатор
          </button>
          <button
            className="btn btn-primary"
            style={{ background: "#3b82f6" }}
            onClick={async () => {
              const themeCode = prompt("Код темы для синхронизации (например: 8. или 4.):");
              if (!themeCode) return;
              try {
                const res = await api.syncTheme(themeCode, auth.token!);
                setSuccess(`Синхронизация темы ${themeCode} запущена (задача: ${res.task_id.slice(0, 8)}...)`);
              } catch (e: any) {
                setError(e.message);
              }
            }}
          >
            Синхронизировать тему
          </button>
          <button
            className="btn btn-primary"
            style={{ background: "#8b5cf6" }}
            onClick={async () => {
              if (!confirm("Синхронизировать ВЕСЬ предмет История? Это займёт время.")) return;
              try {
                const res = await api.syncSubject("История", auth.token!);
                setSuccess(`Синхронизация предмета запущена (задача: ${res.task_id.slice(0, 8)}...)`);
              } catch (e: any) {
                setError(e.message);
              }
            }}
          >
            Синхронизировать весь предмет
          </button>
          <Link href="/dashboard" className="btn btn-primary">Дашборд</Link>
          <button className="btn btn-danger" onClick={logout}>Выйти</button>
        </div>
      </header>
      <main className="container" style={{ padding: "2rem" }}>
        {error && (
          <div style={{ padding: "0.75rem 1rem", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: "var(--radius)", color: "var(--danger)", marginBottom: "1rem" }}>
            {error}
            <button onClick={() => setError("")} style={{ marginLeft: "0.5rem", background: "none", border: "none", cursor: "pointer", color: "var(--danger)" }}>✕</button>
          </div>
        )}
        {success && (
          <div style={{ padding: "0.75rem 1rem", background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: "var(--radius)", color: "var(--success)", marginBottom: "1rem" }}>
            {success}
          </div>
        )}

        {subjects.length === 0 && !showAddSubject ? (
          <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
            <h2 style={{ marginBottom: "1rem", color: "var(--text-secondary)" }}>Пока нет ни одного предмета</h2>
            <p style={{ color: "var(--text-secondary)", marginBottom: "1.5rem" }}>
              Добавьте предмет (например, «История» или «Обществознание»), чтобы начать наполнять базу заданий.
            </p>
            <button className="btn btn-primary" onClick={() => setShowAddSubject(true)}>
              Добавить первый предмет
            </button>
          </div>
        ) : (
          <div className="grid" style={{ gridTemplateColumns: "280px 1fr" }}>
            <div>
              <div className="card">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                  <h3>Предметы</h3>
                  <button className="btn btn-primary" style={{ fontSize: "0.75rem", padding: "0.25rem 0.5rem" }} onClick={() => setShowAddSubject(true)}>+</button>
                </div>
                {showAddSubject && (
                  <div style={{ marginBottom: "0.75rem" }}>
                    <input
                      value={newSubjectName}
                      onChange={(e) => setNewSubjectName(e.target.value)}
                      placeholder="Название предмета"
                      style={{ width: "100%", padding: "0.4rem", border: "1px solid var(--border)", borderRadius: "var(--radius)", fontSize: "0.875rem", marginBottom: "0.5rem" }}
                    />
                    <div style={{ display: "flex", gap: "0.25rem" }}>
                      <button className="btn btn-primary" style={{ fontSize: "0.75rem", flex: 1 }} onClick={handleAddSubject}>Добавить</button>
                      <button className="btn" style={{ fontSize: "0.75rem", background: "var(--border)" }} onClick={() => { setShowAddSubject(false); setNewSubjectName(""); }}>Отмена</button>
                    </div>
                  </div>
                )}
                {subjects.map((s) => (
                  <div
                    key={s.id}
                    onClick={() => setSelectedSubject(s.id)}
                    style={{
                      padding: "0.5rem 0.75rem",
                      borderRadius: "var(--radius)",
                      cursor: "pointer",
                      background: selectedSubject === s.id ? "var(--primary)" : "transparent",
                      color: selectedSubject === s.id ? "white" : "var(--text)",
                      marginBottom: "0.25rem",
                      fontSize: "0.875rem",
                    }}
                  >
                    {s.name}
                  </div>
                ))}
              </div>
            </div>

            <div>
              {selectedSubject && (
                <>
                  <div className="card" style={{ marginBottom: "1rem" }}>
                    <h3 style={{ marginBottom: "0.75rem" }}>Дерево тем</h3>
                    {themeTree.length === 0 ? (
                      <div className="empty-state" style={{ padding: "1.5rem" }}>
                        <p>Темы загружаются из банка заданий ФИПИ</p>
                      </div>
                    ) : (
                      renderThemeTree(themeTree)
                    )}
                  </div>

                  <div className="card">
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                      <h3>
                        Задания ({taskTotal})
                        {selectedTheme && (
                          <button
                            style={{ marginLeft: "0.5rem", fontSize: "0.75rem", background: "var(--border)", border: "none", borderRadius: "var(--radius)", padding: "0.15rem 0.5rem", cursor: "pointer", color: "var(--text-secondary)" }}
                            onClick={() => { setSelectedTheme(""); loadTasksForSubject(selectedSubject); }}
                          >
                            Показать все
                          </button>
                        )}
                      </h3>
                      <button className="btn btn-primary" style={{ fontSize: "0.75rem" }} onClick={() => setShowAddTask(true)}>Добавить задание</button>
                    </div>
                    <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.75rem", flexWrap: "wrap" }}>
                      <select value={filterType} onChange={(e) => setFilterType(e.target.value)} style={{ padding: "0.35rem", border: "1px solid var(--border)", borderRadius: "var(--radius)", fontSize: "0.8rem" }}>
                        <option value="">Все типы</option>
                        <option value="TEST">TEST</option>
                        <option value="ESSAY">ESSAY</option>
                      </select>
                      <button
                        className="btn"
                        style={{ fontSize: "0.75rem", background: "var(--border)" }}
                        onClick={() => {
                          const params: any = { subject_id: selectedSubject };
                          if (selectedTheme) params.theme_id = selectedTheme;
                          if (filterType) params.task_type = filterType;
                          api.listTasks(params, auth.token!).then((data) => { setTasks(data.tasks || []); setTaskTotal(data.total || 0); });
                        }}
                      >
                        Применить
                      </button>
                    </div>
                    {showAddTask && (
                      <AddTaskForm
                        subjectId={selectedSubject}
                        themes={themeTree}
                        token={auth.token!}
                        onCreated={() => {
                          setShowAddTask(false);
                          loadTasks(selectedSubject);
                          setSuccess("Задание добавлено");
                          setTimeout(() => setSuccess(""), 3000);
                        }}
                        onCancel={() => setShowAddTask(false)}
                        onError={setError}
                      />
                    )}
                    {tasks.length === 0 ? (
                      <div className="empty-state" style={{ padding: "1.5rem" }}>
                        <p>Заданий пока нет</p>
                        <button className="btn btn-primary" style={{ marginTop: "0.5rem" }} onClick={() => setShowAddTask(true)}>Добавить первое задание</button>
                      </div>
                    ) : (
                      <div style={{ maxHeight: 400, overflow: "auto" }}>
                        {tasks.map((t) => (
                          <div key={t.id} style={{ padding: "0.5rem 0", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <div>
                              <span className={`badge ${t.type === "TEST" ? "badge-info" : "badge-warning"}`} style={{ marginRight: "0.5rem" }}>
                                {t.type}
                              </span>
                              <span style={{ fontSize: "0.875rem" }}>{t.text_preview}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </main>
    </>
  );
}

function AddTaskForm({
  subjectId,
  themes,
  token,
  onCreated,
  onCancel,
  onError,
}: {
  subjectId: string;
  themes: ThemeNode[];
  token: string;
  onCreated: () => void;
  onCancel: () => void;
  onError: (msg: string) => void;
}) {
  const [taskType, setTaskType] = useState<"TEST" | "ESSAY">("TEST");
  const [themeId, setThemeId] = useState("");
  const [text, setText] = useState("");
  const [options, setOptions] = useState(["", ""]);
  const [answerType, setAnswerType] = useState("single_choice");
  const [correctAnswer, setCorrectAnswer] = useState("");
  const [criteria, setCriteria] = useState([{ name: "", max_score: 1 }]);
  const [examPosition, setExamPosition] = useState("");
  const [difficultyLevel, setDifficultyLevel] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!themeId) { onError("Выберите тему"); return; }
    if (!text.trim()) { onError("Введите текст задания"); return; }
    if (taskType === "TEST" && !correctAnswer.trim()) { onError("Укажите правильный ответ"); return; }
    if (taskType === "ESSAY" && criteria.every((c) => !c.name.trim())) { onError("Добавьте хотя бы один критерий"); return; }

    setSubmitting(true);
    try {
      const payload: any = {
        subject_id: subjectId,
        theme_id: themeId,
        type: taskType,
        text_content: { text: text.trim() },
      };
      if (examPosition) payload.exam_position = parseInt(examPosition);
      if (difficultyLevel) payload.difficulty_level = difficultyLevel;
      if (taskType === "TEST") {
        payload.text_content.options = options.filter((o) => o.trim());
        if (answerType === "single_choice") {
          payload.correct_answer_key = { type: "single_choice", correct_answer: parseInt(correctAnswer) || 1 };
        } else if (answerType === "multiple_choice") {
          payload.correct_answer_key = { type: "multiple_choice", correct_answer: correctAnswer.split(",").map((s) => parseInt(s.trim())).filter(Boolean) };
        } else {
          payload.correct_answer_key = { type: "short_answer", correct_answer: correctAnswer.trim() };
        }
      } else {
        payload.fipi_criteria = criteria.filter((c) => c.name.trim()).map((c, i) => ({
          id: `criterion_${i + 1}`,
          name: c.name.trim(),
          max_score: c.max_score,
        }));
      }
      await api.importTask(payload, token);
      onCreated();
    } catch (e: any) {
      onError(e.message);
    }
    setSubmitting(false);
  };

  const collectThemeIds = (nodes: ThemeNode[]): string[] => {
    let ids: string[] = [];
    for (const n of nodes) {
      ids.push(n.id);
      if (n.children) ids = ids.concat(collectThemeIds(n.children));
    }
    return ids;
  };

  return (
    <div className="card" style={{ marginBottom: "1rem", background: "var(--bg)" }}>
      <h4 style={{ marginBottom: "0.75rem" }}>Новое задание</h4>
      <div className="grid grid-2" style={{ gap: "0.75rem" }}>
        <div className="form-group">
          <label>Тип</label>
          <select value={taskType} onChange={(e) => setTaskType(e.target.value as any)}>
            <option value="TEST">TEST (тестовое)</option>
            <option value="ESSAY">ESSAY (развёрнутый)</option>
          </select>
        </div>
        <div className="form-group">
          <label>Тема</label>
          <select value={themeId} onChange={(e) => setThemeId(e.target.value)}>
            <option value="">Выберите тему</option>
            {collectThemeIds(themes).map((id) => {
              const findName = (nodes: ThemeNode[]): string | null => {
                for (const n of nodes) {
                  if (n.id === id) return n.fipi_code ? `${n.fipi_code} ${n.name}` : n.name;
                  if (n.children) { const r = findName(n.children); if (r) return r; }
                }
                return null;
              };
              return <option key={id} value={id}>{findName(themes)}</option>;
            })}
          </select>
        </div>
      </div>
      <div className="grid grid-2" style={{ gap: "0.75rem", marginTop: "0.75rem" }}>
        <div className="form-group">
          <label>Позиция ЕГЭ (1-21)</label>
          <select value={examPosition} onChange={(e) => setExamPosition(e.target.value)}>
            <option value="">Не указана</option>
            {Array.from({ length: 21 }, (_, i) => i + 1).map((n) => (
              <option key={n} value={n}>Задание {n}</option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label>Уровень сложности</label>
          <select value={difficultyLevel} onChange={(e) => setDifficultyLevel(e.target.value)}>
            <option value="">Не указан</option>
            <option value="Б">Б — базовый</option>
            <option value="П">П — повышенный</option>
            <option value="В">В — высокий</option>
          </select>
        </div>
      </div>
      <div className="form-group">
        <label>Текст задания</label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          style={{ width: "100%", minHeight: 80, padding: "0.5rem", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}
          placeholder="Введите текст задания..."
        />
      </div>

      {taskType === "TEST" && (
        <>
          <div className="form-group">
            <label>Формат ответа</label>
            <select value={answerType} onChange={(e) => setAnswerType(e.target.value)}>
              <option value="single_choice">Один вариант</option>
              <option value="multiple_choice">Несколько вариантов</option>
              <option value="short_answer">Краткий ответ</option>
            </select>
          </div>
          {answerType !== "short_answer" && (
            <div className="form-group">
              <label>Варианты ответов (по одному на строку)</label>
              {options.map((opt, i) => (
                <input
                  key={i}
                  value={opt}
                  onChange={(e) => {
                    const newOpts = [...options];
                    newOpts[i] = e.target.value;
                    setOptions(newOpts);
                  }}
                  placeholder={`Вариант ${i + 1}`}
                  style={{ width: "100%", padding: "0.4rem", border: "1px solid var(--border)", borderRadius: "var(--radius)", fontSize: "0.875rem", marginBottom: "0.25rem" }}
                />
              ))}
              <button
                className="btn"
                style={{ fontSize: "0.75rem", background: "var(--border)", marginTop: "0.25rem" }}
                onClick={() => setOptions([...options, ""])}
              >
                + вариант
              </button>
            </div>
          )}
          <div className="form-group">
            <label>Правильный ответ {answerType === "multiple_choice" ? "(номера через запятую)" : answerType === "single_choice" ? "(номер варианта)" : "(текст)"}</label>
            <input
              value={correctAnswer}
              onChange={(e) => setCorrectAnswer(e.target.value)}
              placeholder={answerType === "multiple_choice" ? "1, 3" : answerType === "single_choice" ? "1" : "Москва"}
              style={{ width: "100%", padding: "0.4rem", border: "1px solid var(--border)", borderRadius: "var(--radius)", fontSize: "0.875rem" }}
            />
          </div>
        </>
      )}

      {taskType === "ESSAY" && (
        <div className="form-group">
          <label>Критерии оценивания ФИПИ</label>
          {criteria.map((c, i) => (
            <div key={i} style={{ display: "flex", gap: "0.5rem", marginBottom: "0.25rem" }}>
              <input
                value={c.name}
                onChange={(e) => {
                  const newCrit = [...criteria];
                  newCrit[i].name = e.target.value;
                  setCriteria(newCrit);
                }}
                placeholder={`Критерий ${i + 1}`}
                style={{ flex: 1, padding: "0.4rem", border: "1px solid var(--border)", borderRadius: "var(--radius)", fontSize: "0.875rem" }}
              />
              <input
                type="number"
                min="1"
                value={c.max_score}
                onChange={(e) => {
                  const newCrit = [...criteria];
                  newCrit[i].max_score = parseInt(e.target.value) || 1;
                  setCriteria(newCrit);
                }}
                style={{ width: 60, padding: "0.4rem", border: "1px solid var(--border)", borderRadius: "var(--radius)", fontSize: "0.875rem" }}
              />
            </div>
          ))}
          <button
            className="btn"
            style={{ fontSize: "0.75rem", background: "var(--border)", marginTop: "0.25rem" }}
            onClick={() => setCriteria([...criteria, { name: "", max_score: 1 }])}
          >
            + критерий
          </button>
        </div>
      )}

      <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.75rem" }}>
        <button className="btn btn-success" onClick={handleSubmit} disabled={submitting}>
          {submitting ? "Сохранение..." : "Добавить задание"}
        </button>
        <button className="btn" style={{ background: "var(--border)" }} onClick={onCancel}>Отмена</button>
      </div>
    </div>
  );
}
