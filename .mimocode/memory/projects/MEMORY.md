# Project memory
_Durable project-level knowledge. Persists across all sessions in this project. Edit only content under italic instructions._

## Project context
_What is this project? What's its goal? High-level identity._

"Репетитор" (Tutor) — a FIPI (ФИПИ) test bank builder and progress analytics platform for tutors and students. First user: one history/social studies tutor. MVP is a closed prototype.

**Goal:** Automate the routine work of tutors — searching FIPI question banks, assembling test variants, auto-grading multiple-choice parts, AI-assisted essay review, and progress tracking dashboards.

**Users:** Tutor (creates tests, assigns to students, reviews essays, views analytics) and Student (registers via invitation code, takes tests with auto-save, views results). Parent role excluded from MVP.

## Rules
_Hard constraints from user that every session must respect._

- **Language**: Always respond to the user in Russian. Code, comments, and technical terms remain in English.
- **TDD mandatory**: RED (write failing tests first) → GREEN (minimal passing code) → REFACTOR.
- **Toolchain order** (every code task): (1) `ruff check --fix .` → (2) `semgrep --config .semgrep/rules.yaml .` (local rules only, NEVER `--config auto` or `p/python`) → (3) `trufflehog filesystem . --only-verified` → (4) code execution via `python C:\Users\Si-N-46\.mimocode\e2b_run.py "command"` → (5) `ast-grep` for renames across 2+ files.
- **Infrastructure files immutable**: `e2b_run.py`, `.mimorules`, `.semgrep/`, `.semgrepignore` — never read, edit, fix, recreate, copy, or move. If `e2b_run.py` fails with infrastructure error: output "INFRASTRUCTURE_ERROR: <details>" and STOP. Never fall back to local execution.
- **No internet-dependent semgrep**: Never use `--config auto` or `p/python`.
- **tests/conftest.py**: If tests import from project root, always create conftest.py adding root to sys.path.
- **No code presented** until all 5 toolchain steps pass.
- **Mandatory UI verification after form changes**: Any change to form fields (frontend or backend schema) MUST be verified through the real UI, not just Swagger/API. The consent/consent_152fz regression (2026-07-07) proved that API-level testing alone misses frontend-specific field name mismatches.

## Architecture decisions
_Major design choices with rationale. The "why" matters more than the "what" for future sessions._

- **Modular Monolith** (not microservices) — allows seamless extraction of domains into separate services later without rewriting business logic. Five domains: IAM, Content (FIPI), Examination, Review & AI, Analytics.
- **FastAPI** — native async (important for GigaChat integration), auto-generated OpenAPI, strong Python ecosystem for text/parsing.
- **Next.js** — SSR for future SEO, good state management for complex test-taking UI with auto-save.
- **PostgreSQL** — relational model + JSONB for flexible task content/criteria storage + transactional integrity.
- **Redis + Celery/RabbitMQ** — cache/sessions + background jobs (FIPI parsing, PDF generation, scheduler for expired attempts). GigaChat requests are synchronous in MVP.
- **GigaChat API (REST)** — AI for essay review suggestions (not autonomous grading). Synchronous with 30s timeout in MVP.
- **Last-Write-Wins** for auto-save (no conflict resolution, client timestamps ignored).
- **Hybrid timer** — server stores `started_at` + `time_limit` + `server_time`; frontend ticks locally for UX; backend validates on every save/submit.
- **UUID PKs everywhere** — prepared for future multi-tenancy (tenant_id on key tables).
- **JSONB for content** — `tasks.text_content`, `correct_answer_key`, `fipi_criteria` all stored as JSONB.
- **152-ФЗ compliance**: consent checkbox at registration, no age verification in MVP (management decision), data on Russian servers only, no self-service deletion in MVP.
- **Parent role excluded from MVP** — table `student_parent` created as placeholder, API deferred to post-MVP.
- **FIPI parser is high-risk** — HTML parsing is fragile; manual import fallback needed; parser "freezed" once stable.
- **Image sync integrated**: `_sync_images_from_full_list()` called as final step in `sync_subject_full()` (NOT `_sync_theme_core()` — more efficient: one full list scan after all themes). Manual UI button and Celery task `sync_images_full_list` still available for standalone use.
- **Subject/theme separation**: Separate codifier dicts per subject — `CODIFIER_THEMES_HISTORY` (1-12, 40 entries) and `CODIFIER_THEMES_SOCIAL` (1-6, fabricated). `SUBJECT_CODIFIERS` dict maps subject name → codifier. This prevents History from containing Geography/Law themes.
- **FIPI counts caching**: `GET /themes/fipi-counts` fetches real counts from FIPI on first request, caches in-memory for 1 hour. Returns `{theme_id, fipi_code, name, test_count, essay_count}`.
- **Progress calculation**: `_calc_student_progress()` uses latest attempt's answers with non-empty `student_input`. `progress_percent = (answers_with_nonempty_input / total_tasks) * 100`.
- **Frontend redesign plan-first**: User requires design plan approval before coding. Two key screens (test creation + test taking) implemented and approved before scaling to all 11 pages. E2E regression testing mandatory after each screen group.
- **"Archivist's Desk" frontend palette**: Warm tones — `--c-primary: #1a1a2e` (ink), `--c-accent: #c9a96e` (gold), `--c-bg: #f8f6f0` (parchment), `--c-success: #4a7c59` (forest green), `--c-danger: #b44a4a` (brick red). Chosen over cold zinc/monochrome for product differentiation. Plan file: `.mimocode/plans/1783478872353-proud-squid.md`.
- **Source Card signature element**: First-class CSS component for displaying inherited source text. Left gold border, warm tint background, uppercase "ИСТОЧНИК" label. Used on test-taking, review, and content preview screens. Unique to this product — no generic SaaS has this.
- **Calm timer for students**: Timer as pill badge (not aggressive countdown). Normal: muted, Warning (<5min): gold accent, Critical (<1min): danger. Never red by default. Reduces exam anxiety.

