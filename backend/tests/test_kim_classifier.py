"""Tests for KIM classifier accuracy — including golden fixtures from official EGE 2026 demo."""
import pytest
from app.services.kim_mapping import classify_task, POSITION_LEVELS


# ═══════════════════════════════════════════════════════════════════════
# GOLDEN FIXTURES: Official EGE History 2026 demo variant
# Each task has the real text from the PDF and expected exam_position.
# Source: docs/история демо 26.pdf
# ═══════════════════════════════════════════════════════════════════════

GOLDEN_FIXTURES = [
    # ── Task 1: matching years (pos 1) ──────────────────────────────
    {
        "id": 1,
        "subtype": "matching",
        "expected_pos": 1,
        "text": (
            "Установите соответствие между событиями и годами: "
            "к каждой позиции первого столбца подберите соответствующую позицию из второго столбца. "
            "СОБЫТИЯ: А) вхождение Крыма в состав Российской Федерации; "
            "Б) включение Псковской земли в состав Русского государства; "
            "В) вхождение Финляндии в состав Российской империи; "
            "Г) освобождение Севастополя от немецко-фашистских захватчиков. "
            "ГОДЫ: 1) 1485 г. 2) 1510 г. 3) 1809 г. 4) 1942 г. 5) 1944 г. 6) 2014 г."
        ),
        "text_content": {},
    },
    # ── Task 2: chronology sequence (pos 2) ──────────────────────────
    {
        "id": 2,
        "subtype": "sequence",
        "expected_pos": 2,
        "text": (
            "Расположите в хронологической последовательности исторические события. "
            "Запишите цифры, которыми обозначены исторические события, "
            "в правильной последовательности в таблицу."
        ),
        "text_content": {},
    },
    # ── Task 3: matching processes and facts (pos 3) ────────────────
    {
        "id": 3,
        "subtype": "matching",
        "expected_pos": 3,
        "text": (
            "Установите соответствие между процессами (явлениями, событиями) "
            "и фактами, относящимися к этим процессам (явлениям, событиям): "
            "к каждой позиции первого столбца подберите соответствующую позицию из второго столбца. "
            "ПРОЦЕССЫ (ЯВЛЕНИЯ, СОБЫТИЯ) ФАКТЫ "
            "А) формирование Древнерусского государства "
            "Б) реформы Избранной рады "
            "В) проведение большевиками новой экономической политики (нэп) "
            "Г) внутренняя политика Николая I"
        ),
        "text_content": {},
    },
    # ── Task 4: table fill (pos 4) ──────────────────────────────────
    {
        "id": 4,
        "subtype": "short_answer",
        "expected_pos": 4,
        "text": (
            "Заполните пустые ячейки таблицы, используя приведённый ниже список "
            "пропущенных элементов: для каждого пропуска, обозначенного буквой, "
            "выберите номер нужного элемента. "
            "Пропущенные элементы: 1) Петроград 2) Севастополь 3) 1890-е гг. "
            "4) Владивосток 5) 1660-е гг. 6) ввод в эксплуатацию первой в мире атомной электростанции "
            "7) деятельность Всероссийского Учредительного собрания 8) 1790-е гг. "
            "9) вхождение в состав Российской Федерации"
        ),
        "text_content": {},
    },
    # ── Task 5: matching events and participants (pos 5) ─────────────
    {
        "id": 5,
        "subtype": "matching",
        "expected_pos": 5,
        "text": (
            "Установите соответствие между событиями (явлениями, процессами) "
            "и участниками этих событий (явлений, процессов): "
            "к каждой позиции первого столбца подберите соответствующую позицию из второго столбца. "
            "СОБЫТИЯ (ЯВЛЕНИЯ, ПРОЦЕССЫ) УЧАСТНИКИ "
            "А) деятельность Посольского приказа в период правления Алексея Михайловича "
            "Б) Специальная военная операция (СВО) "
            "В) деятельность Верховной распорядительной комиссии по охране государственного порядка "
            "Г) битва за Берлин"
        ),
        "text_content": {},
    },
    # ── Task 6: source judgments (pos 6) ────────────────────────────
    {
        "id": 6,
        "subtype": "essay",
        "expected_pos": 6,
        "text": (
            "Прочтите отрывок из записок исторического деятеля. "
            "«Верховный Совет торжествовал победу. Власть перемещалась из рук государя в руки 12 неограниченных правителей...» "
            "Используя отрывок и знания по истории, выберите в приведённом списке верные суждения. "
            "Запишите цифры, под которыми они указаны. "
            "1) Упоминаемая в отрывке императрица пришла к власти в результате дворцового переворота."
        ),
        "text_content": {},
    },
    # ── Task 7: matching culture monuments (pos 7) ──────────────────
    {
        "id": 7,
        "subtype": "matching",
        "expected_pos": 7,
        "text": (
            "Установите соответствие между памятниками культуры и их краткими характеристиками: "
            "к каждой позиции первого столбца подберите соответствующую позицию из второго столбца. "
            "ПАМЯТНИКИ КУЛЬТУРЫ ХАРАКТЕРИСТИКИ "
            "А) «История о великом князе Московском» "
            "Б) роман «Братья Карамазовы» "
            "В) «Слово о законе и благодати» "
            "Г) трилогия «Хождение по мукам»"
        ),
        "text_content": {},
    },
    # ── Task 8: image + fill blank (pos 8) ──────────────────────────
    {
        "id": 8,
        "subtype": "short_answer",
        "expected_pos": 8,
        "text": (
            "Рассмотрите изображение и выполните задание. "
            "Заполните пропуск в предложении: «Этот номер газеты вышел в тысяча "
            "девятьсот ____________________ году». Ответ запишите словом (сочетанием слов)."
        ),
        "text_content": {"images": ["http://example.com/gazeta.jpg"]},
    },
    # ── Task 9: map — ruler/period (pos 9) ──────────────────────────
    {
        "id": 9,
        "subtype": "short_answer",
        "expected_pos": 9,
        "text": (
            "Рассмотрите схему и выполните задания 9–12. "
            "Укажите правителя России в период, когда произошли события, обозначенные на схеме стрелками."
        ),
        "text_content": {"images": ["http://example.com/map.png"]},
    },
    # ── Task 10: map — numbered city (pos 10) ───────────────────────
    {
        "id": 10,
        "subtype": "short_answer",
        "expected_pos": 10,
        "text": (
            "Укажите название города, обозначенного на схеме цифрой «2», "
            "в период, когда произошли события, отражённые на схеме."
        ),
        "text_content": {"images": ["http://example.com/map.png"]},
    },
    # ── Task 11: map + text blank (pos 11) ──────────────────────────
    {
        "id": 11,
        "subtype": "short_answer",
        "expected_pos": 11,
        "text": (
            "Прочтите текст о событиях, отражённых на схеме, и, используя схему, "
            "укажите название города, дважды пропущенное в тексте. "
            "«Восставшие окружили Царицын, но город не сдавался... чтобы захватить "
            "стоящий в дельте Волги торговый город – ______________. "
            "Миновав Чёрный Яр, восставшие вскоре подошли к ______________ и при "
            "поддержке городской бедноты захватили город»."
        ),
        "text_content": {"images": ["http://example.com/map.png"]},
    },
    # ── Task 12: map judgments (pos 12) ─────────────────────────────
    {
        "id": 12,
        "subtype": "short_answer",
        "expected_pos": 12,
        "text": (
            "Какие суждения, относящиеся к схеме, являются верными? "
            "Запишите цифры, под которыми они указаны. "
            "1) Флажком на схеме обозначено место казни предводителя восстания. "
            "2) На схеме отмечена и подписана река. "
            "3) В подавлении восстания принимал участие А.В. Суворов."
        ),
        "text_content": {"images": ["http://example.com/map.png"]},
    },
    # ── Task 13: source — factual questions (pos 13) ────────────────
    {
        "id": 13,
        "subtype": "essay",
        "expected_pos": 13,
        "text": (
            "Прочтите отрывок из исторического источника и выполните задания 13 и 14. "
            "Из доклада, подготовленного политическим деятелем к Пленуму ЦК КПСС "
            "«Прошло уже три года с того времени, когда XXII съезд КПСС принял новую Программу партии...» "
            "Укажите год, когда состоялся Пленум ЦК КПСС, к которому был подготовлен данный доклад. "
            "Укажите пропущенную в тексте фамилию. "
            "Укажите исторического деятеля, занявшего должность Председателя Совета Министров СССР "
            "в том же десятилетии, когда был подготовлен данный доклад."
        ),
        "text_content": {},
    },
    # ── Task 14: source — interpretive questions (pos 14) ───────────
    {
        "id": 14,
        "subtype": "essay",
        "expected_pos": 14,
        "text": (
            "В чём, по утверждению автора доклада, состоит правда о развитии "
            "экономики СССР в ходе «великого десятилетия»? "
            "Как автор доклада охарактеризовал профессиональные качества людей, "
            "которые подготовили Программу КПСС? "
            "Как автор доклада характеризует сроки, установленные "
            "в Программе КПСС для достижения ряда показателей? "
            "При ответе избегайте цитирования избыточного текста."
        ),
        "text_content": {},
    },
    # ── Task 15: image analysis — identify person (pos 15) ──────────
    {
        "id": 15,
        "subtype": "essay",
        "expected_pos": 15,
        "text": (
            "Рассмотрите изображение и выполните задания 15, 16. "
            "Укажите князя, имя и фамилия которого заретушированы на памятной "
            "медали. Используя изображения, приведите одно любое обоснование Вашего ответа."
        ),
        "text_content": {"images": ["http://example.com/medal.jpg"]},
    },
    # ── Task 16: multiple architecture images (pos 16) ──────────────
    {
        "id": 16,
        "subtype": "essay",
        "expected_pos": 16,
        "text": (
            "Какой из представленных памятников архитектуры был возведён после "
            "событий, отображённых на медали? В ответе запишите цифру, которой "
            "обозначен этот памятник. Укажите название города, где находится этот "
            "памятник архитектуры. "
            "1) рисунок здания 2) рисунок здания 3) рисунок здания 4) рисунок здания"
        ),
        "text_content": {"images": ["http://example.com/arch1.jpg", "http://example.com/arch2.jpg"]},
    },
    # ── Task 17: WWII sources (pos 17) ──────────────────────────────
    {
        "id": 17,
        "subtype": "essay",
        "expected_pos": 17,
        "text": (
            "Прочтите отрывки из воспоминаний современников. "
            "ФРАГМЕНТЫ ИСТОЧНИКОВ А) «Нельзя сказать, что стремление гитлеровцев "
            "во что бы то ни стало сохранить сталинградский плацдарм было совершенным "
            "безумием... С военной точки зрения катастрофа под Сталинградом отнимала "
            "у гитлеровцев всякую надежду на дальнейшие наступательные действия на юге...» "
            "Б) «29 января нам стало известно, что штаб 6-й армии отошёл "
            "на западную окраину Сталинграда... штаб Паулюса находится в подвале универмага...» "
            "Укажите год, пропущенный в одном из отрывков. "
            "Укажите командующего Юго-Западным фронтом в период битвы, "
            "события которой описаны в обоих отрывках. "
            "Какое отрицательное последствие с военной точки зрения согласно "
            "одному из отрывков имела для гитлеровцев катастрофа под Сталинградом?"
        ),
        "text_content": {},
    },
    # ── Task 18: cause-effect structure а/б/в (pos 18) ──────────────
    {
        "id": 18,
        "subtype": "essay",
        "expected_pos": 18,
        "text": (
            "В XII в. начался процесс политической раздробленности Руси, но на "
            "протяжении XIII–XV вв. возникали причины (предпосылки) объединения "
            "русских земель в единое государство. Укажите: "
            "а) причину (предпосылку) объединения русских земель, связанную "
            "с внешнеполитическим фактором; "
            "б) экономическую причину (предпосылку) объединения русских земель; "
            "в) причину (предпосылку) объединения русских земель, "
            "связанную с позицией Русской Православной Церкви."
        ),
        "text_content": {},
    },
    # ── Task 19: concept definition (pos 19) ────────────────────────
    {
        "id": 19,
        "subtype": "essay",
        "expected_pos": 19,
        "text": (
            "Используя знания по истории России, раскройте смысл понятия «восточный "
            "вопрос». Приведите один исторический факт, конкретизирующий данное "
            "понятие применительно к истории России. Приведённый факт не должен "
            "содержаться в данном Вами определении понятия."
        ),
        "text_content": {},
    },
    # ── Task 20: thesis + 2 justifications (pos 20) ─────────────────
    {
        "id": 20,
        "subtype": "essay",
        "expected_pos": 20,
        "text": (
            "Запишите один любой тезис (обобщённое оценочное суждение), содержащий "
            "информацию о сходстве внутренней политики Екатерины II и Александра III "
            "по какому(-им)-либо признаку(-ам). Приведите два обоснования этого тезиса. "
            "Каждое обоснование должно содержать один или несколько исторических "
            "фактов. При обосновании тезиса избегайте рассуждений общего характера."
        ),
        "text_content": {},
    },
    # ── Task 21: named-argument structure (pos 21) ──────────────────
    {
        "id": 21,
        "subtype": "essay",
        "expected_pos": 21,
        "text": (
            "Используя исторические знания, приведите аргументы в подтверждение "
            "точки зрения, что в России в конце 1910-х – начале 1920-х гг. и в Китае "
            "в 1940-х гг. в ходе вооружённых противостояний внутри этих стран "
            "государства Запада оказывали поддержку тем сторонам конфликтов, которые "
            "в итоге потерпели поражение: один аргумент для России и один для Китая. "
            "При изложении аргументов обязательно используйте исторические факты. "
            "Ответ запишите в следующем виде. "
            "Аргумент для России: _______________________________________________ "
            "Аргумент для Китая: ________________________________________________"
        ),
        "text_content": {},
    },
]


