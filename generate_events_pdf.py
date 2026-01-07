"""
Скрипт для генерации PDF со справочником событий игры
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from game_events import POSITIVE_EVENTS, NEGATIVE_EVENTS

def create_pdf(output_path="события_игры.pdf"):
    """Создает PDF со справочником событий"""
    
    # Регистрируем шрифты для поддержки кириллицы
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
    subtitle = Paragraph("Справочник событий", subtitle_style)
    story.append(subtitle)
    story.append(Spacer(1, 20))
    
    # Стили
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
    
    event_name_style = ParagraphStyle(
        'EventName',
        parent=styles['Heading3'],
        fontName=font_name,
        fontSize=14,
        textColor=colors.HexColor('#27ae60'),
        spaceAfter=8,
        spaceBefore=15,
        fontStyle='BOLD'
    )
    
    event_name_negative_style = ParagraphStyle(
        'EventNameNegative',
        parent=styles['Heading3'],
        fontName=font_name,
        fontSize=14,
        textColor=colors.HexColor('#e74c3c'),
        spaceAfter=8,
        spaceBefore=15,
        fontStyle='BOLD'
    )
    
    description_style = ParagraphStyle(
        'Description',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=10,
        leftIndent=5,
        rightIndent=5,
        leading=14
    )
    
    impact_style = ParagraphStyle(
        'Impact',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=5,
        leftIndent=10
    )
    
    # === ПОЗИТИВНЫЕ СОБЫТИЯ ===
    story.append(Paragraph("ПОЗИТИВНЫЕ СОБЫТИЯ", section_style))
    
    for i, event in enumerate(POSITIVE_EVENTS, 1):
        story.append(Paragraph(f"{i}. {event['name']}", event_name_style))
        story.append(Paragraph(event['description'], description_style))
        
        # Влияние на ресурсы
        story.append(Paragraph("<b>Влияние на цены ресурсов:</b>", impact_style))
        resource_data = []
        for resource, modifier in sorted(event['resource_modifiers'].items()):
            change = ((modifier - 1.0) * 100)
            if modifier < 1.0:
                change_text = f"↓ {abs(change):.0f}% (дешевеет)"
                color = colors.HexColor('#27ae60')
            else:
                change_text = f"↑ {change:.0f}% (дорожает)"
                color = colors.HexColor('#e74c3c')
            resource_data.append([resource, f"{modifier:.2f}x", change_text])
        
        if resource_data:
            resource_table = Table(resource_data, colWidths=[50*mm, 25*mm, 60*mm])
            resource_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ]))
            story.append(resource_table)
            story.append(Spacer(1, 5))
        
        # Влияние на объекты
        story.append(Paragraph("<b>Влияние на доходы объектов:</b>", impact_style))
        building_data = []
        for building, modifier in sorted(event['building_modifiers'].items()):
            change = ((modifier - 1.0) * 100)
            if modifier > 1.0:
                change_text = f"↑ {change:.0f}% (больше дохода)"
                color = colors.HexColor('#27ae60')
            else:
                change_text = f"↓ {abs(change):.0f}% (меньше дохода)"
                color = colors.HexColor('#e74c3c')
            building_data.append([building, f"{modifier:.2f}x", change_text])
        
        if building_data:
            building_table = Table(building_data, colWidths=[50*mm, 25*mm, 60*mm])
            building_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ]))
            story.append(building_table)
        
        story.append(Spacer(1, 15))
    
    story.append(PageBreak())
    
    # === НЕГАТИВНЫЕ СОБЫТИЯ ===
    story.append(Paragraph("НЕГАТИВНЫЕ СОБЫТИЯ", section_style))
    
    for i, event in enumerate(NEGATIVE_EVENTS, 1):
        story.append(Paragraph(f"{i}. {event['name']}", event_name_negative_style))
        story.append(Paragraph(event['description'], description_style))
        
        # Влияние на ресурсы
        story.append(Paragraph("<b>Влияние на цены ресурсов:</b>", impact_style))
        resource_data = []
        for resource, modifier in sorted(event['resource_modifiers'].items()):
            change = ((modifier - 1.0) * 100)
            if modifier < 1.0:
                change_text = f"↓ {abs(change):.0f}% (дешевеет)"
                color = colors.HexColor('#27ae60')
            else:
                change_text = f"↑ {change:.0f}% (дорожает)"
                color = colors.HexColor('#e74c3c')
            resource_data.append([resource, f"{modifier:.2f}x", change_text])
        
        if resource_data:
            resource_table = Table(resource_data, colWidths=[50*mm, 25*mm, 60*mm])
            resource_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ]))
            story.append(resource_table)
            story.append(Spacer(1, 5))
        
        # Влияние на объекты
        story.append(Paragraph("<b>Влияние на доходы объектов:</b>", impact_style))
        building_data = []
        for building, modifier in sorted(event['building_modifiers'].items()):
            change = ((modifier - 1.0) * 100)
            if modifier > 1.0:
                change_text = f"↑ {change:.0f}% (больше дохода)"
                color = colors.HexColor('#27ae60')
            else:
                change_text = f"↓ {abs(change):.0f}% (меньше дохода)"
                color = colors.HexColor('#e74c3c')
            building_data.append([building, f"{modifier:.2f}x", change_text])
        
        if building_data:
            building_table = Table(building_data, colWidths=[50*mm, 25*mm, 60*mm])
            building_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ]))
            story.append(building_table)
        
        story.append(Spacer(1, 15))
    
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
        "<b>Примечание:</b> Каждый раунд происходит одно позитивное и одно негативное событие. "
        "События выбираются случайным образом и не повторяются до тех пор, пока не закончатся все доступные. "
        "Если событие влияет на один и тот же ресурс или объект, применяется последнее (негативное перезаписывает позитивное).",
        info_style
    ))
    
    # Собираем PDF
    doc.build(story)
    print(f"PDF создан: {output_path}")

if __name__ == "__main__":
    create_pdf("события_игры.pdf")

