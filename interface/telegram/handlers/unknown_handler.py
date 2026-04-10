"""
Handles the full unknown template flow:
- Saves OCR + PNG for the job
- Walks user through identifying prices to replace
- Renders PDF using OCR coordinates
- Offers fine-tune UI link with 60s cleanup timer + reprocess
"""

import asyncio
import json
import re
import shutil
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from processors.templates.price_overlay_processor import fit_font_to_height, format_price
from processors.pdf.pdf_combiner import main as combine_pdf
from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parents[3]
UNKNOWN_TEMPLATES_DIR = BASE_DIR / "data" / "unknown_templates"
OUTPUT_BASE = BASE_DIR / "data" / "jobs"
FONT_DIR = BASE_DIR / "data" / "fonts"
UNKNOWN_UI_PORT = 8002
CLEANUP_SECONDS = 60
COMMA_COEFF = 2


def normalize_price_text(text):
    return re.sub(r"[^0-9.]", "", text.strip())


def find_currency_prefix(ocr_boxes, price_box_raw, page_width, page_height):
    px = price_box_raw["left"]
    py = price_box_raw["top"]
    ph = price_box_raw["height"]
    for box in ocr_boxes:
        text = box.get("text", "").strip().upper()
        if text not in ("$", "USD"):
            continue
        if abs(box["top"] - py) > ph * 0.5:
            continue
        gap = px - (box["left"] + box["width"])
        if 0 <= gap <= 0.03:
            return {
                "x": round(box["left"] * page_width, 2),
                "y": round(box["top"] * page_height, 2),
                "w": round(box["width"] * page_width, 2),
                "h": round(box["height"] * page_height, 2),
                "text": box["text"],
            }
    return None


def find_price_in_ocr(ocr_boxes, price_text, page_width, page_height):
    target = normalize_price_text(price_text)
    try:
        target_val = float(target)
    except ValueError:
        target_val = None
    results = []
    for box in ocr_boxes:
        normalized = normalize_price_text(box.get("text", ""))
        try:
            box_val = float(normalized) if normalized else None
        except ValueError:
            box_val = None
        if normalized == target or (target_val is not None and box_val is not None and target_val == box_val):
            prefix = find_currency_prefix(ocr_boxes, box, page_width, page_height)
            bx = round(box["left"] * page_width, 2)
            by = round(box["top"] * page_height, 2)
            bw = round(box["width"] * page_width, 2)
            bh = round(box["height"] * page_height, 2)
            results.append({
                "x": bx, "y": by, "w": bw, "h": bh,
                "text": box["text"],
                "prefix": prefix,
            })
    return results if results else None


def save_job_data(job_id, ocr_result, png_path, page_width, page_height):
    job_dir = UNKNOWN_TEMPLATES_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    with open(job_dir / "ocr.json", "w", encoding="utf-8") as f:
        json.dump(ocr_result, f, indent=2)

    shutil.copy2(png_path, job_dir / "page_1.png")

    # candidates-format fine_tuning.json (empty candidates to start)
    ft = {
        "template": job_id,
        "page_width": page_width,
        "page_height": page_height,
        "candidates": []
    }
    with open(job_dir / "fine_tuning.json", "w", encoding="utf-8") as f:
        json.dump(ft, f, indent=2)

    return job_dir


def load_fine_tuning(job_id):
    path = UNKNOWN_TEMPLATES_DIR / job_id / "fine_tuning.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def save_fine_tuning(job_id, data):
    path = UNKNOWN_TEMPLATES_DIR / job_id / "fine_tuning.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_ocr(job_id):
    with open(UNKNOWN_TEMPLATES_DIR / job_id / "ocr.json") as f:
        return json.load(f)


def add_candidates(job_id, boxes, new_value):
    ft = load_fine_tuning(job_id)
    next_id = len(ft["candidates"]) + 1
    for box in boxes:
        bx, by, bw, bh = box["x"], box["y"], box["w"], box["h"]
        ft["candidates"].append({
            "id": next_id,
            "text": box["text"],
            "new_value": new_value,
            "prefix": box.get("prefix"),
            "box": {"x": bx, "y": by, "w": bw, "h": bh},
            "font": {
                "family": "Arial",
                "color": "#000000",
                "x": bx, "y": by, "w": bw, "h": bh,
                "offset_x": 0.0, "offset_y": 0.0,
                "size_px": 24,
            }
        })
        next_id += 1
    save_fine_tuning(job_id, ft)