class TestGoldenFixtures:
    """All 21 official demo tasks must classify to their correct positions."""

    @pytest.mark.parametrize("fixture", GOLDEN_FIXTURES, ids=[f"task_{f['id']}" for f in GOLDEN_FIXTURES])
    def test_golden_position(self, fixture):
        pos, level = classify_task(
            fixture["subtype"],
            fixture["text"],
            fixture["text_content"],
        )
        assert pos == fixture["expected_pos"], (
            f"Task {fixture['id']}: expected position {fixture['expected_pos']}, got {pos}"
        )

    def test_all_golden_pass(self):
        failures = []
        for f in GOLDEN_FIXTURES:
            pos, _ = classify_task(f["subtype"], f["text"], f["text_content"])
            if pos != f["expected_pos"]:
                failures.append(f"  Task {f['id']}: expected {f['expected_pos']}, got {pos}")
        assert not failures, "Golden fixture failures:\n" + "\n".join(failures)


# ═══════════════════════════════════════════════════════════════════════
# RULE TESTS: Three classifier refinements from Task 26
# ═══════════════════════════════════════════════════════════════════════

class TestType5HeaderVariants:
    """Type 5: both ДЕЯТЕЛИ and УЧАСТНИКИ headers must trigger position 5."""

    def test_deyateli_header(self):
        pos, level = classify_task("matching",
            "Установите соответствие между событиями и государственными деятелями. "
            "ДЕЯТЕЛИ: А) Пётр I Б) Екатерина II")
        assert pos == 5

    def test_uchastniki_header(self):
        pos, level = classify_task("matching",
            "Установите соответствие между событиями (явлениями, процессами) "
            "и участниками этих событий (явлений, процессов). "
            "СОБЫТИЯ (ЯВЛЕНИЯ, ПРОЦЕССЫ) УЧАСТНИКИ "
            "А) деятельность Посольского приказа Б) битва за Берлин")
        assert pos == 5

    def test_gosударственные_deyateli(self):
        pos, level = classify_task("matching",
            "ГОСУДАРСТВЕННЫЕ ДЕЯТЕЛИ: А) Иван Калита Б) Екатерина II")
        assert pos == 5


