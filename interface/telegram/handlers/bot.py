from dotenv import load_dotenv
load_dotenv()

import os
import requests
import json
import re
from datetime import datetime

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

from processors.pdf.pdf_splitter import split_pdf_to_images
from processors.pdf.pdf_combiner import main as combine_pdf
from processors.templates.price_overlay_processor import main as overlay_main
from processors.templates.template_matcher import match_template

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))

INPUT_BASE_FOLDER = os.path.join(BASE_DIR, "data/input")
OUTPUT_BASE_FOLDER = os.path.join(BASE_DIR, "data/output/pdf")

BOT_TOKEN = "8407912241:AAEOcZkn_1EHUxRwSXHvQs0UVN4L2nC1Jdc"

user_jobs = {}


def is_valid_price(text):
    text = text.strip()

    if not text:
        return False

    if re.search(r"[^\d,.\s]", text):
        return False

    if text.count(".") > 1:
        return False

    if ",," in text:
        return False

    if " " in text:
        parts = text.split(" ")
        if len(parts) != 2:
            return False

        left, right = parts

        if not (left.isdigit() and right.isdigit()):
            return False

        if not (1 <= len(left) <= 3 and len(right) == 3):
            return False

    return True


def normalize_price(text):
    cleaned = text.replace(" ", "").replace(",", "")

    try:
        value = float(cleaned)
        return f"{value:,.2f}"
    except:
        return None


def generate_job_id(chat_id):
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"{now}_{chat_id}"


async def try_process(chat_id, message):
    job = user_jobs.get(chat_id)

    if not job:
        return False

    if "pdf_path" not in job or "price" not in job:
        return False

    pdf_path = job["pdf_path"]
    png_job_folder = job["png_job_folder"]
    job_id = job["job_id"]
    price = job["price"]

    user_jobs.pop(chat_id)

    await message.reply_text("Processing file, please wait...")

    try:
        # folders
        input_images_folder = os.path.join(png_job_folder, "input")
        output_images_folder = os.path.join(png_job_folder, "output")

        os.makedirs(input_images_folder, exist_ok=True)
        os.makedirs(output_images_folder, exist_ok=True)

        # split PDF → input images
        image_paths = split_pdf_to_images(pdf_path, input_images_folder)
        page_1_path = image_paths[0]

        # OCR
        EDEN_API_KEY = os.getenv("EDEN_AI_API_KEY")
        url = "https://api.edenai.run/v2/ocr/ocr"

        with open(page_1_path, "rb") as f:
            files = {"file": f}
            headers = {"Authorization": f"Bearer {EDEN_API_KEY}"}
            data = {"providers": "google", "language": "en"}

            response = requests.post(url, headers=headers, files=files, data=data)

        ocr_result = response.json()

        # template match
        template_path = os.path.join(BASE_DIR, "data/templates/ATS_001/template.json")
        with open(template_path, "r") as f:
            template = json.load(f)

        if not match_template(ocr_result, template):
            await message.reply_text("Template not recognized")
            return

        # copy input → output
        for file_name in os.listdir(input_images_folder):
            src = os.path.join(input_images_folder, file_name)
            dst = os.path.join(output_images_folder, file_name)

            if os.path.isfile(src):
                with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
                    fdst.write(fsrc.read())

        # apply overlay on output images
        overlay_main(output_images_folder, price)

        # output PDF
        output_folder = os.path.join(OUTPUT_BASE_FOLDER, job_id)
        os.makedirs(output_folder, exist_ok=True)

        output_pdf_path = os.path.join(output_folder, "final.pdf")

        combine_pdf(output_images_folder)

        temp_output = os.path.join(output_images_folder, "final.pdf")

        if os.path.exists(temp_output):
            os.rename(temp_output, output_pdf_path)

        # send
        with open(output_pdf_path, "rb") as f:
            await message.reply_document(
                document=f,
                caption=f"Updated file with price: {price}"
            )

    except Exception as e:
        print("Error:", e)

    return True


async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.document:
        return

    document = message.document
    if not document.file_name.lower().endswith(".pdf"):
        return

    chat_id = message.chat_id
    job_id = generate_job_id(chat_id)

    job_folder = os.path.join(INPUT_BASE_FOLDER, job_id)

    pdf_job_folder = os.path.join(job_folder, "pdf")
    png_job_folder = os.path.join(job_folder, "images")

    os.makedirs(pdf_job_folder, exist_ok=True)
    os.makedirs(png_job_folder, exist_ok=True)

    pdf_path = os.path.join(pdf_job_folder, "input.pdf")

    telegram_file = await document.get_file()
    await telegram_file.download_to_drive(pdf_path)

    if chat_id not in user_jobs:
        user_jobs[chat_id] = {}

    user_jobs[chat_id]["pdf_path"] = pdf_path
    user_jobs[chat_id]["png_job_folder"] = png_job_folder
    user_jobs[chat_id]["job_id"] = job_id

    processed = await try_process(chat_id, message)

    if not processed:
        await message.reply_text("Send the price (e.g. 4200 or 4,200)")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    chat_id = message.chat_id
    raw_input = message.text.strip()

    if not is_valid_price(raw_input):
        await message.reply_text("Invalid format. Use 4200, 4,200 or 4 200")
        return

    normalized = normalize_price(raw_input)

    if not normalized:
        await message.reply_text("Invalid number, try again")
        return

    if chat_id not in user_jobs:
        user_jobs[chat_id] = {}

    user_jobs[chat_id]["price"] = normalized

    await try_process(chat_id, message)


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.Document.ALL, handle_pdf))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot listening...")
    app.run_polling()


if __name__ == "__main__":
    main()