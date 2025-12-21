"""
Generate November 2025 PLTR report with SIMPLE INDICATORS
✅ Only: עליה / ירידה (UP / DOWN)
"""

import yfinance as yf
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch


def fetch_stock_data(symbol: str, start_date: str, end_date: str):
    """Fetch stock data from Yahoo Finance"""
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date)
    df["Change%"] = ((df["Close"] - df["Open"]) / df["Open"] * 100).round(2)
    return df


def generate_simple_summary(row):
    """
    Generate summary with SIMPLE English indicators: UP or DOWN
    """
    close = row["Close"]
    low = row["Low"]
    high = row["High"]
    change_pct = row["Change%"]

    # 🔥 SIMPLE: Just UP or DOWN
    if change_pct > 0:
        indicator = "UP"
        desc = f"Stock rose {change_pct:.2f}% during trading."
    elif change_pct < 0:
        indicator = "DOWN"
        desc = f"Stock fell {abs(change_pct):.2f}% during trading."
    else:
        indicator = "FLAT"
        desc = "Stock closed unchanged."

    line1 = f"[{indicator}] {change_pct:+.2f}% | Close: {close:.2f} | Range: {low:.2f}–{high:.2f}"

    return f"{line1}\n{desc}"


def create_pdf_report(df, output_filename, period):
    """Create PDF with simple indicators"""
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
    )
    elements = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=colors.HexColor("#1f77b4"),
        spaceAfter=8,
    )
    title = Paragraph(f"PLTR — Daily Timeline Report ({period})", title_style)
    elements.append(title)

    # Subtitle
    subtitle = Paragraph(
        "Includes daily OHLCV with SIMPLE INDICATORS [UP/DOWN]. "
        "Prices sourced from Yahoo Finance.",
        styles["Normal"],
    )
    elements.append(subtitle)
    elements.append(Spacer(1, 0.2 * inch))

    # Summary statistics
    max_gain = df["Change%"].max()
    max_gain_date = df[df["Change%"] == max_gain].index[0].strftime("%Y-%m-%d")

    min_drop = df["Change%"].min()
    min_drop_date = df[df["Change%"] == min_drop].index[0].strftime("%Y-%m-%d")

    stats_text = f"""
    <b>Period Statistics:</b><br/>
    Total Trading Days: {len(df)} | 
    Opening: ${df['Open'].iloc[0]:.2f} | 
    Closing: ${df['Close'].iloc[-1]:.2f}<br/>
    <b>Highest Gain:</b> {max_gain:+.2f}% on {max_gain_date} | 
    <b>Largest Drop:</b> {min_drop:+.2f}% on {min_drop_date}
    """
    stats = Paragraph(stats_text, styles["Normal"])
    elements.append(stats)
    elements.append(Spacer(1, 0.2 * inch))

    # Prepare table data
    table_data = [
        [
            "Date",
            "Open",
            "High",
            "Low",
            "Close",
            "Chg %",
            "Volume",
            "Indicator & Summary",
        ]
    ]

    for idx, row in df.iterrows():
        date_str = idx.strftime("%Y-%m-%d")
        summary = generate_simple_summary(row)

        table_data.append(
            [
                date_str,
                f"{row['Open']:.2f}",
                f"{row['High']:.2f}",
                f"{row['Low']:.2f}",
                f"{row['Close']:.2f}",
                f"{row['Change%']:+.2f}%",
                f"{int(row['Volume']):,}",
                summary,
            ]
        )

    # Create table
    table = Table(
        table_data,
        colWidths=[
            0.7 * inch,
            0.6 * inch,
            0.6 * inch,
            0.6 * inch,
            0.6 * inch,
            0.6 * inch,
            1.0 * inch,
            2.2 * inch,
        ],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f77b4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 7),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 6),
                ("ALIGN", (0, 1), (6, -1), "CENTER"),
                ("ALIGN", (7, 1), (7, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f0f0f0")],
                ),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )

    elements.append(table)

    # Indicator legend
    elements.append(Spacer(1, 0.2 * inch))
    legend_title = Paragraph("<b>Indicator Legend:</b>", styles["Heading2"])
    elements.append(legend_title)

    legend_text = Paragraph(
        "[UP] = Positive change | [DOWN] = Negative change | [FLAT] = No change",
        styles["Normal"],
    )
    elements.append(legend_text)

    # Sources
    elements.append(Spacer(1, 0.2 * inch))
    sources_title = Paragraph("<b>Sources</b>", styles["Heading2"])
    elements.append(sources_title)

    sources_text = Paragraph(
        "Daily prices (OHLCV): Yahoo Finance API for PLTR.<br/>"
        "Indicators: Auto-generated based on price movements.",
        styles["Normal"],
    )
    elements.append(sources_text)

    doc.build(elements)
    print(f"✅ PDF with simple indicators generated: {output_filename}")


def main():
    """Generate November 2025 report with simple indicators"""
    symbol = "PLTR"

    start_date = "2025-11-01"
    end_date = "2025-11-30"
    period = "November 2025"

    print(f"📊 Fetching {symbol} data for {period}...")

    try:
        df = fetch_stock_data(symbol, start_date, end_date)

        if df.empty:
            print("❌ No data found")
            return

        print(f"✅ Fetched {len(df)} trading days")

        output_filename = "data/data.pdf"
        create_pdf_report(df, output_filename, period)

        print(f"\n✅ Report saved to: {output_filename}")
        print(f"📄 Trading days: {len(df)}")

        # Find highest gain
        max_gain = df["Change%"].max()
        max_date = df[df["Change%"] == max_gain].index[0].strftime("%Y-%m-%d")

        print(f"\n🎯 Highest Gain: {max_gain:+.2f}% on {max_date}")
        print(f"\n✅ SIMPLE: Added [UP]/[DOWN] indicators!")
        print(f"   Example: [UP] +5.05% or [DOWN] -3.20%")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
