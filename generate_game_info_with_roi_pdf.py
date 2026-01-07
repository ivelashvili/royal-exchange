"""
Скрипт для генерации PDF с информацией о ресурсах и объектах игры
Включает расчет доходности в процентах
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from game_config import RESOURCE_PRICES, BUILDING_COSTS, BUILDING_INCOME, BUILDING_CONSTRUCTION_TIME, STARTING_MONEY

def calculate_building_cost(building_name, costs):
    """Рассчитывает стоимость объекта в монетах"""
    total = 0
    for resource, amount in costs.items():
        total += amount * RESOURCE_PRICES.get(resource, 0)
    return total

def calculate_total_income_value(income_data):
    """Рассчитывает общую стоимость дохода в монетах"""
    total = income_data.get("монеты", 0)
    if income_data.get("ресурсы"):
        for resource, amount in income_data["ресурсы"].items():
            total += amount * RESOURCE_PRICES.get(resource, 0)
    return total

def calculate_roi_percentage(building_cost, income_value):
    """Рассчитывает доходность в процентах за раунд"""
    if building_cost == 0:
        return 0
    return (income_value / building_cost) * 100

def format_income(income_data):
    """Форматирует доход в читаемый вид"""
    parts = []
    if income_data.get("монеты", 0) > 0:
        parts.append(f"{income_data['монеты']} монет")
    if income_data.get("ресурсы"):
        for res, amount in income_data["ресурсы"].items():
            parts.append(f"{amount} {res}")
    return ", ".join(parts) if parts else "—"

def format_costs(costs_dict):
    """Форматирует стоимость в читаемый вид"""
    parts = []
    for resource, amount in sorted(costs_dict.items()):
        parts.append(f"{amount} {resource}")
    return ", ".join(parts)

def create_pdf(output_path="игра_информация_с_доходностью.pdf"):
    """Создает PDF с информацией об игре и доходностью"""
    
    # Регистрируем шрифты для поддержки кириллицы
    try:
        # Пробуем найти системные шрифты
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
        ]
        font_registered = False
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('UnicodeFont', font_path))
                    font_registered = True
                    break
                except:
                    continue
    except:
        pass
    
    # Создаем документ
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Определяем шрифт
    font_name = 'UnicodeFont' if 'UnicodeFont' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
    
    # Заголовок
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=20,
        alignment=1,
        fontStyle='BOLD'
    )
    title = Paragraph("КОРОЛЕВСКАЯ БИРЖА", title_style)
    story.append(title)
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=14,
        textColor=colors.HexColor('#666666'),
        spaceAfter=30,
        alignment=1
    )
    subtitle = Paragraph("Справочник ресурсов и объектов с доходностью", subtitle_style)
    story.append(subtitle)
    story.append(Spacer(1, 20))
    
    # === РАЗДЕЛ 1: РЕСУРСЫ ===
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=18,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=15,
        spaceBefore=20,
        fontStyle='BOLD'
    )
    story.append(Paragraph("РЕСУРСЫ", section_style))
    
    # Таблица ресурсов
    resource_data = [["Ресурс", "Начальная цена (монет)"]]
    for resource, price in sorted(RESOURCE_PRICES.items()):
        resource_data.append([resource, str(price)])
    
    resource_table = Table(resource_data, colWidths=[120*mm, 70*mm])
    resource_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
        ('FONTNAME', (0, 1), (-1, -1), font_name),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    story.append(resource_table)
    story.append(Spacer(1, 10))
    
    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=20,
        leftIndent=10
    )
    story.append(Paragraph(f"<b>Начальный капитал каждого игрока:</b> {STARTING_MONEY} монет", info_style))
    story.append(PageBreak())
    
    # === РАЗДЕЛ 2: ОБЪЕКТЫ ===
    story.append(Paragraph("ОБЪЕКТЫ", section_style))
    
    # Таблица объектов с полной информацией
    building_data = [["Объект", "Стоимость (ресурсы)", "Стоимость (монет)", "Время стр-ва", "Доход за раунд", "Доходность %"]]
    
    # Сортируем объекты по стоимости (от дешевых к дорогим)
    buildings_with_data = []
    for building in BUILDING_COSTS.keys():
        costs = BUILDING_COSTS[building]
        cost_monets = calculate_building_cost(building, costs)
        income_data = BUILDING_INCOME[building]
        income_value = calculate_total_income_value(income_data)
        roi = calculate_roi_percentage(cost_monets, income_value)
        buildings_with_data.append((building, costs, cost_monets, income_data, income_value, roi))
    
    # Сортируем по стоимости (от дешевых к дорогим)
    buildings_with_data.sort(key=lambda x: x[2])
    
    for building, costs, cost_monets, income_data, income_value, roi in buildings_with_data:
        build_time = BUILDING_CONSTRUCTION_TIME[building]
        cost_str = format_costs(costs)
        income = format_income(income_data)
        roi_str = f"{roi:.1f}%"
        
        building_data.append([
            building,
            cost_str,
            f"{cost_monets}",
            f"{build_time} раунд{'а' if build_time > 1 else ''}",
            income,
            roi_str
        ])
    
    building_table = Table(building_data, colWidths=[40*mm, 55*mm, 25*mm, 20*mm, 45*mm, 25*mm])
    building_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),
        ('ALIGN', (3, 1), (3, -1), 'CENTER'),
        ('ALIGN', (5, 1), (5, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
        ('FONTNAME', (0, 1), (-1, -1), font_name),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('WORDWRAP', (0, 0), (-1, -1), True),
        # Цветовая индикация доходности
        ('TEXTCOLOR', (5, 1), (5, -1), colors.HexColor('#27ae60')),  # Зеленый для доходности
    ]))
    story.append(building_table)
    
    story.append(Spacer(1, 15))
    
    # Пояснение
    explanation_style = ParagraphStyle(
        'Explanation',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=10,
        leftIndent=10
    )
    story.append(Paragraph(
        "<b>Примечание:</b> Доходность рассчитывается как процент от стоимости объекта за один раунд. "
        "Учитываются как монеты, так и ресурсы (по начальным ценам). Объекты отсортированы по стоимости от дешевых к дорогим.",
        explanation_style
    ))
    
    # Собираем PDF
    doc.build(story)
    print(f"PDF создан: {output_path}")

if __name__ == "__main__":
    create_pdf("игра_информация_с_доходностью.pdf")