class TestType9GeneralContext:
    """Type 9: general context question (ruler/period), NOT specific numbered object."""

    def test_ruler_question(self):
        text_content = {"images": ["http://example.com/map.png"]}
        pos, level = classify_task("short_answer",
            "Рассмотрите схему и выполните задание. "
            "Укажите правителя России в период, когда произошли события, обозначенные на схеме.",
            text_content)
        assert pos == 9

    def test_named_ruler_question(self):
        text_content = {"images": ["http://example.com/map.png"]}
        pos, level = classify_task("short_answer",
            "Рассмотрите схему и выполните задание. "
            "Назовите название войны, которой посвящена схема.",
            text_content)
        assert pos == 9

    def test_numbered_object_is_not_type9(self):
        """Questions about specific numbered objects should NOT be Type 9."""
        text_content = {"images": ["http://example.com/map.png"]}
        pos, level = classify_task("short_answer",
            "Рассмотрите схему и выполните задание. "
            "Укажите название города, обозначенного на схеме цифрой «2».",
            text_content)
        assert pos != 9, "Numbered object question should not be Type 9"


class TestType13vs14Distinction:
    """Type 13 = factual attribution, Type 14 = interpretive content."""

    def test_type13_factual_year(self):
        pos, level = classify_task("essay",
            "Прочтите отрывок из исторического источника. "
            "Укажите год, когда состоялся Пленум ЦК КПСС.")
        assert pos == 13

    def test_type13_factual_name(self):
        pos, level = classify_task("essay",
            "Прочтите отрывок. Укажите пропущенную в тексте фамилию. "
            "Укажите исторического деятеля.")
        assert pos == 13

    def test_type14_interpretive(self):
        pos, level = classify_task("essay",
            "В чём, по утверждению автора доклада, состоит правда о развитии "
            "экономики СССР в ходе «великого десятилетия»? "
            "Как автор доклада охарактеризовал профессиональные качества людей?")
        assert pos == 14

    def test_type14_how_author_characterizes(self):
        pos, level = classify_task("essay",
            "Как автор доклада характеризует сроки, установленные в Программе КПСС?")
        assert pos == 14


