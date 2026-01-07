"""
Генерация PDF со сценарным анализом игры
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from scenario_analysis import generate_scenario_analysis

def create_pdf(output_path="сценарный_анализ.pdf"):
    """Создает PDF со сценарным анализом"""
    
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
    subtitle = Paragraph("Сценарный анализ: 10 наборов по 10 раундов", subtitle_style)
    story.append(subtitle)
    story.append(Spacer(1, 20))
    
    # Генерируем сценарии
    print("Генерация сценариев...")
    scenarios = generate_scenario_analysis(10, 10)
    print(f"Сгенерировано {len(scenarios)} сценариев")
    
    # Стили
    scenario_title_style = ParagraphStyle(
        'ScenarioTitle',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
        spaceBefore=20,
        fontStyle='BOLD'
    )
    
    text_style = ParagraphStyle(
        'Text',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=5,
        leading=12
    )
    
    # Обрабатываем каждый сценарий
    for scenario in scenarios:
        story.append(Paragraph(f"СЦЕНАРИЙ {scenario['scenario_num']}", scenario_title_style))
        
        # События в сценарии
        story.append(Paragraph("<b>События (10 раундов):</b>", text_style))
        events_text = []
        for i, (pos, neg) in enumerate(scenario['events_used'], 1):
            events_text.append(f"Раунд {i}: {pos} + {neg}")
        story.append(Paragraph("<br/>".join(events_text), text_style))
        story.append(Spacer(1, 10))
        
        # Изменения цен на ресурсы
        story.append(Paragraph("<b>Изменения цен на ресурсы (начало → конец):</b>", text_style))
        price_data = [["Ресурс", "Начало", "Конец", "Изменение"]]
        for resource, data in sorted(scenario["price_changes"].items()):
            change = data["change_percent"]
            change_str = f"{change:+.1f}%"
            price_data.append([
                resource,
                f"{data['start']:.2f}",
                f"{data['end']:.2f}",
                change_str
            ])
        
        price_table = Table(price_data, colWidths=[40*mm, 30*mm, 30*mm, 30*mm])
        price_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        story.append(price_table)
        story.append(Spacer(1, 10))
        
        # Доходы объектов
        story.append(Paragraph("<b>Доходы объектов за 10 раундов:</b>", text_style))
        building_data = [["Объект", "Стоимость", "Доход (монеты)", "Доход (ресурсы)", "Общий доход", "ROI %"]]
        
        # Сортируем по общему доходу
        sorted_buildings = sorted(
            scenario["building_results"].items(),
            key=lambda x: x[1]["total_income_value"],
            reverse=True
        )
        
        for building_name, data in sorted_buildings:
            # Форматируем ресурсы
            resources_str = ", ".join([
                f"{amount:.1f} {res}" 
                for res, amount in sorted(data["total_income_resources"].items())
            ]) if data["total_income_resources"] else "—"
            
            building_data.append([
                building_name,
                f"{data['cost']:.0f}",
                f"{data['total_income_coins']:.2f}",
                resources_str[:30] + "..." if len(resources_str) > 30 else resources_str,
                f"{data['total_income_value']:.2f}",
                f"{data['roi_percent']:.1f}%"
            ])
        
        building_table = Table(building_data, colWidths=[35*mm, 25*mm, 25*mm, 40*mm, 25*mm, 20*mm])
        building_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(building_table)
        
        story.append(Spacer(1, 15))
        
        # Разрыв страницы между сценариями
        if scenario['scenario_num'] < len(scenarios):
            story.append(PageBreak())
    
    # Пояснение
    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=8,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=10,
        leftIndent=10,
        rightIndent=10
    )
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "<b>Примечание:</b> Анализ проведен с учетом только влияния событий на цены и доходы. "
        "В реальной игре также будут влиять спрос/предложение игроков и насыщение рынка объектами. "
        "ROI рассчитывается как процент от стоимости объекта за 10 раундов.",
        info_style
    ))
    
    doc.build(story)
    print(f"PDF создан: {output_path}")

if __name__ == "__main__":
    create_pdf("сценарный_анализ.pdf")

