import os
import math
from PIL import Image, ImageDraw

output_dir = os.path.dirname(os.path.abspath(__file__))

# 1. logo_icon_24.svg (Inline SVG 24x24)
svg_icon_24 = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
  <path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2ZM12 6.8L17.2 12L12 17.2L6.8 12L12 6.8Z" fill="currentColor"/>
</svg>"""

# 2. logo_coin_solid_white.svg (512x512)
svg_solid_white = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" fill="none">
  <path fill-rule="evenodd" clip-rule="evenodd" d="M256 40C136.708 40 40 136.708 40 256C40 375.292 136.708 472 256 472C375.292 472 472 375.292 472 256C472 136.708 375.292 40 256 40ZM256 144L368 256L256 368L144 256L256 144Z" fill="#FFFFFF"/>
</svg>"""

# 3. logo_coin_solid_black.svg (512x512)
svg_solid_black = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" fill="none">
  <path fill-rule="evenodd" clip-rule="evenodd" d="M256 40C136.708 40 40 136.708 40 256C40 375.292 136.708 472 256 472C375.292 472 472 375.292 472 256C472 136.708 375.292 40 256 40ZM256 144L368 256L256 368L144 256L256 144Z" fill="#0A0A0C"/>
</svg>"""

# 4. logo_coin_minted_white.svg (512x512)
svg_minted_white = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" fill="none">
  <!-- Outer Rim Ring -->
  <circle cx="256" cy="256" r="212" fill="#111113" stroke="#FFFFFF" stroke-width="12"/>
  <!-- Inner Rim Contour -->
  <circle cx="256" cy="256" r="184" stroke="#FFFFFF" stroke-opacity="0.2" stroke-width="3" stroke-dasharray="6 6"/>
  <!-- Coin Field Recess -->
  <circle cx="256" cy="256" r="176" fill="#161619"/>
  <!-- Inner Diamond Raised Border -->
  <polygon points="256,128 384,256 256,384 128,256" fill="#1E1E23" stroke="#FFFFFF" stroke-opacity="0.3" stroke-width="4"/>
  <!-- Central Diamond Cutout Hole -->
  <polygon points="256,152 360,256 256,360 152,256" fill="#0A0A0C" stroke="#FFFFFF" stroke-width="8"/>
</svg>"""

# 5. logo_coin_minted_dark.svg (512x512)
svg_minted_dark = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" fill="none">
  <!-- Outer Rim Ring -->
  <circle cx="256" cy="256" r="212" fill="#F4F4F6" stroke="#0A0A0C" stroke-width="12"/>
  <!-- Inner Rim Contour -->
  <circle cx="256" cy="256" r="184" stroke="#0A0A0C" stroke-opacity="0.2" stroke-width="3" stroke-dasharray="6 6"/>
  <!-- Coin Field Recess -->
  <circle cx="256" cy="256" r="176" fill="#FFFFFF"/>
  <!-- Inner Diamond Raised Border -->
  <polygon points="256,128 384,256 256,384 128,256" fill="#EAEAEF" stroke="#0A0A0C" stroke-opacity="0.3" stroke-width="4"/>
  <!-- Central Diamond Cutout Hole -->
  <polygon points="256,152 360,256 256,360 152,256" fill="#F4F4F6" stroke="#0A0A0C" stroke-width="8"/>
</svg>"""

# 6. logo_app_icon_dark.svg (512x512)
svg_app_icon_dark = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" fill="none">
  <rect width="512" height="512" rx="124" fill="#0A0A0C"/>
  <rect x="16" y="16" width="480" height="480" rx="108" fill="#111113" stroke="#202024" stroke-width="4"/>
  <!-- Minted Coin Emblem -->
  <circle cx="256" cy="256" r="160" fill="#161619" stroke="#FFFFFF" stroke-width="8"/>
  <circle cx="256" cy="256" r="140" stroke="#FFFFFF" stroke-opacity="0.15" stroke-width="2" stroke-dasharray="4 4"/>
  <!-- Raised Diamond Border -->
  <polygon points="256,164 348,256 256,348 164,256" fill="#1E1E23" stroke="#FFFFFF" stroke-opacity="0.25" stroke-width="3"/>
  <!-- Central Diamond Hole -->
  <polygon points="256,182 330,256 256,330 182,256" fill="#0A0A0C" stroke="#FFFFFF" stroke-width="6"/>
</svg>"""

