import os
import cv2
import numpy as np


def find_lines(image_path, debug_dir=None):
    """
    Find all horizontal and vertical lines + small boxes (checkboxes) in a form image.
    Returns list of shapes: [{"x", "y", "w", "h", "type": "horizontal"|"vertical"|"box"}]
    """
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 210, 255, cv2.THRESH_BINARY_INV)

    # --- Horizontal lines (15px min width, filter by aspect ratio after) ---
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1))
    horizontal = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel, iterations=2)

    # --- Vertical lines (15px min height, filter by aspect ratio after) ---
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 15))
    vertical = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel, iterations=2)

    # --- Save debug images ---
    if debug_dir is None:
        debug_dir = os.path.join(os.path.dirname(image_path), "..", "..", "tests", "debug")
    os.makedirs(debug_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(image_path))[0]
    cv2.imwrite(os.path.join(debug_dir, f"{base}_1_gray.png"), gray)
    cv2.imwrite(os.path.join(debug_dir, f"{base}_2_thresh.png"), thresh)
    cv2.imwrite(os.path.join(debug_dir, f"{base}_3_lines_mask.png"), cv2.add(horizontal, vertical))

    shapes = []

    # Extract horizontal lines: width must be at least 10x the height
    for cnt in cv2.findContours(horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > h * 10:
            shapes.append({"x": x, "y": y, "w": w, "h": h, "type": "horizontal"})

    # Extract vertical lines: height must be at least 10x the width
    for cnt in cv2.findContours(vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
        x, y, w, h = cv2.boundingRect(cnt)
        if h > w * 10:
            shapes.append({"x": x, "y": y, "w": w, "h": h, "type": "vertical"})

    # --- Detect checkboxes: hollow squares ---
    # Use RETR_TREE to find contours with holes (hollow shapes)
    all_contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if hierarchy is not None:
        for i, cnt in enumerate(all_contours):
            x, y, w, h = cv2.boundingRect(cnt)
            # Size filter: realistic checkbox range
            if w < 12 or h < 12 or w > 80 or h > 80:
                continue
            # Aspect ratio: roughly square
            if not (0.6 <= w / h <= 1.6):
                continue
            # Hollow check: contour area vs bounding box area should be small (just the border)
            cnt_area = cv2.contourArea(cnt)
            box_area = w * h
            fill_ratio = cnt_area / box_area if box_area > 0 else 1
            # A hollow square border fills ~20-40% of its bounding box
            if fill_ratio > 0.4:
                continue
            # Must have a child contour (the hollow interior)
            if hierarchy[0][i][2] == -1:
                continue
            shapes.append({"x": x, "y": y, "w": w, "h": h, "type": "box"})

    shapes.sort(key=lambda s: s["y"])
    return shapes


def annotate_lines(image_path, shapes, output_path):
    """Draw detected shapes on image for visual inspection."""
    img = cv2.imread(image_path)
    colors = {"horizontal": (0, 0, 255), "vertical": (0, 200, 0), "box": (255, 100, 0)}
    for s in shapes:
        color = colors.get(s["type"], (128, 128, 128))
        cv2.rectangle(img, (s["x"], s["y"]), (s["x"] + s["w"], s["y"] + s["h"]), color, 2)
    cv2.imwrite(output_path, img)
    print(f"  Annotated: {output_path} ({len(shapes)} shapes)")