def render_from_fine_tuning(job_id):
    ft = load_fine_tuning(job_id)
    job_dir = UNKNOWN_TEMPLATES_DIR / job_id
    png_path = job_dir / "page_1.png"

    image = Image.open(png_path).convert("RGB")
    draw = ImageDraw.Draw(image)

    for candidate in ft["candidates"]:
        box = candidate["box"]
        font_data = candidate["font"]
        new_value = candidate["new_value"]
        prefix = candidate.get("prefix")

        x = int(round(font_data["x"] + font_data.get("offset_x", 0)))
        y = int(round(font_data["y"] + font_data.get("offset_y", 0)))
        w = int(round(font_data["w"]))
        h = int(round(font_data["h"]))

        original_has_comma = "," in candidate["text"]
        new_has_comma = float(new_value) >= 1000
        adjusted_h = h
        if original_has_comma and not new_has_comma:
            adjusted_h = h - COMMA_COEFF
        elif not original_has_comma and new_has_comma:
            adjusted_h = h + COMMA_COEFF

        font = fit_font_to_height(font_data["family"], adjusted_h, candidate["text"])
        currency_symbol = prefix["text"] if prefix else ""
        wb_x = int(round(prefix["x"])) if prefix else x

        draw.rectangle([wb_x, y - 2, x + w + 2, y + h + 5], fill="#FFFFFF")

        formatted = format_price(float(new_value), {
            "currency_symbol": currency_symbol,
            "thousands_separator": ",",
            "decimal_separator": ".",
            "decimal_places": 2
        })
        text_bbox = font.getbbox(formatted)
        left, top, right, _ = text_bbox
        text_width = right - left
        draw.text(
            (x + w - text_width - left, y - top),
            formatted,
            fill=font_data.get("color", "#000000"),
            font=font
        )

    output_dir = job_dir / "output"
    output_dir.mkdir(exist_ok=True)
    out_png = output_dir / "page_1.png"
    image.save(out_png)

    combine_pdf(str(output_dir))

    final_pdf = output_dir / "final.pdf"
    output_pdf_dir = OUTPUT_BASE / job_id / "output"
    output_pdf_dir.mkdir(parents=True, exist_ok=True)
    output_pdf = output_pdf_dir / "final.pdf"
    if final_pdf.exists():
        shutil.move(str(final_pdf), str(output_pdf))

    return output_pdf


def cleanup_job(job_id):
    job_dir = UNKNOWN_TEMPLATES_DIR / job_id
    if job_dir.exists():
        shutil.rmtree(job_dir)
    output_dir = OUTPUT_BASE / job_id
    if output_dir.exists():
        shutil.rmtree(output_dir)


async def schedule_cleanup(job_id, seconds=CLEANUP_SECONDS):
    await asyncio.sleep(seconds)
    cleanup_job(job_id)


# --- Bot interaction steps ---

async def start_unknown_flow(job_id, ocr_result, png_path, page_width, page_height, message):
    save_job_data(job_id, ocr_result, png_path, page_width, page_height)
    await message.reply_text(
        "Template not recognized.\n\nPlease provide the current Price 1 that needs changing."
    )


async def handle_unknown_message(job_id, user_jobs, text, message, context):
    chat_id = message.chat_id
    state = user_jobs.get(chat_id, {}).get("unknown_state")
    ft = load_fine_tuning(job_id)
    if ft is None:
        return False

    ocr = load_ocr(job_id)
    ocr_boxes = ocr.get("google", {}).get("bounding_boxes", [])
    page_width = ft["page_width"]
    page_height = ft["page_height"]
    price_count = len(ft["candidates"])

    if state == "awaiting_current_price":
        boxes = find_price_in_ocr(ocr_boxes, text, page_width, page_height)
        if not boxes:
            await message.reply_text(
                f"Could not find \"{text}\" on the page. Please check and try again."
            )
            return True

        user_jobs[chat_id]["pending_boxes"] = boxes
        user_jobs[chat_id]["unknown_state"] = "awaiting_new_price"
        found_count = len(boxes)
        await message.reply_text(
            f"Found {found_count} occurrence(s). What should Price {price_count + 1} be replaced with?"
        )
        return True

    if state == "awaiting_new_price":
        try:
            float(text.replace(",", ""))
        except ValueError:
            await message.reply_text("Invalid price. Please enter a number like 1200 or 1,200.00")
            return True

        boxes = user_jobs[chat_id].pop("pending_boxes")
        add_candidates(job_id, boxes, text.replace(",", ""))

        ft = load_fine_tuning(job_id)
        price_count = len(ft["candidates"])
        user_jobs[chat_id]["unknown_state"] = "awaiting_current_price"

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("All done ✓", callback_data=f"unknown_done|{job_id}")
        ]])
        await message.reply_text(
            f"Got it. Any more prices to change? (Price {price_count + 1})\n\nSend the current price or tap All done.",
            reply_markup=keyboard
        )
        return True

    return False


async def finalize_unknown(job_id, chat_id, user_jobs, message, context):
    await message.reply_text("Processing, please wait...")

    try:
        output_pdf = render_from_fine_tuning(job_id)
    except Exception as e:
        import traceback
        traceback.print_exc()
        await message.reply_text(f"Error rendering: {e}")
        return

    with open(output_pdf, "rb") as f:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Looks good", callback_data=f"unknown_good|{job_id}"),
            InlineKeyboardButton("✗ I don't like it", callback_data=f"unknown_bad|{job_id}"),
        ]])
        await message.reply_document(
            document=f,
            caption="Here is your file.",
            reply_markup=keyboard
        )


async def handle_unknown_callback(query, job_id, action, user_jobs, context):
    chat_id = query.message.chat_id

    if action == "unknown_done":
        await query.answer()
        await finalize_unknown(job_id, chat_id, user_jobs, query.message, context)

    elif action == "unknown_good":
        await query.answer("Great!")
        cleanup_job(job_id)
        user_jobs.pop(chat_id, None)

    elif action == "unknown_bad":
        await query.answer()
        ui_link = f"http://localhost:{UNKNOWN_UI_PORT}/?job={job_id}"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Reprocess", callback_data=f"unknown_reprocess|{job_id}")
        ]])
        await query.message.reply_text(
            f"Open this link to adjust:\n{ui_link}\n\nWhen done, tap Reprocess.",
            reply_markup=keyboard
        )

    elif action == "unknown_reprocess":
        await query.answer()
        await finalize_unknown(job_id, chat_id, user_jobs, query.message, context)
