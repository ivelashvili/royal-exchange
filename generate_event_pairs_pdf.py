"""
Скрипт для генерации PDF с парами событий для проверки
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from game_events import EVENT_PAIRS, POSITIVE_EVENTS, NEGATIVE_EVENTS

# Создаем словари для быстрого поиска
positive_dict = {e["name"]: e for e in POSITIVE_EVENTS}
negative_dict = {e["name"]: e for e in NEGATIVE_EVENTS}

def create_pdf(output_path="пары_событий.pdf"):
    """Создает PDF с парами событий"""
    
    # Регистрируем шрифты
    try:
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
        ]
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('UnicodeFont', font_path))
                    break
                except:
                    continue
    except:
        pass
    
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
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
    subtitle = Paragraph("Пары событий для проверки (25 пар)", subtitle_style)
    story.append(subtitle)
    story.append(Spacer(1, 20))
    
    # Стили
    pair_number_style = ParagraphStyle(
        'PairNumber',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
        spaceBefore=15,
        fontStyle='BOLD'
    )
    
    event_name_positive = ParagraphStyle(
        'EventNamePositive',
        parent=styles['Heading3'],
        fontName=font_name,
        fontSize=12,
        textColor=colors.HexColor('#27ae60'),
        spaceAfter=5,
        spaceBefore=10,
        fontStyle='BOLD'
    )
    
    event_name_negative = ParagraphStyle(
        'EventNameNegative',
        parent=styles['Heading3'],
        fontName=font_name,
        fontSize=12,
        textColor=colors.HexColor('#e74c3c'),
        spaceAfter=5,
        spaceBefore=10,
        fontStyle='BOLD'
    )
    
    description_style = ParagraphStyle(
        'Description',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=8,
        leftIndent=5,
        rightIndent=5,
        leading=12
    )
    
    impact_style = ParagraphStyle(
        'Impact',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=8,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=3,
        leftIndent=10
    )
    
    combined_style = ParagraphStyle(
        'Combined',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        textColor=colors.HexColor('#8e44ad'),
        spaceAfter=5,
        leftIndent=10,
        fontStyle='BOLD'
    )
    
    # Обрабатываем каждую пару
    for i, pair in enumerate(EVENT_PAIRS, 1):
        positive_event = positive_dict[pair["positive"]]
        negative_event = negative_dict[pair["negative"]]
        
        # Номер пары
        story.append(Paragraph(f"ПАРА {i}", pair_number_style))
        
        # Позитивное событие
        story.append(Paragraph(f"✓ {positive_event['name']}", event_name_positive))
        story.append(Paragraph(positive_event['description'], description_style))
        
        # Влияние позитивного события
        if positive_event['resource_modifiers'] or positive_event['building_modifiers']:
            story.append(Paragraph("<b>Влияние:</b>", impact_style))
            
            # Ресурсы
            if positive_event['resource_modifiers']:
                res_text = "Ресурсы: "
                res_items = []
                for res, mod in sorted(positive_event['resource_modifiers'].items()):
                    change = ((mod - 1.0) * 100)
                    if mod < 1.0:
                        res_items.append(f"{res} ({mod:.2f}x, ↓{abs(change):.0f}%)")
                    else:
                        res_items.append(f"{res} ({mod:.2f}x, ↑{change:.0f}%)")
                story.append(Paragraph(res_text + ", ".join(res_items), impact_style))
            
            # Объекты
            if positive_event['building_modifiers']:
                build_text = "Объекты: "
                build_items = []
                for build, mod in sorted(positive_event['building_modifiers'].items()):
                    change = ((mod - 1.0) * 100)
                    if mod > 1.0:
                        build_items.append(f"{build} ({mod:.2f}x, ↑{change:.0f}%)")
                    else:
                        build_items.append(f"{build} ({mod:.2f}x, ↓{abs(change):.0f}%)")
                story.append(Paragraph(build_text + ", ".join(build_items), impact_style))
        
        story.append(Spacer(1, 5))
        
        # Негативное событие
        story.append(Paragraph(f"✗ {negative_event['name']}", event_name_negative))
        story.append(Paragraph(negative_event['description'], description_style))
        
        # Влияние негативного события
        if negative_event['resource_modifiers'] or negative_event['building_modifiers']:
            story.append(Paragraph("<b>Влияние:</b>", impact_style))
            
            # Ресурсы
            if negative_event['resource_modifiers']:
                res_text = "Ресурсы: "
                res_items = []
                for res, mod in sorted(negative_event['resource_modifiers'].items()):
                    change = ((mod - 1.0) * 100)
                    if mod < 1.0:
                        res_items.append(f"{res} ({mod:.2f}x, ↓{abs(change):.0f}%)")
                    else:
                        res_items.append(f"{res} ({mod:.2f}x, ↑{change:.0f}%)")
                story.append(Paragraph(res_text + ", ".join(res_items), impact_style))
            
            # Объекты
            if negative_event['building_modifiers']:
                build_text = "Объекты: "
                build_items = []
                for build, mod in sorted(negative_event['building_modifiers'].items()):
                    change = ((mod - 1.0) * 100)
                    if mod > 1.0:
                        build_items.append(f"{build} ({mod:.2f}x, ↑{change:.0f}%)")
                    else:
                        build_items.append(f"{build} ({mod:.2f}x, ↓{abs(change):.0f}%)")
                story.append(Paragraph(build_text + ", ".join(build_items), impact_style))
        
        story.append(Spacer(1, 5))
        
        # Итоговое влияние (перемножение)
        story.append(Paragraph("<b>ИТОГОВОЕ ВЛИЯНИЕ (после перемножения):</b>", combined_style))
        
        # Находим пересечения
        combined_resources = {}
        combined_buildings = {}
        
        # Ресурсы
        for res, pos_mod in positive_event['resource_modifiers'].items():
            if res in negative_event['resource_modifiers']:
                neg_mod = negative_event['resource_modifiers'][res]
                combined_mod = pos_mod * neg_mod
                combined_resources[res] = combined_mod
        
        # Объекты
        for build, pos_mod in positive_event['building_modifiers'].items():
            if build in negative_event['building_modifiers']:
                neg_mod = negative_event['building_modifiers'][build]
                combined_mod = pos_mod * neg_mod
                combined_buildings[build] = combined_mod
        
        if combined_resources:
            res_text = "Ресурсы с пересечением: "
            res_items = []
            for res, mod in sorted(combined_resources.items()):
                change = ((mod - 1.0) * 100)
                if mod < 1.0:
                    res_items.append(f"{res} ({mod:.2f}x, ↓{abs(change):.0f}%)")
                else:
                    res_items.append(f"{res} ({mod:.2f}x, ↑{change:.0f}%)")
            story.append(Paragraph(res_text + ", ".join(res_items), combined_style))
        
        if combined_buildings:
            build_text = "Объекты с пересечением: "
            build_items = []
            for build, mod in sorted(combined_buildings.items()):
                change = ((mod - 1.0) * 100)
                if mod > 1.0:
                    build_items.append(f"{build} ({mod:.2f}x, ↑{change:.0f}%)")
                else:
                    build_items.append(f"{build} ({mod:.2f}x, ↓{abs(change):.0f}%)")
            story.append(Paragraph(build_text + ", ".join(build_items), combined_style))
        
        if not combined_resources and not combined_buildings:
            story.append(Paragraph("Пересечений нет - события влияют на разные ресурсы/объекты", combined_style))
        
        story.append(Spacer(1, 15))
        
        # Разрыв страницы каждые 3 пары
        if i % 3 == 0 and i < len(EVENT_PAIRS):
            story.append(PageBreak())
    
    # Пояснение
    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=10,
        leftIndent=10,
        rightIndent=10
    )
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "<b>Примечание:</b> Если позитивное и негативное события влияют на один и тот же ресурс или объект, "
        "их модификаторы перемножаются. Например: позитивное событие дает 0.6x, негативное дает 1.8x, "
        "итоговый модификатор = 0.6 × 1.8 = 1.08x (цена растет на 8%).",
        info_style
    ))
    
    doc.build(story)
    print(f"PDF создан: {output_path}")

if __name__ == "__main__":
    create_pdf("пары_событий.pdf")

