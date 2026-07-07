# Аудит фронтенда: интерактивные элементы vs эндпоинты

## Найденные баги (9 штук)

### 1. [CRITICAL] Register: consent → consent_152fz
- **Где**: `src/app/auth/register/page.tsx:32` → `api.register({consent: true})`
- **Что**: Бэкенд `RegisterRequest` ждёт поле `consent_152fz: bool`, фронт шлёт `consent: true`
- **Результат**: Каждая регистрация падает с 422
- **Фикс**: В register/page.tsx заменить `consent: form.consent` на `consent_152fz: form.consent`

### 2. [CRITICAL] Tests list: t.id vs t.test_id
- **Где**: `src/app/tests/page.tsx` — строки 136-151 (expand, assign, delete, navigate)
- **Что**: Бэкенд `list_tests` возвращает `{test_id: "..."}`, фронт читает `t.id`
- **Результат**: Expand карточки, назначение, удаление, переход к деталям — ничего не работает
- **Фикс**: Заменить все `t.id` → `t.test_id` на странице tests/page.tsx

### 3. [CRITICAL] Student Dashboard: поля ответа не совпадают
- **Где**: `src/app/dashboard/page.tsx:137-158` (StudentDashboard)
- **Что**: Бэкенд `get_student_tests` возвращает `{assignment_status, attempt_status, tasks_count}`, фронт читает `{status, score, task_count}`
- **Результат**: Статус всегда пустой, балл undefined, количество заданий 0
- **Фикс**: Исправить чтение полей: `t.attempt_status || t.assignment_status`, убрать `score`, `t.tasks_count`

### 4. [CRITICAL] Sidebar (Student): ссылка /tests — Tutor-страница
- **Где**: `src/components/layout/Sidebar.tsx:15`
- **Что**: STUDENT_LINKS ведёт на `/tests` — это страница репетитора, которая редиректит студентов на логин
- **Результат**: Студент не может зайти в "Мои тесты"
- **Фикс**: Либо создать отдельную страницу `/my-tests` для студента, либо сделать `/tests`универсальной (проверять роль)

### 5. [HIGH] Review: selected.id vs selected.answer_id
- **Где**: `src/app/review/page.tsx:46`
- **Что**: `gradeAnswer(selected.id, ...)` — в объекте из `getReviewQueue` поле называется `answer_id`, не `id`
- **Результат**: Оценка не сохраняется (отправляется undefined answer_id)
- **Фикс**: `selected.answer_id` вместо `selected.id`

### 6. [HIGH] Content: text_content.text vs text_preview
- **Где**: `src/app/content/page.tsx:203`
- **Что**: Бэкенд `list_tasks` возвращает `text_preview` (строка), фронт лезет в `t.text_content?.text`
- **Результат**: Список заданий показывает пустой текст
- **Фикс**: `t.text_preview` вместо `t.text_content?.text`; добавить `exam_position` в ответ бэкенда

### 7. [HIGH] Attempt: старые ответы не загружаются
- **Где**: `src/app/tests/[id]/attempt/page.tsx:49`
- **Что**: `t.text_content?.student_input` — поля `student_input` нет в `TaskListItem` схеме
- **Результат**: При возврате к незавершённому тесту все ответы стираются
- **Фикс**: Загружать ответы отдельным запросом (или добавить поле в `TaskListItem`)

### 8. [MEDIUM] Dashboard: generateCode без try/catch
- **Где**: `src/app/dashboard/page.tsx:30-33`
- **Что**: `await api.generateInvitationCode(30, token)` без обёртки
- **Результат**: Ошибка сети → unhandled promise rejection
- **Фикс**: Обернуть в try/catch

### 9. [LOW] Auth: <a> вместо <Link>
- **Где**: register/page.tsx:91, login/page.tsx (ссылка на регистрацию)
- **Что**: Используется `<a href>` вместо `<Link>` из Next.js
- **Результат**: Полная перезагрузка страницы, потеря SPA-состояния
- **Фикс**: Заменить на `import Link from "next/link"`

---

## Эндпоинты которые существуют но не используются фронтендом

| api.ts функция | Эндпоинт | Статус |
|---|---|---|
| `getThemeTaskCounts` | GET `/themes/task-counts` | Определена, нигде не вызывается |
| `getTestAssignments` | GET `/tests/{id}/assignments` | Определена, нигде не вызывается |
| `getDashboard` | GET `/analytics/dashboard` | Определена, нигде не вызывается |
| `createTheme` | POST `/content/themes` | Определена, нигде не вызывается |
| `importTask` | POST `/content/tasks/import` | Определена, нигде не вызывается |
| `getSyncStatus` | GET `/fipi/sync-status` | Определена, нигде не вызывается |
| `replaceTask` | POST `/tests/{id}/tasks/{id}/replace` | Определена, нигде не вызывается |

---

## Страницы без проблем

| Страница | Статус |
|---|---|
| `/auth/login` | OK (кроме <a> вместо <Link>) |
| `/tests/new` | OK — все вызовы корректны (createTestAsync, getTaskStatus, generateEGE, getSubjects, getThemeTree, getFipiCounts) |
| `/tests/[id]` | OK — getTest, deleteTest, removeTaskFromTest работают корректно |
| `/tests/[id]/attempt` | OK — getAttempt, getAttemptTasks, saveAnswer, submitAttempt работают (кроме бага #7 с загрузкой ответов) |
| Sidebar (Tutor) | OK — навигация через router.push |
