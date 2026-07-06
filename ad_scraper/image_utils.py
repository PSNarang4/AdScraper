from __future__ import annotations

import random
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def draw_magnifying_glass(draw, x, y, color):
    draw.circle((x, y), 3.5, outline=color, width=2)
    draw.line([(x + 2, y + 2), (x + 5.5, y + 5.5)], fill=color, width=2)

def draw_camera(draw, x, y, color):
    draw.rounded_rectangle([(x - 5.5, y - 4), (x + 5.5, y + 4)], radius=1, outline=color, width=2)
    draw.circle((x, y), 1.5, outline=color, width=2)
    draw.rectangle([(x - 3.5, y - 5), (x - 1.5, y - 4)], fill=color)

def draw_mic(draw, x, y, color):
    draw.rounded_rectangle([(x - 1.5, y - 6), (x + 1.5, y + 2)], radius=1.5, fill=color)
    draw.arc([(x - 3.5, y - 2), (x + 3.5, y + 4)], start=0, end=180, fill=color, width=2)
    draw.line([(x, y + 4), (x, y + 6.5)], fill=color, width=2)
    draw.line([(x - 2.5, y + 6.5), (x + 2.5, y + 6.5)], fill=color, width=2)

def draw_cart(draw, x, y, color):
    draw.circle((x - 3, y + 5.5), 1.5, fill=color)
    draw.circle((x + 3, y + 5.5), 1.5, fill=color)
    draw.line([(x - 8, y - 7), (x - 6.5, y + 2), (x + 4.5, y + 2), (x + 7.5, y - 4), (x - 8, y - 4)], fill=color, width=2)
    draw.line([(x - 8, y - 7), (x - 10.5, y - 7)], fill=color, width=2)

def draw_barcode_scanner(draw, x, y, color):
    d = 4
    draw.line([(x - 5.5, y - 5.5), (x - 5.5 + d, y - 5.5)], fill=color, width=2)
    draw.line([(x - 5.5, y - 5.5), (x - 5.5, y - 5.5 + d)], fill=color, width=2)
    draw.line([(x - 5.5, y + 5.5), (x - 5.5 + d, y + 5.5)], fill=color, width=2)
    draw.line([(x - 5.5, y + 5.5), (x - 5.5, y + 5.5 - d)], fill=color, width=2)
    draw.line([(x + 5.5, y - 5.5), (x + 5.5 - d, y - 5.5)], fill=color, width=2)
    draw.line([(x + 5.5, y - 5.5), (x + 5.5, y - 5.5 + d)], fill=color, width=2)
    draw.line([(x + 5.5, y + 5.5), (x + 5.5 - d, y + 5.5)], fill=color, width=2)
    draw.line([(x + 5.5, y + 5.5), (x + 5.5, y + 5.5 - d)], fill=color, width=2)
    draw.line([(x - 3.5, y), (x + 3.5, y)], fill=(235, 50, 50), width=1)