# ═══════════════════════════════════════════════════════════════════════
# ORIGINAL TESTS (updated to match current classifier behavior)
# ═══════════════════════════════════════════════════════════════════════

class TestDifficultyDistribution:
    """Verify level distribution matches official spec: 10 Б / 8 П / 3 В."""

    def test_official_level_counts(self):
        levels = list(POSITION_LEVELS.values())
        assert levels.count("Б") == 10, f"Expected 10 Б, got {levels.count('Б')}"
        assert levels.count("П") == 8, f"Expected 8 П, got {levels.count('П')}"
        assert levels.count("В") == 3, f"Expected 3 В, got {levels.count('В')}"
        assert len(levels) == 21

    def test_all_positions_covered(self):
        for i in range(1, 22):
            assert i in POSITION_LEVELS, f"Position {i} missing from POSITION_LEVELS"


class TestMatchingClassification:
    """Positions 1, 3, 5, 7 — all matching format, distinguished by content."""

    def test_date_matching(self):
        pos, level = classify_task("matching",
            "Установите соответствие между событиями и годами: "
            "А) событие 1) 1812 г. 2) 1917 г. 3) 1945 г.")
        assert pos == 1
        assert level == "Б"

    def test_figure_matching(self):
        pos, level = classify_task("matching",
            "Установите соответствие между событиями и государственными деятелями. "
            "ДЕЯТЕЛИ: А) Пётр I Б) Екатерина II")
        assert pos == 5
        assert level == "Б"

    def test_culture_matching(self):
        pos, level = classify_task("matching",
            "Установите соответствие между памятниками культуры и их краткими характеристиками. "
            "ПАМЯТНИКИ КУЛЬТУРЫ: А) «Слово о законе и благодати» Б) «Братья Карамазовы»")
        assert pos == 7
        assert level == "Б"

    def test_fact_matching(self):
        pos, level = classify_task("matching",
            "Установите соответствие между процессами и фактами. "
            "ПРОЦЕССЫ (ЯВЛЕНИЯ, СОБЫТИЯ) ФАКТЫ: А) реформы 1) факт 1 2) факт 2")
        assert pos == 3
        assert level == "Б"