## Discovered durable knowledge
_Cross-task facts that survive across sessions. Promoted from session checkpoints' §7 when proven durable._

- **Data model**: ~14 tables: tenants, users, profiles, tutor_student, student_parent, invitation_codes, subjects, themes, tasks, tests, test_tasks, test_assignments, attempts, answers.
- **API contracts**: 13 endpoints defined (register, login, themes tree, create test, assign test, attempt get, attempt tasks, auto-save PATCH, submit, AI check, manual grade, dashboard, invitation codes).
- **Task types**: TEST (auto-graded by keys, supports single_choice, multiple_choice, short_answer, match, sequence) and ESSAY (AI-assisted, manually graded by rubric).
- **Reattempt logic**: New attempts created for retests; `test_assignments` stays COMPLETED after first submission.
- **Analytics**: All attempts count (retests included). Per-theme: trend (first vs last), average, attempt count. Dashboard returns max_score per day when multiple attempts on same day. Empty state for students with no data.
- **Unassign endpoint created**: `DELETE /{test_id}/assignments/{student_id}` removes TestAssignment record.
- **FIPI counts endpoint created**: `GET /themes/fipi-counts?subject_id=` — fetches real counts from FIPI, caches 1h in-memory.
- **FIPI project IDs**: EGE History: `068A227D253BA6C04D0C832387FD0D89` (on `ege.fipi.ru`). OGE History: `3CBBE97571208D9140697A6C2ABE91A0` (on `oge.fipi.ru`). Different banks, different project IDs. Other subjects need different IDs.
- **Progress formula**: `progress_percent = (answers_with_nonempty_input / total_tasks) * 100`. Based on latest attempt.
- **Student answers endpoint**: `GET /{test_id}/assignments/{student_id}/answers` returns task list with student_input, auto_score, manual_score, ai_feedback.
- **`getAttemptTasks` schema gap**: `TaskListItem` (in `app/schemas/attempt.py`) only has `task_id, order_number, type, text_content` — no `student_input`. Attempt page reads `t.text_content?.student_input` which is always undefined. Must extend schema or add answers endpoint to support re-entry.
- **API method naming mismatches (2026-07-06)**: Backend API methods don't always match frontend `api.ts` exports. Key mismatches found during frontend redesign: `getStudents` → `getTutorStudents`, `assignTest` → `assignTestToStudents`, `unassignTest` → `unassignStudent`, `generateInvitationCode` requires `(expiresInDays, token)` not just `(token)`. `listTasks` returns `{total, tasks}` object, not `any[]`.
- See MEMORY-fipi-parsing.md (24 entries) — FIPI sync bugs, pagesize bug, Celery issues, DB cascades, dedup rules
- See MEMORY-fipi-images.md (19 entries) — ShowPicture/Playwright investigation, URL patterns, image extraction findings
- **Type 6 may be TEST, not essay.** User suspects real Type 6 (checkboxes with digits) should have type=TEST. Current code only searches in essay section. Verification pending.
- **Types 11 and 12 still empty.** Map+text and map+judgments patterns not matching any tasks. May need additional structural patterns.
- **800 null tasks (22.7%)** — all are essays without structural markers. User wants repeating-pattern analysis (Task 25).
- **All 21 positions must be non-zero.** User explicitly requires complete coverage. Types 12 and 16 must be fixed even if counts are small.
- See MEMORY-kim-history.md (22 entries) — superseded distribution snapshots, completed classifier fixes, dead code removals, git history
- See MEMORY-kim-history.md (additional) — completed Task 26 classifier fixes, FIPI parser architecture, image URL patterns, golden fixtures, full backfill distribution
- See MEMORY-frontend-fipi-history.md (17 entries) — completed frontend redesign/audit, FIPI image investigation history, task dedup history, coverage snapshots
- **Tasks table schema**: No `created_at` column. Columns: id, subject_id, theme_id, type, text_content, correct_answer_key, fipi_criteria, source_url, metadata, exam_position, difficulty_level.
- **Image dedup on re-run verified**: Two layers: (1) `download_task_images()` skips files when `local_path.exists()` — file-level dedup; (2) `_sync_images_from_full_list()` compares `existing_nonempty == new_nonempty` — content-based dedup. No duplication on re-run; updates only when images actually change.
- **KNOWN ISSUES — images (2026-07-07)**:
  1. **Контекстные картинки не всегда привязываются**: Задания, которые должны иметь общую картинку от блока-предшественника, иногда остаются без неё. Причина: stateful-проход зависит от порядка qblock'ов в HTML, а FIPI может возвращать другой порядок при разных запросах.
  2. **Двойные картинки**: Некоторые задания получают 2+ изображения, хотя должны иметь одну. Причина: накопление `shared_images` из нескольких standalone-блоков вместо замены текущей контекстной картинки.
  3. **Позиция 12 (суждения + схема)**: 1.4% покрытия в БД (1 из 73). Причина: GUID-матчинг между полным списком FIPI и тематическим списком далёкий от полного (9 из 73 совпали). Задания в БД имеют другие GUID, чем в полном списке.
  4. **✅ Форматирование заданий на установление соответствий FIXED (2026-07-09)**: CSS classes added with word-wrap, table-layout:fixed, mobile responsive stacking. Applied to attempt page and test detail page.
