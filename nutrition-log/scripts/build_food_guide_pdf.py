#!/usr/bin/env python3
"""Build the 'Guida Alimenti' reference PDF (carbs/protein/fat/micronutrient rankings)."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)

OUTPUT_PATH = "guida-alimenti-nutrizione.pdf"

styles = getSampleStyleSheet()
title_style = ParagraphStyle("TitleIT", parent=styles["Title"], fontSize=20, spaceAfter=6)
subtitle_style = ParagraphStyle("SubtitleIT", parent=styles["Normal"], fontSize=11, textColor=colors.grey, spaceAfter=14)
h2_style = ParagraphStyle("H2IT", parent=styles["Heading2"], fontSize=15, spaceBefore=18, spaceAfter=4, textColor=colors.HexColor("#1f3d5c"))
note_style = ParagraphStyle("NoteIT", parent=styles["Normal"], fontSize=9.5, textColor=colors.grey, spaceAfter=10, leading=13)
cell_style = ParagraphStyle("CellIT", parent=styles["Normal"], fontSize=9.5, leading=12)
cell_bold = ParagraphStyle("CellBoldIT", parent=cell_style, fontName="Helvetica-Bold")

HEADER_BG = colors.HexColor("#1f3d5c")
ROW_ALT_BG = colors.HexColor("#f2f5f8")


def p(text, style=cell_style):
    return Paragraph(text, style)


def build_table(rows, col_widths):
    header = [p(h, cell_bold) for h in rows[0]]
    data = [header] + [[p(c) for c in row] for row in rows[1:]]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9d2da")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT_BG))
    table.setStyle(TableStyle(style))
    return table


carb_rows = [
    ["#", "Alimento", "Carboidrati /100g", "Score", "Nota"],
    ["1", "Avena (fiocchi)", "~60 g", "9/10", "Integrale, fibra alta, rilascio graduale"],
    ["2", "Legumi (cotti)", "~20 g", "9/10", "Fibra, proteine, micronutrienti, GI basso"],
    ["3", "Pasta integrale (cotta)", "~28 g", "8/10", "Più fibra e più lenta della raffinata"],
    ["4", "Cereali integrali (farro, orzo)", "~25 g", "8/10", "Fibra, GI basso"],
    ["5", "Banana", "~23 g", "8/10", "Fibra + potassio + micronutrienti"],
    ["6", "Pane integrale", "~45 g", "7/10", "Più fibra e più saziante del pane bianco"],
    ["7", "Patate (bollite)", "~17 g", "7/10", "Potassio, alimento intero"],
    ["8", "Pasta (raffinata, cotta)", "~30 g", "5/10", "Pratica, ottima pre-lungo/pre-gara"],
    ["9", "Riso bianco (cotto)", "~28 g", "4/10", "Raffinato, ma leggero pre-corsa"],
    ["10", "Pane (raffinato)", "~50 g", "4/10", "Raffinato, poca fibra"],
]

protein_rows = [
    ["#", "Alimento", "Proteine /100g", "Score", "Nota"],
    ["1", "Pollo", "~25-31 g", "9/10", "Magro, fresco, completo"],
    ["2", "Pesce in generale", "~20-25 g", "9/10", "Fresco, completo, bonus omega-3"],
    ["3", "Tonno", "~25 g", "8/10", "Pratico, completo"],
    ["4", "Uova", "~13 g", "8/10", "Completo, poco lavorato, versatile"],
    ["5", "Yogurt greco", "~10 g", "8/10", "Fresco, completo, pratico"],
    ["6", "Bresaola", "~32 g", "7/10", "Magra e completa, ma processata"],
    ["7", "Legumi", "~7-9 g", "7/10", "Vegetale, fibra bonus"],
    ["8", "Ricotta / fiocchi di latte", "~11-13 g", "7/10", "Fresco, completo"],
    ["9", "Carne rossa", "~26-27 g", "6/10", "Completo ma più grassi saturi"],
    ["10", "Parmigiano / grana", "~33 g", "5/10", "Molto grasso e salato, booster"],
]

fat_rows = [
    ["#", "Alimento", "Grassi /100g", "Score", "Nota"],
    ["1", "Olio extravergine d'oliva", "~100 g", "9/10", "Monoinsaturo, il migliore"],
    ["2", "Noci", "~65 g", "9/10", "Omega-3 vegetali"],
    ["3", "Pesce grasso (salmone, sgombro)", "~13 g", "9/10", "Omega-3 essenziali + proteina"],
    ["4", "Mandorle", "~50 g", "8/10", "Grassi buoni + vitamina E"],
    ["5", "Semi di lino / chia", "~40 g", "8/10", "Omega-3 + fibra"],
    ["6", "Avocado", "~15 g", "8/10", "Monoinsaturi + fibra"],
    ["7", "Arachidi", "~49 g", "6/10", "Ok ma calorico, porzioni piccole"],
    ["8", "Formaggi stagionati", "~28 g", "4/10", "Saturi, ok come booster"],
    ["9", "Burro", "~81 g", "3/10", "Saturo, da limitare"],
    ["10", "Salumi grassi (salame, pancetta, mortadella)", "~30-40 g", "3/10", "Saturi + sodio alto"],
]

micro_rows = [
    ["#", "Alimento", "Score", "Nota"],
    ["1", "Verdure a foglia verde", "9/10", "Ferro, vitamina K, folati, magnesio"],
    ["2", "Pesce grasso (salmone, sgombro, sardine)", "9/10", "Omega-3, vitamina D, B12"],
    ["3", "Agrumi", "8/10", "Vitamina C, assorbimento ferro"],
    ["4", "Legumi", "8/10", "Ferro, folati, fibra, magnesio"],
    ["5", "Broccoli / crucifere", "8/10", "Vitamina C, K, folati, fibra"],
    ["6", "Uova", "8/10", "B12, colina, vitamina D"],
    ["7", "Frutta secca (noci/mandorle)", "7/10", "Magnesio, vitamina E"],
    ["8", "Latticini (yogurt, latte)", "7/10", "Calcio, B12, proteine"],
    ["9", "Frutti di bosco", "7/10", "Antiossidanti, vitamina C, fibra"],
    ["10", "Cereali integrali", "6/10", "Magnesio, fibra, vitamine gruppo B"],
]


def main():
    doc = SimpleDocTemplate(
        OUTPUT_PATH, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
    )
    story = []

    story.append(Paragraph("Guida agli Alimenti", title_style))
    story.append(Paragraph(
        "Classifiche di riferimento per carboidrati, proteine, grassi e micronutrienti "
        "&mdash; preparata per il piano nutrizionale personale.",
        subtitle_style,
    ))
    story.append(Paragraph(
        "Nota metodologica: i valori per 100&nbsp;g sono indicativi (porzioni come consumate/cotte dove "
        "rilevante). Lo &ldquo;Score&rdquo; 1-10 è una valutazione pratica elaborata per questo documento "
        "(qualità nutrizionale, fibra, livello di lavorazione, praticità), non un indice clinico ufficiale "
        "(es. ANDI) &mdash; va preso come orientamento generale, non come dato scientifico preciso.",
        note_style,
    ))

    story.append(Paragraph("Top 10 &mdash; Fonti di Carboidrati", h2_style))
    story.append(Paragraph("Orientato a un runner: fibra, densità di micronutrienti, profilo glicemico, integrale vs raffinato.", note_style))
    story.append(build_table(carb_rows, [1.1 * cm, 6.3 * cm, 2.6 * cm, 1.6 * cm, 4.9 * cm]))

    story.append(Paragraph("Top 10 &mdash; Fonti di Proteine", h2_style))
    story.append(Paragraph("Valutate per magrezza, completezza aminoacidica, livello di lavorazione e praticità quotidiana.", note_style))
    story.append(build_table(protein_rows, [1.1 * cm, 6.3 * cm, 2.6 * cm, 1.6 * cm, 4.9 * cm]))

    story.append(PageBreak())

    story.append(Paragraph("Top 10 &mdash; Fonti di Grassi", h2_style))
    story.append(Paragraph("Non tutti i grassi sono uguali: valutati per qualità del profilo lipidico (mono/poli-insaturi e omega-3 in alto, saturi in basso).", note_style))
    story.append(build_table(fat_rows, [1.1 * cm, 7.3 * cm, 2.3 * cm, 1.6 * cm, 4.2 * cm]))

    story.append(Paragraph("Top 10 &mdash; Alimenti per Micronutrienti", h2_style))
    story.append(Paragraph("Densità di vitamine e minerali: score pratico semplificato di orientamento.", note_style))
    story.append(build_table(micro_rows, [1.1 * cm, 8.3 * cm, 1.8 * cm, 5.3 * cm]))

    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "Documento generato come riferimento personale nell'ambito del piano di coaching nutrizionale "
        "(nutrition-log/nutrition-profile.json). Non sostituisce il parere di un medico o nutrizionista.",
        note_style,
    ))

    doc.build(story)
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
