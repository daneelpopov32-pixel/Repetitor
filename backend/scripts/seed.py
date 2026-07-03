"""
Seed script for filling the database with test data.
Run: python -m scripts.seed
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://repetitor:repetitor@localhost:5432/repetitor")

from app.database import engine, async_session
from app.models import (
    Tenant, User, Profile, Subject, Theme, Task, Test, TestTask, TestAssignment
)
from app.utils.security import hash_password
from datetime import datetime


async def seed():
    async with async_session() as db:
        tenant = Tenant(name="Demo Tenant")
        db.add(tenant)
        await db.flush()

        tutor = User(
            tenant_id=tenant.id,
            email="tutor@demo.com",
            password_hash=hash_password("demo123"),
            role="TUTOR",
        )
        db.add(tutor)
        await db.flush()
        db.add(Profile(
            user_id=tutor.id,
            first_name="Демо",
            last_name="Репетитор",
            consent_152fz_at=datetime.utcnow(),
        ))

        student = User(
            tenant_id=tenant.id,
            email="student@demo.com",
            password_hash=hash_password("demo123"),
            role="STUDENT",
        )
        db.add(student)
        await db.flush()
        db.add(Profile(
            user_id=student.id,
            first_name="Демо",
            last_name="Ученик",
            birth_date=datetime(2008, 5, 15).date(),
            consent_152fz_at=datetime.utcnow(),
        ))

        await db.flush()

        subj_history = Subject(name="История")
        subj_social = Subject(name="Обществознание")
        db.add_all([subj_history, subj_social])
        await db.flush()

        themes_history = [
            ("1", "Древний мир", [
                ("1.1", "Первобытное общество", [
                    ("1.1.1", "Охота и собирательство", []),
                    ("1.1.2", "Земледелие и скотоводство", []),
                ]),
                ("1.2", "Древний Египет", [
                    ("1.2.1", "Фараоны и пирамиды", []),
                    ("1.2.2", "Религия Древнего Египта", []),
                ]),
            ]),
            ("2", "Средние века", [
                ("2.1", "Византия", []),
                ("2.2", "Арабский халифат", []),
            ]),
        ]

        themes_social = [
            ("1", "Человек и общество", [
                ("1.1", "Понятие личности", []),
                ("1.2", "Общественные ценности", []),
            ]),
            ("2", "Политическая сфера", [
                ("2.1", "Формы правления", [
                    ("2.1.1", "Монархия", []),
                    ("2.1.2", "Республика", []),
                ]),
                ("2.2", "Политические партии", []),
            ]),
        ]

        async def create_themes(subject_id, theme_defs, parent_id=None):
            result = []
            for code, name, children in theme_defs:
                theme = Theme(
                    subject_id=subject_id,
                    parent_theme_id=parent_id,
                    fipi_code=code,
                    name=name,
                )
                db.add(theme)
                await db.flush()
                result.append(theme)
                if children:
                    child_themes = await create_themes(subject_id, children, theme.id)
                    result.extend(child_themes)
            return result

        h_themes = await create_themes(subj_history.id, themes_history)
        s_themes = await create_themes(subj_social.id, themes_social)

        all_themes = h_themes + s_themes

        test_tasks_data = [
            (subj_history.id, "1.1.1", "Кто из перечисленных учёных изучал первобытное общество?", ["Д.И. Менделеев", "В.О. Ключевский", "А.А. Валуев"], 2, "single_choice"),
            (subj_history.id, "1.2.1", "В какой стране расположены пирамиды?", ["Греция", "Египет", "Рим", "Китай"], 2, "single_choice"),
            (subj_history.id, "2.1", "В каком году пало Западная Римская империя?", [], 0, "short_answer"),
            (subj_history.id, "1.1.2", "Какие из перечисленных занятий были характерны для земледельцев?", ["Охота", "Скотоводство", "Земледелие", "Рыболовство"], [2, 3], "multiple_choice"),
            (subj_history.id, "2.2", "Назовите три последствия арабского завоевания.", [], 0, "essay"),
            (subj_social.id, "1.1", "Что такое социализация?", [], 0, "short_answer"),
            (subj_social.id, "1.2", "Какие ценности характерны для демократического общества?", ["Свобода", "Равенство", "Подчинение", "Справедливость"], [1, 2, 4], "multiple_choice"),
            (subj_social.id, "2.1.1", "Примером монархии является правление:", ["Президента", "Короля", "Премьер-министра"], 2, "single_choice"),
            (subj_social.id, "2.1.2", "В республике глава государства:", ["Назначается пожизненно", "Избирается населением", "Наследует трон"], 2, "single_choice"),
            (subj_social.id, "2.2", "Чем партии отличаются от движений?", [], 0, "essay"),
            (subj_history.id, "1.2.2", "Как назывался главный бог Древнего Египта?", [], 0, "short_answer"),
            (subj_history.id, "1.1.1", "Период неолита характеризуется:", ["Использованием металлов", "Земледелием", "Ледниковым периодом", "Появлением письменности"], 2, "single_choice"),
            (subj_social.id, "1.1", "Какие факторы влияют на формирование личности?", ["Генетика", "Семья", "Образование", "Погода"], [1, 2, 3], "multiple_choice"),
            (subj_history.id, "2.1", "Опишите причины падения Римской империи.", [], 0, "essay"),
            (subj_social.id, "2.1.1", "В какой стране сейчас действует монархия?", ["Франция", "Япония", "Германия", "Италия"], 2, "single_choice"),
        ]

        theme_name_map = {t.fipi_code: t.id for t in all_themes}

        essay_criteria = [
            {"id": "criterion_1", "name": "Правильность утверждения", "max_score": 1},
            {"id": "criterion_2", "name": "Аргументация", "max_score": 2},
            {"id": "criterion_3", "name": "Использование терминов", "max_score": 1},
        ]

        tasks = []
        for subj_id, theme_code, text, options, correct, qtype in test_tasks_data:
            theme_id = theme_name_map.get(theme_code)
            if not theme_id:
                continue

            text_content = {"text": text}
            correct_answer_key = None
            fipi_criteria = None

            if qtype == "essay":
                task_type = "ESSAY"
                fipi_criteria = essay_criteria
            else:
                task_type = "TEST"
                if options:
                    text_content["options"] = options
                if qtype == "multiple_choice":
                    correct_answer_key = {"type": "multiple_choice", "correct_answer": correct}
                elif qtype == "single_choice":
                    correct_answer_key = {"type": "single_choice", "correct_answer": correct}
                else:
                    correct_answer_key = {"type": "short_answer", "correct_answer": "римляне" if "Римская" in text else "Ра" if "бог" in text else "период"}

            task = Task(
                subject_id=subj_id,
                theme_id=theme_id,
                type=task_type,
                text_content=text_content,
                correct_answer_key=correct_answer_key,
                fipi_criteria=fipi_criteria,
            )
            db.add(task)
            tasks.append(task)

        await db.flush()

        test = Test(
            tutor_id=tutor.id,
            title="Демо-тест по Истории",
            time_limit_minutes=30,
        )
        db.add(test)
        await db.flush()

        for i, task in enumerate(tasks[:8]):
            db.add(TestTask(test_id=test.id, task_id=task.id, order_number=i + 1))

        db.add(TestAssignment(test_id=test.id, student_id=student.id))

        await db.commit()
        print(f"Seed complete!")
        print(f"  Tenant: {tenant.name}")
        print(f"  Tutor: tutor@demo.com / demo123")
        print(f"  Student: student@demo.com / demo123")
        print(f"  Subjects: 2 (История, Обществознание)")
        print(f"  Themes: {len(all_themes)}")
        print(f"  Tasks: {len(tasks)}")
        print(f"  Test: {test.title} ({len(tasks[:8])} tasks)")


if __name__ == "__main__":
    asyncio.run(seed())