# 7. logo_app_icon_light.svg (512x512)
svg_app_icon_light = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" fill="none">
  <rect width="512" height="512" rx="124" fill="#F4F4F6"/>
  <rect x="16" y="16" width="480" height="480" rx="108" fill="#FFFFFF" stroke="#E4E4E7" stroke-width="4"/>
  <!-- Minted Coin Emblem -->
  <circle cx="256" cy="256" r="160" fill="#F4F4F6" stroke="#0A0A0C" stroke-width="8"/>
  <circle cx="256" cy="256" r="140" stroke="#0A0A0C" stroke-opacity="0.15" stroke-width="2" stroke-dasharray="4 4"/>
  <!-- Raised Diamond Border -->
  <polygon points="256,164 348,256 256,348 164,256" fill="#E5E5EA" stroke="#0A0A0C" stroke-opacity="0.25" stroke-width="3"/>
  <!-- Central Diamond Hole -->
  <polygon points="256,182 330,256 256,330 182,256" fill="#F4F4F6" stroke="#0A0A0C" stroke-width="6"/>
</svg>"""

# 8. favicon_coin.svg (512x512)
svg_favicon_coin = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" fill="none">
  <rect width="512" height="512" rx="120" fill="#0A0A0C"/>
  <rect x="24" y="24" width="464" height="464" rx="96" fill="#111113" stroke="#202024" stroke-width="8"/>
  <!-- High Contrast Coin with Diamond Hole -->
  <circle cx="256" cy="256" r="168" fill="#FFFFFF"/>
  <polygon points="256,168 344,256 256,344 168,256" fill="#111113"/>
</svg>"""

# 9. logo_horizontal_dark.svg (600x120)
svg_horizontal_dark = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 120" fill="none">
  <g transform="translate(20, 16)">
    <path fill-rule="evenodd" clip-rule="evenodd" d="M44 4C21.9086 4 4 21.9086 4 44C4 66.0914 21.9086 84 44 84C66.0914 84 84 66.0914 84 44C84 21.9086 66.0914 4 44 4ZM44 24L64 44L44 64L24 44L44 24Z" fill="#FFFFFF"/>
  </g>
  <text x="132" y="72" font-family="'Outfit', 'Inter', -apple-system, sans-serif" font-size="46" font-weight="700" letter-spacing="-1.5" fill="#FFFFFF">MonoFinance</text>
</svg>"""

# 10. logo_horizontal_light.svg (600x120)
svg_horizontal_light = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 120" fill="none">
  <g transform="translate(20, 16)">
    <path fill-rule="evenodd" clip-rule="evenodd" d="M44 4C21.9086 4 4 21.9086 4 44C4 66.0914 21.9086 84 44 84C66.0914 84 84 66.0914 84 44C84 21.9086 66.0914 4 44 4ZM44 24L64 44L44 64L24 44L44 24Z" fill="#0A0A0C"/>
  </g>
  <text x="132" y="72" font-family="'Outfit', 'Inter', -apple-system, sans-serif" font-size="46" font-weight="700" letter-spacing="-1.5" fill="#0A0A0C">MonoFinance</text>
</svg>"""

files = {
    'logo_icon_24.svg': svg_icon_24,
    'logo_coin_solid_white.svg': svg_solid_white,
    'logo_coin_solid_black.svg': svg_solid_black,
    'logo_coin_minted_white.svg': svg_minted_white,
    'logo_coin_minted_dark.svg': svg_minted_dark,
    'logo_app_icon_dark.svg': svg_app_icon_dark,
    'logo_app_icon_light.svg': svg_app_icon_light,
    'favicon_coin.svg': svg_favicon_coin,
    'logo_horizontal_dark.svg': svg_horizontal_dark,
    'logo_horizontal_light.svg': svg_horizontal_light,
}

