#!/usr/bin/env python3
"""Собирает инженерный отчёт report.pdf средствами ReportLab."""

from __future__ import annotations

import math
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "report.pdf"

NAVY = colors.black
BLUE = colors.black
CYAN = colors.black
ORANGE = colors.black
GREEN = colors.black
RED = colors.black
INK = colors.black
MUTED = colors.HexColor("#444444")
LIGHT = colors.white
LINE_COLOR = colors.HexColor("#777777")
WHITE = colors.white


def register_fonts() -> None:
    regular = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    bold = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    mono = Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
    serif = Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf")
    serif_italic = Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf")
    for path in (regular, bold, mono, serif, serif_italic):
        if not path.exists():
            raise FileNotFoundError(f"Не найден шрифт {path}")
    pdfmetrics.registerFont(TTFont("DV", str(regular)))
    pdfmetrics.registerFont(TTFont("DV-Bold", str(bold)))
    pdfmetrics.registerFont(TTFont("DV-Mono", str(mono)))
    pdfmetrics.registerFont(TTFont("DV-Serif", str(serif)))
    pdfmetrics.registerFont(TTFont("DV-Serif-Italic", str(serif_italic)))
    pdfmetrics.registerFontFamily(
        "DV-Serif", normal="DV-Serif", italic="DV-Serif-Italic"
    )


register_fonts()


styles = getSampleStyleSheet()
TITLE = ParagraphStyle(
    "TitleDV",
    fontName="DV-Bold",
    fontSize=27,
    leading=32,
    textColor=INK,
    alignment=TA_LEFT,
    spaceAfter=8 * mm,
)
SUBTITLE = ParagraphStyle(
    "SubtitleDV",
    fontName="DV",
    fontSize=12,
    leading=17,
    textColor=INK,
)
H1 = ParagraphStyle(
    "H1DV",
    fontName="DV-Bold",
    fontSize=19,
    leading=23,
    textColor=INK,
    spaceBefore=1 * mm,
    spaceAfter=5 * mm,
    keepWithNext=True,
)
H2 = ParagraphStyle(
    "H2DV",
    fontName="DV-Bold",
    fontSize=12.5,
    leading=16,
    textColor=INK,
    spaceBefore=4 * mm,
    spaceAfter=2.5 * mm,
    keepWithNext=True,
)
BODY = ParagraphStyle(
    "BodyDV",
    fontName="DV",
    fontSize=9.5,
    leading=14.2,
    textColor=INK,
    spaceAfter=2.5 * mm,
)
SMALL = ParagraphStyle(
    "SmallDV",
    fontName="DV",
    fontSize=7.7,
    leading=10.3,
    textColor=MUTED,
)
TABLE = ParagraphStyle(
    "TableDV",
    fontName="DV",
    fontSize=7.4,
    leading=9.6,
    textColor=INK,
)
TABLE_BOLD = ParagraphStyle(
    "TableBoldDV",
    parent=TABLE,
    fontName="DV-Bold",
    textColor=NAVY,
)
BULLET = ParagraphStyle(
    "BulletDV",
    parent=BODY,
    leftIndent=5 * mm,
    firstLineIndent=-3.5 * mm,
    bulletIndent=0,
    spaceAfter=1.8 * mm,
)
CALLOUT = ParagraphStyle(
    "CalloutDV",
    parent=BODY,
    fontSize=9,
    leading=13.5,
    textColor=NAVY,
    spaceAfter=0,
)
CODE = ParagraphStyle(
    "CodeDV",
    fontName="DV-Mono",
    fontSize=7.2,
    leading=10.2,
    textColor=INK,
)
MATH = ParagraphStyle(
    "MathDV",
    fontName="DV-Serif",
    fontSize=10.5,
    leading=22,
    textColor=INK,
    alignment=TA_CENTER,
    spaceBefore=1.5 * mm,
    spaceAfter=2 * mm,
)
QUOTE = ParagraphStyle(
    "QuoteDV",
    parent=BODY,
    leftIndent=8 * mm,
    rightIndent=5 * mm,
    borderColor=CYAN,
    borderWidth=0,
    borderPadding=0,
    textColor=MUTED,
)


def para(text: str, style: ParagraphStyle = BODY) -> Paragraph:
    return Paragraph(text, style)


def bullets(items: list[str]) -> list[Paragraph]:
    return [Paragraph(f"• {item}", BULLET) for item in items]


def callout(title: str, text: str, color: colors.Color = CYAN) -> Table:
    content = Paragraph(f"<b>{title}</b><br/>{text}", CALLOUT)
    table = Table([[content]], colWidths=[166 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), WHITE),
                ("LINEABOVE", (0, 0), (-1, 0), 0.5, LINE_COLOR),
                ("LINEBELOW", (0, -1), (-1, -1), 0.5, LINE_COLOR),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
            ]
        )
    )
    return table


def data_table(
    rows: list[list[str | Paragraph]],
    widths: list[float],
    *,
    header: bool = True,
    font_size: float = 7.4,
) -> Table:
    converted: list[list[Paragraph]] = []
    for row_index, row in enumerate(rows):
        style = TABLE_BOLD if header and row_index == 0 else TABLE
        if font_size != TABLE.fontSize:
            style = ParagraphStyle(
                f"table-{font_size}-{row_index}",
                parent=style,
                fontSize=font_size,
                leading=font_size * 1.3,
            )
        converted.append(
            [cell if isinstance(cell, Paragraph) else Paragraph(str(cell), style) for cell in row]
        )
    table = Table(converted, colWidths=widths, repeatRows=1 if header else 0)
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE_COLOR),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.4 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.4 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2.1 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.1 * mm),
        ("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1), [WHITE, WHITE]),
    ]
    if header:
        commands.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), WHITE),
                ("TEXTCOLOR", (0, 0), (-1, 0), INK),
                ("LINEBELOW", (0, 0), (-1, 0), 0.9, INK),
            ]
        )
        for cell in converted[0]:
            cell.style.textColor = INK
    table.setStyle(TableStyle(commands))
    return table