def apply_mobile_chrome(image_path: str | Path, keyword: str = "", platform: str = "blinkit") -> None:
    path = Path(image_path)
    if not path.exists():
        return

    img = Image.open(path).convert("RGB")
    W, H = img.size

    plat = platform.lower()
    if plat in ("zepto", "flipkart"):
        bg_color = (255, 255, 255)
    elif plat == "amazon":
        bg_color = (248, 222, 173)
    else:
        bg_color = (252, 250, 242)
    text_color = (0, 0, 0)

    draw = ImageDraw.Draw(img)

    status_bar_height = 28
    draw.rectangle([(0, 0), (W, status_bar_height)], fill=bg_color)

    try:
        font_path = "C:/Windows/Fonts/segoeui.ttf"
        font = ImageFont.truetype(font_path, 12)
        font_small = ImageFont.truetype(font_path, 8)
        font_badge = ImageFont.truetype(font_path, 7)
    except Exception:
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_badge = ImageFont.load_default()

    time_str = datetime.now().strftime("%I:%M").lstrip("0")
    if not time_str:
        time_str = "5:14"
    draw.text((16, 6), time_str, fill=text_color, font=font)

    if plat in ("flipkart", "amazon"):
        loc_x = 56
        loc_y = 13
        draw.circle((loc_x, loc_y - 2), 2, outline=text_color, width=1)
        draw.line([(loc_x - 2, loc_y - 2), (loc_x, loc_y + 3), (loc_x + 2, loc_y - 2)], fill=text_color, width=1)
    else:
        snap_x = 56
        snap_y = 14
        draw.circle((snap_x, snap_y - 2), 3, outline=text_color, width=1)
        draw.line([(snap_x - 3, snap_y - 2), (snap_x - 4, snap_y + 3), (snap_x + 4, snap_y + 3), (snap_x + 3, snap_y - 2)], fill=text_color, width=1)
        draw.line([(snap_x - 4, snap_y + 3), (snap_x - 2, snap_y + 1), (snap_x, snap_y + 3), (snap_x + 2, snap_y + 1), (snap_x + 4, snap_y + 3)], fill=text_color, width=1)

    if plat != "amazon":
        mail_x = 69
        mail_y = 11
        draw.rectangle([(mail_x, mail_y), (mail_x + 9, mail_y + 6)], outline=text_color, width=1)
        draw.line([(mail_x, mail_y), (mail_x + 4, mail_y + 3), (mail_x + 9, mail_y)], fill=text_color, width=1)

    if plat != "amazon":
        chat_x = 85
        chat_y = 11
        draw.rounded_rectangle([(chat_x, chat_y), (chat_x + 8, chat_y + 6)], radius=1, outline=text_color, width=1)
        draw.polygon([(chat_x + 2, chat_y + 6), (chat_x + 1, chat_y + 8), (chat_x + 4, chat_y + 6)], fill=text_color)

    if plat != "flipkart":
        clock_x = W - 162
        clock_y = 15
        draw.circle((clock_x, clock_y), 3, outline=text_color, width=1)
        draw.line([(clock_x, clock_y), (clock_x, clock_y - 2)], fill=text_color, width=1)
        draw.line([(clock_x, clock_y), (clock_x + 2, clock_y)], fill=text_color, width=1)

    wifi_x = W - 146
    wifi_y = 17
    draw.circle((wifi_x, wifi_y), 1.5, fill=text_color)
    draw.arc([(wifi_x - 4, wifi_y - 4), (wifi_x + 4, wifi_y + 4)], start=220, end=320, fill=text_color, width=1)
    draw.arc([(wifi_x - 7, wifi_y - 7), (wifi_x + 7, wifi_y + 7)], start=220, end=320, fill=text_color, width=1)
    draw.arc([(wifi_x - 10, wifi_y - 10), (wifi_x + 10, wifi_y + 10)], start=220, end=320, fill=text_color, width=1)

    if plat == "amazon":
        bt_x = W - 128
        bt_y = 9
        bt_points = [
            (bt_x - 2.5, bt_y + 2.5),
            (bt_x + 2.5, bt_y + 7.5),
            (bt_x, bt_y + 10),
            (bt_x, bt_y),
            (bt_x + 2.5, bt_y + 2.5),
            (bt_x - 2.5, bt_y + 7.5)
        ]
        draw.line(bt_points, fill=text_color, width=1)

    volte_x = W - 117
    if plat == "zepto":
        draw.text((volte_x + 2, 6), "Vo", fill=text_color, font=font_small)
        draw.text((volte_x, 15), "LTE", fill=text_color, font=font_small)
        draw.text((volte_x + 16, 8), "5G", fill=text_color, font=font_small)
    else:
        draw.text((volte_x + 2, 6), "Vo", fill=text_color, font=font_small)
        draw.text((volte_x, 15), "LTE", fill=text_color, font=font_small)

    sig_x = W - 78
    if plat not in ("zepto", "flipkart", "amazon"):
        draw.text((sig_x - 7, 7), "R", fill=text_color, font=font_small)
    for i in range(5):
        h = 2 + i * 2
        draw.rectangle([(sig_x + i * 3, 18 - h), (sig_x + i * 3 + 1.5, 18)], fill=text_color)

    if plat == "zepto":
        bat_pct_str = "25%"
    elif plat == "flipkart":
        bat_pct_str = "73%"
    elif plat == "amazon":
        bat_pct_str = "74%"
    else:
        bat_pct_str = "39%"
    draw.text((W - 57, 6), bat_pct_str, fill=text_color, font=font)

    bat_x = W - 28
    bat_y = 10
    draw.rectangle([(bat_x, bat_y), (bat_x + 12, bat_y + 7)], outline=text_color, width=1)
    draw.rectangle([(bat_x + 13, bat_y + 2), (bat_x + 14, bat_y + 5)], fill=text_color)
    if plat == "zepto":
        fill_w = 3
    elif plat in ("flipkart", "amazon"):
        fill_w = 9
    else:
        fill_w = 5
    draw.rectangle([(bat_x + 2, bat_y + 2), (bat_x + 2 + fill_w, bat_y + 5)], fill=text_color)

    header_start_y = 28
    header_end_y = 28 + 56
    draw.rectangle([(0, header_start_y), (W, header_end_y)], fill=bg_color)

    arrow_y = header_start_y + 28
    draw.line([(16, arrow_y), (28, arrow_y)], fill=(0, 0, 0), width=2)
    draw.line([(16, arrow_y), (21, arrow_y - 5)], fill=(0, 0, 0), width=2)
    draw.line([(16, arrow_y), (21, arrow_y + 5)], fill=(0, 0, 0), width=2)

    if plat == "zepto":
        input_x1 = 40
        input_x2 = W - 16
        input_y1 = header_start_y + 10
        input_y2 = header_end_y - 10
        draw.rounded_rectangle([(input_x1, input_y1), (input_x2, input_y2)], radius=18, fill=(255, 255, 255))
        draw_magnifying_glass(draw, input_x1 + 14, header_start_y + 28, (120, 120, 120))
        draw.text((input_x1 + 28, input_y1 + 8), keyword, fill=(51, 51, 51), font=font)
    elif plat == "flipkart":
        input_x1 = 40
        input_x2 = W - 44
        input_y1 = header_start_y + 10
        input_y2 = header_end_y - 10
        draw.rounded_rectangle([(input_x1, input_y1), (input_x2, input_y2)], radius=18, fill=(255, 255, 255))
        draw_magnifying_glass(draw, input_x1 + 14, header_start_y + 28, (120, 120, 120))
        draw.text((input_x1 + 28, input_y1 + 8), keyword, fill=(51, 51, 51), font=font)
        cart_x = W - 22
        cart_y = header_start_y + 26
        draw_cart(draw, cart_x, cart_y, (0, 0, 0))
        draw.ellipse([(cart_x + 2, cart_y - 10), (cart_x + 12, cart_y)], fill=(235, 50, 50))
        draw.text((cart_x + 5, cart_y - 9), "1", fill=(255, 255, 255), font=font_badge)
    elif plat == "amazon":
        input_x1 = 40
        input_x2 = W - 44
        input_y1 = header_start_y + 10
        input_y2 = header_end_y - 10
        draw.rounded_rectangle([(input_x1, input_y1), (input_x2, input_y2)], radius=18, fill=(255, 255, 255))
        draw_magnifying_glass(draw, input_x1 + 14, header_start_y + 28, (120, 120, 120))
        draw.text((input_x1 + 28, input_y1 + 8), keyword, fill=(51, 51, 51), font=font)
        draw_camera(draw, input_x2 - 38, header_start_y + 28, (100, 100, 100))
        draw_mic(draw, input_x2 - 18, header_start_y + 28, (100, 100, 100))
        draw_barcode_scanner(draw, W - 22, header_start_y + 28, (0, 0, 0))
    else:
        input_x1 = 40
        input_x2 = W - 40
        input_y1 = header_start_y + 10
        input_y2 = header_end_y - 10
        draw.rounded_rectangle([(input_x1, input_y1), (input_x2, input_y2)], radius=18, fill=(255, 255, 255))
        draw.text((input_x1 + 16, input_y1 + 8), keyword, fill=(51, 51, 51), font=font)
        draw_mic(draw, W - 20, header_start_y + 28, (0, 0, 0))

    if plat != "amazon":
        x_circle_x = input_x2 - 18
        x_circle_y = input_y1 + 18
        draw.circle((x_circle_x, x_circle_y), 7, fill=(222, 222, 222))
        draw.line([(x_circle_x - 3, x_circle_y - 3), (x_circle_x + 3, x_circle_y + 3)], fill=(255, 255, 255), width=1)
        draw.line([(x_circle_x - 3, x_circle_y + 3), (x_circle_x + 3, x_circle_y - 3)], fill=(255, 255, 255), width=1)

    nav_bar_height = 20
    draw.rectangle([(0, H - nav_bar_height), (W, H)], fill=(0, 0, 0))

    pill_width = 120
    pill_height = 4
    pill_x1 = (W - pill_width) // 2
    pill_y1 = H - (nav_bar_height // 2) - (pill_height // 2)
    draw.rounded_rectangle([(pill_x1, pill_y1), (pill_x1 + pill_width, pill_y1 + pill_height)], radius=2, fill=(255, 255, 255))

    img.save(path)
