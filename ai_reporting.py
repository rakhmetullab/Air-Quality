# ai_reporting.py - Функциональность AI-отчетов и анализа данных

import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from fpdf import FPDF

from config import FACILITIES_COORD, OPENAI_API_KEY
from data_service import fetch_pollution_history, get_pollutant_name_safe
import streamlit as st

def call_openai_dummy(prompt: str) -> str:
    """
    Временная заглушка функции OpenAI API для отладки.
    
    Args:
        prompt: Текстовый запрос для AI
        
    Returns:
        Фиктивный ответ
    """
    # Создаем базовый анализ на основе подсказки
    pollutants = ["CO", "NO", "NO2", "O3", "SO2", "PM2.5", "PM10"]
    
    report = """
# Air Quality Analysis Report

## Overview
This is an automatically generated report based on the pollution data provided. Due to API limitations, this is a simplified template report.

## Analysis of Current Levels

"""
    
    # Добавляем раздел для каждого загрязнителя
    for poll in pollutants:
        report += f"""
### {poll} Analysis
        
#### Potential Reasons for Observed Levels
- Industrial emissions from nearby facilities
- Weather conditions affecting dispersion
- Seasonal variations in pollution sources
        
#### Health and Operational Benefits
- Maintaining safe levels reduces respiratory health risks
- Improves working conditions for facility personnel
- Reduces long-term environmental impact
        
#### Recommendations
- Regular monitoring and maintenance of emission control systems
- Implement enhanced filtration during high-risk periods
- Consider upgrading to more efficient pollution control technology

"""
    
    # Добавляем заключение
    report += """
## Conclusion
Regular monitoring and proactive management of air quality parameters is essential for both regulatory compliance and operational efficiency. 
We recommend reviewing this data on a weekly basis and implementing the suggested improvements where applicable.
    """
    
    return report

def generate_report(df: pd.DataFrame, period: str) -> str:
    """
    Генерирует аналитический отчет на основе данных о загрязнении.
    
    Args:
        df: DataFrame с данными о загрязнении
        period: Период отчета (hourly, daily, weekly)
        
    Returns:
        Текстовый отчет с анализом
    """
    # Check if OpenAI API key is available
    if not OPENAI_API_KEY:
        st.warning("OpenAI API key is missing. Using demo mode with sample responses.")
    
    # Aggregate pollutant statistics
    agg_df = df.groupby('pollutant')['value'].agg(['min', 'max', 'mean']).round(2)
    agg = agg_df.to_dict(orient='index')
    
    # Build a detailed prompt for the AI
    summary = (
        f"Over the last {period}, the observed pollutant levels were as follows: "
        + ", ".join([
            f"{pol.upper()}: average {vals['mean']} µg/m³ (minimum {vals['min']}, maximum {vals['max']})"
            for pol, vals in agg.items()
        ]) + "."
    )

    prompt = (
        "You are an environmental AI specialist.\n\n"
        "Analyze the pollutant level summary provided below. "
        "For each pollutant, describe:\n"
        "  1. Potential reasons for the observed levels\n"
        "  2. Health and operational benefits of maintaining safe levels\n"
        "  3. Actionable recommendations\n\n"
        "Your response should be no less than 500 words, clearly structured with headings for each section.\n\n"
        f"Summary:\n{summary}"
    )

    # Используем заглушку вместо реального вызова OpenAI API
    # В будущем здесь можно добавить реальный вызов OpenAI API при наличии ключа
    if OPENAI_API_KEY:
        # TODO: Implement actual OpenAI API call here when ready
        # For now, still using the dummy function
        return call_openai_dummy(prompt)
    else:
        return call_openai_dummy(prompt)