class TunnelDiagram(Flowable):
    """План и вид сбоку тоннеля в одном векторном рисунке."""

    def __init__(self) -> None:
        super().__init__()
        self.width = 166 * mm
        self.height = 105 * mm

    def draw(self) -> None:
        c = self.canv
        c.saveState()
        c.setFont("DV-Bold", 9)
        c.setFillColor(NAVY)
        c.drawString(0, self.height - 8, "План сверху")
        c.drawString(0, 58 * mm, "Вид сбоку")

        # Top view.
        x0, y0 = 20 * mm, 70 * mm
        belt_w, belt_h = 126 * mm, 24 * mm
        c.setFillColor(colors.HexColor("#F5F5F5"))
        c.setStrokeColor(colors.HexColor("#777777"))
        c.roundRect(x0, y0, belt_w, belt_h, 3 * mm, fill=1, stroke=1)
        for x in range(int(x0 + 5 * mm), int(x0 + belt_w - 2 * mm), int(7 * mm)):
            c.setStrokeColor(colors.HexColor("#BBBBBB"))
            c.line(x, y0 + 2 * mm, x, y0 + belt_h - 2 * mm)
        box_x = x0 + 46 * mm
        c.setFillColor(colors.HexColor("#EAEAEA"))
        c.setStrokeColor(colors.HexColor("#555555"))
        c.rect(box_x, y0 + 3 * mm, 40 * mm, 18 * mm, fill=1, stroke=1)
        c.setFillColor(INK)
        c.setFont("DV", 6.7)
        c.drawCentredString(box_x + 20 * mm, y0 + 11 * mm, "600 × 400 mm")
        self._camera(c, 7 * mm, y0 + 6 * mm, "FRONT", 0)
        self._camera(c, 151 * mm, y0 + 6 * mm, "REAR", 180)
        self._camera(c, box_x + 12 * mm, y0 + 27 * mm, "LEFT", -90)
        self._camera(c, box_x + 12 * mm, y0 - 9 * mm, "RIGHT", 90)
        c.setFillColor(BLUE)
        c.setStrokeColor(BLUE)
        c.line(x0 + 8 * mm, y0 + 12 * mm, x0 + 22 * mm, y0 + 12 * mm)
        c.line(x0 + 22 * mm, y0 + 12 * mm, x0 + 18 * mm, y0 + 15 * mm)
        c.line(x0 + 22 * mm, y0 + 12 * mm, x0 + 18 * mm, y0 + 9 * mm)
        c.setFont("DV-Bold", 6.5)
        c.drawString(x0 + 3 * mm, y0 + 16 * mm, "1 m/s")

        # Side view.
        sy = 4 * mm
        c.setFillColor(colors.HexColor("#F5F5F5"))
        c.setStrokeColor(colors.HexColor("#777777"))
        c.rect(20 * mm, sy + 12 * mm, 126 * mm, 8 * mm, fill=1, stroke=1)
        # Transfer gap.
        c.setFillColor(WHITE)
        c.rect(80 * mm, sy + 11.5 * mm, 12 * mm, 9 * mm, fill=1, stroke=0)
        c.setStrokeColor(ORANGE)
        c.setLineWidth(1.5)
        c.line(80 * mm, sy + 12 * mm, 80 * mm, sy + 20 * mm)
        c.line(92 * mm, sy + 12 * mm, 92 * mm, sy + 20 * mm)
        c.setFillColor(colors.HexColor("#EAEAEA"))
        c.setStrokeColor(colors.HexColor("#555555"))
        c.rect(66 * mm, sy + 20 * mm, 40 * mm, 24 * mm, fill=1, stroke=1)
        self._camera(c, 82 * mm, sy + 49 * mm, "TOP", 0)
        c.setStrokeColor(CYAN)
        c.setLineWidth(0.8)
        c.line(86 * mm, sy + 49 * mm, 86 * mm, sy + 44 * mm)
        self._camera(c, 61 * mm, sy, "BOTTOM A", 45)
        self._camera(c, 101 * mm, sy, "BOTTOM B", 135)
        c.setFillColor(ORANGE)
        c.setFont("DV-Bold", 6.8)
        c.drawCentredString(86 * mm, sy + 7.2 * mm, "gap 120 mm")
        c.setFillColor(MUTED)
        c.setFont("DV", 6.2)
        c.drawString(114 * mm, sy + 38 * mm, "Reader'ы наклонены")
        c.drawString(114 * mm, sy + 34.5 * mm, "или используют зеркало,")
        c.drawString(114 * mm, sy + 31 * mm, "чтобы сложить путь 900 mm")
        c.restoreState()

    @staticmethod
    def _camera(c, x: float, y: float, label: str, angle: float) -> None:
        c.saveState()
        c.translate(x, y)
        c.rotate(angle)
        c.setFillColor(NAVY)
        c.setStrokeColor(NAVY)
        c.roundRect(0, 0, 8 * mm, 6 * mm, 1 * mm, fill=1, stroke=0)
        c.setFillColor(CYAN)
        c.circle(1.2 * mm, 3 * mm, 1 * mm, fill=1, stroke=0)
        c.restoreState()
        c.setFillColor(NAVY)
        c.setFont("DV-Bold", 5.2)
        c.drawCentredString(x + 4 * mm, y - 2.3 * mm, label)


class ArchitectureDiagram(Flowable):
    def __init__(self) -> None:
        super().__init__()
        self.width = 166 * mm
        self.height = 56 * mm

    def draw(self) -> None:
        c = self.canv
        c.saveState()
        nodes = [
            (0, 15, 28, 25, "Фотоэлемент\n+ энкодер", CYAN),
            (35, 15, 33, 25, "7 × DataMan\nдекодирование", BLUE),
            (75, 15, 34, 25, "Edge K410\nагрегация", GREEN),
            (116, 15, 24, 25, "ПЛК / СУ\nсортировка", ORANGE),
            (146, 15, 20, 25, "Отвод\nошибок", RED),
        ]
        for x, y, w, h, label, color in nodes:
            x *= mm
            y *= mm
            w *= mm
            h *= mm
            c.setFillColor(colors.Color(color.red, color.green, color.blue, alpha=0.10))
            c.setStrokeColor(color)
            c.setLineWidth(1.1)
            c.roundRect(x, y, w, h, 3 * mm, fill=1, stroke=1)
            c.setFillColor(NAVY)
            c.setFont("DV-Bold", 7.3)
            lines = label.split("\n")
            for index, line in enumerate(lines):
                c.drawCentredString(x + w / 2, y + h / 2 + (4 - index * 8), line)
        for x1, x2 in [(28, 35), (68, 75), (109, 116), (140, 146)]:
            self._arrow(c, x1 * mm, 27.5 * mm, x2 * mm, 27.5 * mm)
        c.setFillColor(MUTED)
        c.setFont("DV", 6.5)
        c.drawCentredString(51.5 * mm, 8 * mm, "trigger + Ethernet")
        c.drawCentredString(92 * mm, 8 * mm, "JSON events")
        c.drawCentredString(128 * mm, 8 * mm, "result + idempotency key")
        c.setStrokeColor(LINE_COLOR)
        c.setDash(3, 2)
        c.line(92 * mm, 45 * mm, 92 * mm, 52 * mm)
        c.setFillColor(MUTED)
        c.drawCentredString(92 * mm, 53 * mm, "облако: только телеметрия, не контур управления")
        c.restoreState()

    @staticmethod
    def _arrow(c, x1: float, y1: float, x2: float, y2: float) -> None:
        c.setStrokeColor(NAVY)
        c.setFillColor(NAVY)
        c.setLineWidth(1)
        c.line(x1, y1, x2 - 1.5 * mm, y2)
        c.line(x2 - 1.5 * mm, y2, x2 - 3 * mm, y2 + 1.4 * mm)
        c.line(x2 - 1.5 * mm, y2, x2 - 3 * mm, y2 - 1.4 * mm)