- **✅ Matching task overflow FIXED (2026-07-09)**: CSS classes `.matching-grid`, `.matching-item`, `.matching-answer-grid` added to globals.css. `word-wrap: break-word` on items, `table-layout: fixed` on answer grid, mobile breakpoint at 640px stacks columns. Applied to both attempt page and test detail page. Build passes. Verification screenshots pending.
- **Docker compose needs `-p` flag**: `docker compose -p repetitor up -d db` when run from root dir.
- **DB URL for local scripts**: Override `DATABASE_URL_SYNC` env var to `postgresql+psycopg2://repetitor:repetitor@localhost:5432/repetitor` (`.env` uses Docker-internal `db` hostname).
- **DB column name**: Tasks table column is `metadata` (NOT `metadata_`). Prior session scripts used wrong name — may have caused silent failures.
- **Current DB state (2026-07-08)**: 1518 History tasks, 681 Social Studies tasks, 2199 total. Prior 3380 was intermediate; text_hash dedup after resync brought it to 1518.
- **Source text MUST be stored separately from task text**: Prepending source text to `task["text"]` breaks `_detect_task_type()` and matching detection. Store in `task["source_text"]` / `text_content.source_text` as a dedicated field. Frontend reads it directly via `text_content.source_text`.
- **`jsonb_array_length` doesn't exist in PostgreSQL**: Use `(column)::jsonb` cast before calling jsonb functions, or use `jsonb_array_length()` with proper casting.
- **User trusts FIPI as authoritative source**: User corrected agent — "на ФИПИ не может такой ситуации быть" — images on FIPI are always correct for their task. Wrong images in our DB come from our sync bugs, not FIPI errors.
- **Never overwrite images on download failure**: `fipi_urls` always stored; `images` only updated when `download_task_images()` succeeds. Prevents losing existing images when FIPI returns 404.
- **GitHub remote configured**: `origin` → `https://github.com/daneelpopov32-pixel/Repetitor.git`, branch `master`.
- **Matching task CSS pattern**: Use CSS classes (`.matching-grid`, `.matching-item`, `.matching-answer-grid`) instead of inline styles for matching task layout. Key properties: `word-wrap: break-word`, `overflow-wrap: break-word`, `table-layout: fixed`, `width: 100%`. Mobile breakpoint at 640px stacks columns.
- **FIPI matching tasks embed uppercase column names**: Instruction text ends with two uppercase groups (e.g., "ПАМЯТНИКИ КУЛЬТУРЫ ХАРАКТЕРИСТИКИ"). Left group = left column header, right group = right column header. `getFipiHeaders()` extracts them; `getInstruction()` strips them from instruction text. Always use extracted FIPI names as column headers (fallback to "Левый столбец"/"Правый столбец" if extraction fails).
- **Image flicker fix**: `<motion.div>` without `key` causes React to reuse DOM element when task changes — `<img>` src changes cause brief un-paint. Fix: `key={task.task_id}` forces clean unmount/remount. Also use `key={imgPath}` (not `key={i}`) for image containers within a task.
- **User trusts FIPI as authoritative — never blame FIPI for our bugs**: User corrected agent when it claimed "FIPI limitation" for task `3443603a` simply saved without GUID. "Да нет никакого ограничения, ты просто записал его в базу без GUID." Always check DB entry completeness before blaming FIPI.
- **Image lightbox pattern**: Simple click-to-expand centered on screen, Escape/click-overlay to close. No +/- zoom buttons needed. Full-screen overlay with `position: fixed, inset: 0, background: rgba(0,0,0,0.85)`.
- **Image coverage 100% confirmed for positions 8-12, 16**: All 314 tasks across these 6 positions have images. Task `3443603a` fixed by copying image from identical task `eb0cd075` in same theme.
- **Duplicate GUID groups caused false 100% coverage**: 551 duplicate groups, 1073 extra rows. Audit saw unique GUIDs (100%), generator picked random rows including shadows without images. Dedup via `DISTINCT ON (metadata->>'fipi_guid')` keeps best copy.
- **Post-dedup DB state**: 1595 unique tasks (was 2668). All positions 8-12,16 at 100% coverage. Zero remaining duplicates by GUID.
- **Dedup SQL pattern**: `DISTINCT ON (metadata->>'fipi_guid') ORDER BY guid, (has_images), (has_fipi_urls), id` — keeps best copy. Must delete answers → test_tasks → tasks in FK order.
- **Frontend/DB image mismatch possible**: DB shows images for tasks that frontend renders without. Check actual image files on disk vs DB paths when investigating.
- See MEMORY-fipi-sync-details.md (30 entries) — ShowPicture variants, GUID mismatch investigation, text_hash sync, completed bug fixes, files_location, image scenarios, distribution history
- **Backend field naming mismatch**: Frontend `tests/page.tsx` used `a.score` but backend `_calc_student_progress()` returns `progress_percent`. Always cross-check API response field names when UI data doesn't render.
- **getTutorStudents returns student objects, not dashboard**: `/analytics/tutor/students` was returning dashboard summaries with `student_id` field. Fixed to return `{id, email, first_name, last_name}` from User+Profile tables. Frontend modal needs `id` for checkbox keys.
- **Student role guard on tests page**: Tests page (`/tests`) must guard against non-TUTOR roles early (before render), not just in useEffect. Without guard, students see TUTOR UI for ~5s before redirect.
- **Attempt page duplicate answer inputs**: Lines 236-243 (textarea for non-option tasks) and 268-274 (text input for all non-matching) both render simultaneously. Need mutual exclusion.
- **✅ Attempt page radio/checkbox FIXED (2026-07-09)**: Tasks with options now show clickable radio buttons (single choice) or checkboxes (multiple choice) instead of static text + text input. `answer_type` field added to backend `get_attempt_tasks` response (extracted from `correct_answer_key.type`). Free text input only shows for tasks without options.
- **Progress bar field name**: Backend `_calc_student_progress()` returns `progress_percent` spread into assignment dicts via `**progress`. Frontend reads `(a.progress_percent ?? a.score)`. If progress bar shows 0%, check whether student has actually saved any answers (non-empty `student_input`).
- **VPS deployment (2026-07-09)**: Server at 95.163.153.112 (Ubuntu 24.04, 2GB RAM, 30GB NVMe, VIEs-1 tarif ₽593/month, valid until 04.08.2026). Domain kimstudy.ru bought on Aeza. Deploy script: `deploy.sh` at project root with Docker, Nginx, docker-compose.prod.yml, certbot.
- **Windows SSH cannot pipe passwords**: OpenSSH for Windows exists but bash tool cannot pass passwords to interactive SSH prompts. Workaround: user runs commands on server manually.
- **DNS propagation for .ru domains**: Use `nslookup kimstudy.ru 8.8.8.8` to check external propagation vs local ISP cache. RIPN nameservers respond quickly but A records may take minutes to hours.
- **Heredoc variable expansion on server**: When sending shell commands to user for manual execution, heredocs with `$host`, `$remote_addr` etc. will expand to empty strings if quotes are lost. Use `\$` escapes or `printf`/`tee` for configs with shell variables. Always warn user about this.
- **deploy.sh must be in git**: Script created locally but never pushed — user cloned repo and it wasn't there. Always commit deploy scripts.
- **Docker daemon may fail on fresh Ubuntu 24.04 VPS**: `systemctl start docker` can fail. Debug with `journalctl -xeu docker.service`. May need to remove snap docker or fix iptables.