def create_report_pdf(facility: str, period: str, timestamp: datetime, report_text: str, pollutant_data: pd.DataFrame) -> BytesIO:
    """
    Создает PDF-отчет на основе текстового анализа и данных.
    
    Args:
        facility: Название объекта
        period: Период отчета
        timestamp: Временная метка создания отчета
        report_text: Текстовый анализ от AI
        pollutant_data: DataFrame с данными о загрязнении
        
    Returns:
        BytesIO объект с PDF-файлом
    """
    try:
        # Проверяем наличие файлов шрифтов DejaVu на сервере
        import os
        font_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fonts')
        dejavu_regular = os.path.join(font_path, 'DejaVuSansCondensed.ttf')
        dejavu_bold = os.path.join(font_path, 'DejaVuSansCondensed-Bold.ttf')
        dejavu_italic = os.path.join(font_path, 'DejaVuSansCondensed-Oblique.ttf')
        
        # Если шрифты не найдены, используем стандартные шрифты и безопасные имена
        use_custom_fonts = (os.path.exists(dejavu_regular) and 
                           os.path.exists(dejavu_bold) and 
                           os.path.exists(dejavu_italic))
    except:
        use_custom_fonts = False
    
    # Инициализируем простую версию PDF без специальных шрифтов
    pdf = FPDF()
    pdf.add_page()
    
    # Используем базовые шрифты
    pdf.set_font("Arial", "B", 16)
    
    # Название
    pdf.cell(190, 10, f"Air Quality Assessment Report", ln=True, align='C')
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, f"{period} Report for {facility}", ln=True, align='C')
    
    # Дата и время
    pdf.set_font("Arial", "I", 10)
    pdf.cell(190, 10, f"Generated on: {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}", ln=True, align='C')
    pdf.ln(5)
    
    # Добавляем статистику по загрязнителям
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "Pollutant Statistics", ln=True)
    pdf.ln(2)
    
    # Создаем таблицу
    pdf.set_font("Arial", "", 9)
    col_width = 45
    row_height = 10
    
    # Заголовок таблицы
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(col_width, row_height, "Pollutant", 1, 0, 'C', True)
    pdf.cell(col_width, row_height, "Minimum (ug/m3)", 1, 0, 'C', True)
    pdf.cell(col_width, row_height, "Average (ug/m3)", 1, 0, 'C', True)
    pdf.cell(col_width, row_height, "Maximum (ug/m3)", 1, 1, 'C', True)
    
    # Получаем статистику
    stats = pollutant_data.groupby('pollutant')['value'].agg(['min', 'max', 'mean']).round(2)
    
    # Данные таблицы
    pdf.set_fill_color(255, 255, 255)
    for pollutant, row in stats.iterrows():
        # Используем безопасное имя загрязнителя
        name = get_pollutant_name_safe(pollutant)
        pdf.cell(col_width, row_height, name, 1, 0, 'C')
        pdf.cell(col_width, row_height, str(row['min']), 1, 0, 'C')
        pdf.cell(col_width, row_height, str(row['mean']), 1, 0, 'C')
        pdf.cell(col_width, row_height, str(row['max']), 1, 1, 'C')
    
    pdf.ln(10)
    
    # Добавляем AI-анализ
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "AI Analysis and Recommendations", ln=True)
    pdf.ln(2)
    
    # Форматируем и добавляем текст отчета
    pdf.set_font("Arial", "", 10)
    
    # Заменяем проблемные символы на их безопасные версии
    safe_report = (report_text
        .replace("CO₂", "CO2")
        .replace("NO₂", "NO2")
        .replace("SO₂", "SO2")
        .replace("O₃", "O3")
        .replace("PM₂.₅", "PM2.5")
        .replace("PM₁₀", "PM10")
        .replace("µg/m³", "ug/m3")
    )
    
    # Разбиваем текст на строки с учетом ширины страницы
    pdf.multi_cell(190, 7, safe_report)
    
    # Добавляем нижний колонтитул
    pdf.ln(10)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(190, 10, "This report was generated using AI analysis and should be reviewed by a qualified environmental specialist.", ln=True, align='C')
    
    # Возвращаем PDF как байты
    pdf_bytes = BytesIO()
    
    # Исправленный код для записи PDF в BytesIO
    try:
        # Попробуем использовать новую версию FPDF (fpdf2)
        pdf_output = pdf.output(dest='S')
        if isinstance(pdf_output, str):
            pdf_bytes.write(pdf_output.encode('latin-1'))
        else:
            # Уже байты или bytearray, нет необходимости в encode
            pdf_bytes.write(pdf_output)
    except Exception as e:
        # Резервный вариант для старых версий FPDF
        pdf.output(pdf_bytes, 'F')
    
    pdf_bytes.seek(0)
    return pdf_bytes

def render_ai_insights() -> None:
    """
    Отображает страницу AI-аналитики и отчетов.
    """
    st.header("🤖 AI Insights & Reports")
    
    facility = st.selectbox("Select Facility", list(FACILITIES_COORD.keys()), key="ai_facility")
    period = st.selectbox("Select Report Period", ["Hourly", "Daily", "Weekly"], key="ai_period")
    lat, lon = FACILITIES_COORD[facility]
    hours = {'Hourly':1, 'Daily':24, 'Weekly':168}[period]
    
    df = fetch_pollution_history(lat, lon, hours)
    if df.empty:
        st.error("No data available to generate report.")
        return
        
    if st.button("Generate AI Report"):
        with st.spinner("Generating AI report..."):
            report = generate_report(df, period.lower())
            st.subheader(f"{period} Report for {facility}")
            st.markdown(report)
            
            try:
                # Create PDF report
                timestamp = datetime.utcnow()
                pdf_bytes = create_report_pdf(facility, period, timestamp, report, df)
                
                # Offer download button for PDF
                st.download_button(
                    label="Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"air_quality_report_{facility.replace(' ', '_')}_{period.lower()}_{timestamp.strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    key="download_pdf",
                    help="Download the complete report as a PDF file"
                )
                
                st.success("Report generated successfully! Click the button above to download the PDF version.")
            except Exception as e:
                st.error(f"Error generating PDF: {e}")
                st.info("Although the PDF could not be generated, you can copy the text report above.")
            
            # Add option to send report by email (for future implementation)
            with st.expander("Email Options (Coming Soon)"):
                st.text_input("Email Address", placeholder="recipient@example.com")
                st.button("Send Report via Email", disabled=True)
                st.info("Email functionality will be enabled in a future update.")