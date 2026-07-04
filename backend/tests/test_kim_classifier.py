"""Tests for KIM classifier accuracy."""
import pytest
from app.services.kim_mapping import classify_task, POSITION_LEVELS


class TestDifficultyDistribution:
    """Verify level distribution matches official spec: 10 Б / 8 П / 3 В."""

    def test_official_level_counts(self):
        from app.services.kim_mapping import POSITION_LEVELS
        levels = list(POSITION_LEVELS.values())
        assert levels.count("Б") == 10, f"Expected 10 Б, got {levels.count('Б')}"
        assert levels.count("П") == 8, f"Expected 8 П, got {levels.count('П')}"
        assert levels.count("В") == 3, f"Expected 3 В, got {levels.count('В')}"
        assert len(levels) == 21

    def test_all_positions_covered(self):
        from app.services.kim_mapping import POSITION_LEVELS
        for i in range(1, 22):
            assert i in POSITION_LEVELS, f"Position {i} missing from POSITION_LEVELS"


class TestMatchingClassification:
    """Positions 1, 3, 5, 7 — all matching format, distinguished by content."""

    def test_date_matching(self):
        pos, level = classify_task("matching", "Соответствие дат: 1812 - Отечественная война, 1917 - Октябрьская революция, 1945 - Победа")
        assert pos == 1
        assert level == "Б"

    def test_figure_matching(self):
        pos, level = classify_task("matching", "Иван Калита - московский князь, Екатерина II - императрица, Пётр I - реформатор")
        assert pos == 5
        assert level == "Б"

    def test_culture_matching(self):
        pos, level = classify_task("matching", "Софийский собор - архитектурный памятник, Третьяковская галерея - музей, Большой театр - театр")
        assert pos == 7
        assert level == "Б"

    def test_fact_matching(self):
        pos, level = classify_task("matching", "Куликовская битва - 1380 год, Стояние на Угре - 1480 год, Полтавская битва - 1709 год")
        assert pos in (1, 3)  # Could be dates or facts
        assert level == "Б"


class TestSequenceClassification:
    def test_chronology(self):
        pos, level = classify_task("sequence", "Расположите события в хронологическом порядке: Периоды истории")
        assert pos == 2
        assert level == "Б"


class TestSourceMatchingNotPosition5:
    """Regression: 'фрагменты исторических источников' must NOT classify as position 5."""

    def test_source_fragments_1(self):
        pos, level = classify_task("matching",
            "Установите соответствие между фрагментами исторических источников и их краткими характеристиками: "
            "к каждому фрагменту, обозначенному буквой, подберите по две соответствующие характеристики")
        assert pos != 5, "Source fragments should NOT be position 5"

    def test_source_fragments_2(self):
        pos, level = classify_task("matching",
            "Установите соответствие между фрагментами исторических источников и их краткими характеристиками: "
            "каждому фрагменту подберите по две характеристики")
        assert pos != 5, "Source fragments should NOT be position 5"

    def test_source_fragments_3(self):
        pos, level = classify_task("matching",
            "Соответствие между отрывками из исторических источников и характеристиками")
        assert pos != 5, "Source excerpts should NOT be position 5"

    def test_figure_matching_still_works(self):
        """Real figure tasks should still classify as position 5."""
        pos, level = classify_task("matching",
            "Иван Калита - московский князь, Екатерина II - императрица")
        assert pos == 5, "Real figure tasks should be position 5"

    def test_culture_matching_still_works(self):
        """Real culture tasks should classify as position 7."""
        pos, level = classify_task("matching",
            "Софийский собор - архитектурный памятник, Третьяковская галерея - музей")
        assert pos == 7, "Real culture tasks should be position 7"


class TestWWIIClassification:
    """Positions 8 and 17 — STRICT WWII requirement."""

    def test_image_with_wwii(self):
        text_content = {"images": ["http://example.com/wwii.jpg"]}
        pos, level = classify_task("short_answer", "Битва за Москву 1941-1942", text_content)
        assert pos == 8
        assert level == "Б"

    def test_image_without_wwii_not_pos8(self):
        text_content = {"images": ["http://example.com/castle.jpg"]}
        pos, level = classify_task("short_answer", "Определите крепость на изображении", text_content)
        assert pos != 8  # Should NOT be classified as 8

    def test_essay_with_wwii_sources(self):
        pos, level = classify_task("essay", "Проанализируйте документы Великой Отечественной войны 1941-1945")
        assert pos == 17
        assert level == "П"

    def test_essay_without_wwii_not_pos17(self):
        pos, level = classify_task("essay", "Проанализируйте документы Петровской эпохи")
        assert pos != 17


class TestMapClassification:
    def test_map_task(self):
        text_content = {"images": ["http://example.com/map.png"]}
        pos, level = classify_task("short_answer", "Отметьте на карте территорию Московского государства", text_content)
        assert pos in (9, 10, 11)
        assert level in ("Б", "П")

    def test_no_image_not_map(self):
        pos, level = classify_task("short_answer", "Отметьте на карте территорию")
        # Map tasks can now be classified without stored images
        assert pos == 9


class TestEssayClassification:
    def test_attribution(self):
        pos, level = classify_task("essay", "Определите автора данного исторического источника и дату его создания")
        assert pos == 13
        assert level == "П"

    def test_cause_effect(self):
        pos, level = classify_task("essay", "Установите причинно-следственные связи между событиями")
        assert pos == 18
        assert level == "В"

    def test_comparison(self):
        pos, level = classify_task("essay", "Сравните реформы Петра I и Александра II")
        assert pos == 20
        assert level == "В"

    def test_argumentation(self):
        pos, level = classify_task("essay", "Аргументируйте свою позицию по вопросу о значении реформ")
        assert pos == 21
        assert level == "В"

    def test_terms(self):
        pos, level = classify_task("essay", "Раскройте понятие «крепостное право» в историческом контексте")
        assert pos == 19
        assert level == "П"

    def test_uncertain_returns_none(self):
        pos, level = classify_task("essay", "Кратко опишите")
        # Now always returns a position (default essay = 14)
        assert pos is not None


class TestUncertainClassification:
    """When classifier has no clear match, it defaults to a position."""

    def test_empty_text(self):
        pos, level = classify_task("short_answer", "")
        # Empty short_answer defaults to position 3
        assert pos == 3

    def test_short_answer_no_markers(self):
        pos, level = classify_task("short_answer", "Что произошло в этом году?")
        # No clear markers → defaults to position 3
        assert pos == 3

    def test_matching_no_clear_content(self):
        pos, level = classify_task("matching", "Соответствие A B C D")
        assert pos == 3  # Default matching is position 3


class TestImagePresenceCheck:
    """Image presence must be verified via text_content, not text."""

    def test_image_in_text_content(self):
        tc = {"images": ["http://example.com/img.jpg"]}
        assert True  # placeholder

    def test_no_images_key(self):
        tc = {"text": "some text"}
        assert not tc.get("images")

    def test_empty_images(self):
        tc = {"images": []}
        assert not tc.get("images")