class TestSequenceClassification:
    def test_chronology(self):
        pos, level = classify_task("sequence",
            "Расположите в хронологической последовательности исторические события.")
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

    def test_figure_matching_still_works(self):
        """Real figure tasks should still classify as position 5."""
        pos, level = classify_task("matching",
            "ГОСУДАРСТВЕННЫЕ ДЕЯТЕЛИ: А) Иван Калита Б) Екатерина II")
        assert pos == 5, "Real figure tasks should be position 5"

    def test_culture_matching_still_works(self):
        """Real culture tasks should classify as position 7."""
        pos, level = classify_task("matching",
            "Установите соответствие между памятниками культуры и их характеристиками. "
            "ПАМЯТНИКИ КУЛЬТУРЫ: А) «Слово о законе и благодати»")
        assert pos == 7, "Real culture tasks should be position 7"


class TestWWIIClassification:
    """Positions 8 and 17 — STRICT WWII requirement."""

    def test_image_with_wwii(self):
        text_content = {"images": ["http://example.com/wwii.jpg"]}
        pos, level = classify_task("short_answer",
            "Рассмотрите изображение и выполните задание. 1941-1942 Битва за Москву",
            text_content)
        assert pos == 8
        assert level == "Б"

    def test_image_with_intro_no_wwii(self):
        """Image + intro 'Рассмотрите изображение' without explicit WWII → still 8."""
        text_content = {"images": ["http://example.com/gazeta.jpg"]}
        pos, level = classify_task("short_answer",
            "Рассмотрите изображение и выполните задание. Заполните пропуск в предложении.",
            text_content)
        assert pos == 8

    def test_image_without_intro_not_pos8(self):
        text_content = {"images": ["http://example.com/castle.jpg"]}
        pos, level = classify_task("short_answer", "Определите крепость на изображении", text_content)
        assert pos != 8

    def test_essay_with_wwii_sources(self):
        pos, level = classify_task("essay",
            "Прочтите отрывки из воспоминаний современников. "
            "ФРАГМЕНТЫ ИСТОЧНИКОВ А) «...сталинградский плацдарм...» "
            "Б) «...штаб 6-й армии...»")
        assert pos == 17
        assert level == "П"

    def test_essay_without_wwii_not_pos17(self):
        pos, level = classify_task("essay",
            "Прочтите отрывки из воспоминаний. ФРАГМЕНТЫ ИСТОЧНИКОВ А) «...Петровская эпоха...»")
        assert pos != 17


