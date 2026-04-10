from dotenv import load_dotenv
load_dotenv()

import os
import requests
import json
import re
from datetime import datetime

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

from telegram.ext import CallbackQueryHandler

from processors.pdf.pdf_splitter import split_pdf_to_images
from processors.pdf.pdf_combiner import main as combine_pdf
from processors.templates.price_overlay_processor import main as overlay_main
from processors.templates.template_matcher import find_matching_template
from interface.telegram.handlers.unknown_handler import (
    start_unknown_flow,
    handle_unknown_message,
    handle_unknown_callback,
)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))

JOBS_BASE_FOLDER = os.path.join(BASE_DIR, "data/jobs")
TEMPLATES_DIR = os.path.join(BASE_DIR, "data/templates")
LOG_FILE = os.path.join(BASE_DIR, "data/logs/jobs.json")

BOT_TOKEN = "8407912241:AAEOcZkn_1EHUxRwSXHvQs0UVN4L2nC1Jdc"

user_jobs = {}


def log_job(status, job_id):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    entry = {
        "job_id": job_id,
        "timestamp": datetime.now().isoformat(),
        "status": status
    }

    data = []

    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
                    if not isinstance(data, list):
                        data = []
        except Exception:
            data = []

    data.append(entry)

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


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
        return value
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
        input_images_folder = png_job_folder
        output_images_folder = os.path.join(JOBS_BASE_FOLDER, job_id, "output", "images")

        os.makedirs(output_images_folder, exist_ok=True)

        image_paths = split_pdf_to_images(pdf_path, input_images_folder)
        page_1_path = image_paths[0]

        EDEN_API_KEY = os.getenv("EDEN_AI_API_KEY")
        url = "https://api.edenai.run/v2/ocr/ocr"

        with open(page_1_path, "rb") as f:
            files = {"file": f}
            headers = {"Authorization": f"Bearer {EDEN_API_KEY}"}
            data = {"providers": "google", "language": "en"}

            response = requests.post(url, headers=headers, files=files, data=data)

        ocr_result = response.json()

        template = find_matching_template(ocr_result, TEMPLATES_DIR)

        if not template:
            log_job("failed", job_id)
            from PIL import Image as _Image
            with _Image.open(page_1_path) as _img:
                _pw, _ph = _img.size
            user_jobs[chat_id] = {
                "unknown_job_id": job_id,
                "unknown_state": "awaiting_current_price",
            }
            await start_unknown_flow(
                job_id, ocr_result, page_1_path,
                page_width=_pw, page_height=_ph,
                message=message
            )
            return

        for file_name in os.listdir(input_images_folder):
            src = os.path.join(input_images_folder, file_name)
            dst = os.path.join(output_images_folder, file_name)

            if os.path.isfile(src):
                with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
                    fdst.write(fsrc.read())

        overlay_main(output_images_folder, price, template)

        output_pdf_path = os.path.join(JOBS_BASE_FOLDER, job_id, "output", "final.pdf")

        combine_pdf(output_images_folder)

        temp_output = os.path.join(output_images_folder, "final.pdf")

        if os.path.exists(temp_output):
            os.rename(temp_output, output_pdf_path)

        with open(output_pdf_path, "rb") as f:
            await message.reply_document(
                document=f,
                caption="Updated file"
            )

        log_job("success", job_id)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Error:", e)
        log_job("failed", job_id)

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

    job_folder = os.path.join(JOBS_BASE_FOLDER, job_id)

    pdf_job_folder = os.path.join(job_folder, "input", "pdf")
    png_job_folder = os.path.join(job_folder, "input", "images")

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

    # Unknown template flow takes priority
    job = user_jobs.get(chat_id, {})
    if job.get("unknown_state"):
        job_id = job.get("unknown_job_id")
        handled = await handle_unknown_message(job_id, user_jobs, raw_input, message, context)
        if handled:
            return

    # Only respond if user has an active job
    if chat_id not in user_jobs:
        return

    if not is_valid_price(raw_input):
        await message.reply_text("Invalid format. Use 4200, 4,200 or 4 200")
        return

    normalized = normalize_price(raw_input)

    if not normalized:
        await message.reply_text("Invalid number, try again")
        return

    user_jobs[chat_id]["price"] = normalized

    await try_process(chat_id, message)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data:
        return

    data = query.data
    if "|" not in data:
        return

    action, job_id = data.split("|", 1)
    if action.startswith("unknown_"):
        await handle_unknown_callback(query, job_id, action, user_jobs, context)


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.Document.ALL, handle_pdf))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("Bot listening...")
    app.run_polling()


if __name__ == "__main__":
    main()