class StateDiagram(Flowable):
    def __init__(self) -> None:
        super().__init__()
        self.width = 166 * mm
        self.height = 42 * mm

    def draw(self) -> None:
        c = self.canv
        c.saveState()
        states = [
            ("WAIT", 2, NAVY),
            ("TRACK", 37, BLUE),
            ("COLLECT", 72, CYAN),
            ("FINALIZE", 107, GREEN),
        ]
        for label, x, color in states:
            c.setFillColor(colors.Color(color.red, color.green, color.blue, alpha=0.12))
            c.setStrokeColor(color)
            c.roundRect(x * mm, 17 * mm, 26 * mm, 14 * mm, 3 * mm, fill=1, stroke=1)
            c.setFillColor(NAVY)
            c.setFont("DV-Bold", 7.2)
            c.drawCentredString((x + 13) * mm, 22.5 * mm, label)
        for x1, x2 in [(28, 37), (63, 72), (98, 107)]:
            ArchitectureDiagram._arrow(c, x1 * mm, 24 * mm, x2 * mm, 24 * mm)
        # Three outcomes.
        x = 141 * mm
        for y, label, color in [(32, "OK", GREEN), (22, "NO_READ", ORANGE), (12, "INCOMPLETE", RED)]:
            c.setFillColor(color)
            c.roundRect(x, (y - 4) * mm, 24 * mm, 7 * mm, 2 * mm, fill=1, stroke=0)
            c.setFillColor(WHITE)
            c.setFont("DV-Bold", 5.8)
            c.drawCentredString(x + 12 * mm, (y - 1.8) * mm, label)
            ArchitectureDiagram._arrow(c, 133 * mm, 24 * mm, x, y * mm)
        c.setFillColor(MUTED)
        c.setFont("DV", 6.2)
        c.drawCentredString(15 * mm, 10 * mm, "нет коробки")
        c.drawCentredString(50 * mm, 10 * mm, "box_id + окно")
        c.drawCentredString(85 * mm, 10 * mm, "лица + коды")
        c.drawCentredString(120 * mm, 10 * mm, "проверка покрытия")
        c.restoreState()


class ReportDoc(BaseDocTemplate):
    def __init__(self, filename: str) -> None:
        super().__init__(
            filename,
            pagesize=A4,
            leftMargin=22 * mm,
            rightMargin=22 * mm,
            topMargin=20 * mm,
            bottomMargin=19 * mm,
            title="Шестисторонний тоннель считывания штрихкодов",
            author="Кандидат",
            subject="Тестовое задание Ozon 2026, вариант 2",
        )
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="normal",
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )
        self.addPageTemplates(
            [
                PageTemplate(id="report", frames=[frame], onPage=self._page),
            ]
        )

    @staticmethod
    def _page(canvas, doc) -> None:
        page = canvas.getPageNumber()
        if page == 1:
            return
        canvas.saveState()
        canvas.setStrokeColor(LINE_COLOR)
        canvas.setLineWidth(0.5)
        canvas.line(22 * mm, 14 * mm, A4[0] - 22 * mm, 14 * mm)
        canvas.setFillColor(MUTED)
        canvas.setFont("DV", 7)
        canvas.drawString(22 * mm, 9 * mm, "Ozon 2026 • Концепт для тестового задания • v1.0")
        canvas.drawRightString(A4[0] - 22 * mm, 9 * mm, f"{page}")
        canvas.restoreState()


def section_title(number: str, title: str) -> Paragraph:
    return para(f"{number}. {title}", H1)


