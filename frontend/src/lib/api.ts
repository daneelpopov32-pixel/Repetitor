const API_BASE = "/api/v1";

interface RequestOptions extends RequestInit {
  token?: string;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function request<T = any>(path: string, options: RequestOptions = {}): Promise<T> {
  const { token, ...fetchOptions } = options;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE}${path}`, { ...fetchOptions, headers });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return res.json() as any;
}

export const api = {
  register: (data: any) => request("/auth/register", { method: "POST", body: JSON.stringify(data) }),
  login: (data: any) => request("/auth/login", { method: "POST", body: JSON.stringify(data) }),

  getSubjects: (token: string) => request<any[]>("/themes/subjects", { token }),
  getThemeTree: (subjectId: string, token: string) =>
    request<any>(`/themes/tree?subject_id=${subjectId}`, { token }),
  getThemeTaskCounts: (subjectId: string, token: string) =>
    request<any[]>(`/themes/task-counts?subject_id=${subjectId}`, { token }),

  getTests: (params: Record<string, string>, token: string) => {
    const q = new URLSearchParams(params);
    return request<any[]>(`/tests?${q.toString()}`, { token });
  },
  getStudentTests: (token: string) =>
    request<any[]>("/tests/student", { token }),
  getTest: (testId: string, token: string) => request<any>(`/tests/${testId}`, { token }),
  deleteTest: (testId: string, token: string) =>
    request<any>(`/tests/${testId}`, { method: "DELETE", token }),
  removeTaskFromTest: (testId: string, taskId: string, token: string) =>
    request<any>(`/tests/${testId}/tasks/${taskId}`, { method: "DELETE", token }),
  replaceTask: (testId: string, taskId: string, newType: string, token: string) =>
    request<any>(`/tests/${testId}/tasks/${taskId}/replace?new_type=${newType}`, { method: "POST", token }),
  assignTestToStudents: (testId: string, studentIds: string[], token: string) =>
    request<any[]>(`/tests/${testId}/assign`, {
      method: "POST",
      body: JSON.stringify({ student_ids: studentIds }),
      token,
    }),
  getTutorStudents: (token: string) => request<any[]>("/analytics/tutor/students", { token }),
  createTest: (data: any, token: string) =>
    request<any>("/tests", { method: "POST", body: JSON.stringify(data), token }),

  startAttempt: (testId: string, token: string) =>
    request<any>(`/attempts/0/start?test_id=${testId}`, { method: "POST", token }),
  getAttempt: (attemptId: string, token: string) =>
    request<any>(`/attempts/${attemptId}`, { token }),
  getAttemptTasks: (attemptId: string, token: string) =>
    request<any>(`/attempts/${attemptId}/tasks`, { token }),
  saveAnswer: (attemptId: string, taskId: string, studentInput: string, token: string) =>
    request<any>(`/attempts/${attemptId}/answers/${taskId}`, {
      method: "PATCH",
      body: JSON.stringify({ student_input: studentInput }),
      token,
    }),
  submitAttempt: (attemptId: string, token: string) =>
    request<any>(`/attempts/${attemptId}/submit`, { method: "POST", token }),

  aiCheck: (taskId: string, studentAnswer: string, token: string) =>
    request<any>("/review/ai-check", {
      method: "POST",
      body: JSON.stringify({ task_id: taskId, student_answer: studentAnswer }),
      token,
    }),
  gradeAnswer: (answerId: string, scores: any, comment: string, token: string) =>
    request<any>("/review/grade", {
      method: "POST",
      body: JSON.stringify({ answer_id: answerId, scores, comment }),
      token,
    }),
  getReviewQueue: (token: string) => request<any[]>("/review/queue", { token }),

  getDashboard: (studentId: string, token: string) =>
    request<any>(`/analytics/dashboard?student_id=${studentId}`, { token }),

  generateInvitationCode: (expiresInDays: number, token: string) =>
    request<any>("/invitation-codes", {
      method: "POST",
      body: JSON.stringify({ expires_in_days: expiresInDays }),
      token,
    }),

  createSubject: (name: string, token: string) =>
    request<any>("/content/subjects", {
      method: "POST",
      body: JSON.stringify({ name }),
      token,
    }),
  createTheme: (data: { subject_id: string; parent_theme_id?: string; fipi_code?: string; name: string }, token: string) =>
    request<any>("/content/themes", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),
  importTask: (data: any, token: string) =>
    request<any>("/content/tasks/import", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),
  listTasks: (params: { subject_id?: string; theme_id?: string; task_type?: string }, token: string) => {
    const q = new URLSearchParams();
    if (params.subject_id) q.set("subject_id", params.subject_id);
    if (params.theme_id) q.set("theme_id", params.theme_id);
    if (params.task_type) q.set("task_type", params.task_type);
    return request<any[]>(`/content/tasks?${q.toString()}`, { token });
  },

  syncCodifier: (subjectName: string, token: string) =>
    request<any>("/fipi/sync-codifier", {
      method: "POST",
      body: JSON.stringify({ subject_name: subjectName }),
      token,
    }),
  createTestAsync: (data: { title: string; theme_codes: string[]; count_per_theme: number; task_type: string; time_limit_minutes?: number }, token: string) =>
    request<any>("/fipi/create-test", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),
  getTaskStatus: (taskId: string, token: string) =>
    request<any>(`/fipi/task-status/${taskId}`, { token }),
};