for fname, content in files.items():
    fpath = os.path.join(output_dir, fname)
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    print(f'Generated: {fname}')

# Generate High-Res Raster PNGs via PIL with 4x Super-Sampling for clean anti-aliasing
def render_app_icon(size=512):
    scale = 4
    canvas_size = size * scale
    img = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Outer squircle
    rx = 124 * scale
    draw.rounded_rectangle([0, 0, canvas_size, canvas_size], radius=rx, fill=(10, 10, 12, 255))
    
    # Inner border
    b_margin = 16 * scale
    b_rx = 108 * scale
    draw.rounded_rectangle(
        [b_margin, b_margin, canvas_size - b_margin, canvas_size - b_margin],
        radius=b_rx,
        fill=(17, 17, 19, 255),
        outline=(32, 32, 36, 255),
        width=int(4 * scale)
    )
    
    # Coin center
    cx = canvas_size // 2
    cy = canvas_size // 2
    
    # Coin body
    r_coin = 160 * scale
    draw.ellipse(
        [cx - r_coin, cy - r_coin, cx + r_coin, cy + r_coin],
        fill=(22, 22, 25, 255),
        outline=(255, 255, 255, 255),
        width=int(8 * scale)
    )
    
    # Raised Diamond Border
    d_raised = 92 * scale
    raised_poly = [(cx, cy - d_raised), (cx + d_raised, cy), (cx, cy + d_raised), (cx - d_raised, cy)]
    draw.polygon(raised_poly, fill=(30, 30, 35, 255), outline=(255, 255, 255, 75))
    
    # Central Diamond Hole
    d_hole = 74 * scale
    hole_poly = [(cx, cy - d_hole), (cx + d_hole, cy), (cx, cy + d_hole), (cx - d_hole, cy)]
    draw.polygon(hole_poly, fill=(10, 10, 12, 255), outline=(255, 255, 255, 255))
    
    # Downsample with Lanczos
    resampled = img.resize((size, size), Image.Resampling.LANCZOS)
    return resampled

def render_solid_coin(color=(255, 255, 255, 255), size=512):
    scale = 4
    canvas_size = size * scale
    img = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cx = canvas_size // 2
    cy = canvas_size // 2
    r = 216 * scale
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    
    # Cutout hole (transparent)
    d = 112 * scale
    hole_poly = [(cx, cy - d), (cx + d, cy), (cx, cy + d), (cx - d, cy)]
    
    # Masking
    mask = Image.new('L', (canvas_size, canvas_size), 255)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.polygon(hole_poly, fill=0)
    
    img.putalpha(Image.composite(img.getchannel('A'), mask, mask))
    return img.resize((size, size), Image.Resampling.LANCZOS)

# Render and save PNGs
icon_512 = render_app_icon(512)
icon_512.save(os.path.join(output_dir, 'logo_app_icon_512.png'), 'PNG')
print('Generated: logo_app_icon_512.png')

icon_192 = render_app_icon(192)
icon_192.save(os.path.join(output_dir, 'logo_app_icon_192.png'), 'PNG')
print('Generated: logo_app_icon_192.png')

solid_white_512 = render_solid_coin((255, 255, 255, 255), 512)
solid_white_512.save(os.path.join(output_dir, 'logo_coin_solid_white_512.png'), 'PNG')
print('Generated: logo_coin_solid_white_512.png')

solid_black_512 = render_solid_coin((10, 10, 12, 255), 512)
solid_black_512.save(os.path.join(output_dir, 'logo_coin_solid_black_512.png'), 'PNG')
print('Generated: logo_coin_solid_black_512.png')

print('All vector and raster logo assets generated successfully!')