def build_story() -> list[Flowable]:
    story: list[Flowable] = []

    # 1. Cover.
    story.extend(
        [
            Spacer(1, 52 * mm),
            para("ТЕСТОВОЕ ЗАДАНИЕ OZON 2026 • ВАРИАНТ 2", ParagraphStyle("kicker", parent=SUBTITLE, fontName="DV", fontSize=10, textColor=INK, spaceAfter=8 * mm)),
            para("Считывание штрихкодов<br/>на конвейере", TITLE),
            para(
                "Программно-аппаратная концепция и базовый прототип",
                SUBTITLE,
            ),
            Spacer(1, 22 * mm),
            Table(
                [
                    [para("1 m/s", ParagraphStyle("metric", fontName="DV-Bold", fontSize=17, textColor=INK, alignment=TA_CENTER)), para("650 mm", ParagraphStyle("metric2", fontName="DV-Bold", fontSize=17, textColor=INK, alignment=TA_CENTER)), para("6 граней", ParagraphStyle("metric3", fontName="DV-Bold", fontSize=17, textColor=INK, alignment=TA_CENTER))],
                    [para("скорость", ParagraphStyle("ml1", parent=SMALL, textColor=MUTED, alignment=TA_CENTER)), para("ширина ленты", ParagraphStyle("ml2", parent=SMALL, textColor=MUTED, alignment=TA_CENTER)), para("полное покрытие", ParagraphStyle("ml3", parent=SMALL, textColor=MUTED, alignment=TA_CENTER))],
                ],
                colWidths=[55 * mm, 55 * mm, 55 * mm],
                rowHeights=[12 * mm, 8 * mm],
                style=TableStyle(
                    [
                        ("BOX", (0, 0), (-1, -1), 0.7, INK),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE_COLOR),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("BACKGROUND", (0, 0), (-1, -1), WHITE),
                    ]
                ),
            ),
            Spacer(1, 58 * mm),
            para("Автор: кандидат • Дата: 17.09.2026", ParagraphStyle("coverfoot", parent=SUBTITLE, fontSize=9.5)),
            para("Статус: концепт; закупка только после оптического PoC", ParagraphStyle("coverfoot2", parent=SUBTITLE, fontSize=8.5, textColor=MUTED)),
            PageBreak(),
        ]
    )

    # 2. Summary.
    story.extend(
        [
            section_title("01", "Резюме решения"),
            para(
                "Задача выглядит как обычное чтение штрихкода, но главное ограничение спрятано "
                "в словах <b>«на любой грани»</b>. Нижняя грань лежит на ленте, а передняя и задняя "
                "быстро меняют видимость. Поэтому одна камера сверху принципиально не подходит.",
            ),
            callout(
                "Предложение в одной фразе",
                "Поставить перед сортировкой затемнённый шестисторонний тоннель: 7 smart-reader'ов "
                "Cognex DataMan 3816X, два нижних ракурса через transfer-gap, датчик входа, энкодер и "
                "локальный edge-компьютер, который объединяет все находки по одной коробке.",
            ),
            Spacer(1, 5 * mm),
            data_table(
                [
                    ["Решение", "Почему так"],
                    ["7 reader'ов / 6 граней", "Один reader на верх, боковые, переднюю и заднюю грань; два на низ для взаимного перекрытия и защиты от края gap."],
                    ["Распознавание внутри reader'а", "Меньше сетевого трафика и вычислительного риска: на edge идут короткие события, а не семь 16 MP видеопотоков."],
                    ["Локальная обработка", "До сортировщика максимум 3 m, значит нужен детерминированный ответ без зависимости от Интернета."],
                    ["Без нейросети", "1D/2D-код уже имеет строгую геометрию и контрольные суммы. Специализированный декодер проще проверить и сертифицировать."],
                    ["Отвод ошибок", "Если грань не подтверждена или нет чтения, коробка не получает выдуманный маршрут, а уходит на ручную проверку."],
                ],
                [49 * mm, 117 * mm],
            ),
            Spacer(1, 5 * mm),
            para("Что именно сделано", H2),
            *bullets(
                [
                    "Выбраны конкретные модели сенсоров, оптики, света, edge-компьютера и сети.",
                    "Проверены поле зрения, пиксельная плотность, смаз и временной бюджет.",
                    "Описана механика полного обзора, включая физически сложную нижнюю грань.",
                    "Собран Python-прототип: события, box tracking, дедупликация, HTTP callback и тесты.",
                    "Заданы метрики, приёмочный датасет, риск-регистр и шаги PoC.",
                ]
            ),
            PageBreak(),
        ]
    )

    # 3. Requirements and assumptions.
    story.extend(
        [
            section_title("02", "Требования, допущения и границы"),
            para("Из исходного PDF я считаю обязательными следующие условия:"),
            data_table(
                [
                    ["Параметр", "Дано", "Что это меняет"],
                    ["Конвейер", "ширина 650 mm, скорость 1 m/s", "Нужна короткая выдержка и жёсткая синхронизация."],
                    ["Коробка", "600 × 400 × 400 mm", "Поле зрения каждой камеры должно перекрывать соответствующую грань с запасом."],
                    ["Интервал", "2 s", "При тоннеле короче 2 m штатно внутри только одна коробка, но код поддерживает несколько окон."],
                    ["Этикетка", "78 × 25 mm; штрихи около 60 × 16,7 mm", "В расчёте используем 60 mm как полезную ширину кода."],
                    ["Количество", "несколько кодов, в том числе на одной грани", "Нельзя возвращать только первую находку; нужны координаты и дедупликация кадров."],
                    ["Место", "не дальше 3 m от сортировки", "Обработка только локально; результат отправляется сразу после выхода."],
                ],
                [32 * mm, 43 * mm, 91 * mm],
            ),
            para("Чего в задании нет", H2),
            *bullets(
                [
                    "Симвология, минимальный X-dimension (ширина узкого элемента), качество печати и допустимое повреждение.",
                    "Ориентация коробки, разброс размеров, зазор между коробками и возможность модифицировать конвейер.",
                    "Тип интерфейса ПЛК, политика при NO_READ и допустимая задержка.",
                    "Освещённость, пыль, температура, вибрация и требования по машинной безопасности.",
                ]
            ),
            callout(
                "Инженерное допущение",
                "Разрешена вставка двух коротких конвейерных секций с gap 120 mm. Для заданной коробки длиной "
                "не менее 400 mm она мостит такой gap. До закупки это должен подтвердить механик на реальном картоне, "
                "а нижний узел должен иметь ограждение и аварийный останов.",
                ORANGE,
            ),
            Spacer(1, 4 * mm),
            para(
                "Абсолютное обещание «прочитать все коды» нельзя доказать на коробке с заранее неизвестным числом "
                "наклеек. Поэтому я перевожу его в проверяемое требование: полное покрытие шести граней, отсутствие "
                "тихих отказов и package read rate на размеченной выборке не ниже согласованного порога.",
            ),
            PageBreak(),
        ]
    )

    # 4. Calculations.
    story.extend(
        [
            section_title("03", "Оптический и временной расчёт"),
            para(
                "Выбран DataMan 3816X: вариант X читает 1D/2D, сенсор имеет 5320 × 3032 px. "
                "Для 16 mm объектива производитель указывает FoV 625 × 355 mm на 700 mm и "
                "1080 × 615 mm на 1200 mm.<super>[1][2]</super>",
            ),
            para("Поле зрения на рабочей дистанции 900 mm", H2),
            para(
                "Для эскиза достаточно линейной интерполяции между двумя точками производителя:",
            ),
            para(
                "<i>FoV</i><sub>x</sub>(900) = 625 + "
                "<super>900 - 700</super>⁄<sub>1200 - 700</sub> · (1080 - 625) = 807 mm",
                MATH,
            ),
            para(
                "<i>FoV</i><sub>y</sub>(900) = 355 + "
                "<super>900 - 700</super>⁄<sub>1200 - 700</sub> · (615 - 355) = 459 mm",
                MATH,
            ),
            para(
                "ρ = <i>N</i><sub>x</sub> / <i>FoV</i><sub>x</sub> "
                "= 5320 / 807 ≈ 6,59 px/mm; "
                "<i>N</i><sub>label</sub> = ρ · 60 ≈ 395 px",
                MATH,
            ),
            para(
                "<i>b</i> = <i>v</i> · <i>t</i><sub>exp</sub> "
                "= 1 · 75 · 10<super>-6</super> = 0,075 mm ≈ 0,49 px",
                MATH,
            ),
            data_table(
                [
                    ["Величина", "Результат", "Вывод"],
                    ["Горизонтальное поле зрения", "807 mm", "Перекрывает грань 600 mm с запасом 207 mm."],
                    ["Вертикальное поле зрения", "459 mm", "Перекрывает высоту 400 mm с запасом 59 mm."],
                    ["Плотность изображения", "6,59 px/mm", "60 mm штрихов дают около 395 px по ширине."],
                    ["Смаз за экспозицию", "0,075 mm", "Около 0,49 px; движение практически заморожено."],
                ],
                [83 * mm, 27 * mm, 56 * mm],
            ),
            Spacer(1, 4 * mm),
            callout(
                "Почему 75 μs",
                "Для белого HPIT производитель указывает максимальное high-frequency illumination time 75 μs.<super>[5]</super> "
                "Короткий мощный импульс важнее красивой непрерывной подсветки: он уменьшает смаз на движущейся коробке.",
            ),
            Spacer(1, 4 * mm),
            para("Проверка временного бюджета", H2),
            data_table(
                [
                    ["Этап", "Целевое время"],
                    ["Окно наблюдения коробки в тоннеле", "до 1,2 s"],
                    ["Закрытие box window после задней грани", "до 50 ms"],
                    ["Агрегация, JSON и локальный POST", "p95 не более 200 ms"],
                    ["Запас до сортировщика при 0,8-1,0 m", "0,8-1,0 s"],
                ],
                [105 * mm, 61 * mm],
            ),
            para(
                "Важно: 395 px по ширине этикетки - это не гарантия для любого кода. Перед PoC нужно узнать "
                "минимальный X-dimension. Если узкий элемент меньше примерно 0,3 mm или печать сильно размыта, "
                "нужен более узкий FoV, дополнительный reader или более крупная этикетка.",
            ),
            PageBreak(),
        ]
    )

    # 5. Hardware.
    story.extend(
        [
            section_title("04", "Состав оборудования"),
            data_table(
                [
                    ["Узел", "Модель / кол-во", "Ключевые данные", "Почему выбран"],
                    ["Smart-reader", "Cognex DataMan 3816X / 7", "16,13 MP; 5320 × 3032; electronic shutter 15 μs-200 ms; 1D/2D; 2 × GbE; IP67.<super>[1][3]</super>", "Высокая плотность пикселей, встроенный декодер, multi-reader sync, промышленный корпус."],
                    ["Объектив", "CLN-C16F65-HSLL-HR / 7", "16 mm, high-speed liquid lens, high-res.<super>[4]</super>", "Фокус можно подстроить при небольшом разбросе положения коробки."],
                    ["Свет", "HPIT white + 380-TORCH-HR-COVPL / 7", "Мощный импульс, поляризованная крышка.<super>[4][5]</super>", "Уменьшает смаз и блик от прозрачного скотча."],
                    ["Наличие коробки", "SICK WTB4FP-21311120ZZZ / 2", "4-220 mm; response <0,5 ms; 1000 Hz; IP66/IP67.<super>[6]</super>", "Вход и выход формируют box window; частоты достаточно с огромным запасом."],
                    ["Положение ленты", "SICK DFS60E-S4EA01024 + BEF-MRS-10-U / 1", "1024 имп./оборот; энкодер DFS60 до 65 536 ppr; IP65/IP67.<super>[7]</super>", "Триггер по расстоянию остаётся точным при просадке скорости."],
                    ["Edge", "OnLogic Karbon K410 / 1", "Atom x6425E, 4C/4T; 16 GB; 512 GB SSD; 2 × GbE; 9-48 VDC; -40...70 °C.<super>[8]</super>", "Достаточно для событий и журналов; fanless и промышленное питание."],
                    ["Сеть", "Moxa EDS-G4012 / 1", "12 гигабитных портов; managed; резервирование и VLAN.<super>[9]</super>", "7 reader'ов, edge, uplink и запас для сервиса."],
                ],
                [26 * mm, 38 * mm, 52 * mm, 50 * mm],
                font_size=6.6,
            ),
            Spacer(1, 4 * mm),
            para("Питание и сеть", H2),
            *bullets(
                [
                    "Reader: отдельные 24 VDC линии с автоматами; пиково до 2 A на устройство по спецификации.<super>[3]</super>",
                    "Edge и switch питаются от промышленного 24 VDC БП с UPS/DC-buffer минимум на корректную остановку и отправку тревоги.",
                    "Reader VLAN отделён от корпоративной сети; наружу разрешён только callback к ПЛК/СУ и мониторинг.",
                    "Все M12/RJ45 экраны и рама заземляются по руководствам производителя.",
                ]
            ),
            callout(
                "Что не надо покупать сразу",
                "Сначала один reader, один HPIT и реальные коробки. Если оптический PoC не читает худшие этикетки, "
                "семь одинаковых комплектов покупать рано.",
                ORANGE,
            ),
            PageBreak(),
        ]
    )

    # 6. Layout.
    story.extend(
        [
            section_title("05", "Физическое расположение"),
            TunnelDiagram(),
            Spacer(1, 2 * mm),
            data_table(
                [
                    ["Reader", "Что видит", "Монтаж"],
                    ["TOP", "верх 600 × 400 mm", "Над центром; оптическая дистанция около 900 mm."],
                    ["LEFT / RIGHT", "две боковые грани 400 × 400 mm", "По бокам, с небольшим углом 10-15° против зеркального блика."],
                    ["FRONT / REAR", "передняя и задняя 600 × 400 mm", "Высокие диагональные ракурсы; путь складывается зеркалом или рамой, чтобы тоннель поместился до сортировщика."],
                    ["BOTTOM A / B", "низ 600 × 400 mm", "Смотрят навстречу друг другу через gap 120 mm; серия кадров по импульсам энкодера."],
                ],
                [31 * mm, 50 * mm, 85 * mm],
            ),
            Spacer(1, 3 * mm),
            para(
                "Внутри тоннеля матовые тёмные панели отсекают внешний свет. Все кронштейны имеют шкалу и "
                "фиксатор, а калибровочная пластина задаёт единую систему координат каждой грани. Для низа "
                "предусмотрены съёмное защитное стекло, продувка и контроль загрязнения.",
            ),
            callout(
                "Почему два reader'а снизу",
                "Gap открывает низ постепенно. Один наклонный ракурс может потерять этикетку у кромки или в тени. "
                "Два встречных ракурса дают перекрытие; агрегатор объединяет их события по координате.",
            ),
            PageBreak(),
        ]
    )

    # 7. Architecture.
    story.extend(
        [
            section_title("06", "Вычислительная архитектура"),
            ArchitectureDiagram(),
            para("Почему локально", H2),
            *bullets(
                [
                    "При 1 m/s каждые 100 ms - это 100 mm пути. Сеть до облака добавляет непредсказуемую задержку и новый отказ.",
                    "DataMan уже декодирует изображение. Edge получает десятки коротких событий на коробку, а не гигабайты кадров.",
                    "При потере внешней связи линия продолжает сортировать, а телеметрия накапливается локально.",
                    "В облако можно отправлять агрегированные метрики и ограниченную выборку NO_READ, но не принимать оттуда решение текущей коробки.",
                ]
            ),
            para("Интерфейсы", H2),
            data_table(
                [
                    ["Связь", "Контракт"],
                    ["Датчики -> reader/PLC", "24 V digital input; энкодерные импульсы; общий box trigger."],
                    ["Reader -> edge", "Ethernet TCP; событие: reader_id, face, data, symbology, time, position, quality."],
                    ["Edge -> СУ", "HTTP POST JSON в демо; в production адаптер под EtherNet/IP, PROFINET или Modbus/TCP. DataMan поддерживает промышленные Ethernet-протоколы.<super>[3]</super>"],
                    ["Диагностика", "Health, heartbeat, счётчики NO_READ/INCOMPLETE, температура, заполнение SSD, PTP/NTP drift."],
                ],
                [39 * mm, 127 * mm],
            ),
            para("Результат имеет `box_id` как ключ идемпотентности. Повторный POST не должен дважды запускать сортировочный механизм. Конфигурация versioned; каждое решение хранит версию настроек и firmware reader'ов."),
            PageBreak(),
        ]
    )

    # 8. Algorithm.
    story.extend(
        [
            section_title("07", "Алгоритм от датчика до сортировки"),
            StateDiagram(),
            data_table(
                [
                    ["Шаг", "Что происходит", "Зачем"],
                    ["1. START", "Входной W4F создаёт box_id и окно положения по энкодеру.", "Не смешать две соседние коробки."],
                    ["2. TRIGGER", "Reader'ы получают аппаратные или distance-based триггеры.", "Повторяемые кадры независимо от небольшого изменения скорости."],
                    ["3. DECODE", "Каждый DataMan ищет все разрешённые 1D/2D коды в нескольких кадрах.", "Несколько попыток при складке, блике или наклоне."],
                    ["4. NORMALIZE", "Edge проверяет формат, время, symbology, reader_id и переводит координату в систему грани.", "Отбросить повреждённое событие и сравнивать ракурсы."],
                    ["5. ASSOCIATE", "Событие попадает в box window по box_id; резервно - по времени и энкодеру.", "Reader не обязан знать бизнес-идентификатор."],
                    ["6. DEDUPE", "Одинаковые data + symbology + face в близких координатах считаются одной наклейкой.", "Не отправлять один код 20 раз из 20 кадров."],
                    ["7. COVERAGE", "Нужны 6 граней и heartbeat всех 7 reader'ов, даже когда кода нет.", "Различить честный NO_READ и отказ камеры."],
                    ["8. FINALIZE", "Выходной датчик закрывает окно; формируется OK, NO_READ или INCOMPLETE.", "Безопасное решение до сортировщика."],
                    ["9. SEND", "JSON уходит с Idempotency-Key = box_id; 3 короткие попытки.", "Пережить единичный сетевой сбой без дубля."],
                    ["10. AUDIT", "Сохраняются результат, времена, версия конфигурации и диагностика.", "Разбор ошибок и контроль метрик."],
                ],
                [24 * mm, 83 * mm, 59 * mm],
                font_size=6.9,
            ),
            Spacer(1, 3 * mm),
            callout(
                "Правило безопасности",
                "Только OK разрешает автоматическую сортировку. NO_READ и INCOMPLETE ведут в exception lane. "
                "Система не угадывает код по тексту под штрихами и не использует прошлую коробку.",
                RED,
            ),
            PageBreak(),
        ]
    )

    # 9. Dedupe and contract.
    story.extend(
        [
            section_title("08", "Несколько кодов и дедупликация"),
            para(
                "Есть два разных случая: reader много раз увидел <b>одну наклейку</b> и на коробке реально есть "
                "<b>две наклейки с одинаковыми данными</b>. Сравнивать только строку кода нельзя.",
            ),
            para("Ключ физической наклейки", H2),
            callout(
                "Упрощённая формула демо",
                "same_label = same(data, symbology, face) AND distance(position) ≤ 0,08 размера грани",
            ),
            Spacer(1, 4 * mm),
            *bullets(
                [
                    "Близкие координаты в соседних кадрах сливаются, счётчик frame_hits растёт.",
                    "Одинаковые данные в далёких координатах остаются двумя occurrences.",
                    "Для сортировки есть unique_codes, для аудита - occurrences с face, position и readers.",
                    "Если координат нет, одинаковые данные на одной грани в демо сливаются. В production координата обязательна.",
                ]
            ),
            para("Пример выходного контракта", H2),
            Table(
                [[para(
                    "{<br/>"
                    "&nbsp;&nbsp;\"box_id\": \"OZON-DEMO-001\",<br/>"
                    "&nbsp;&nbsp;\"status\": \"OK\",<br/>"
                    "&nbsp;&nbsp;\"unique_codes\": [\"24652856131000\", \"BOX-SECOND-CODE\"],<br/>"
                    "&nbsp;&nbsp;\"occurrence_count\": 3,<br/>"
                    "&nbsp;&nbsp;\"missing_faces\": [], \"missing_readers\": [],<br/>"
                    "&nbsp;&nbsp;\"processing_window_ms\": 800<br/>"
                    "}", CODE)]],
                colWidths=[166 * mm],
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F5F5")),
                        ("BOX", (0, 0), (-1, -1), 0.5, LINE_COLOR),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5 * mm),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5 * mm),
                        ("TOPPADDING", (0, 0), (-1, -1), 4 * mm),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
                    ]
                ),
            ),
            Spacer(1, 4 * mm),
            para(
                "Порог 0,08 - стартовое значение, а не догма. Его калибруют на реальных траекториях: слишком "
                "большой порог сольёт соседние наклейки, слишком маленький создаст дубли одной наклейки.",
            ),
            PageBreak(),
        ]
    )

    # 10. Libraries and NN.
    story.extend(
        [
            section_title("09", "Библиотеки и нейросети"),
            para("Нейросеть в основном решении не используется", H2),
            para(
                "Это сознательный выбор. Штрихкод - формальный сигнал с известной структурой, quiet zone и "
                "контрольной суммой. Специализированный decoder лучше объясним, быстрее на edge и не требует "
                "обучающего датасета. DataMan 3816X поддерживает Code 128, Code 39, Interleaved 2 of 5, "
                "UPC/EAN, Data Matrix, QR, PDF417, MaxiCode и Aztec.<super>[3]</super>",
            ),
            data_table(
                [
                    ["Компонент", "Где используется", "Обоснование"],
                    ["Cognex DataMan firmware", "production decode", "Аппаратно согласованные сенсор, объектив, свет и decoder; multi-reader sync; промышленная диагностика."],
                    ["Python standard library", "агрегатор, HTTP, JSON, retry, тесты", "Демо стартует без установки пакетов, а логика видна в исходниках."],
                    ["ZXing-C++ (optional)", "decode-image на локальных файлах", "Зрелая open-source C++ библиотека с Python binding и широким набором 1D/2D форматов.<super>[10]</super>"],
                    ["Pillow (optional)", "загрузка изображения", "Только адаптер формата; не участвует в production-контуре."],
                ],
                [42 * mm, 47 * mm, 77 * mm],
            ),
            para("Когда нейросеть всё-таки может понадобиться", H2),
            para(
                "Отдельная модель уместна не для декодирования, а для поиска сильно повреждённой этикетки или "
                "диагностики причин NO_READ. Это следующая версия, а не скрытая часть текущего решения. Тогда "
                "понадобится отдельное обоснование архитектуры и датасет: реальные коробки, разметка polygon/bbox, "
                "деление по партиям и складам, аугментации смаза, блика, перспективы, пыли и окклюзии. Пока такой "
                "датасет не нужен и в проект не заявлен.",
            ),
            callout(
                "Почему это честнее",
                "Добавить YOLO в презентацию легко, но без датасета с конкретной линии он увеличит риск. Базовое "
                "решение должно сначала исчерпать специализированный промышленный decoder и правильную оптику.",
                GREEN,
            ),
            PageBreak(),
        ]
    )

    # 11. Metrics.
    story.extend(
        [
            section_title("10", "Метрики и приёмочные испытания"),
            data_table(
                [
                    ["Метрика", "Формула / смысл", "Цель PoC"],
                    ["Package read rate", "коробки, где найдены все размеченные физические наклейки / все коробки", "≥ 99,9% в согласованном operational domain"],
                    ["Per-code recall", "правильно найденные наклейки / все наклейки", "≥ 99,95%"],
                    ["False decode", "значение, которого нет на коробке", "0; любая ошибка блокирует запуск"],
                    ["Silent incomplete", "неполное покрытие, ошибочно помеченное OK", "0"],
                    ["Duplicate accuracy", "правильно сохранены одинаковые коды в разных местах", "100% на специальной выборке"],
                    ["Latency", "finish trigger -> ACK от СУ", "p95 ≤ 250 ms; p99 ≤ 400 ms"],
                    ["Availability", "готовность тоннеля без планового сервиса", "≥ 99,5% на пилоте"],
                    ["NO_READ rate", "коробки с 0 codes при полном покрытии", "мониторинг по смене, reader'у и типу этикетки"],
                ],
                [38 * mm, 83 * mm, 45 * mm],
                font_size=6.9,
            ),
            para("Приёмочный набор", H2),
            *bullets(
                [
                    "Не менее 10 000 проходов после настройки. Примерно 3 000 без отказа уже дают одностороннюю 95% границу около 99,9% по правилу трёх; 10 000 дают запас и разрезы по условиям.",
                    "Реальные коробки по всем допустимым размерам, цветам картона, партиям принтера и состоянию скотча.",
                    "Каждая грань, углы, повороты 0-180°, две и более наклейки, одинаковые данные в двух местах.",
                    "Контролируемые дефекты: низкий контраст, складка, частичная окклюзия, блик, загрязнение, вибрация.",
                    "Разметка: box_id, все физические наклейки, точное значение, symbology, face, polygon, условие дефекта.",
                ]
            ),
            callout(
                "Главное правило теста",
                "Настраивать на одной части коробок, а считать метрики на другой. Иначе получится красивый, но завышенный результат.",
                ORANGE,
            ),
            PageBreak(),
        ]
    )

    # 12. Failure modes.
    story.extend(
        [
            section_title("11", "Отказы и защитные меры"),
            data_table(
                [
                    ["Риск", "Как обнаружить", "Что делать"],
                    ["Reader не отвечает", "heartbeat / нет face_observed", "INCOMPLETE, exception lane, тревога по конкретному reader_id."],
                    ["Блик от скотча", "падение quality, рост NO_READ по ракурсу", "Поляризация, угол 10-15°, второй кадр с другой экспозицией."],
                    ["Грязное стекло снизу", "дрейф контраста и NO_READ bottom", "Продувка, регламент очистки, контрольное изображение."],
                    ["Коробка перекошена", "датчики края / координата вне калибровки", "Боковые направляющие, больший FoV, reject при выходе из зоны."],
                    ["Две коробки слишком близко", "перекрытые box windows", "Замедлить/разделить поток; не угадывать привязку."],
                    ["Сбой callback", "нет 2xx ACK", "Короткий retry, локальный журнал, безопасный отвод."],
                    ["Потеря 24 V", "watchdog / UPS telemetry", "DC-buffer, fail-safe выход ПЛК, восстановление журнала."],
                    ["Gap цепляет коробку", "датчик тока, механический тест", "Носовые ролики, ограничение минимальной длины, ограждение и E-stop."],
                    ["Ложное чтение фона", "код вне polygon коробки / duplicate across boxes", "Матовый фон, ROI, checksum, spatial gate."],
                ],
                [39 * mm, 55 * mm, 72 * mm],
                font_size=6.8,
            ),
            Spacer(1, 4 * mm),
            para("Fail-safe поведение", H2),
            para(
                "Сигнал OK должен быть активным решением, а не отсутствием ошибки. При перезапуске edge, потере "
                "heartbeat, переполнении очереди или несинхронном времени линия либо направляет текущие коробки в "
                "exception lane, либо останавливается по политике склада. Это решение утверждается вместе с владельцем ПЛК.",
            ),
            PageBreak(),
        ]
    )

    # 13. Scaling.
    story.extend(
        [
            section_title("12", "Масштабирование"),
            data_table(
                [
                    ["Изменение", "Что меняем"],
                    ["Коробка меньше", "ROI по данным ToF/датчика размера; жидкая линза перефокусируется; не уменьшать FoV, пока не подтверждён X-dimension."],
                    ["Коробка больше", "Поднять/раздвинуть раму, пересчитать FoV и px/mm; при нехватке плотности разделить грань между двумя reader'ами."],
                    ["Скорость выше 1 m/s", "Сократить экспозицию или усилить импульс; увеличить частоту distance trigger; заново проверить blur и latency."],
                    ["Более мелкий код", "Узкий FoV, больше reader'ов, объектив с большим фокусным расстоянием или требование к печати."],
                    ["Новые 1D/2D типы", "Включить только нужные symbology в job reader'а; прогнать отдельную матрицу углов и размеров."],
                    ["Неровная мягкая упаковка", "Добавить 3D/ToF для формы и отдельный алгоритм локализации; коробочный тоннель напрямую не переносить."],
                    ["Несколько линий", "Один edge на линию для независимости; центрально собирать только метрики и конфигурации."],
                ],
                [47 * mm, 119 * mm],
            ),
            para("Простое правило перерасчёта", H2),
            callout(
                "Плотность",
                "px_per_mm = sensor_pixels / FoV_mm; pixels_per_module = px_per_mm × X_dimension_mm. "
                "После любого изменения коробки, дистанции или объектива этот расчёт делается заново.",
            ),
            Spacer(1, 4 * mm),
            para(
                "Механика проектируется модульно: профильная рама с координатной сеткой, отдельные узлы TOP, SIDE, "
                "END и BOTTOM. Тогда для новой линии можно добавить reader или переставить узел, не переписывая "
                "контракт событий и агрегатор.",
            ),
            para("Ограничение пропускной способности", H2),
            para(
                "При интервале 2 s поток равен 30 коробок/мин. Edge-процессор имеет большой запас, потому что получает "
                "события. Первым ограничением станет не CPU, а оптическое окно и невозможность разделить две слишком "
                "близкие коробки. Поэтому scaling начинается с механики и триггеров, а не с GPU.",
            ),
            PageBreak(),
        ]
    )

    # 14. Implementation.
    story.extend(
        [
            section_title("13", "План внедрения и состав поставки"),
            data_table(
                [
                    ["Этап", "Результат", "Критерий перехода"],
                    ["0. Уточнение", "Symbology, X-dimension, допуски коробки, интерфейс ПЛК, exception policy.", "Подписанный operational domain."],
                    ["1. Оптический PoC", "1 reader + HPIT, 200-500 худших этикеток, все углы и скорости.", "Нет false decode; recall достаточен для проектирования тоннеля."],
                    ["2. Механический стенд", "Рама, gap, 7 ракурсов, энкодер, ограждение.", "Стабильная проводка коробки, полное покрытие граней."],
                    ["3. Интеграция", "Edge software, callback ПЛК, журналы, dashboard, fail-safe.", "Сценарии отказа проходят FAT."],
                    ["4. Пилот", "10 000 размеченных проходов на линии.", "Метрики раздела 10 выполнены; SAT подписан."],
                    ["5. Эксплуатация", "Регламент очистки, запасной reader, backup конфигурации, мониторинг.", "Стабильная смена без silent incomplete."],
                ],
                [29 * mm, 86 * mm, 51 * mm],
                font_size=6.9,
            ),
            para("BOM без цены", H2),
            para(
                "В отчёте намеренно нет выдуманной стоимости: DataMan, HPIT и промышленная механика обычно "
                "котируются через поставщика, а цена зависит от региона, кабелей и сервиса. Для запроса КП нужны: "
                "7 × DM3816X, 7 × 16 mm HSLL, 7 × HPIT white с polarizer, 2 × WTB4FP, 1 × DFS60 с колесом, "
                "K410, EDS-G4012, 24 V PSU/UPS, шкаф, кабели, рама, две conveyor-секции и exception lane.",
            ),
            para("Что лежит в приложенном проекте", H2),
            *bullets(
                [
                    "`src/barcode_tunnel`: модели событий, агрегатор, HTTP API, callback и optional image decoder.",
                    "`examples/events.jsonl`: воспроизводимый сценарий с 6 гранями, повторным кадром и одинаковыми кодами в двух местах.",
                    "`tests`: проверки OK, NO_READ, INCOMPLETE, dedupe, temporal association и HTTP.",
                    "`config/tunnel.json`: ожидаемые грани, окно, radius dedupe и callback.",
                    "`README.md`: команды запуска и простое объяснение принятых решений.",
                ]
            ),
            PageBreak(),
        ]
    )

    # 15. Demo.
    story.extend(
        [
            section_title("14", "Базовая реализация"),
            para("Запуск симуляции", H2),
            Table(
                [[para("PYTHONPATH=src python3 -m barcode_tunnel simulate \\\n+examples/events.jsonl --config config/tunnel.json", CODE)]],
                colWidths=[166 * mm],
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F5F5")),
                        ("BOX", (0, 0), (-1, -1), 0.5, LINE_COLOR),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5 * mm),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5 * mm),
                        ("TOPPADDING", (0, 0), (-1, -1), 4 * mm),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
                    ]
                ),
            ),
            Spacer(1, 4 * mm),
            para("Запуск тестов", H2),
            Table(
                [[para("PYTHONPATH=src python3 -m unittest discover -s tests -v", CODE)]],
                colWidths=[166 * mm],
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F5F5")),
                        ("BOX", (0, 0), (-1, -1), 0.5, LINE_COLOR),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5 * mm),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5 * mm),
                        ("TOPPADDING", (0, 0), (-1, -1), 4 * mm),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
                    ]
                ),
            ),
            Spacer(1, 5 * mm),
            data_table(
                [
                    ["Тест", "Что доказывает"],
                    ["repeated_frames_are_deduplicated", "Два соседних кадра одной наклейки -> одна occurrence; далёкая одинаковая наклейка остаётся второй."],
                    ["missing_face_is_incomplete", "Наличие кода сверху не скрывает отказ нижней или боковой камеры."],
                    ["all_faces_without_code_is_no_read", "Полное наблюдение без кода отличается от технического отказа."],
                    ["event_without_box_id", "Событие может привязаться к единственному активному временному окну."],
                    ["invalid_face", "Некорректные входные данные отклоняются до решения сортировки."],
                    ["HTTP health/event", "Сервер отвечает и принимает старт коробки; в sandbox без loopback тест честно skip."],
                ],
                [69 * mm, 97 * mm],
            ),
            para(
                "Прототип не притворяется firmware DataMan. Он закрывает системную часть, где чаще всего появляются "
                "опасные ошибки: смешивание коробок, потеря одинаковых наклеек, silent camera failure и повторная доставка команды.",
            ),
            PageBreak(),
        ]
    )

    # 16. Conclusion and sources.
    story.extend(
        [
            section_title("15", "Вывод"),
            para(
                "Предложенная архитектура физически покрывает шесть граней, укладывается в локальный временной "
                "контур и не требует нейросети. Самые важные решения - transfer-gap для низа, короткий импульсный "
                "свет, координатная дедупликация и fail-safe статусы.",
            ),
            callout(
                "Решение о запуске",
                "GO на оптический PoC с одним DataMan 3816X. NO-GO на закупку полного комплекта, пока не известны "
                "X-dimension, реальные дефекты этикеток и механическая допустимость gap.",
                GREEN,
            ),
            Spacer(1, 5 * mm),
            para("Первичные источники", H2),
            *[
                para(item, SMALL)
                for item in [
                    "[1] Cognex. DataMan 380 Series Systems, модели DM3816QL/X и разрешение. https://docs.cognex.com/dmst_2620/web/EN/DM380_Manual/Content/Topics/getting-started/systems-380.htm",
                    "[2] Cognex. DataMan 3816 Field of View, 16/25 mm. https://docs.cognex.com/dmst_2610/web/EN/DM380_Manual/Content/Topics/setting-up-device/dm380-fov-16MP.htm",
                    "[3] Cognex. DataMan 380 specifications: codes, Ethernet, I/O, power, IP67. https://docs.cognex.com/dmst_2532/web/EN/DM380_Manual/Content/Topics/specifications/specifications-3800.htm",
                    "[4] Cognex. Lenses and Integrated Lights / HPIT accessories. https://docs.cognex.com/dmst_2530/web/EN/DM380_Manual/Content/Topics/getting-started/lenses.htm ; https://docs.cognex.com/dmst_2532/web/EN/DM380_Manual/Content/Topics/getting-started/external-lights.htm",
                    "[5] Cognex. Illumination Options. https://docs.cognex.com/dmst_2541/web/EN/DM380_Manual/Content/Topics/getting-started/Illumination-options-dm380.htm",
                    "[6] SICK. W4F miniature photoelectric sensors. https://www.sick.com/medias/Brose-en-Update-2025.pdf",
                    "[7] SICK. DFS60 incremental encoder. https://www.sick.com/il/en/catalog/products/motion-control-sensors/incremental-encoders/dfs60/c/g244428",
                    "[8] OnLogic. Karbon K410/K430 product documentation. https://support.onlogic.com/product-documentation/rugged-products/karbon-k400-series/k410-k430",
                    "[9] Moxa. EDS-G4012 Series. https://www.moxa.com/en/products/industrial-network-infrastructure/ethernet-switches/layer-2-managed-switches/eds-g4012-series",
                    "[10] ZXing-C++ project. https://github.com/zxing-cpp/zxing-cpp",
                ]
            ],
            Spacer(1, 4 * mm),
            para(
                "Версии online-документации проверены 17.09.2026. Перед закупкой нужно сверить доступные SKU, "
                "региональные сертификаты и совместимость аксессуаров у поставщика.",
                SMALL,
            ),
        ]
    )
    return story


def main() -> None:
    doc = ReportDoc(str(OUTPUT))
    doc.build(build_story())
    print(OUTPUT)


if __name__ == "__main__":
    main()
