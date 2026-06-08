import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("EMAIL_PASSWORD")

def enviar_reporte(stats):
    try:
        fecha = datetime.now().strftime("%Y-%m-%d")
        asunto = f"🚀 Pipeline Backtest — {fecha} — {stats['gold']} tickers Gold"

        cuerpo = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">

        <h2>📊 Reporte Diario del Pipeline</h2>
        <p><strong>Fecha:</strong> {fecha}</p>
        <p><strong>Duración:</strong> {stats['duracion']} segundos ({stats['duracion']//60} minutos)</p>

        <hr>

        <h3>Resultados</h3>
        <table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f0f0f0;">
                <td><strong>Paso</strong></td>
                <td><strong>Resultado</strong></td>
            </tr>
            <tr>
                <td>🥉 Bronze</td>
                <td>✅ {stats['bronze_ok']} exitosos | ❌ {stats['bronze_fallidos']} fallidos</td>
            </tr>
            <tr>
                <td>🥈 Silver</td>
                <td>✅ {stats['silver_ok']} válidos | ⚠️ {stats['dead_letter']} Dead Letter</td>
            </tr>
            <tr>
                <td>🥇 Gold</td>
                <td>✅ {stats['gold']} tickers | ❌ {stats['gold_rechazados']} rechazados</td>
            </tr>
        </table>

        <hr>

        <h3>📁 40 Tickers seleccionados hoy</h3>
        <p style="line-height: 2;">{', '.join(stats['seleccionados'])}</p>

        <hr>

        <p style="color: gray; font-size: 12px;">
        Pipeline Backtest — {fecha}
        </p>

        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = asunto
        msg["From"] = EMAIL
        msg["To"] = EMAIL
        msg.attach(MIMEText(cuerpo, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL, PASSWORD)
            server.sendmail(EMAIL, EMAIL, msg.as_string())

        logger.info(f"📧 Reporte enviado a {EMAIL}")

    except Exception as e:
        logger.error(f"❌ Error enviando reporte: {e}")


if __name__ == "__main__":
    # Prueba del email
    enviar_reporte({
        "duracion": 1839,
        "bronze_ok": 5659,
        "bronze_fallidos": 161,
        "silver_ok": 2061,
        "dead_letter": 3098,
        "gold": 965,
        "gold_rechazados": 1096,
        "seleccionados": ["AAPL", "TSLA", "NVDA", "AMZN", "META"]
    })