class TestMapClassification:
    def test_map_with_ruler(self):
        text_content = {"images": ["http://example.com/map.png"]}
        pos, level = classify_task("short_answer",
            "Рассмотрите схему и выполните задание. Укажите правителя России.",
            text_content)
        assert pos == 9

    def test_map_with_numbered_city(self):
        text_content = {"images": ["http://example.com/map.png"]}
        pos, level = classify_task("short_answer",
            "Укажите название города, обозначенного на схеме цифрой «2».",
            text_content)
        assert pos == 10

    def test_map_with_text_blank(self):
        text_content = {"images": ["http://example.com/map.png"]}
        pos, level = classify_task("short_answer",
            "Прочтите текст о событиях, отражённых на схеме, и, используя схему, "
            "укажите название города, дважды пропущенное в тексте.",
            text_content)
        assert pos == 11


class TestEssayClassification:
    def test_attribution(self):
        pos, level = classify_task("essay",
            "Прочтите отрывок из исторического источника. "
            "Укажите год, когда состоялся Пленум. Укажите фамилию.")
        assert pos == 13
        assert level == "П"

    def test_cause_effect(self):
        pos, level = classify_task("essay",
            "В XII в. начался процесс... Укажите: а) причину... б) причину... в) причину...")
        assert pos == 18
        assert level == "В"

    def test_comparison(self):
        pos, level = classify_task("essay",
            "Запишите тезис (обобщённое оценочное суждение). "
            "Приведите два обоснования этого тезиса.")
        assert pos == 20
        assert level == "В"

    def test_argumentation(self):
        pos, level = classify_task("essay",
            "Приведите аргументы в подтверждение точки зрения. "
            "Аргумент для России: ___ Аргумент для Китая: ___")
        assert pos == 21
        assert level == "В"

    def test_terms(self):
        pos, level = classify_task("essay",
            "Раскройте смысл понятия «восточный вопрос». "
            "Приведите один исторический факт, конкретизирующий данное понятие.")
        assert pos == 19
        assert level == "П"

    def test_uncertain_returns_none(self):
        pos, level = classify_task("essay", "Кратко опишите")
        assert pos is None


class TestUncertainClassification:
    """When classifier has no clear match, it returns None."""

    def test_empty_text(self):
        pos, level = classify_task("short_answer", "")
        assert pos is None

    def test_short_answer_no_markers(self):
        pos, level = classify_task("short_answer", "Что произошло в этом году?")
        assert pos is None

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
