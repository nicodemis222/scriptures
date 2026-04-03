#!/usr/bin/env python3
"""Generate professional scripture app icon for Tauri macOS app."""

from PIL import Image, ImageDraw, ImageFont
import math
import os

def create_scripture_icon(size):
    """Create a professional scripture/Bible reader icon."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    s = size

    # --- Background: rounded rectangle with dark gradient ---
    corner_r = int(s * 0.19)
    bg_top = (35, 30, 38)
    bg_bot = (22, 20, 26)

    for y in range(s):
        t = y / s
        r = int(bg_top[0] * (1 - t) + bg_bot[0] * t)
        g = int(bg_top[1] * (1 - t) + bg_bot[1] * t)
        b = int(bg_top[2] * (1 - t) + bg_bot[2] * t)
        draw.line([(0, y), (s - 1, y)], fill=(r, g, b, 255))

    mask = Image.new('L', (s, s), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, s - 1, s - 1], radius=corner_r, fill=255)
    img.putalpha(mask)
    draw = ImageDraw.Draw(img)

    # --- Subtle radial glow behind book ---
    glow_img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_img)
    cx, cy = s // 2, int(s * 0.48)
    max_r = int(s * 0.38)
    for radius in range(max_r, 0, -1):
        t = radius / max_r
        alpha = int(40 * (1 - t * t))
        glow_draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                         fill=(210, 170, 80, alpha))
    img = Image.alpha_composite(img, glow_img)
    draw = ImageDraw.Draw(img)

    # --- Light rays emanating from center ---
    rays_img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    rays_draw = ImageDraw.Draw(rays_img)
    ray_cx, ray_cy = s // 2, int(s * 0.45)
    num_rays = 12
    for i in range(num_rays):
        angle = (2 * math.pi * i / num_rays) - math.pi / 2
        inner_r = int(s * 0.28)
        outer_r = int(s * 0.46)
        half_w = math.pi / (num_rays * 2.5)
        x1 = ray_cx + int(inner_r * math.cos(angle - half_w))
        y1 = ray_cy + int(inner_r * math.sin(angle - half_w))
        x2 = ray_cx + int(outer_r * math.cos(angle))
        y2 = ray_cy + int(outer_r * math.sin(angle))
        x3 = ray_cx + int(inner_r * math.cos(angle + half_w))
        y3 = ray_cy + int(inner_r * math.sin(angle + half_w))
        rays_draw.polygon([(ray_cx, ray_cy), (x1, y1), (x2, y2), (x3, y3)],
                         fill=(210, 175, 80, 15))
    img = Image.alpha_composite(img, rays_img)
    draw = ImageDraw.Draw(img)

    # --- Book dimensions ---
    book_cx = s // 2
    book_cy = int(s * 0.52)
    book_w = int(s * 0.62)
    book_h = int(s * 0.44)

    lp_left = book_cx - int(book_w * 0.50)
    lp_right = book_cx - int(s * 0.01)
    lp_top = book_cy - int(book_h * 0.48)
    lp_bot = book_cy + int(book_h * 0.48)
    rp_left = book_cx + int(s * 0.01)
    rp_right = book_cx + int(book_w * 0.50)
    rp_top = lp_top
    rp_bot = lp_bot

    # Cover shadow
    shadow_off = int(s * 0.015)
    draw.rounded_rectangle(
        [lp_left + shadow_off, lp_top + shadow_off,
         rp_right + shadow_off, lp_bot + shadow_off],
        radius=int(s * 0.02), fill=(10, 8, 12, 120))

    # Book cover edges
    cover_color = (90, 55, 30)
    cover_offset = int(s * 0.012)
    draw.rounded_rectangle(
        [lp_left - cover_offset, lp_top + cover_offset,
         rp_right + cover_offset, lp_bot + cover_offset],
        radius=int(s * 0.02), fill=cover_color)

    # Pages
    page_color = (245, 235, 215)
    page_color_r = (240, 230, 210)
    draw.rounded_rectangle([lp_left, lp_top, lp_right, lp_bot],
                          radius=int(s * 0.015), fill=page_color)
    draw.rounded_rectangle([rp_left, rp_top, rp_right, rp_bot],
                          radius=int(s * 0.015), fill=page_color_r)

    # Center spine
    spine_color = (180, 160, 130)
    draw.line([(book_cx, lp_top), (book_cx, lp_bot)],
             fill=spine_color, width=max(1, int(s * 0.006)))

    # --- Text lines on pages ---
    line_color = (180, 165, 140, 180)
    line_h = max(1, int(s * 0.012))
    line_gap = int(s * 0.028)
    line_mx = int(s * 0.035)
    line_mt = int(s * 0.05)

    # Left page lines
    ly = lp_top + line_mt
    idx = 0
    while ly + line_h < lp_bot - int(s * 0.04):
        lx1 = lp_left + line_mx
        factor = 0.85 if idx % 3 != 0 else 0.6
        lx2 = lp_right - line_mx
        actual_x2 = lx1 + int((lx2 - lx1) * factor)
        draw.rounded_rectangle([lx1, ly, actual_x2, ly + line_h],
                              radius=max(1, line_h // 2), fill=line_color)
        ly += line_gap
        idx += 1

    # Right page lines
    ly = rp_top + line_mt
    idx = 0
    while ly + line_h < rp_bot - int(s * 0.04):
        lx1 = rp_left + line_mx
        factor = 0.9 if idx % 4 != 0 else 0.55
        lx2 = rp_right - line_mx
        actual_x2 = lx1 + int((lx2 - lx1) * factor)
        draw.rounded_rectangle([lx1, ly, actual_x2, ly + line_h],
                              radius=max(1, line_h // 2), fill=line_color)
        ly += line_gap
        idx += 1

    # --- Small golden cross on left page ---
    cross_cx = (lp_left + lp_right) // 2
    cross_cy = lp_top + int(s * 0.03)
    cross_h = int(s * 0.055)
    cross_w = int(s * 0.035)
    cross_thick = max(1, int(s * 0.012))
    gold = (195, 160, 80, 200)
    draw.rounded_rectangle(
        [cross_cx - cross_thick // 2, cross_cy - cross_h // 2,
         cross_cx + cross_thick // 2, cross_cy + cross_h // 2],
        radius=max(1, cross_thick // 3), fill=gold)
    hbar_y = cross_cy - int(cross_h * 0.15)
    draw.rounded_rectangle(
        [cross_cx - cross_w // 2, hbar_y - cross_thick // 2,
         cross_cx + cross_w // 2, hbar_y + cross_thick // 2],
        radius=max(1, cross_thick // 3), fill=gold)

    # --- Golden banner with "S" at top ---
    banner_w = int(s * 0.30)
    banner_h = int(s * 0.09)
    banner_y = int(s * 0.10)
    banner_left = book_cx - banner_w // 2
    banner_right = book_cx + banner_w // 2

    gold_mid = (200, 165, 70)
    gold_light = (225, 195, 100)

    draw.rounded_rectangle(
        [banner_left, banner_y, banner_right, banner_y + banner_h],
        radius=int(s * 0.02), fill=gold_mid)
    draw.rounded_rectangle(
        [banner_left + int(s * 0.01), banner_y + int(s * 0.005),
         banner_right - int(s * 0.01), banner_y + int(banner_h * 0.45)],
        radius=int(s * 0.015), fill=gold_light)

    try:
        font_size = int(banner_h * 0.75)
        font = ImageFont.truetype(
            "/System/Library/Fonts/Supplemental/Georgia Bold.ttf", font_size)
    except Exception:
        try:
            font = ImageFont.truetype(
                "/System/Library/Fonts/Georgia.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

    text = "S"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = book_cx - tw // 2
    ty = banner_y + (banner_h - th) // 2 - bbox[1]
    draw.text((tx, ty), text, fill=(60, 40, 15), font=font)

    # --- Thin golden border ---
    border_img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border_img)
    border_draw.rounded_rectangle(
        [1, 1, s - 2, s - 2], radius=corner_r,
        outline=(180, 150, 70, 50), width=max(1, int(s * 0.006)))
    img = Image.alpha_composite(img, border_img)

    return img


def main():
    icons_dir = "/Users/matthewjohnson/Projects/scriptures/frontend/src-tauri/icons"

    print("Generating master icon at 1024x1024...")
    master = create_scripture_icon(1024)

    # Save required Tauri sizes
    sizes = {
        "32x32.png": 32,
        "128x128.png": 128,
        "128x128@2x.png": 256,
    }
    for filename, sz in sizes.items():
        resized = master.resize((sz, sz), Image.LANCZOS)
        resized.save(f"{icons_dir}/{filename}", "PNG")
        print(f"  Saved {filename} ({sz}x{sz})")

    # Save master
    master.save(f"{icons_dir}/icon_master_1024.png", "PNG")

    # Create iconset for .icns
    iconset_dir = f"{icons_dir}/icon.iconset"
    os.makedirs(iconset_dir, exist_ok=True)

    iconset_sizes = {
        "icon_16x16.png": 16,
        "icon_16x16@2x.png": 32,
        "icon_32x32.png": 32,
        "icon_32x32@2x.png": 64,
        "icon_128x128.png": 128,
        "icon_128x128@2x.png": 256,
        "icon_256x256.png": 256,
        "icon_256x256@2x.png": 512,
        "icon_512x512.png": 512,
        "icon_512x512@2x.png": 1024,
    }
    for filename, sz in iconset_sizes.items():
        resized = master.resize((sz, sz), Image.LANCZOS)
        resized.save(f"{iconset_dir}/{filename}", "PNG")
    print("  Created iconset directory")

    # Create .ico (Windows)
    # Pillow ICO requires explicit sizes parameter for multi-size
    ico_sizes_list = [(16, 16), (32, 32), (48, 48), (256, 256)]
    # Create the 256x256 version and save with sizes param
    ico_img = master.resize((256, 256), Image.LANCZOS)
    ico_img.save(f"{icons_dir}/icon.ico", format="ICO", sizes=ico_sizes_list)
    print("  Saved icon.ico")

    # Create .icns using iconutil
    import subprocess
    result = subprocess.run(
        ["iconutil", "-c", "icns", iconset_dir, "-o", f"{icons_dir}/icon.icns"],
        capture_output=True, text=True)
    if result.returncode == 0:
        print("  Saved icon.icns")
    else:
        print(f"  iconutil error: {result.stderr}")

    # Cleanup
    import shutil
    shutil.rmtree(iconset_dir)
    os.remove(f"{icons_dir}/icon_master_1024.png")
    print("  Cleaned up temp files")

    print("\nAll icon files generated!")


if __name__ == "__main__":
    main()
