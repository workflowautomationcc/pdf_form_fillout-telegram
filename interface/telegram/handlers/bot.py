from dotenv import load_dotenv
load_dotenv()

import os
import uuid
import requests
import json

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

from pdf2image import convert_from_path

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
PDF_FOLDER = os.path.join(BASE_DIR, "data/input/pdf")
PNG_FOLDER = os.path.join(BASE_DIR, "data/input/images")

BOT_TOKEN = "8407912241:AAEOcZkn_1EHUxRwSXHvQs0UVN4L2nC1Jdc"  # ⚠️ replace if needed


async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = update.message

    if not message or not message.document:
        return

    document = message.document

    if not document.file_name.lower().endswith(".pdf"):
        return

    job_id = str(uuid.uuid4())

    pdf_job_folder = os.path.join(PDF_FOLDER, job_id)
    png_job_folder = os.path.join(PNG_FOLDER, job_id)

    os.makedirs(pdf_job_folder, exist_ok=True)
    os.makedirs(png_job_folder, exist_ok=True)

    pdf_path = os.path.join(pdf_job_folder, "input.pdf")

    telegram_file = await document.get_file()
    await telegram_file.download_to_drive(pdf_path)

    print(f"PDF saved: {pdf_path}")

    try:
        # PDF → PNG
        images = convert_from_path(pdf_path, dpi=300)
        first_page = images[0]

        png_path = os.path.join(png_job_folder, "page_1.png")
        first_page.save(png_path, "PNG")

        print(f"PNG created: {png_path}")

        # OCR (Eden AI)
        EDEN_API_KEY = os.getenv("EDEN_AI_API_KEY")

        url = "https://api.edenai.run/v2/ocr/ocr"

        with open(png_path, "rb") as f:
            files = {"file": f}
            headers = {
                "Authorization": f"Bearer {EDEN_API_KEY}"
            }
            data = {
                "providers": "google",
                "language": "en"
            }

            response = requests.post(url, headers=headers, files=files, data=data)

        ocr_result = response.json()
        print("OCR result received")

        # Save OCR JSON
        ocr_output_path = os.path.join(png_job_folder, "ocr.json")

        with open(ocr_output_path, "w") as f:
            json.dump(ocr_result, f, indent=2)

        print(f"OCR saved: {ocr_output_path}")

    except Exception as e:
        print("Error:", e)


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.Document.ALL, handle_pdf))

    print("Bot listening...")
    app.run_polling()


if __name__ == "__main__":
    main()