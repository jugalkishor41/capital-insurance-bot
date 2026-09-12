"""
Capital Insurance Investments — YouTube Finance & Insurance Shorts Bot v1
- Viral trending Finance + Insurance topics
- SEO optimized titles & descriptions
- Random themes every video
- Channel logo support
- Topic-related background images
- Voice synced highlighting
- SEBI (finance) / IRDAI (insurance) disclaimer — auto-selected per topic
- 2 minute videos
"""
import os, json, random, time, datetime, schedule, pickle, urllib.request, urllib.parse
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Pillow 10+ removed Image.ANTIALIAS (renamed to Image.LANCZOS), but
# moviepy 1.0.3's internal resizer still references the old name —
# this patch keeps moviepy's .resize() (used for the Ken Burns zoom
# effect) working regardless of which Pillow version the runner has.
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, VideoFileClip
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from groq import Groq

# ══════════════════════════════════════════════════════════
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_KEY")
CLIENT_SECRETS = "client_secrets.json"
TOKEN_FILE     = "youtube_token.pkl"
OUTPUT_DIR     = Path("output_videos")
LOG_FILE       = Path("upload_log.json")
TOPICS_FILE    = Path("custom_topics.json")
LANGUAGE       = "hi"

SEBI_DISCLAIMER  = "Ye video sirf educational purpose ke liye hai. Hum SEBI registered advisor nahi hain. Koi bhi investment apni research aur advisor ki salah se karein."
SEBI_SHORT       = "⚠️ Educational Only | Not SEBI Registered Advisor"
IRDAI_DISCLAIMER = "Ye video sirf educational purpose ke liye hai. Insurance is the subject matter of solicitation. Policy lene se pehle documents dhyan se padhein."
IRDAI_SHORT      = "⚠️ Educational Only | Insurance is Subject Matter of Solicitation"

# Keywords that mark a topic as Insurance (else it defaults to Finance/SEBI)
INSURANCE_KEYWORDS = (
    "insurance", "बीमा", "policy", "पॉलिसी", "term plan", "टर्म",
    "ulip", "यूलिप", "claim", "क्लेम", "nominee", "नॉमिनी",
    "endowment", "एंडोमेंट", "premium", "प्रीमियम", "rider", "राइडर",
    "health cover", "हेल्थ कवर", "critical illness", "फैमिली फ्लोटर",
    "family floater", "irdai", "sum assured", "सम एश्योर्ड",
)

def get_disclaimer(topic: str):
    """Returns (short_bar_text, full_disclaimer_text) based on topic category."""
    t = (topic or "").lower()
    if any(k in t for k in INSURANCE_KEYWORDS):
        return IRDAI_SHORT, IRDAI_DISCLAIMER
    return SEBI_SHORT, SEBI_DISCLAIMER

W, H           = 1080, 1920
FPS            = 30
CHANNEL_NAME   = "Capital Insurance Investments"
CHANNEL_HANDLE = "@CapitalInsuranceInvestments"

# Logo path — tries multiple locations and common formats
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
LOGO_PATHS = []
for _dir in (SCRIPT_DIR, ".", os.getcwd()):
    for _name in ("channel_logo.png", "channel_logo.jpg", "channel_logo.jpeg",
                  "channel_logo.PNG", "channel_logo.JPG"):
        LOGO_PATHS.append(os.path.join(_dir, _name))

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]

# ══════════════════════════════════════════════════════════
#  8 UNIQUE COLOR THEMES
# ══════════════════════════════════════════════════════════
THEMES = [
    {"name":"green",   "primary":(15,130,60),  "dark":(8,80,35),   "bg":(240,255,245), "light":(200,240,215)},
    {"name":"red",     "primary":(200,35,35),  "dark":(140,15,15), "bg":(255,244,244), "light":(255,210,210)},
    {"name":"blue",    "primary":(20,90,190),  "dark":(10,55,130), "bg":(240,246,255), "light":(200,220,255)},
    {"name":"orange",  "primary":(200,85,0),   "dark":(140,55,0),  "bg":(255,246,235), "light":(255,220,180)},
    {"name":"purple",  "primary":(90,40,170),  "dark":(60,20,120), "bg":(246,240,255), "light":(220,200,255)},
    {"name":"teal",    "primary":(0,130,120),  "dark":(0,85,80),   "bg":(235,255,253), "light":(180,240,235)},
    {"name":"maroon",  "primary":(130,15,55),  "dark":(85,8,35),   "bg":(255,240,245), "light":(255,200,220)},
    {"name":"indigo",  "primary":(50,50,170),  "dark":(30,30,120), "bg":(240,240,255), "light":(200,200,255)},
]

# ══════════════════════════════════════════════════════════
#  VIRAL FINANCE + INSURANCE TOPICS
# ══════════════════════════════════════════════════════════
VIRAL_TOPICS = [
    # ── Finance / Investment (SEBI disclaimer) ──
    "SIP से 1 करोड़ का फंड कैसे बनाएं - पूरा प्लान",
    "पहली सैलरी से निवेश शुरू करने के 5 आसान तरीके",
    "म्यूचुअल फंड में निवेश करने से पहले ये 3 गलतियां मत करें",
    "80C के तहत टैक्स बचाने के 7 सबसे असरदार तरीके",
    "50-30-20 रूल से पैसे बचाने का सबसे आसान फॉर्मूला",
    "इमरजेंसी फंड कितना होना चाहिए और कैसे बनाएं",
    "शेयर बाजार में निवेश शुरू करने से पहले जानें ये 5 बातें",
    "क्रेडिट कार्ड का सही इस्तेमाल कैसे करें - 5 जरूरी टिप्स",
    "रिटायरमेंट प्लानिंग 25 की उम्र से क्यों जरूरी है",
    "गोल्ड में निवेश करें या नहीं - पूरी जानकारी",
    "फिक्स्ड डिपॉजिट vs म्यूचुअल फंड - कौन बेहतर है",
    "पर्सनल लोन लेने से पहले ये 5 बातें जरूर जानें",
    "क्रेडिट स्कोर कैसे सुधारें - 5 आसान तरीके",
    "बजट बनाना क्यों जरूरी है - महीने भर का सिंपल प्लान",
    "इंडेक्स फंड क्या है और क्यों है सबसे सेफ निवेश",
    "टैक्स सेविंग के लिए ELSS फंड कितना फायदेमंद है",
    "कर्ज से बाहर निकलने का सबसे तेज तरीका",
    "पैसे बचाने की 5 आदतें जो अमीर लोग अपनाते हैं",
    "NPS में निवेश करने के फायदे जो आप नहीं जानते",
    "स्टॉक मार्केट में लॉन्ग टर्म vs शॉर्ट टर्म - क्या चुनें",

    # ── Insurance (IRDAI disclaimer) ──
    "टर्म इंश्योरेंस क्यों है हर परिवार के लिए जरूरी",
    "हेल्थ इंश्योरेंस क्लेम करते समय ये 5 गलतियां न करें",
    "एंडोमेंट प्लान के 5 बड़े फायदे जो आपको पता होने चाहिए",
    "ULIP vs टर्म इंश्योरेंस - आपके लिए क्या सही है",
    "इंश्योरेंस प्रीमियम पर टैक्स बचाने का पूरा तरीका (80C, 80D)",
    "नॉमिनी कैसे चुनें - इंश्योरेंस पॉलिसी में जरूरी नियम",
    "क्रिटिकल इलनेस कवर क्यों जरूरी है 30 की उम्र के बाद",
    "फैमिली फ्लोटर हेल्थ प्लान के फायदे - एक पॉलिसी पूरे परिवार के लिए",
    "टर्म इंश्योरेंस लेते समय ये 5 गलतियां हर कोई करता है",
    "हेल्थ इंश्योरेंस कितने का लेना चाहिए - सही अमाउंट कैसे तय करें",
    "इंश्योरेंस पॉलिसी सरेंडर करने से पहले जानें ये बातें",
    "बच्चों के लिए चाइल्ड इंश्योरेंस प्लान क्यों जरूरी है",
    "वेटिंग पीरियड क्या होता है हेल्थ इंश्योरेंस में",
    "इंश्योरेंस एजेंट vs ऑनलाइन पॉलिसी - कहां से खरीदें",
    "क्लेम रिजेक्ट होने की 5 सबसे बड़ी वजहें और बचाव",
]

# ══════════════════════════════════════════════════════════
#  FONT LOADER
# ══════════════════════════════════════════════════════════
def load_font(size, bold=True):
    import glob
    if bold:
        paths = (
            glob.glob("/usr/share/fonts/**/*Devanagari*Bold*", recursive=True) +
            glob.glob("/usr/share/fonts/**/*Noto*Bold*", recursive=True) +
            ["/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
             "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
             "C:\\Windows\\Fonts\\NirmalaB.ttf",
             "C:\\Windows\\Fonts\\Nirmala.ttf",
             "C:\\Windows\\Fonts\\mangalb.ttf",
             "C:\\Windows\\Fonts\\mangal.ttf",
             "C:\\Windows\\Fonts\\arialbd.ttf"]
        )
    else:
        paths = (
            glob.glob("/usr/share/fonts/**/*Devanagari*Regular*", recursive=True) +
            ["/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
             "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
             "C:\\Windows\\Fonts\\Nirmala.ttf",
             "C:\\Windows\\Fonts\\mangal.ttf",
             "C:\\Windows\\Fonts\\arial.ttf"]
        )
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except:
            continue
    return ImageFont.load_default()

def load_latin_font(size, bold=True):
    """Guaranteed-Latin font (DejaVu/Arial) — use for pure English/ASCII text
    like channel name, button labels (LIKE/SHARE/SUBSCRIBE/NOW PLAYING).
    Devanagari-priority fonts often lack full Latin glyph coverage and
    render English text as empty boxes even when Hindi renders fine."""
    paths = (
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "C:\\Windows\\Fonts\\arialbd.ttf",
         "C:\\Windows\\Fonts\\segoeuib.ttf"] if bold else
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "C:\\Windows\\Fonts\\arial.ttf",
         "C:\\Windows\\Fonts\\segoeui.ttf"]
    )
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return load_font(size, bold)

def _is_pure_ascii(s):
    try:
        s.encode("ascii")
        return True
    except UnicodeEncodeError:
        return False

def pick_font(text, size, bold=True):
    """DejaVu for pure-ASCII strings (guaranteed Latin coverage),
    Devanagari-priority font for anything with Hindi characters."""
    if _is_pure_ascii(text):
        return load_latin_font(size, bold)
    return load_font(size, bold)


def measure_mixed(draw, text, size, bold=True):
    """Width of a line that may mix Hindi + English words, measuring
    each word with its own correct font (avoids using one font's
    metrics for a script it wasn't designed for)."""
    words = text.split()
    total = 0
    space_w = draw.textlength(" ", font=load_latin_font(size, bold))
    for i, w in enumerate(words):
        f = pick_font(w, size, bold)
        total += draw.textlength(w, font=f)
        if i < len(words) - 1:
            total += space_w
    return total


def wrap_mixed(text, size, max_w, draw, bold=True):
    """Like wrap(), but safe for lines mixing Hindi and English words
    (e.g. 'SIP से 1 करोड़ का फंड')."""
    safe_max_w = max_w * 0.90
    words = text.split()
    lines, cur = [], []
    for word in words:
        test = cur + [word]
        tw = measure_mixed(draw, " ".join(test), size, bold)
        if tw > safe_max_w and cur:
            lines.append(" ".join(cur))
            cur = [word]
        else:
            cur = test
    if cur:
        lines.append(" ".join(cur))
    return lines


def draw_mixed_text(draw, xy, text, size, fill, anchor="mm", bold=True):
    """Draws a line that may mix Hindi + English words, rendering each
    word with the font that actually has its glyphs, positioned so the
    combined line matches the requested anchor (mm=center, lm=left)."""
    x, y = xy
    words = text.split()
    total_w = measure_mixed(draw, text, size, bold)
    space_w = draw.textlength(" ", font=load_latin_font(size, bold))

    if anchor[0] == "m":
        cx = x - total_w / 2
    else:
        cx = x

    for i, w in enumerate(words):
        f = pick_font(w, size, bold)
        ww = draw.textlength(w, font=f)
        v_anchor = "l" + anchor[1]
        draw.text((cx, y), w, font=f, fill=fill, anchor=v_anchor)
        cx += ww + space_w

# ══════════════════════════════════════════════════════════
#  TEXT WRAP
# ══════════════════════════════════════════════════════════
def wrap(text, font, max_w, draw):
    # Safety margin: Devanagari conjuncts/matras render WIDER than
    # draw.textlength() predicts on this Pillow setup (no complex-script
    # shaping engine) — a 10% safety margin stops lines from visually
    # overflowing/overlapping even when the raw measurement says they fit.
    safe_max_w = max_w * 0.90
    words = text.split()
    lines, cur = [], []
    for word in words:
        test = " ".join(cur + [word])
        try:
            bbox = draw.textbbox((0, 0), test, font=font)
            tw = bbox[2] - bbox[0]
        except Exception:
            try:
                tw = draw.textlength(test, font=font)
            except Exception:
                tw = len(test) * 20
        if tw > safe_max_w and cur:
            lines.append(" ".join(cur))
            cur = [word]
        else:
            cur.append(word)
    if cur:
        lines.append(" ".join(cur))
    return lines

# ══════════════════════════════════════════════════════════
#  TOPIC IMAGE DOWNLOADER
# ══════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════
#  HAND-DRAWN VECTOR ICONS — no font/emoji dependency, always renders
# ══════════════════════════════════════════════════════════
def draw_icon(draw, cx, cy, kind, color, size=46):
    r = size / 2
    if kind == "like":
        draw.rounded_rectangle(
            [cx - r*0.55, cy - r*0.05, cx + r*0.55, cy + r*0.95],
            radius=8, fill=color
        )
        draw.polygon([
            (cx - r*0.18, cy - r*0.05),
            (cx - r*0.18, cy - r*0.70),
            (cx + r*0.05, cy - r*0.98),
            (cx + r*0.32, cy - r*0.80),
            (cx + r*0.20, cy - r*0.05),
        ], fill=color)
    elif kind == "share":
        node_r = size * 0.13
        p1 = (cx - r*0.75, cy)
        p2 = (cx + r*0.55, cy - r*0.62)
        p3 = (cx + r*0.55, cy + r*0.62)
        lw = max(3, int(size*0.09))
        draw.line([p1, p2], fill=color, width=lw)
        draw.line([p1, p3], fill=color, width=lw)
        for p in (p1, p2, p3):
            draw.ellipse([p[0]-node_r, p[1]-node_r, p[0]+node_r, p[1]+node_r], fill=color)
    elif kind == "bell":
        bx, by = cx, cy
        draw.polygon([
            (bx, by - r*0.95),
            (bx - r*0.78, by + r*0.55),
            (bx + r*0.78, by + r*0.55),
        ], fill=color)
        draw.ellipse([bx - r*0.24, by + r*0.48, bx + r*0.24, by + r*0.82], fill=color)
        draw.ellipse([bx - r*0.13, by - r*1.12, bx + r*0.13, by - r*0.88], fill=color)

def draw_flow_diagram(draw, cx, cy, w, h, steps, theme):
    """Cause-effect flow diagram — 2-4 labeled boxes connected by arrows.
    e.g. ['Earnings ↓', 'Investor Sentiment ↓', 'Price ↓']"""
    import math
    p, d, light = theme["primary"], theme["dark"], theme["light"]
    white, black = (255,255,255), (30,30,30)
    n = max(2, min(4, len(steps)))
    steps = steps[:n]

    box_w = w * 0.78
    box_h = h * 0.16
    gap   = h * 0.10
    total_h = n*box_h + (n-1)*gap
    start_y = cy - total_h/2

    for i, step in enumerate(steps):
        by = start_y + i*(box_h+gap)
        bx1, bx2 = cx-box_w/2, cx+box_w/2
        col = p if i == n-1 else white
        txt_col = white if i == n-1 else black
        draw.rounded_rectangle([bx1+4, by+4, bx2+4, by+box_h+4], radius=16, fill=(150,150,150))
        draw.rounded_rectangle([bx1, by, bx2, by+box_h], radius=16, fill=col, outline=p, width=4)
        f = pick_font(step, int(box_h*0.42))
        draw_mixed_text(draw, (cx, by+box_h/2), step, int(box_h*0.42), txt_col, anchor="mm")
        if i < n-1:
            ax = cx
            ay1 = by+box_h+6
            ay2 = by+box_h+gap-6
            draw.line([ax, ay1, ax, ay2], fill=d, width=8)
            draw.polygon([(ax-14, ay2-6), (ax+14, ay2-6), (ax, ay2+14)], fill=d)


def draw_comparison(draw, cx, cy, w, h, theme, label_a, value_a, label_b, value_b):
    """Side-by-side comparison boxes — e.g. dividends ₹54,000 vs ₹7,700.
    The larger value is highlighted in the theme's primary color."""
    p, d, light = theme["primary"], theme["dark"], theme["light"]
    white, black = (255,255,255), (30,30,30)

    def _num(v):
        s = str(v).lower().replace(",", "").replace("₹", "").replace("$", "").replace("%", "").strip()
        mult = 1
        for suf, m in (("crore",1e7),("cr",1e7),("lakh",1e5),("lac",1e5),("l",1e5),
                       ("million",1e6),("m",1e6),("billion",1e9),("b",1e9),("k",1e3)):
            if s.endswith(suf):
                s = s[:-len(suf)].strip()
                mult = m
                break
        try:
            return float(s) * mult
        except Exception:
            return 0

    a_bigger = _num(value_a) >= _num(value_b)
    box_w = w*0.44
    box_h = min(h*0.7, w*0.6)  # cap height so value text has room, avoids VS overlap
    gap = w*0.08
    x1 = cx - box_w - gap/2
    x2 = cx + gap/2
    by = cy - box_h/2

    for (bx, label, value, is_bigger) in [
        (x1, label_a, value_a, a_bigger), (x2, label_b, value_b, not a_bigger)
    ]:
        col = p if is_bigger else light
        txt_col = white if is_bigger else black
        draw.rounded_rectangle([bx+4, by+4, bx+box_w+4, by+box_h+4], radius=20, fill=(150,150,150))
        draw.rounded_rectangle([bx, by, bx+box_w, by+box_h], radius=20, fill=col, outline=p, width=5)
        f_val = load_latin_font(int(box_h*0.17))
        draw.text((bx+box_w/2, by+box_h*0.30), str(value), font=f_val, fill=txt_col, anchor="mm")
        f_lbl = pick_font(str(label), int(box_h*0.11))
        draw_mixed_text(draw, (bx+box_w/2, by+box_h*0.75), str(label), int(box_h*0.11), txt_col, anchor="mm")
        if is_bigger:
            draw.polygon([(bx+box_w/2-22, by-16),(bx+box_w/2+22, by-16),(bx+box_w/2, by-44)], fill=d)

    f_vs = load_latin_font(int(min(h,w)*0.09))
    vs_r = min(h,w)*0.055
    draw.ellipse([cx-vs_r, cy-vs_r, cx+vs_r, cy+vs_r], fill=d, outline=white, width=4)
    draw.text((cx, cy), "VS", font=f_vs, fill=white, anchor="mm")


def draw_point_visual(draw, cx, cy, w, h, visual_spec, point_text, theme):
    """Renders whichever visual the script asked for this point:
    icon (default), comparison boxes, or a cause-effect flow diagram."""
    spec = visual_spec or {"type": "icon"}
    vtype = spec.get("type", "icon")
    if vtype == "comparison":
        draw_comparison(draw, cx, cy, w, h, theme,
                        spec["label_a"], spec["value_a"],
                        spec["label_b"], spec["value_b"])
    elif vtype == "flow":
        draw_flow_diagram(draw, cx, cy, w, h, spec["steps"], theme)
    else:
        illus_kind = get_illustration_kind(point_text)
        draw_illustration(draw, cx, cy, w, h, illus_kind, theme)


def get_illustration_kind(text):
    """Maps a topic/tip string to one of our original flat-design
    illustration categories (no external images, no copyright risk)."""
    t = (text or "").lower()
    checks = [
        (("sip","निवेश","invest","mutual fund","म्यूचुअल","index fund","शेयर","stock","बाजार","market"), "growth"),
        (("टैक्स","tax","80c","elss"), "tax"),
        (("बजट","budget","50-30-20"), "budget"),
        (("इमरजेंसी","emergency","सुरक्षा","सुरक्षित","protect","safe","secure"), "safe"),
        (("क्रेडिट कार्ड","credit card"), "creditcard"),
        (("रिटायरमेंट","retirement","nps"), "retirement"),
        (("गोल्ड","gold"), "gold"),
        (("फिक्स्ड डिपॉजिट","fixed deposit"," fd","बैंक"), "bank"),
        (("लोन","loan","कर्ज"), "loan"),
        (("क्रेडिट स्कोर","credit score"), "creditscore"),
        (("नॉमिनी","nominee"), "nominee"),
        (("क्लेम","claim","दस्तावेज","document"), "document"),
        (("एडवाइजर","advisor","एक्सपर्ट","expert","सलाह","consultant"), "handshake"),
        (("फैमिली","family","चाइल्ड","child"), "family"),
        (("टर्म","term","हेल्थ इंश्योरेंस","health insurance","health cover",
          "एंडोमेंट","endowment","ulip","यूलिप","प्रीमियम","premium",
          "क्रिटिकल इलनेस","critical illness","इंश्योरेंस","insurance"), "shield"),
    ]
    for keys, kind in checks:
        if any(k in t for k in keys):
            return kind
    return "growth"


def draw_person(draw, cx, cy, size, pose, theme, variant=0):
    """Original flat-design 2D human character — the channel's recurring
    'guide' who acts out each point (pointing at a chart, worried about
    a loan, protected by insurance, etc.), the way professional finance
    explainer videos use a narrator character. Hand-drawn shapes only.
    variant: 0/1/2 cycles skin tone + outfit color for visual variety."""
    import math
    p, d = theme["primary"], theme["dark"]
    skins = [(240,200,165), (200,150,110), (120,80,60)]
    outfits = [p, (60,70,110), (90,60,110)]
    skin = skins[variant % 3]
    outfit = outfits[variant % 3]
    white, black = (255,255,255), (35,35,35)
    s = size

    head_r = s*0.17
    head_cy = cy - s*0.30
    neck_w = s*0.08

    # Legs (simple, waist-down, only visible if pose is full standing)
    leg_w = s*0.11
    draw.rounded_rectangle([cx-s*0.14, cy+s*0.14, cx-s*0.14+leg_w, cy+s*0.5], radius=8, fill=(40,40,55))
    draw.rounded_rectangle([cx+s*0.14-leg_w, cy+s*0.14, cx+s*0.14, cy+s*0.5], radius=8, fill=(40,40,55))
    draw.rounded_rectangle([cx-s*0.17, cy+s*0.46, cx-s*0.17+leg_w+s*0.05, cy+s*0.52], radius=6, fill=black)
    draw.rounded_rectangle([cx+s*0.17-leg_w-s*0.05, cy+s*0.46, cx+s*0.17, cy+s*0.52], radius=6, fill=black)

    # Body (torso)
    body_w = s*0.4
    body_top = cy - s*0.18
    draw.rounded_rectangle([cx-body_w/2, body_top, cx+body_w/2, cy+s*0.18], radius=s*0.12, fill=outfit)
    # collar/tie hint
    draw.polygon([(cx-s*0.05,body_top),(cx+s*0.05,body_top),(cx,body_top+s*0.1)], fill=white)

    # Arms — pose dependent
    arm_w = max(6, int(s*0.075))
    sh_l = (cx-body_w/2+6, body_top+s*0.04)
    sh_r = (cx+body_w/2-6, body_top+s*0.04)

    if pose == "point_up":
        draw.line([sh_r, (cx+s*0.42, cy-s*0.32)], fill=outfit, width=arm_w)
        draw.ellipse([cx+s*0.42-9, cy-s*0.32-9, cx+s*0.42+9, cy-s*0.32+9], fill=skin)
        draw.line([sh_l, (cx-s*0.22, cy+s*0.14)], fill=outfit, width=arm_w)
    elif pose == "worried":
        draw.line([sh_r, (cx+s*0.14, head_cy+s*0.02)], fill=outfit, width=arm_w)
        draw.ellipse([cx+s*0.14-9, head_cy+s*0.02-9, cx+s*0.14+9, head_cy+s*0.02+9], fill=skin)
        draw.line([sh_l, (cx-s*0.22, cy+s*0.1)], fill=outfit, width=arm_w)
    elif pose == "happy_arms":
        draw.line([sh_r, (cx+s*0.34, cy-s*0.38)], fill=outfit, width=arm_w)
        draw.ellipse([cx+s*0.34-9, cy-s*0.38-9, cx+s*0.34+9, cy-s*0.38+9], fill=skin)
        draw.line([sh_l, (cx-s*0.34, cy-s*0.38)], fill=outfit, width=arm_w)
        draw.ellipse([cx-s*0.34-9, cy-s*0.38-9, cx-s*0.34+9, cy-s*0.38+9], fill=skin)
    elif pose == "hold_out":
        draw.line([sh_r, (cx+s*0.3, cy+s*0.05)], fill=outfit, width=arm_w)
        draw.ellipse([cx+s*0.3-9, cy+s*0.05-9, cx+s*0.3+9, cy+s*0.05+9], fill=skin)
        draw.line([sh_l, (cx-s*0.3, cy+s*0.05)], fill=outfit, width=arm_w)
        draw.ellipse([cx-s*0.3-9, cy+s*0.05-9, cx-s*0.3+9, cy+s*0.05+9], fill=skin)
    else:  # idle
        draw.line([sh_r, (cx+s*0.24, cy+s*0.16)], fill=outfit, width=arm_w)
        draw.line([sh_l, (cx-s*0.24, cy+s*0.16)], fill=outfit, width=arm_w)

    # Head
    draw.rounded_rectangle([cx-neck_w/2, head_cy+head_r*0.6, cx+neck_w/2, body_top+8], radius=6, fill=skin)
    draw.ellipse([cx-head_r, head_cy-head_r, cx+head_r, head_cy+head_r], fill=skin)
    # simple hair
    draw.pieslice([cx-head_r, head_cy-head_r, cx+head_r, head_cy+head_r], 180, 360, fill=(45,35,30))
    # face
    eye_dx = head_r*0.35
    for sx in (-1,1):
        ex = cx+sx*eye_dx
        draw.ellipse([ex-4, head_cy-4, ex+4, head_cy+4], fill=black)
    if pose == "worried":
        draw.arc([cx-head_r*0.35, head_cy+head_r*0.15, cx+head_r*0.35, head_cy+head_r*0.55], 200, 340, fill=black, width=4)
        for sx in (-1,1):
            bx = cx+sx*head_r*0.5
            draw.line([bx, head_cy-head_r*0.6, bx+sx*8, head_cy-head_r*0.35], fill=(60,60,180), width=3)
    elif pose in ("happy_arms","point_up"):
        draw.arc([cx-head_r*0.4, head_cy+head_r*0.05, cx+head_r*0.4, head_cy+head_r*0.5], 15, 165, fill=black, width=4)
    else:
        draw.line([cx-head_r*0.25, head_cy+head_r*0.35, cx+head_r*0.25, head_cy+head_r*0.35], fill=black, width=3)


PERSON_SKIN_TONES = [(235,190,150), (200,150,110), (150,105,70)]

def draw_mascot(draw, cx, cy, size, pose, theme):
    """Original mascot — 'Rupee Buddy', a friendly coin character.
    Hand-drawn shapes only, no external assets, no copied IP.
    pose: 'idle' | 'wave' | 'point' | 'happy' — cycling poses across
    screen cuts gives a subtle sense of life/animation without needing
    real frame-by-frame animation."""
    import math
    p, d = theme["primary"], theme["dark"]
    gold = (235, 185, 55)
    gold_d = (185, 135, 15)
    white, black = (255,255,255), (30,30,30)
    r = size / 2

    # Body (coin)
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=gold, outline=gold_d, width=max(3,int(size*0.035)))
    draw.ellipse([cx-r*0.82, cy-r*0.82, cx+r*0.82, cy+r*0.82], outline=gold_d, width=max(2,int(size*0.02)))

    # Face
    eye_dx, eye_dy = r*0.28, -r*0.08
    eye_r = r*0.09
    for sx in (-1, 1):
        ex = cx + sx*eye_dx
        draw.ellipse([ex-eye_r, cy+eye_dy-eye_r, ex+eye_r, cy+eye_dy+eye_r], fill=black)
        # tiny highlight
        draw.ellipse([ex-eye_r*0.3, cy+eye_dy-eye_r, ex+eye_r*0.3, cy+eye_dy-eye_r*0.4], fill=white)

    # Mouth — varies slightly by pose for a bit of expression variety
    mouth_y = cy + r*0.22
    if pose == "happy":
        draw.arc([cx-r*0.32, mouth_y-r*0.22, cx+r*0.32, mouth_y+r*0.18], 10, 170, fill=black, width=max(3,int(size*0.03)))
    else:
        draw.arc([cx-r*0.26, mouth_y-r*0.14, cx+r*0.26, mouth_y+r*0.14], 15, 165, fill=black, width=max(3,int(size*0.03)))

    # Rupee symbol on chest (below face)
    f_rs = load_latin_font(int(r*0.5))
    draw.text((cx, cy+r*0.55), "₹", font=f_rs, fill=gold_d, anchor="mm")

    # Arms — pose-dependent
    arm_w = max(4, int(size*0.05))
    if pose == "wave":
        # right arm raised, waving
        draw.line([cx+r*0.65, cy+r*0.1, cx+r*1.15, cy-r*0.55], fill=gold_d, width=arm_w)
        draw.ellipse([cx+r*1.15-10, cy-r*0.55-10, cx+r*1.15+10, cy-r*0.55+10], fill=gold)
        draw.line([cx-r*0.65, cy+r*0.1, cx-r*0.95, cy+r*0.5], fill=gold_d, width=arm_w)
    elif pose == "point":
        draw.line([cx+r*0.65, cy+r*0.05, cx+r*1.3, cy-r*0.05], fill=gold_d, width=arm_w)
        draw.ellipse([cx+r*1.3-9, cy-r*0.05-9, cx+r*1.3+9, cy-r*0.05+9], fill=gold)
        draw.line([cx-r*0.65, cy+r*0.1, cx-r*0.95, cy+r*0.5], fill=gold_d, width=arm_w)
    else:  # idle / happy
        draw.line([cx-r*0.65, cy+r*0.1, cx-r*0.95, cy+r*0.5], fill=gold_d, width=arm_w)
        draw.line([cx+r*0.65, cy+r*0.1, cx+r*0.95, cy+r*0.5], fill=gold_d, width=arm_w)


def draw_illustration(draw, cx, cy, w, h, kind, theme):
    """Original flat-design vector illustration — hand-coded shapes,
    no external assets, drawn fresh for this bot."""
    p, d, light = theme["primary"], theme["dark"], theme["light"]
    white, black = (255,255,255), (30,30,30)
    s = min(w, h)

    if kind == "growth":
        variant = random.randint(0, 2)
        px = cx - s*0.30
        draw_person(draw, px, cy+s*0.05, s*0.62, "point_up", theme, variant)
        icx = cx + s*0.20
        style = random.choice(["bars", "line_dots", "coins_stack"])
        if style == "bars":
            base_y = cy + s*0.28
            heights = [0.18, 0.30, 0.44, 0.60]
            bar_w = s*0.09
            start_x = icx - s*0.20
            for i, hh in enumerate(heights):
                bx = start_x + i*(bar_w+s*0.045)
                by = base_y - s*hh
                col = p if i < len(heights)-1 else d
                draw.rounded_rectangle([bx, by, bx+bar_w, base_y], radius=6, fill=col)
            ax1, ay1 = start_x-8, base_y - s*heights[0] - 16
            ax2, ay2 = start_x + 3*(bar_w+s*0.045) + bar_w + 14, base_y - s*heights[-1] - s*0.18
            draw.line([ax1,ay1,ax2,ay2], fill=d, width=8)
            import math
            rad = math.radians(20)
            dx, dy = math.cos(rad)*20, math.sin(rad)*20
            draw.polygon([(ax2,ay2),(ax2-dx-10,ay2+dy-6),(ax2-dx+6,ay2+dy+10)], fill=d)
        elif style == "line_dots":
            pts = [(-0.20,0.24),(-0.06,0.06),(0.08,0.14),(0.20,-0.10),(0.32,-0.28)]
            xy = [(icx+px2*s, cy+py2*s) for px2, py2 in pts]
            for i in range(len(xy)-1):
                draw.line([xy[i], xy[i+1]], fill=p, width=int(s*0.022))
            for i, (x,y) in enumerate(xy):
                r = s*0.026
                col = d if i == len(xy)-1 else p
                draw.ellipse([x-r,y-r,x+r,y+r], fill=col, outline=white, width=3)
        else:  # coins_stack
            gold, gold_d = (230,180,40), (180,130,10)
            for i, yoff in enumerate([0.30, 0.18, 0.06, -0.06]):
                ew = s*(0.22 + i*0.035)
                draw.ellipse([icx-ew/2, cy+yoff*s-s*0.04, icx+ew/2, cy+yoff*s+s*0.04],
                            fill=gold, outline=gold_d, width=3)
            f = load_latin_font(int(s*0.09))
            draw.text((icx, cy-s*0.02), "₹", font=f, fill=gold_d, anchor="mm")

    elif kind == "safe":
        variant = random.randint(0, 2)
        px = cx - s*0.28
        draw_person(draw, px, cy+s*0.05, s*0.6, "happy_arms", theme, variant)
        icx = cx + s*0.24
        bw, bh = s*0.36, s*0.36
        draw.rounded_rectangle([icx-bw/2, cy-bh/2, icx+bw/2, cy+bh/2], radius=12, fill=(90,90,100), outline=(50,50,60), width=5)
        r = s*0.10
        draw.ellipse([icx-r, cy-r, icx+r, cy+r], fill=(220,220,225), outline=(50,50,60), width=4)
        for ang in range(0, 360, 45):
            import math
            rad = math.radians(ang)
            x2, y2 = icx+math.cos(rad)*r*0.8, cy+math.sin(rad)*r*0.8
            draw.line([icx, cy, x2, y2], fill=(50,50,60), width=3)

    elif kind == "handshake":
        v1, v2 = random.randint(0,2), (random.randint(0,2))
        draw_person(draw, cx-s*0.22, cy+s*0.04, s*0.58, "hold_out", theme, v1)
        draw_person(draw, cx+s*0.22, cy+s*0.04, s*0.58, "hold_out", theme, v2)
        draw.ellipse([cx-s*0.05, cy-s*0.02, cx+s*0.05, cy+s*0.08], fill=(240,200,165))

    elif kind == "tax":
        variant = random.randint(0, 2)
        px = cx - s*0.28
        draw_person(draw, px, cy+s*0.05, s*0.6, "point_up", theme, variant)
        icx = cx + s*0.26
        cw, ch = s*0.36, s*0.36
        draw.rounded_rectangle([icx-cw/2, cy-ch/2, icx+cw/2, cy+ch/2], radius=12, fill=white, outline=p, width=5)
        for r in range(4):
            for c in range(3):
                bx = icx-cw/2+10+c*(cw-20)/2
                by = cy-ch/2+10+r*(ch-20)/3.6
                draw.rounded_rectangle([bx,by,bx+(cw-32)/3, by+10], radius=4, fill=light if (r+c)%2 else p)

    elif kind == "budget":
        r = s*0.32
        import math
        segs = [0.5, 0.3, 0.2]
        cols = [p, d, light]
        start = -90
        for frac, col in zip(segs, cols):
            end = start + frac*360
            draw.pieslice([cx-r,cy-r,cx+r,cy+r], start, end, fill=col)
            start = end
        draw.ellipse([cx-r*0.45,cy-r*0.45,cx+r*0.45,cy+r*0.45], fill=white)

    elif kind == "emergency":
        # Umbrella
        r = s*0.34
        draw.pieslice([cx-r, cy-r*0.55, cx+r, cy+r*0.75], 180, 360, fill=p)
        for i in range(5):
            nx = cx - r + i*(2*r/4)
            draw.line([nx, cy+r*0.1, nx, cy+r*0.24], fill=d, width=6)
        draw.line([cx, cy+r*0.1, cx, cy+r*0.85], fill=d, width=10)
        draw.arc([cx-30, cy+r*0.65, cx+30, cy+r*1.05], 0, 180, fill=d, width=10)
        draw.polygon([(cx-8,cy-r*0.7),(cx+8,cy-r*0.7),(cx,cy-r*1.0)], fill=d)

    elif kind == "creditcard":
        cw, ch = s*0.7, s*0.44
        draw.rounded_rectangle([cx-cw/2, cy-ch/2, cx+cw/2, cy+ch/2], radius=20, fill=p, outline=d, width=4)
        draw.rounded_rectangle([cx-cw/2, cy-ch/2+ch*0.28, cx+cw/2, cy-ch/2+ch*0.42], radius=0, fill=d)
        draw.rounded_rectangle([cx-cw/2+22, cy+ch*0.05, cx-cw/2+80, cy+ch*0.2], radius=6, fill=light)
        for i in range(4):
            draw.ellipse([cx-cw/2+22+i*10, cy+ch*0.28, cx-cw/2+32+i*10, cy+ch*0.34], fill=white)

    elif kind == "retirement":
        r = s*0.22
        draw.ellipse([cx-r, cy-s*0.42, cx+r, cy-s*0.42+2*r], fill=(250,180,60))
        for ang in range(0, 360, 30):
            import math
            rad = math.radians(ang)
            x1 = cx + math.cos(rad)*(r+8)
            y1 = cy-s*0.42+r + math.sin(rad)*(r+8)
            x2 = cx + math.cos(rad)*(r+26)
            y2 = cy-s*0.42+r + math.sin(rad)*(r+26)
            draw.line([x1,y1,x2,y2], fill=(250,180,60), width=6)
        draw.line([cx-s*0.4, cy+s*0.18, cx+s*0.4, cy+s*0.18], fill=d, width=8)
        draw.line([cx-s*0.05, cy+s*0.18, cx-s*0.22, cy-s*0.02], fill=p, width=10)
        draw.line([cx-s*0.22, cy-s*0.02, cx-s*0.05, cy+s*0.18], fill=p, width=10)
        draw.ellipse([cx-s*0.3, cy-s*0.1, cx-s*0.14, cy+s*0.06], fill=d)

    elif kind == "gold":
        for i, off in enumerate([0.18, 0.06, -0.06]):
            bw, bh = s*0.5, s*0.14
            by = cy + off*s
            draw.rounded_rectangle([cx-bw/2, by-bh/2, cx+bw/2, by+bh/2],
                                   radius=8, fill=(230,180,40), outline=(180,130,10), width=3)
        draw.ellipse([cx-s*0.16, cy-s*0.32, cx+s*0.16, cy-s*0.06], fill=(240,195,60), outline=(180,130,10), width=3)
        f = load_latin_font(int(s*0.13))
        draw.text((cx, cy-s*0.19), "₹", font=f, fill=(150,105,10), anchor="mm")

    elif kind == "bank":
        bw, bh = s*0.7, s*0.4
        bx, by = cx-bw/2, cy-bh/2+s*0.1
        draw.polygon([(cx, by-s*0.22),(bx-10, by),(bx+bw+10, by)], fill=d)
        draw.rectangle([bx, by, bx+bw, by+bh], fill=p)
        for i in range(4):
            px = bx + bw*0.15 + i*bw*0.23
            draw.rectangle([px, by+10, px+bw*0.1, by+bh-10], fill=white)
        draw.rectangle([bx-14, by+bh, bx+bw+14, by+bh+16], fill=d)

    elif kind == "loan":
        variant = random.randint(0, 2)
        px = cx - s*0.30
        draw_person(draw, px, cy+s*0.05, s*0.6, "worried", theme, variant)
        icx = cx + s*0.24
        hw, hh = s*0.30, s*0.22
        draw.polygon([(icx, cy-s*0.28),(icx-hw/2-8, cy-s*0.08),(icx+hw/2+8, cy-s*0.08)], fill=d)
        draw.rectangle([icx-hw/2, cy-s*0.08, icx+hw/2, cy-s*0.08+hh], fill=p)
        draw.rectangle([icx-hw*0.12, cy-s*0.08+hh*0.4, icx+hw*0.12, cy-s*0.08+hh], fill=white)

    elif kind == "creditscore":
        r = s*0.34
        import math
        draw.arc([cx-r,cy-r,cx+r,cy+r], 180, 360, fill=light, width=22)
        draw.arc([cx-r,cy-r,cx+r,cy+r], 180, 300, fill=p, width=22)
        rad = math.radians(240)
        nx, ny = cx+math.cos(rad)*r*0.8, cy+math.sin(rad)*r*0.8
        draw.line([cx,cy,nx,ny], fill=d, width=8)
        draw.ellipse([cx-12,cy-12,cx+12,cy+12], fill=d)

    elif kind == "nominee":
        for off, col in [(-s*0.16, p), (s*0.16, d)]:
            hx = cx+off
            draw.ellipse([hx-s*0.09, cy-s*0.32, hx+s*0.09, cy-s*0.14], fill=col)
            draw.rounded_rectangle([hx-s*0.15, cy-s*0.1, hx+s*0.15, cy+s*0.3], radius=18, fill=col)
        hx1, hx2 = cx-s*0.02, cx+s*0.1
        hy = cy - s*0.32
        draw.polygon([(cx,hy+18),(cx-18,hy),(cx-9,hy),(cx-9,hy-14),(cx+9,hy-14),(cx+9,hy),(cx+18,hy),(cx,hy+18)], fill=(220,50,80))

    elif kind == "document":
        dw, dh = s*0.5, s*0.62
        draw.rounded_rectangle([cx-dw/2, cy-dh/2, cx+dw/2, cy+dh/2], radius=14, fill=white, outline=p, width=5)
        for i in range(5):
            ly = cy-dh/2+dh*0.22+i*dh*0.13
            draw.line([cx-dw/2+22, ly, cx+dw/2-22, ly], fill=light, width=6)
        draw.ellipse([cx+dw*0.12, cy+dh*0.12, cx+dw*0.42, cy+dh*0.42], fill=(60,170,90))
        f = load_latin_font(int(s*0.12))
        draw.text((cx+dw*0.27, cy+dh*0.27), "✓", font=f, fill=white, anchor="mm")

    elif kind == "family":
        draw_person(draw, cx-s*0.2, cy+s*0.1, s*0.55, "idle", theme, 0)
        draw_person(draw, cx+s*0.2, cy+s*0.1, s*0.5, "idle", theme, 1)
        draw_person(draw, cx, cy+s*0.24, s*0.32, "happy_arms", theme, 2)

    else:  # "shield" — default for insurance topics
        variant = random.randint(0, 2)
        px = cx - s*0.26
        draw_person(draw, px, cy+s*0.06, s*0.6, "happy_arms", theme, variant)
        sx, sy = cx + s*0.26, cy
        sw, sh = s*0.32, s*0.38
        draw.polygon([
            (sx, sy-sh/2), (sx+sw/2, sy-sh/2+sh*0.18),
            (sx+sw/2, sy+sh*0.08), (sx, sy+sh/2),
            (sx-sw/2, sy+sh*0.08), (sx-sw/2, sy-sh/2+sh*0.18),
        ], fill=p, outline=d, width=4)
        draw.line([sx-sw*0.18, sy-sh*0.02, sx-sw*0.02, sy+sh*0.14], fill=white, width=8)
        draw.line([sx-sw*0.02, sy+sh*0.14, sx+sw*0.22, sy-sh*0.16], fill=white, width=8)


def paste_ai_character(img, char_path, y1, y2, frame_w):
    """Composites the AI-generated presenter character into a frame,
    removing its near-white background (simple brightness threshold —
    good enough for flat vector art on a plain white background) and
    standing it in the bottom-right of the given [y1, y2] card zone."""
    try:
        ci = Image.open(char_path).convert("RGBA")
        arr = np.array(ci)
        rgb = arr[:, :, :3].astype(int)
        brightness = rgb.sum(axis=2)
        # Near-white pixels (the generated plain background) -> transparent
        mask = brightness > 720
        arr[:, :, 3] = np.where(mask, 0, 255)
        ci = Image.fromarray(arr, "RGBA")

        card_h = y2 - y1
        target_h = int(card_h * 0.68)
        ratio = ci.width / ci.height
        target_w = int(target_h * ratio)
        ci = ci.resize((target_w, target_h), Image.LANCZOS)

        px = frame_w - target_w - 40
        py = y2 - target_h - 10
        img.paste(ci, (px, py), ci)
    except Exception as e:
        print(f"  AI character paste skipped: {e}")


def generate_thumbnail_scene(topic, hook, is_insurance):
    """Asks Groq to invent a specific, creative visual SCENARIO for the
    thumbnail character — matching the style of top finance channels
    (character sleeping while money grows beside the bed, climbing
    stairs of coins, buried under falling charts, etc.) instead of
    reusing one generic pose for every video. Falls back to a solid
    generic pose on any failure, so a flaky call never blocks the
    thumbnail from being made."""
    fallback = (
        "holding a green insurance shield, confident smile, thumbs up"
        if is_insurance else
        "holding cash and pointing at a rising bar chart, excited expression"
    )
    try:
        groq_client = Groq(api_key=GEMINI_API_KEY)
        prompt = (
            "You design viral YouTube thumbnail SCENES for a finance/insurance "
            "channel, in the style of top creators (e.g. a character sleeping "
            "peacefully while a money plant grows beside the bed, a character "
            "climbing a staircase made of coins, a character comically buried "
            "under a falling stock chart, a character sitting calmly on a huge "
            "pile of cash while chaos happens around them).\n\n"
            f"Video topic: {topic}\n"
            f"Video hook: {hook}\n"
            f"Category: {'Insurance' if is_insurance else 'Finance/Investment'}\n\n"
            "Invent ONE specific, visually punchy scene (not a generic pose) "
            "for a single cartoon character that captures this exact topic's "
            "core emotion or idea. Describe only the character's pose, "
            "expression, and any props/props-interaction — 1 sentence, under "
            "25 words, in English, for an image generation prompt. "
            "No text/words in the scene. Return ONLY that one sentence, "
            "nothing else."
        )
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_completion_tokens=200,
            reasoning_effort="low",
        )
        scene = completion.choices[0].message.content.strip().strip('"')
        if scene and 8 < len(scene) < 220:
            print(f"  Thumbnail scene: {scene}")
            return scene
    except Exception as e:
        print(f"  Thumbnail scene generation failed ({e}), using generic pose")
    return fallback


def get_ai_character_image(pose_desc, size=700, seed=42):
    """Generates a 2D character illustration for the THUMBNAIL only via
    Pollinations.ai (genuinely free, no API key/signup needed). Returns
    None on any failure (slow response, network issue, rate limit) —
    the caller then falls back to the reliable hand-drawn draw_person(),
    so a flaky free service can never break video generation."""
    import hashlib
    cache_dir = Path("character_images")
    cache_dir.mkdir(exist_ok=True)
    safe = hashlib.md5((pose_desc + str(seed)).encode()).hexdigest()[:10]
    img_path = cache_dir / f"char_{safe}.png"
    if img_path.exists():
        return str(img_path)

    base_desc = (
        "flat vector illustration, 2D cartoon character, confident young "
        "Indian financial advisor, short black hair, light stubble, "
        "wearing white shirt and navy blue blazer, simple flat colors, "
        "plain white background, no text, no watermark, clean vector art, "
        "professional finance explainer style"
    )
    prompt = f"{base_desc}, {pose_desc}"
    url = (f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}"
           f"?width={size}&height={size}&seed={seed}&nologo=true")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=25) as r:
            data = r.read()
        if len(data) < 2000:  # suspiciously small = likely an error page, not an image
            raise RuntimeError("response too small, likely not a real image")
        with open(img_path, "wb") as f:
            f.write(data)
        print(f"  AI thumbnail character generated ({pose_desc[:35]}...)")
        return str(img_path)
    except Exception as e:
        print(f"  AI character generation failed ({e}), using hand-drawn fallback")
        return None


def get_topic_image(topic, seed_suffix=""):
    """Fetch a topic-relevant image. Tries Pexels (free API, real
    keyword-matched photos) first, falls back to Picsum (seeded random
    photography, always works, no key needed) if Pexels isn't configured
    or fails. source.unsplash.com is NOT used — Unsplash permanently
    retired that endpoint in 2024 (it now returns HTTP 503)."""
    import hashlib
    cache_dir = Path("topic_images")
    cache_dir.mkdir(exist_ok=True)
    safe = hashlib.md5((topic + seed_suffix).encode()).hexdigest()[:10]
    img_path = cache_dir / f"{safe}.jpg"
    if img_path.exists():
        return str(img_path)

    t = topic.lower()
    kw_map = {
        ("sip","निवेश","invest","mutual fund","म्यूचुअल"): "investment growth finance",
        ("टैक्स","tax","80c","elss"):                       "tax savings india",
        ("बजट","budget","50-30-20"):                        "budget planning money",
        ("इमरजेंसी फंड","emergency fund"):                   "emergency fund savings",
        ("शेयर","stock","बाजार","market","index fund"):     "stock market india",
        ("क्रेडिट कार्ड","credit card"):                     "credit card finance",
        ("रिटायरमेंट","retirement","nps"):                   "retirement planning india",
        ("गोल्ड","gold"):                                    "gold investment india",
        ("फिक्स्ड डिपॉजिट","fixed deposit","fd"):            "bank savings india",
        ("पर्सनल लोन","loan","कर्ज"):                        "personal loan finance",
        ("क्रेडिट स्कोर","credit score"):                    "credit score finance",
        ("टर्म इंश्योरेंस","term plan","term insurance"):    "term insurance family",
        ("हेल्थ इंश्योरेंस","health cover","health insurance"): "health insurance india",
        ("एंडोमेंट","endowment"):                            "insurance policy documents",
        ("ulip","यूलिप"):                                    "investment insurance india",
        ("नॉमिनी","nominee"):                                "family finance planning",
        ("क्रिटिकल इलनेस","critical illness"):               "health insurance hospital",
        ("फैमिली फ्लोटर","family floater"):                  "family health insurance",
        ("चाइल्ड इंश्योरेंस","child insurance"):             "family savings india",
        ("क्लेम","claim"):                                   "insurance claim documents",
        ("प्रीमियम","premium"):                              "insurance premium finance",
    }

    keyword = "finance money india"
    for keys, kw in kw_map.items():
        if isinstance(keys, str):
            keys = (keys,)
        if any(k in t for k in keys):
            keyword = kw
            break

    pexels_key = os.environ.get("PEXELS_API_KEY", "")
    if pexels_key:
        try:
            search_url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(keyword)}&per_page=5&orientation=portrait"
            req = urllib.request.Request(search_url, headers={"Authorization": pexels_key})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode())
            photos = data.get("photos", [])
            if photos:
                pick = random.choice(photos)
                photo_url = pick["src"]["portrait"]
                img_req = urllib.request.Request(photo_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(img_req, timeout=15) as r:
                    with open(img_path, "wb") as f:
                        f.write(r.read())
                print(f"  Image (Pexels): {keyword}")
                return str(img_path)
        except Exception as e:
            print(f"  Pexels failed ({e}), falling back to Picsum")

    # Fallback: Picsum — no keyword matching, but always works, no key needed
    try:
        seed = safe
        url = f"https://picsum.photos/seed/{seed}/1080/1920"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            with open(img_path, "wb") as f:
                f.write(r.read())
        print(f"  Image (Picsum fallback, seed={seed})")
        return str(img_path)
    except Exception as e:
        print(f"  Image failed: {e}")
        return None

# ══════════════════════════════════════════════════════════
#  BUILD VIDEO FRAME
# ══════════════════════════════════════════════════════════
def build_frame(theme, screen_num, title, tips,
                highlight_idx=-1, total=5, topic_image=None, topic=None,
                point_image=None, point_text=None, layout="stacked",
                visual_spec=None, ai_character_path=None):
    p     = theme["primary"]
    d     = theme["dark"]
    bg    = theme["bg"]
    light = theme["light"]
    white = (255, 255, 255)
    black = (20, 20, 20)

    img  = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)

    # ── Background image (topic related) ─────────────────
    if topic_image and os.path.exists(topic_image):
        try:
            ti = Image.open(topic_image).convert("RGB")
            ti = ti.resize((W, H))
            overlay = Image.new("RGB", (W, H), bg)
            img = Image.blend(ti, overlay, 0.78)
            draw = ImageDraw.Draw(img)
        except Exception as e:
            print(f"  BG error: {e}")

    # ── Diagonal pattern ──────────────────────────────────
    sc = tuple(max(0, c-18) for c in bg)
    for i in range(-H, W+H, 80):
        draw.line([(i, 0), (i+H, H)], fill=sc, width=35)

    # ── TOP BANNER (gradient) ─────────────────────────────
    banner_h = 230
    for y in range(banner_h):
        alpha = y / banner_h
        r2 = int(p[0] * (1-alpha*0.3))
        g2 = int(p[1] * (1-alpha*0.3))
        b2 = int(p[2] * (1-alpha*0.3))
        draw.line([(0,y),(W,y)], fill=(r2,g2,b2))

    # Channel Logo
    logo_cx, logo_cy = 112, 112
    logo_r = 88

    for glow in [6, 4, 2]:
        alpha_col = tuple(min(255, c+60) for c in p)
        draw.ellipse([logo_cx-logo_r-glow, logo_cy-logo_r-glow,
                      logo_cx+logo_r+glow, logo_cy+logo_r+glow],
                    fill=alpha_col)
    draw.ellipse([logo_cx-logo_r-3, logo_cy-logo_r-3,
                  logo_cx+logo_r+3, logo_cy+logo_r+3], fill=white)

    logo_placed = False
    for lp in LOGO_PATHS:
        if os.path.exists(lp):
            try:
                li = Image.open(lp).convert("RGBA")
                ls = logo_r * 2
                li = li.resize((ls, ls), Image.LANCZOS)
                mask = Image.new("L", (ls, ls), 0)
                ImageDraw.Draw(mask).ellipse([0,0,ls,ls], fill=255)
                img.paste(li, (logo_cx-logo_r, logo_cy-logo_r), mask)
                draw = ImageDraw.Draw(img)
                logo_placed = True
                break
            except Exception as e:
                print(f"  Logo err {lp}: {e}")

    if not logo_placed:
        draw.ellipse([logo_cx-logo_r, logo_cy-logo_r,
                      logo_cx+logo_r, logo_cy+logo_r], fill=white)
        draw.text((logo_cx, logo_cy-18), "Capital",
                 font=load_latin_font(38), fill=p, anchor="mm")
        draw.text((logo_cx, logo_cy+28), "Insurance",
                 font=load_latin_font(30), fill=d, anchor="mm")

    # ── Channel name / handle — AUTO-SIZED pill, guaranteed-Latin font ──
    cn_font = load_latin_font(52)
    ch_font = load_latin_font(34, bold=False)

    name_tw = draw.textlength(CHANNEL_NAME, font=cn_font)
    name_w  = int(name_tw) + 46
    draw.rounded_rectangle([210, 42, 210+name_w, 42+70],
                           radius=35, fill=(0, 0, 0))
    draw.text((233, 77), CHANNEL_NAME,
             font=cn_font, fill=white, anchor="lm")

    handle_tw = draw.textlength(CHANNEL_HANDLE, font=ch_font)
    handle_w  = int(handle_tw) + 40
    draw.rounded_rectangle([210, 122, 210+handle_w, 122+52],
                           radius=26, fill=(0, 0, 0))
    draw.text((230, 148), CHANNEL_HANDLE,
             font=ch_font, fill=(240,240,240), anchor="lm")

    # Subscribe pill (vector bell icon, not emoji — always renders)
    sw, sh = 290, 60
    sx = W - sw - 25
    sy = 158
    draw.rounded_rectangle([sx+3, sy+3, sx+sw+3, sy+sh+3],
                           radius=30, fill=d)
    draw.rounded_rectangle([sx, sy, sx+sw, sy+sh],
                           radius=30, fill=white)
    draw.text((sx+sw//2+22, sy+sh//2), "SUBSCRIBE",
             font=load_latin_font(34), fill=p, anchor="mm")
    draw.ellipse([sx-70, sy, sx-10, sy+sh], fill=white)
    draw_icon(draw, sx-40, sy+sh//2, "bell", p, size=40)

    # ══════════════════════════════════════════════════════
    #  MODE 1: SINGLE-POINT REVEAL (screens 1, 2, 3)
    #  Large point-specific image + caption in the FOOTER
    #  3 alternating layouts for visual variety across videos
    # ══════════════════════════════════════════════════════
    if point_text is not None:
        badge_y = banner_h + 20
        f_badge = load_latin_font(38)
        draw.ellipse([40, badge_y, 40+64, badge_y+64], fill=p)
        draw.text((72, badge_y+32), str(screen_num),
                 font=f_badge, fill=white, anchor="mm")
        f_lbl = pick_font("पॉइंट", 34)
        draw.text((118, badge_y+32), f"पॉइंट {screen_num} / 3",
                 font=f_lbl, fill=p, anchor="lm")

        img_y1 = badge_y + 84
        footer_h = 175
        footer_y = H - 285 - footer_h - 18
        img_y2 = footer_y - 15
        mascot_poses = {1: "wave", 2: "point", 3: "happy"}
        mpose = mascot_poses.get(screen_num, "idle")

        if layout == "split":
            # Left color panel (illustration) + right white panel (big numeral)
            mid_x = (26 + (W-26)) // 2
            draw.rounded_rectangle([26, img_y1+6, W-26, img_y2+6],
                                   radius=26, fill=(140,140,140))
            draw.rounded_rectangle([26, img_y1, mid_x, img_y2],
                                   radius=0, fill=light)
            draw.rounded_rectangle([mid_x, img_y1, W-26, img_y2],
                                   radius=0, fill=(250,250,250))
            draw.rounded_rectangle([26, img_y1, W-26, img_y2],
                                   radius=26, outline=p, width=6)
            draw.line([mid_x, img_y1+10, mid_x, img_y2-10], fill=p, width=4)
            icx = (26 + mid_x) // 2
            icy = (img_y1 + img_y2) // 2
            iw  = (mid_x-26) * 0.7
            ih  = (img_y2 - img_y1) * 0.7
            draw_point_visual(draw, icx, icy, iw, ih, visual_spec, point_text, theme)
            f_num_big = load_latin_font(int((img_y2-img_y1)*0.55))
            draw.text(((mid_x+(W-26))//2, (img_y1+img_y2)//2), str(screen_num),
                     font=f_num_big, fill=p, anchor="mm")
            draw_mascot(draw, mid_x+70, img_y1+70, 90, mpose, theme)

        elif layout == "badge":
            # Circular badge illustration on a soft gradient card
            draw.rounded_rectangle([26, img_y1+6, W-26, img_y2+6],
                                   radius=26, fill=(140,140,140))
            draw.rounded_rectangle([26, img_y1, W-26, img_y2],
                                   radius=26, fill=light, outline=p, width=6)
            bcx = (26 + (W-26)) // 2
            bcy = (img_y1 + img_y2) // 2
            brad = min(W-100, img_y2-img_y1-60) // 2
            for g in range(3, 0, -1):
                draw.ellipse([bcx-brad-g*8, bcy-brad-g*8, bcx+brad+g*8, bcy+brad+g*8],
                            outline=p, width=3)
            draw.ellipse([bcx-brad, bcy-brad, bcx+brad, bcy+brad], fill=white, outline=p, width=6)
            draw_point_visual(draw, bcx, bcy, brad*1.15, brad*1.15, visual_spec, point_text, theme)
            draw_mascot(draw, W-115, img_y1+95, 100, mpose, theme)

        else:  # "stacked" — default
            draw.rounded_rectangle([26, img_y1+6, W-26, img_y2+6],
                                   radius=26, fill=(140,140,140))
            draw.rounded_rectangle([26, img_y1, W-26, img_y2],
                                   radius=26, fill=(250,250,250))
            icx = (26 + (W-26)) // 2
            icy = (img_y1 + img_y2) // 2
            iw  = (W-52) * 0.68
            ih  = (img_y2 - img_y1) * 0.68
            draw_point_visual(draw, icx, icy, iw, ih, visual_spec, point_text, theme)
            draw.rounded_rectangle([26, img_y1, W-26, img_y2],
                                   radius=26, outline=p, width=6)
            draw_mascot(draw, W-110, img_y1+95, 100, mpose, theme)

        # ── AI presenter character (same image reused all video long) ──
        if ai_character_path and os.path.exists(ai_character_path):
            paste_ai_character(img, ai_character_path, img_y1, img_y2, W)
            draw = ImageDraw.Draw(img)

        # ── Footer caption (the point text lives HERE, not up top) ──
        draw.rounded_rectangle([28, footer_y+6, W-28, footer_y+footer_h+6],
                               radius=24, fill=(130,130,130))
        draw.rounded_rectangle([28, footer_y, W-28, footer_y+footer_h],
                               radius=24, fill=p)
        draw.rounded_rectangle([28, footer_y, 100, footer_y+footer_h],
                               radius=24, fill=d)
        f_num = load_latin_font(52)
        draw.ellipse([112, footer_y+footer_h//2-38, 188, footer_y+footer_h//2+38],
                    fill=white)
        draw.text((150, footer_y+footer_h//2), str(screen_num),
                 font=f_num, fill=p, anchor="mm")
        clines = wrap_mixed(point_text, 48, W-260, draw)
        cy = footer_y + footer_h//2 - len(clines)*28
        for line in clines:
            draw_mixed_text(draw, (205, cy), line, 48, white, anchor="lm")
            cy += 56

    # ══════════════════════════════════════════════════════
    #  MODE 2: INTRO (screen 0) — same visual language as the
    #  point screens: big topic illustration + caption in FOOTER
    #  (tips are NOT revealed yet — kept for step-by-step reveal)
    # ══════════════════════════════════════════════════════
    elif screen_num == 0:
        lbl_y = banner_h + 20
        draw.ellipse([40, lbl_y+12, 40+44, lbl_y+12+44], fill=p)
        draw.polygon([(62,lbl_y+20),(52,lbl_y+40),(60,lbl_y+38),(56,lbl_y+52),(74,lbl_y+32),(65,lbl_y+34)], fill=white)
        draw.text((100, lbl_y+34), "3 जरूरी पॉइंट्स आगे",
                 font=pick_font("3 जरूरी पॉइंट्स आगे", 34), fill=p, anchor="lm")

        img_y1 = lbl_y + 84
        footer_h = 200
        footer_y = H - 285 - footer_h - 18
        img_y2 = footer_y - 15

        draw.rounded_rectangle([26, img_y1+6, W-26, img_y2+6],
                               radius=26, fill=(140,140,140))
        draw.rounded_rectangle([26, img_y1, W-26, img_y2],
                               radius=26, fill=(250,250,250))
        illus_kind = get_illustration_kind(title)
        icx = (26 + (W-26)) // 2
        icy = (img_y1 + img_y2) // 2
        iw  = (W-52) * 0.62
        ih  = (img_y2 - img_y1) * 0.62
        draw_illustration(draw, icx, icy, iw, ih, illus_kind, theme)
        draw.rounded_rectangle([26, img_y1, W-26, img_y2],
                               radius=26, outline=p, width=6)
        draw_mascot(draw, W-110, img_y1+95, 100, "wave", theme)

        # Teaser dots — hints 3 points are coming, in the image card
        for i in range(3):
            cx = 140 + i*80
            cy = img_y2 - 55
            draw.ellipse([cx-28, cy-28, cx+28, cy+28],
                        fill=white, outline=p, width=4)
            draw.text((cx, cy), str(i+1), font=load_latin_font(34),
                     fill=p, anchor="mm")

        # ── AI presenter character (same image reused all video long) ──
        if ai_character_path and os.path.exists(ai_character_path):
            paste_ai_character(img, ai_character_path, img_y1, img_y2, W)
            draw = ImageDraw.Draw(img)

        # ── Footer caption — the hook/title lives HERE ──
        draw.rounded_rectangle([28, footer_y+6, W-28, footer_y+footer_h+6],
                               radius=24, fill=(130,130,130))
        draw.rounded_rectangle([28, footer_y, W-28, footer_y+footer_h],
                               radius=24, fill=p)
        tlines = wrap_mixed(title, 52, W-100, draw)
        t_y = footer_y + footer_h//2 - len(tlines)*32
        for line in tlines:
            draw_mixed_text(draw, (W//2, t_y), line, 52, white, anchor="mm")
            t_y += 64

    # ══════════════════════════════════════════════════════
    #  MODE 3: OUTRO RECAP (screen 4) — all 3 points shown
    #  together as a summary, now that they've been revealed
    # ══════════════════════════════════════════════════════
    else:
        ty = banner_h + 22
        th = 140
        draw.rounded_rectangle([34, ty+5, W-24, ty+th+5],
                               radius=22, fill=(180,180,180))
        draw.rounded_rectangle([28, ty, W-28, ty+th],
                               radius=22, fill=white, outline=p, width=5)
        tlines = wrap_mixed(title, 50, W-120, draw)
        t_y = ty + th//2 - len(tlines)*28
        for line in tlines:
            draw_mixed_text(draw, (W//2, t_y), line, 50, p, anchor="mm")
            t_y += 58
        draw_mascot(draw, W-95, ty+70, 90, "happy", theme)

        item_start = ty + th + 20
        item_h     = 145
        gap        = 18
        f_num      = load_latin_font(46)
        for idx, tip in enumerate(tips[:3]):
            iy = item_start + idx * (item_h + gap)
            if iy + item_h > H - 230:
                break
            draw.rounded_rectangle([34, iy+6, W-24, iy+item_h+6],
                                   radius=22, fill=(150,150,150))
            draw.rounded_rectangle([28, iy, W-28, iy+item_h],
                                   radius=22, fill=white, outline=p, width=3)
            draw.rounded_rectangle([28, iy, 96, iy+item_h],
                                   radius=22, fill=p)
            draw.ellipse([108, iy+item_h//2-32, 176, iy+item_h//2+32],
                        fill=d)
            draw.text((142, iy+item_h//2), str(idx+1),
                     font=f_num, fill=white, anchor="mm")
            ilines = wrap_mixed(tip, 44, W-230, draw)
            it_y = iy + item_h//2 - len(ilines)*26
            for line in ilines:
                draw_mixed_text(draw, (196, it_y), line, 44, black, anchor="lm")
                it_y += 54

    # ── DISCLAIMER BAR (SEBI for finance / IRDAI for insurance) ──
    disclaimer_short, _ = get_disclaimer(topic)
    sebi_y = H - 285
    draw.rectangle([0, sebi_y, W, sebi_y+60], fill=(170, 15, 15))
    draw.text((W//2, sebi_y+30),
             disclaimer_short,
             font=load_latin_font(22), fill=(255,255,255), anchor="mm")

    # ── PROGRESS DOTS ─────────────────────────────────────
    dot_y = H - 198
    for dd in range(total):
        dx = W//2 - (total-1)*24 + dd*48
        if dd == screen_num:
            draw.ellipse([dx-16, dot_y-16, dx+16, dot_y+16], fill=p)
        else:
            draw.ellipse([dx-9, dot_y-9, dx+9, dot_y+9],
                        outline=p, width=3, fill=bg)

    # ── CTA BUTTONS (vector icons, no emoji/font dependency) ──
    cta_y = H - 175
    btn_h = 115
    pad   = 14
    btn_w = (W - 56 - pad*2) // 3
    f_btn = load_latin_font(36)

    buttons = [
        ("like",  "LIKE",      (220,50,50)),
        ("share", "SHARE",     (50,130,220)),
        ("bell",  "SUBSCRIBE", (20,160,80)),
    ]

    for i, (kind, label, btn_col) in enumerate(buttons):
        bx = 28 + i * (btn_w + pad)

        # Button shadow — solid dark color, not RGBA (RGBA on an RGB
        # image renders corrupted, which caused the blank-looking buttons)
        draw.rounded_rectangle([bx+4, cta_y+4, bx+btn_w+4, cta_y+btn_h+4],
                               radius=22, fill=(20,20,20))
        draw.rounded_rectangle([bx, cta_y, bx+btn_w, cta_y+btn_h],
                               radius=22, fill=btn_col)
        draw.rounded_rectangle([bx+6, cta_y+4, bx+btn_w-6, cta_y+42],
                               radius=16,
                               fill=tuple(min(255,c+50) for c in btn_col))

        draw_icon(draw, bx+btn_w//2, cta_y+38, kind, white, size=44)
        draw.text((bx+btn_w//2, cta_y+btn_h-24), label,
                 font=f_btn, fill=white, anchor="mm")

        if screen_num % 2 == i % 2:
            draw.ellipse([bx+btn_w//2-52, cta_y+40-52,
                          bx+btn_w//2+52, cta_y+40+52],
                        outline=white, width=3)

    return np.array(img)

# ══════════════════════════════════════════════════════════
#  THUMBNAIL
# ══════════════════════════════════════════════════════════
def generate_thumbnail(script_data, theme, output_path, topic_image=None, topic=None):
    TW, TH = 1280, 720
    p, d, bg = theme["primary"], theme["dark"], theme["bg"]
    white, black = (255,255,255), (20,20,20)

    img  = Image.new("RGB", (TW, TH), bg)
    draw = ImageDraw.Draw(img)

    # Background image
    if topic_image and os.path.exists(topic_image):
        try:
            ti = Image.open(topic_image).convert("RGB").resize((TW, TH))
            overlay = Image.new("RGB", (TW, TH), bg)
            img = Image.blend(ti, overlay, 0.72)
            draw = ImageDraw.Draw(img)
        except:
            pass

    # Top banner
    draw.rectangle([0, 0, TW, 100], fill=p)
    draw.text((TW//2, 50), CHANNEL_HANDLE,
             font=load_latin_font(46), fill=white, anchor="mm")

    # Left accent
    draw.rectangle([0, 0, 16, TH], fill=p)

    # ── Character panel (right side) — AI image if available, else
    # our reliable hand-drawn character as fallback ──
    char_x1 = TW - 360
    is_insurance = script_data.get("_category") == "Insurance"
    pose_desc = generate_thumbnail_scene(
        topic or script_data.get("title", ""), script_data.get("hook", ""), is_insurance
    )
    ai_char_path = get_ai_character_image(pose_desc, seed=random.randint(1000, 9999))
    if ai_char_path and os.path.exists(ai_char_path):
        try:
            ci = Image.open(ai_char_path).convert("RGB")
            cw, ch = TW-char_x1, TH-110
            cr = ci.width / ci.height
            br = cw / ch
            if cr > br:
                nh, nw = ch, int(ch*cr)
            else:
                nw, nh = cw, int(cw/cr)
            ci = ci.resize((nw, nh), Image.LANCZOS)
            left = (nw-cw)//2
            top  = max(0, (nh-ch)//3)
            ci = ci.crop((left, top, left+cw, top+ch))
            img.paste(ci, (char_x1, 110))
            draw = ImageDraw.Draw(img)
        except Exception as e:
            print(f"  Thumbnail AI char paste failed ({e}), using hand-drawn")
            ai_char_path = None
    if not ai_char_path:
        draw.rounded_rectangle([char_x1, 110, TW-28, TH-20], radius=20, fill=(250,250,250), outline=p, width=4)
        pose = "happy_arms" if is_insurance else "point_up"
        draw_person(draw, char_x1+165, 400, 340, pose, theme, 0)

    text_right_edge = char_x1 - 20

    # Title
    title = script_data.get("thumbnail_title",
            script_data.get("hook", "Finance Tips"))[:42]
    draw.rounded_rectangle([28, 115, text_right_edge, 300],
                           radius=20, fill=white, outline=p, width=4)
    tlines = wrap_mixed(title, 58, text_right_edge-110, draw)
    ty = 208 - len(tlines)*32
    for line in tlines:
        draw_mixed_text(draw, ((28+text_right_edge)//2, ty), line, 58, p, anchor="mm")
        ty += 66

    # Tips
    tips = script_data.get("key_points", [])[:3]
    tip_y = 315
    for i, tip in enumerate(tips):
        draw.rounded_rectangle([28, tip_y, text_right_edge, tip_y+90],
                               radius=18, fill=white, outline=p, width=2)
        draw.rounded_rectangle([28, tip_y, 82, tip_y+90],
                               radius=18, fill=p)
        draw.text((55, tip_y+45), str(i+1),
                 font=load_latin_font(44), fill=white, anchor="mm")
        draw_mixed_text(draw, (100, tip_y+45), tip[:42], 38, black, anchor="lm")
        tip_y += 105

    img.save(output_path, "JPEG", quality=95)

# ══════════════════════════════════════════════════════════
#  VOICEOVER
# ══════════════════════════════════════════════════════════
EDGE_TTS_VOICES = ["hi-IN-MadhurNeural", "hi-IN-SwaraNeural"]

def generate_voiceover(script_text, output_path, lang="hi"):
    """Tries Microsoft Edge TTS first (far more natural Hindi voice than
    gTTS), falls back to gTTS if edge-tts isn't installed or the network
    call fails — so a missing/broken edge-tts never breaks the pipeline."""
    try:
        import edge_tts, asyncio
        voice = random.choice(EDGE_TTS_VOICES)

        async def _gen():
            communicate = edge_tts.Communicate(script_text, voice, rate="+2%")
            await communicate.save(output_path)

        asyncio.run(_gen())
        audio = AudioFileClip(output_path)
        dur = audio.duration
        audio.close()
        if dur < 1:
            raise RuntimeError("Edge TTS produced near-empty audio")
        print(f"  Voiceover (Edge TTS, {voice}): {dur:.1f}s")
        return dur
    except Exception as e:
        print(f"  Edge TTS failed ({e}), falling back to gTTS")
        tts = gTTS(text=script_text, lang=lang, slow=False, tld="co.in")
        tts.save(output_path)
        audio = AudioFileClip(output_path)
        dur = audio.duration
        audio.close()
        print(f"  Voiceover (gTTS fallback): {dur:.1f}s")
        return dur

# ══════════════════════════════════════════════════════════
#  VIDEO
# ══════════════════════════════════════════════════════════
def build_caption_chunks(script_text, audio_duration, skip_last_frac=0.08, words_per_chunk=6):
    """Splits the narration into short caption chunks and estimates a
    (start, duration) for each by distributing them proportionally to
    word count across the audio. Approximate (no real forced-alignment),
    but good enough for readable on-screen captions synced to speech.
    Chunks that would fall in the outro (last skip_last_frac of the
    video, which has no picture area to caption over) are dropped."""
    import re
    clauses = re.split(r"[।.!?,\n]+", script_text)
    words = []
    for c in clauses:
        words.extend(c.strip().split())
    words = [w for w in words if w]
    if not words:
        return []

    chunks = [" ".join(words[i:i+words_per_chunk]) for i in range(0, len(words), words_per_chunk)]
    total_words = len(words)
    usable_duration = audio_duration * (1 - skip_last_frac)

    result = []
    word_cursor = 0
    for chunk in chunks:
        n = len(chunk.split())
        start = (word_cursor / total_words) * usable_duration
        end   = ((word_cursor + n) / total_words) * usable_duration
        word_cursor += n
        if start >= usable_duration:
            break
        result.append((chunk, start, max(0.4, end - start)))
    return result


def make_caption_clip(text, strip_y, strip_h):
    """Renders one caption chunk as a semi-transparent bar + white text,
    returned as an RGB numpy array + a matching alpha mask array."""
    img = Image.new("RGBA", (W, strip_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([40, 6, W-40, strip_h-6], radius=18, fill=(0, 0, 0, 165))
    lines = wrap_mixed(text, 40, W-140, draw)[:2]
    ty = strip_h//2 - len(lines)*26
    for line in lines:
        draw_mixed_text(draw, (W//2, ty), line, 40, (255,255,255,255), anchor="mm")
        ty += 52
    arr = np.array(img)
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3] / 255.0
    return rgb, alpha


def create_short_video(script_data, audio_path, audio_duration,
                       theme, output_path, topic=None):
    from moviepy.editor import CompositeVideoClip, CompositeAudioClip, afx

    tips  = script_data.get("key_points", ["Tip 1","Tip 2","Tip 3"])
    hook  = script_data.get("hook", "Finance Tips")[:42]
    title = script_data.get("thumbnail_title", hook)[:42]

    topic_image = get_topic_image(topic or "finance")
    visuals = script_data.get("visuals", [{"type":"icon"}]*3)
    while len(visuals) < 3:
        visuals.append({"type": "icon"})
    has_rich_visual = any(v.get("type") in ("comparison", "flow") for v in visuals[:3])
    video_layout = "stacked" if has_rich_visual else random.choice(["stacked", "split", "badge"])
    print(f"  Layout template: {video_layout}")

    # AI presenter character — generated ONCE per video (not per screen)
    # so it (a) stays visually consistent across the whole video and
    # (b) only costs one network call, keeping the pipeline reliable.
    # Falls back to nothing (existing hand-drawn scene characters still
    # appear inside the icon illustrations) if the free API is slow/down.
    is_insurance_topic = get_disclaimer(topic or "")[1] == IRDAI_DISCLAIMER
    presenter_pose = (
        "confident pose, arms crossed, holding a green insurance shield, warm smile"
        if is_insurance_topic else
        "excited pose, one arm raised pointing up, holding cash, big smile, dynamic energy"
    )
    ai_presenter_path = get_ai_character_image(
        presenter_pose, seed=random.randint(1000, 9999)
    )

    # Timing — 2 minute video
    intro = audio_duration * 0.12
    t1    = audio_duration * 0.27
    t2    = audio_duration * 0.27
    t3    = audio_duration * 0.26
    outro = audio_duration * 0.08

    print(f"  Timing: {audio_duration:.1f}s total | intro={intro:.1f} tip1={t1:.1f} tip2={t2:.1f} tip3={t3:.1f} outro={outro:.1f}")

    # Build frames — one point revealed at a time, each with its own image
    f_intro = build_frame(theme, 0, title, tips, total=5,
                          topic_image=topic_image, topic=topic, ai_character_path=ai_presenter_path)
    f_t1 = build_frame(theme, 1, title, tips, total=5, topic=topic, point_text=tips[0], layout=video_layout, visual_spec=visuals[0], ai_character_path=ai_presenter_path)
    f_t2 = build_frame(theme, 2, title, tips, total=5, topic=topic, point_text=tips[1], layout=video_layout, visual_spec=visuals[1], ai_character_path=ai_presenter_path)
    f_t3 = build_frame(theme, 3, title, tips, total=5, topic=topic, point_text=tips[2], layout=video_layout, visual_spec=visuals[2], ai_character_path=ai_presenter_path)
    f_outro = build_frame(theme, 4, f"Yaad Rakho! {CHANNEL_NAME}", tips, total=5,
                          topic_image=topic_image, topic=topic, ai_character_path=ai_presenter_path)

    # Ken Burns — a subtle, slow zoom-in on each static frame so nothing
    # feels like a dead still image. Each clip zooms independently over
    # its own duration; CompositeVideoClip crops anything past the
    # canvas edge, so this never needs manual re-centering math.
    def kenburns(img_array, duration, zoom_to=1.045):
        clip = ImageClip(img_array).set_duration(duration)
        clip = clip.resize(lambda t: 1 + (zoom_to-1) * (t/max(duration,0.01)))
        clip = clip.set_position(("center","center"))
        return clip

    segments = [
        (f_intro, intro), (f_t1, t1), (f_t2, t2), (f_t3, t3), (f_outro, outro),
    ]
    clips = []
    t_cursor = 0
    for img_arr, dur in segments:
        clips.append(kenburns(img_arr, dur).set_start(t_cursor))
        t_cursor += dur

    layers = list(clips)

    # ── Burned-in captions, synced (approximately) to the narration ──
    script_text = script_data.get("script", "")
    if script_text:
        strip_h = 130
        strip_y = 1427 - strip_h - 10  # bottom of the shared image-card zone
        for chunk_text, start, dur in build_caption_chunks(script_text, audio_duration):
            try:
                rgb, alpha = make_caption_clip(chunk_text, strip_y, strip_h)
                cclip = (ImageClip(rgb).set_duration(dur)
                        .set_mask(ImageClip(alpha, ismask=True).set_duration(dur))
                        .set_position((0, strip_y)).set_start(start))
                layers.append(cclip)
            except Exception as e:
                print(f"  Caption chunk skipped: {e}")

    video = CompositeVideoClip(layers, size=(W, H)).set_duration(t_cursor)

    # ── Audio: voice + optional background music (if a track is provided) ──
    voice = AudioFileClip(audio_path)
    final_audio = voice
    bgm_path = None
    for candidate in ("bgm.mp3", "assets/bgm.mp3", "background_music.mp3"):
        if os.path.exists(candidate):
            bgm_path = candidate
            break
    if bgm_path:
        try:
            bgm = AudioFileClip(bgm_path).fx(afx.audio_loop, duration=voice.duration)
            bgm = bgm.fx(afx.volumex, 0.10)
            final_audio = CompositeAudioClip([bgm, voice])
            print(f"  Background music: {bgm_path}")
        except Exception as e:
            print(f"  Background music failed ({e}), continuing with voice only")

    video = video.set_audio(final_audio)
    video.write_videofile(output_path, fps=FPS, codec="libx264",
                         audio_codec="aac", threads=4, logger=None)
    print(f"  Video: {output_path}")
    return topic_image

# ══════════════════════════════════════════════════════════
#  SEO SCRIPT GENERATOR
# ══════════════════════════════════════════════════════════
def get_market_snapshot():
    """Fetches today's real Nifty 50 + Sensex level and day-change via
    yfinance, so the AI script can reference ACTUAL current numbers
    instead of hallucinated ones. Returns None (silently) on any failure
    — network issues, yfinance rate limits, market holidays — so this
    never blocks video generation."""
    try:
        import yfinance as yf
        lines = []
        for ticker, label in [("^NSEI", "Nifty 50"), ("^BSESN", "Sensex")]:
            t = yf.Ticker(ticker)
            hist = t.history(period="2d")
            if len(hist) >= 2:
                today = hist["Close"].iloc[-1]
                prev = hist["Close"].iloc[-2]
                pct = (today - prev) / prev * 100
                arrow = "▲" if pct >= 0 else "▼"
                lines.append(f"{label}: {today:,.0f} {arrow} {pct:+.2f}%")
        if lines:
            snapshot = " | ".join(lines)
            print(f"  Market snapshot: {snapshot}")
            return snapshot
    except Exception as e:
        print(f"  Market data unavailable ({e}), continuing without it")
    return None


def generate_finance_script(topic, lang="hi"):
    groq_client = Groq(api_key=GEMINI_API_KEY)

    _, disclaimer_line = get_disclaimer(topic)
    is_insurance = disclaimer_line == IRDAI_DISCLAIMER
    category = "Insurance" if is_insurance else "Finance/Investment"
    hashtag_set = (
        "#इंश्योरेंस #Insurance #CapitalInsuranceInvestments #IRDAI #TermInsurance #HealthInsurance #MoneyTips"
        if is_insurance else
        "#फाइनेंस #Finance #CapitalInsuranceInvestments #Investment #SIP #MoneyTips #PersonalFinance"
    )

    market_snapshot = get_market_snapshot() if not is_insurance else None
    market_line = (
        f"TODAY'S REAL MARKET DATA (use this instead of guessing, if relevant to the topic): {market_snapshot}\n"
        if market_snapshot else ""
    )

    prompt = (
        "You are a VIRAL Hindi YouTube Finance & Insurance content creator for Indian audience.\n"
        f"Channel: {CHANNEL_NAME} — Paisa Samjho, Future Sanwaro\n"
        f"Category: {category}\n"
        + market_line +
        "Topic: " + topic + "\n\n"
        "Create a VIRAL finance/insurance video script. Return ONLY valid JSON:\n"
        "{\n"
        "  \"title\": \"VIRAL Hindi title 55-65 chars — use numbers, emotions, curiosity — must end with #Shorts\",\n"
        "  \"description\": \"SEO description 400-500 chars. Line1: hook. Line2-3: what viewers learn. Line4: CTA to follow + watch our latest long-form deep-dive video for the full explanation. Then 20 hashtags mix Hindi+English\",\n"
        "  \"hook\": \"Shocking opening line MAX 38 chars\",\n"
        f"  \"script\": \"Natural Hindi speech 280-300 words for 2 minute video. Start dramatic. Explain points 1-2 in detail with real examples. Before revealing point 3, add ONE curiosity-gap line like 'लेकिन सबसे जरूरी बात अभी बाकी है' or 'रुको, ये तीसरा पॉइंट सबसे ज्यादा पैसे बचाएगा' to keep viewers watching. Explain point 3. End with: {CHANNEL_NAME} follow karo, aur poora explanation ke liye hamari latest long video dekho\",\n"
        "  \"key_points\": [\n"
        "    \"Short powerful Hindi point 1 MAX 38 chars\",\n"
        "    \"Short powerful Hindi point 2 MAX 38 chars\",\n"
        "    \"Short powerful Hindi point 3 MAX 38 chars\"\n"
        "  ],\n"
        "  \"visuals\": [\n"
        "    {\"type\": \"icon\"},\n"
        "    {\"type\": \"icon\"},\n"
        "    {\"type\": \"icon\"}\n"
        "  ],\n"
        "  \"thumbnail_title\": \"Bold Hindi text MAX 32 chars\",\n"
        "  \"pinned_comment\": \"A-vs-B poll style question in Hindi, e.g. 'SIP se karoge ya FD se? Comment mein A ya B likho!'\"\n"
        "}\n\n"
        "SEO RULES:\n"
        "1. Title must have: number OR emotion word (चौंकाने वाला/जरूरी/खतरनाक/समझदारी भरा)\n"
        "2. key_points: exactly 3, MAX 38 chars, action-oriented\n"
        f"3. Description hashtags: {hashtag_set}\n"
        "4. script: 280-300 words, conversational Hindi, factually careful (no guaranteed-return claims for finance, no false claim-approval promises for insurance)\n"
        "4b. MANDATORY retention hook: the curiosity-gap line before point 3 is not optional — it's what keeps Shorts viewers from swiping away\n"
        f"5. At the very end of the script, naturally mention: \"{disclaimer_line}\"\n"
        "6. VISUALS ARRAY — exactly 3 objects, one per key_point, in order. Each object's \"type\" is one of:\n"
        "   - \"icon\" — default, a themed icon illustration for the point (use this most of the time)\n"
        "   - \"comparison\" — ONLY if that key_point compares two concrete numbers/options. Add fields:\n"
        "     \"label_a\", \"value_a\" (short, e.g. \"₹54,000\" or \"12%\"), \"label_b\", \"value_b\"\n"
        "   - \"flow\" — ONLY if that key_point describes a 2-4 step cause-and-effect chain. Add field:\n"
        "     \"steps\": [\"short step 1\", \"short step 2\", \"short step 3\"] (each under 20 Hindi chars)\n"
        "   Most videos should be all \"icon\" type — only use comparison/flow when the point is GENUINELY about\n"
        "   comparing two numbers or a clear multi-step chain. Never force it.\n"
        "7. Return ONLY JSON, no other text"
    )

    completion = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_completion_tokens=3000,
        reasoning_effort="low",
        response_format={"type": "json_object"},
    )
    raw = completion.choices[0].message.content
    if not raw or not raw.strip():
        raise RuntimeError(
            "Groq se khaali response mila. Check karo: (1) API key sahi hai, "
            "(2) console.groq.com pe quota/credits available hain, "
            "(3) model 'openai/gpt-oss-120b' abhi bhi active hai. "
            f"Full completion object: {completion}"
        )
    text = raw.strip()
    if "```" in text:
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else parts[0]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  ⚠️ Raw Groq response that failed to parse:\n{raw[:500]}")
        raise
    data["_lang"] = lang
    data["_category"] = category

    # Validate + fix
    tips = data.get("key_points", [])
    fixed = []
    fallbacks = ["समझदारी से निवेश करें", "पॉलिसी documents पढ़ें", "एक्सपर्ट से सलाह लें"]
    for t in tips:
        t = str(t).strip()
        if t and len(t) > 3:
            fixed.append(t[:40])
    while len(fixed) < 3:
        fixed.append(fallbacks[len(fixed)])
    data["key_points"] = fixed[:3]

    # Validate visuals — must be exactly 3 well-formed entries, else fall
    # back to plain "icon" (which always works via keyword matching)
    raw_visuals = data.get("visuals", [])
    fixed_visuals = []
    if isinstance(raw_visuals, list):
        for v in raw_visuals[:3]:
            if not isinstance(v, dict):
                fixed_visuals.append({"type": "icon"})
                continue
            vtype = v.get("type", "icon")
            if vtype == "comparison" and all(
                v.get(k) for k in ("label_a", "value_a", "label_b", "value_b")
            ):
                fixed_visuals.append({
                    "type": "comparison",
                    "label_a": str(v["label_a"])[:20], "value_a": str(v["value_a"])[:12],
                    "label_b": str(v["label_b"])[:20], "value_b": str(v["value_b"])[:12],
                })
            elif vtype == "flow" and isinstance(v.get("steps"), list) and len(v["steps"]) >= 2:
                fixed_visuals.append({
                    "type": "flow",
                    "steps": [str(s)[:22] for s in v["steps"][:4]],
                })
            else:
                fixed_visuals.append({"type": "icon"})
    while len(fixed_visuals) < 3:
        fixed_visuals.append({"type": "icon"})
    data["visuals"] = fixed_visuals[:3]

    hook = str(data.get("hook", "पैसों का ये राज़")).strip()
    data["hook"] = hook[:40]

    # Ensure title has #Shorts
    title = data.get("title", topic + " #Shorts")
    if "#Shorts" not in title and "#shorts" not in title:
        title = title[:62] + " #Shorts"
    data["title"] = title[:100]

    print(f"  Category: {data['_category']}")
    print(f"  Title: {data['title']}")
    print(f"  Tips: {data['key_points']}")
    print(f"  Visuals: {[v['type'] for v in data['visuals']]}")
    return data

# ══════════════════════════════════════════════════════════
#  TOPIC MANAGEMENT
# ══════════════════════════════════════════════════════════
def get_top_performing_topics(top_n=5, max_check=25):
    """Looks at the last few uploads, fetches their real view counts via
    the YouTube Data API, and returns the topics of the best performers
    — used to bias future AI topic generation toward what's actually
    working. Returns [] on any failure (auth, quota, network) so this
    never blocks the main pipeline."""
    if not LOG_FILE.exists():
        return []
    try:
        with open(LOG_FILE, encoding="utf-8") as f:
            log = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return []
    recent = log[-max_check:]
    ids = [e["video_id"] for e in recent if e.get("video_id")]
    if not ids:
        return []
    try:
        yt = get_youtube_client()
        stats = {}
        for i in range(0, len(ids), 50):
            batch = ids[i:i+50]
            resp = yt.videos().list(part="statistics", id=",".join(batch)).execute()
            for item in resp.get("items", []):
                stats[item["id"]] = int(item["statistics"].get("viewCount", 0))
        scored = [(e["topic"], stats.get(e["video_id"], 0)) for e in recent if e.get("video_id") in stats]
        scored.sort(key=lambda x: x[1], reverse=True)
        top = [t for t, v in scored[:top_n] if v > 0]
        if top:
            print(f"  Top performing recent topics: {top}")
        return top
    except Exception as e:
        print(f"  Performance feedback unavailable ({e})")
        return []


def get_used_topics():
    if not LOG_FILE.exists():
        return []
    try:
        with open(LOG_FILE, encoding="utf-8") as f:
            return [e["topic"] for e in json.load(f)]
    except (json.JSONDecodeError, UnicodeDecodeError):
        print(f"  ⚠️ {LOG_FILE} corrupt tha, khaali list se shuru kar rahe hain")
        return []

def get_next_topic(lang="hi"):
    used = get_used_topics()

    # Custom topics (Telegram se)
    if TOPICS_FILE.exists():
        try:
            with open(TOPICS_FILE, encoding="utf-8") as f:
                custom = json.load(f)
            unused = [t for t in custom if t not in used]
            if unused:
                print(f"  Custom topic: {unused[0]}")
                return unused[0]
        except (json.JSONDecodeError, UnicodeDecodeError):
            print(f"  ⚠️ {TOPICS_FILE} corrupt tha, skip kar rahe hain")

    # AI fresh topics
    cache = Path("ai_topics_cache.json")
    if cache.exists():
        try:
            with open(cache, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("date") == datetime.date.today().isoformat():
                unused = [t for t in data.get("topics",[]) if t not in used]
                if unused:
                    return random.choice(unused)
        except (json.JSONDecodeError, UnicodeDecodeError):
            print("  ⚠️ ai_topics_cache.json corrupt tha, ignore karke fresh topics generate kar rahe hain")
            try:
                cache.unlink()
            except OSError:
                pass

    try:
        top_performers = get_top_performing_topics()
        performance_hint = (
            f"\nThese recent topics performed well (high views) — lean toward similar angles/wording where natural: "
            f"{'; '.join(top_performers)}\n" if top_performers else ""
        )
        groq_client = Groq(api_key=GEMINI_API_KEY)
        prompt = (
            "Generate 15 VIRAL trending Hindi Finance & Insurance topics for Indian YouTube Shorts 2026.\n"
            "Mix roughly half Finance/Investment (SIP, tax, budgeting, stocks, credit, loans, savings) "
            "and half Insurance (term insurance, health insurance, claims, premiums, nominee, riders).\n"
            "Topics should be:\n"
            "- High search volume in India\n"
            "- Clickbait style but informative and factually safe (no guaranteed-return or guaranteed-claim claims)\n"
            "- About common money/insurance problems Indians face\n"
            "- Include numbers or power words\n"
            + performance_hint +
            "Return ONLY a JSON array of Hindi strings."
        )
        comp = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role":"user","content":prompt}],
            temperature=0.9,
            max_completion_tokens=2000,
            reasoning_effort="low",
        )
        text = comp.choices[0].message.content.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        topics = json.loads(text.strip())
        with open(cache, "w", encoding="utf-8") as f:
            json.dump({"date":datetime.date.today().isoformat(),"topics":topics},f,ensure_ascii=False)
        unused = [t for t in topics if t not in used]
        if unused:
            return random.choice(unused)
    except Exception as e:
        print(f"  AI topics failed: {e}")

    # Viral backup list
    unused = [t for t in VIRAL_TOPICS if t not in used]
    if not unused:
        unused = VIRAL_TOPICS
    return random.choice(unused)

# ══════════════════════════════════════════════════════════
#  YOUTUBE UPLOAD
# ══════════════════════════════════════════════════════════
def get_youtube_client():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE,"rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE,"wb") as f:
            pickle.dump(creds,f)
    return build("youtube","v3",credentials=creds)

SERIES_FILE = Path("series_counter.json")
PLAYLIST_CACHE_FILE = Path("playlist_cache.json")

def get_next_series_number(category: str) -> int:
    """Tracks a running episode count per category (Finance/Insurance)
    so videos can carry 'Series #N' branding — gives viewers a reason
    to binge and signals to YouTube's algorithm that this is a
    consistent, ongoing series (helps discoverability)."""
    counts = {}
    if SERIES_FILE.exists():
        try:
            with open(SERIES_FILE, encoding="utf-8") as f:
                counts = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            counts = {}
    counts[category] = counts.get(category, 0) + 1
    try:
        with open(SERIES_FILE, "w", encoding="utf-8") as f:
            json.dump(counts, f, ensure_ascii=False)
    except OSError:
        pass
    return counts[category]


def get_or_create_playlist(yt, title, description):
    """Finds (or creates) a playlist by title, caching the ID locally so
    we don't re-search/re-create on every single upload."""
    cache = {}
    if PLAYLIST_CACHE_FILE.exists():
        try:
            with open(PLAYLIST_CACHE_FILE, encoding="utf-8") as f:
                cache = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            cache = {}
    if title in cache:
        return cache[title]

    try:
        resp = yt.playlists().list(part="snippet", mine=True, maxResults=50).execute()
        for item in resp.get("items", []):
            if item["snippet"]["title"] == title:
                cache[title] = item["id"]
                with open(PLAYLIST_CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(cache, f, ensure_ascii=False)
                return item["id"]

        created = yt.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {"title": title, "description": description},
                "status": {"privacyStatus": "public"},
            },
        ).execute()
        pid = created["id"]
        cache[title] = pid
        with open(PLAYLIST_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
        print(f"  Created playlist: {title}")
        return pid
    except Exception as e:
        print(f"  Playlist setup failed ({e})")
        return None


def add_video_to_playlist(yt, playlist_id, video_id):
    if not playlist_id:
        return
    try:
        yt.playlistItems().insert(
            part="snippet",
            body={"snippet": {
                "playlistId": playlist_id,
                "resourceId": {"kind": "youtube#video", "videoId": video_id},
            }},
        ).execute()
        print("  Added to playlist")
    except Exception as e:
        print(f"  Add-to-playlist failed ({e})")


def report_best_posting_times(max_check=60):
    """Groups recent uploads by the hour they were posted and reports
    average views per hour-slot, using real view counts from the
    YouTube Data API. This is a REPORT, not an auto-scheduler — GitHub
    Actions cron times are static in the workflow YAML and can't be
    changed from inside the Python script, so use this output to
    manually adjust the cron times in the .yml file if one slot is
    consistently outperforming the others."""
    if not LOG_FILE.exists():
        return
    try:
        with open(LOG_FILE, encoding="utf-8") as f:
            log = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return
    recent = log[-max_check:]
    ids = [e["video_id"] for e in recent if e.get("video_id")]
    if not ids:
        return
    try:
        yt = get_youtube_client()
        stats = {}
        for i in range(0, len(ids), 50):
            batch = ids[i:i+50]
            resp = yt.videos().list(part="statistics", id=",".join(batch)).execute()
            for item in resp.get("items", []):
                stats[item["id"]] = int(item["statistics"].get("viewCount", 0))
        by_hour = {}
        for e in recent:
            vid = e.get("video_id")
            if vid not in stats:
                continue
            hour = int(e["date"][11:13])
            by_hour.setdefault(hour, []).append(stats[vid])
        if not by_hour:
            return
        print("  📊 Views by posting hour (IST, approx):")
        for hour in sorted(by_hour, key=lambda h: -sum(by_hour[h])/len(by_hour[h])):
            views = by_hour[hour]
            print(f"     {hour:02d}:00 → avg {sum(views)/len(views):.0f} views ({len(views)} videos)")
    except Exception as e:
        print(f"  Posting-time report unavailable ({e})")


def get_latest_long_video_url():
    """Finds the most recent long-form upload's URL, for cross-promoting
    it in Shorts descriptions ('watch the full explanation'). Returns
    None if no long-form video has been uploaded yet — the caller then
    just skips that line rather than linking to nothing."""
    if not LOG_FILE.exists():
        return None
    try:
        with open(LOG_FILE, encoding="utf-8") as f:
            log = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    long_entries = [e for e in log if str(e.get("theme","")).endswith("-long") and e.get("url")]
    if not long_entries:
        return None
    return long_entries[-1]["url"]


STOPWORDS_HI_EN = set("""
के का की को है हैं में से पर और या एक ये यह वह अगर तो भी सकते सकता हो होगा
कैसे क्या कब कहाँ कौन जरूरी अच्छा बड़ा नया साल महीने दिन बार
the a an is are of to in for and or if you your how what when why do does
""".split())

def extract_dynamic_tags(topic, key_points, max_tags=8):
    """Pulls real, meaningful keywords out of THIS specific video's topic
    and key points (stripping common stopwords/numbers) so every upload
    gets some tags tailored to what it's actually about, on top of the
    fixed category tags — better long-tail discoverability than a
    static 10-tag list repeated on every single video."""
    import re
    text = topic + " " + " ".join(key_points)
    words = re.findall(r"[A-Za-z\u0900-\u097F]+", text)
    seen, tags = set(), []
    for w in words:
        wl = w.lower()
        if len(w) < 3 or wl in STOPWORDS_HI_EN or wl in seen:
            continue
        seen.add(wl)
        tags.append(w)
        if len(tags) >= max_tags:
            break
    return tags


def upload_to_youtube(yt, video_path, thumb_path, script_data, topic=''):
    lang  = script_data.get("_lang","hi")
    raw_title = script_data["title"]
    # Add #Shorts if not present
    if "#Shorts" not in raw_title and "#shorts" not in raw_title:
        raw_title = raw_title[:60] + " | #Shorts"
    title = raw_title[:100]
    is_insurance = script_data.get("_category") == "Insurance"
    series_category = "Insurance" if is_insurance else "Finance"
    series_num = get_next_series_number(series_category)
    series_label = f"{series_category} Tips" if not is_insurance else "Insurance Guide"

    desc  = script_data.get("description","")
    if not desc:
        _, disclaimer_line = get_disclaimer(topic)
        desc = (
            f"{CHANNEL_NAME} — Paisa Samjho, Future Sanwaro\n\n"
            f"इस वीडियो में जानें: {script_data.get('hook','')}\n\n"
            f"Follow करें: {CHANNEL_HANDLE}\n\n"
            f"{disclaimer_line}\n\n"
            + (
                "#इंश्योरेंस #Insurance #CapitalInsuranceInvestments #Shorts #IRDAI "
                "#TermInsurance #HealthInsurance #InsurancePolicy #MoneyTips #FinanceIndia "
                "#InsuranceTips #PolicyBazaar #LifeInsurance #FinancialPlanning"
                if is_insurance else
                "#फाइनेंस #Finance #CapitalInsuranceInvestments #Shorts #Investment "
                "#SIP #MoneyTips #PersonalFinance #StockMarket #TaxSaving "
                "#MutualFunds #FinancialFreedom #MoneyManagement #IndiaFinance"
            )
        )
    long_url = get_latest_long_video_url()
    if long_url and long_url not in desc:
        desc = f"🎥 Poora deep-dive explanation: {long_url}\n\n" + desc
    desc = f"📺 {series_label} — Episode #{series_num}\n\n" + desc

    base_tags = (
        [
            "insurance tips hindi", "capital insurance investments", "term insurance",
            "health insurance", "insurance claim", "irdai", "insurance policy",
            "life insurance india", "insurance shorts", "बीमा",
        ] if is_insurance else
        [
            "finance tips hindi", "capital insurance investments", "sip investment",
            "mutual funds", "personal finance", "tax saving", "stock market india",
            "money management", "finance shorts", "निवेश",
        ]
    )
    # Dynamic tags — pull real keywords out of THIS video's actual topic
    # and key points, so tags aren't the same fixed 10 on every upload
    dynamic_tags = extract_dynamic_tags(topic, script_data.get("key_points", []))
    tags = (base_tags + dynamic_tags)[:20]  # YouTube tags have a combined length limit

    body = {
        "snippet": {
            "title": title,
            "description": desc[:5000],
            "tags": tags,
            "categoryId": "25",
            "defaultLanguage": lang,
            "defaultAudioLanguage": lang,
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
            "madeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    req   = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = req.next_chunk()
        if status:
            print(f"  Upload: {int(status.progress()*100)}%")

    video_id = response.get("id")
    print(f"  Live: https://youtube.com/shorts/{video_id}")

    try:
        yt.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumb_path, mimetype="image/jpeg")
        ).execute()
        print("  Thumbnail OK")
    except Exception as e:
        print(f"  Thumbnail: {e}")

    # Pinned comment
    comment = script_data.get("pinned_comment","")
    if not comment:
        comment = f"Ye tips already try kar rahe ho (A) ya aaj se start karoge (B)? Comment mein A ya B likho 👇\n{CHANNEL_NAME} ko Follow karna na bhoolein! 🔔"
    try:
        yt.commentThreads().insert(
            part="snippet",
            body={"snippet":{
                "videoId": video_id,
                "topLevelComment":{"snippet":{"textOriginal":comment}}
            }}
        ).execute()
        print("  Comment posted")
    except Exception as e:
        print(f"  Comment: {e}")

    # Add to category playlist (Finance / Insurance) — helps discoverability
    playlist_title = "Insurance Guide 🛡️" if is_insurance else "Finance & Investment Tips 📈"
    playlist_id = get_or_create_playlist(
        yt, playlist_title,
        f"{CHANNEL_NAME} — sabhi {series_category.lower()} Shorts ek jagah."
    )
    add_video_to_playlist(yt, playlist_id, video_id)

    return video_id

def log_upload(topic, video_id, title, theme_name):
    log = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, encoding="utf-8") as f:
                log = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            print(f"  ⚠️ {LOG_FILE} corrupt tha, naye se shuru kar rahe hain")
            log = []
    # GitHub Actions runners default to UTC — convert to IST (+5:30) so
    # logged timestamps (and the posting-time report) reflect the actual
    # local time the video went live for Indian viewers.
    ist_now = datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)
    is_long = str(theme_name).endswith("-long")
    log.append({
        "date": ist_now.isoformat(),
        "topic": topic, "video_id": video_id,
        "title": title, "theme": theme_name,
        "url": (f"https://youtube.com/watch?v={video_id}" if is_long
                else f"https://youtube.com/shorts/{video_id}"),
    })
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

# ══════════════════════════════════════════════════════════
#  MAIN PIPELINE
# ══════════════════════════════════════════════════════════
def run_qa_checks(video_path, min_duration=10, max_duration=190):
    """Sanity checks before uploading — catches an obviously broken
    render (corrupt/tiny file, near-silent audio, missing audio track,
    wildly wrong duration) before it goes live on the channel. Returns
    (ok: bool, reason: str) rather than raising, so a failed check can
    be logged clearly and skip the upload instead of crashing the run."""
    if not os.path.exists(video_path):
        return False, "video file was not created"
    if os.path.getsize(video_path) < 50_000:
        return False, f"video file suspiciously small ({os.path.getsize(video_path)} bytes) — likely a broken render"

    issues = []
    try:
        clip = VideoFileClip(video_path)
        dur = clip.duration
        if dur < min_duration or dur > max_duration:
            issues.append(f"duration {dur:.1f}s is outside the expected {min_duration}-{max_duration}s range")
        if clip.audio is None:
            issues.append("video has no audio track at all")
        else:
            try:
                peak = clip.audio.max_volume()
                if peak < 0.01:
                    issues.append(f"audio appears silent/near-silent (peak volume {peak:.4f})")
            except Exception as e:
                issues.append(f"could not verify audio volume ({e})")
        clip.close()
    except Exception as e:
        return False, f"could not open the rendered video to inspect it ({e})"

    if issues:
        return False, "; ".join(issues)
    return True, "OK"


def run_pipeline():
    OUTPUT_DIR.mkdir(exist_ok=True)
    ts    = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # Get topic FIRST, then select theme based on it
    topic = get_next_topic(lang=LANGUAGE)
    import hashlib
    topic_hash = int(hashlib.md5(topic.encode()).hexdigest(), 16)
    theme = THEMES[topic_hash % len(THEMES)]

    print(f"\n{'='*55}")
    print(f"  Topic : {topic}")
    print(f"  Theme : {theme['name']}")
    print(f"{'='*55}")

    audio_path = str(OUTPUT_DIR / f"audio_{ts}.mp3")
    video_path = str(OUTPUT_DIR / f"short_{ts}.mp4")
    thumb_path = str(OUTPUT_DIR / f"thumb_{ts}.jpg")

    try:
        print("\n1/5: Generating viral script...")
        data = generate_finance_script(topic, lang=LANGUAGE)

        print("\n2/5: Hindi voiceover (2 min)...")
        duration = generate_voiceover(data["script"], audio_path, lang=LANGUAGE)

        print("\n3/5: Building video with graphics...")
        topic_image = create_short_video(
            data, audio_path, duration, theme, video_path, topic=topic
        )

        print("\n4/5: Thumbnail...")
        generate_thumbnail(data, theme, thumb_path, topic_image=topic_image, topic=topic)

        print("\n4.5/5: QA check before upload...")
        qa_ok, qa_reason = run_qa_checks(video_path)
        if not qa_ok:
            print(f"  ❌ QA CHECK FAILED: {qa_reason}")
            print("  Skipping upload — a broken video will NOT go live. "
                  "Check the files in output_videos/ to debug, then re-run.")
            return
        print("  ✅ QA check passed")

        print("\n5/5: Uploading to YouTube...")
        yt = get_youtube_client()
        vid = upload_to_youtube(yt, video_path, thumb_path, data, topic=topic)

        log_upload(topic, vid, data["title"], theme["name"])

        # Informational only — cron times are static in the workflow
        # YAML, this just tells you (in the logs) which slot to favor
        try:
            report_best_posting_times()
        except Exception as e:
            print(f"  Posting-time report skipped: {e}")

        for fp in [audio_path, thumb_path]:
            if os.path.exists(fp):
                os.remove(fp)

        print(f"\n🎉 Done! https://youtube.com/shorts/{vid}")
        return vid

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback; traceback.print_exc()
        raise

# ══════════════════════════════════════════════════════════
#  LONG-FORM (15 MIN) VIDEO ENGINE
#  — Trending topics (Google Trends + YouTube) with 70% weightage
#    to fresh trends, 30% to evergreen topic list
# ══════════════════════════════════════════════════════════
LW, LH = 1920, 1080  # landscape dimensions for long-form video

def fetch_google_trends_topics(n=10):
    """Uses pytrends (unofficial Google Trends API). Requires: pip install pytrends"""
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl="hi-IN", tz=330)
        seed_terms = ["SIP investment", "insurance policy", "mutual fund", "tax saving", "term insurance"]
        pytrends.build_payload(kw_list=seed_terms, geo="IN", timeframe="now 7-d")
        related = pytrends.related_queries()
        topics = []
        for kw, data in (related or {}).items():
            if data is None:
                continue
            rising = data.get("rising")
            top = data.get("top")
            if rising is not None and not rising.empty:
                topics += rising["query"].tolist()
            if top is not None and not top.empty:
                topics += top["query"].tolist()[:5]
        topics = list(dict.fromkeys([t for t in topics if t]))
        print(f"  Google Trends: {len(topics)} topics found")
        return topics[:n]
    except ImportError:
        print("  ⚠️ pytrends install nahi hai — 'pip install pytrends' chalao. Skipping Google Trends.")
        return []
    except Exception as e:
        print(f"  Google Trends fetch failed: {e}")
        return []

def fetch_youtube_trending_topics(yt, n=10):
    """Searches recent high-view finance/insurance videos on YouTube India for trending angles."""
    try:
        queries = ["finance tips hindi", "insurance hindi", "SIP investment hindi",
                   "personal finance india", "tax saving hindi"]
        titles = []
        published_after = (datetime.datetime.utcnow() - datetime.timedelta(days=14)).isoformat("T") + "Z"
        for q in queries:
            res = yt.search().list(
                part="snippet", q=q, type="video", order="viewCount",
                regionCode="IN", relevanceLanguage="hi", maxResults=5,
                publishedAfter=published_after,
            ).execute()
            for item in res.get("items", []):
                titles.append(item["snippet"]["title"])
        titles = list(dict.fromkeys(titles))
        print(f"  YouTube trending: {len(titles)} titles found")
        return titles[:n]
    except Exception as e:
        print(f"  YouTube trending fetch failed: {e}")
        return []

def get_next_long_topic(yt=None):
    """70% weightage to fresh trending topics (Google Trends + YouTube),
    30% to the evergreen VIRAL_TOPICS list. Falls back gracefully if trend
    sources are unavailable (no internet, pytrends not installed, quota, etc.)"""
    used = get_used_topics()

    trending = []
    trending += fetch_google_trends_topics(n=10)
    if yt:
        trending += fetch_youtube_trending_topics(yt, n=10)
    trending = [t for t in trending if t and t not in used]

    if trending and random.random() < 0.70:
        topic = random.choice(trending)
        print(f"  Selected via TRENDING (70% path): {topic}")
        return topic

    unused_static = [t for t in VIRAL_TOPICS if t not in used]
    pool = unused_static or VIRAL_TOPICS
    topic = random.choice(pool)
    print(f"  Selected via EVERGREEN list (30% path / trend fallback): {topic}")
    return topic

# ══════════════════════════════════════════════════════════
#  LONG-FORM SCRIPT GENERATOR (6 chapters, ~15 min)
# ══════════════════════════════════════════════════════════
def generate_long_script(topic, lang="hi"):
    groq_client = Groq(api_key=GEMINI_API_KEY)

    _, disclaimer_line = get_disclaimer(topic)
    is_insurance = disclaimer_line == IRDAI_DISCLAIMER
    category = "Insurance" if is_insurance else "Finance/Investment"

    prompt = (
        "You are a VIRAL Hindi YouTube Finance & Insurance educator making a DEEP-DIVE "
        "15-minute long-form video (not a Short).\n"
        f"Channel: {CHANNEL_NAME}\n"
        f"Category: {category}\n"
        "Topic: " + topic + "\n\n"
        "Create a complete 15-minute (~2200-2400 words total) Hindi deep-dive script "
        "broken into exactly 6 chapters. Return ONLY valid JSON:\n"
        "{\n"
        '  "title": "VIRAL Hindi long-form title 60-90 chars, curiosity/number driven, NO #Shorts tag",\n'
        '  "description": "SEO description 600-800 chars covering all chapters, then 15 hashtags mix Hindi+English",\n'
        '  "hook": "First 10-second dramatic hook line, MAX 60 chars",\n'
        '  "chapters": [\n'
        '    {"heading":"Chapter title MAX 40 chars","narration":"350-420 words natural Hindi speech, explain with real examples and numbers","visual":{"type":"icon"}}\n'
        "    // exactly 6 such chapter objects\n"
        "  ],\n"
        '  "thumbnail_title": "Bold Hindi text MAX 35 chars",\n'
        '  "pinned_comment": "A-vs-B poll style Hindi question, e.g. \'Dividend stocks ya Growth stocks? Comment mein A ya B likho!\'"\n'
        "}\n\n"
        "RULES:\n"
        "1. Chapter 1 = Hook + Problem statement, Chapters 2-5 = deep explanation with examples/numbers/comparisons, "
        f"Chapter 6 = Summary + CTA to follow {CHANNEL_NAME}\n"
        "2. Total narration across all 6 chapters must be ~2200-2400 words (~15 minutes spoken Hindi)\n"
        "3. Be factually careful — no guaranteed-return claims for finance topics, "
        "no guaranteed-claim-approval promises for insurance topics\n"
        f"4. In the final chapter, naturally mention this disclaimer: \"{disclaimer_line}\"\n"
        "5. Each chapter's \"visual\" object has a \"type\": one of:\n"
        "   - \"icon\" — default themed icon (use for most chapters)\n"
        "   - \"comparison\" — ONLY if that chapter's core point compares two concrete numbers. Add fields:\n"
        "     \"label_a\", \"value_a\", \"label_b\", \"value_b\" (short strings, e.g. \"₹54,000\")\n"
        "   - \"flow\" — ONLY if that chapter explains a 2-4 step cause-and-effect chain. Add field:\n"
        "     \"steps\": [\"short step 1\", \"short step 2\", \"short step 3\"] (each under 22 Hindi chars)\n"
        "   Use comparison/flow only where it genuinely fits that chapter's content — most should be \"icon\".\n"
        "6. Return ONLY the JSON object, no other text, no markdown fences"
    )

    completion = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_completion_tokens=8000,
        reasoning_effort="low",
        response_format={"type": "json_object"},
    )
    raw = completion.choices[0].message.content
    if not raw or not raw.strip():
        raise RuntimeError(
            "Groq se khaali response mila (long script). API key/quota console.groq.com pe check karo."
        )
    text = raw.strip()
    if "```" in text:
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else parts[0]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        print(f"  ⚠️ Raw Groq response that failed to parse:\n{raw[:800]}")
        raise

    data["_lang"] = lang
    data["_category"] = category

    chapters = data.get("chapters", [])
    if len(chapters) < 3:
        raise RuntimeError(f"Long script mein sirf {len(chapters)} chapters bane (kam se kam 3 chahiye). Dobara try karo.")

    # Validate each chapter's visual spec — fall back to "icon" if malformed
    for ch in chapters:
        v = ch.get("visual", {})
        if not isinstance(v, dict):
            ch["visual"] = {"type": "icon"}
            continue
        vtype = v.get("type", "icon")
        if vtype == "comparison" and all(v.get(k) for k in ("label_a","value_a","label_b","value_b")):
            ch["visual"] = {
                "type": "comparison",
                "label_a": str(v["label_a"])[:20], "value_a": str(v["value_a"])[:12],
                "label_b": str(v["label_b"])[:20], "value_b": str(v["value_b"])[:12],
            }
        elif vtype == "flow" and isinstance(v.get("steps"), list) and len(v["steps"]) >= 2:
            ch["visual"] = {"type": "flow", "steps": [str(s)[:22] for s in v["steps"][:4]]}
        else:
            ch["visual"] = {"type": "icon"}
    data["chapters"] = chapters

    title = str(data.get("title", topic)).strip()
    data["title"] = title[:100]

    print(f"  Category: {category} | Chapters: {len(chapters)}")
    print(f"  Title: {data['title']}")
    return data

# ══════════════════════════════════════════════════════════
#  LONG-FORM LANDSCAPE FRAME BUILDER
# ══════════════════════════════════════════════════════════
def build_long_frame(theme, chapter_num, total_chapters, heading, topic_image=None, topic=None, visual_spec=None):
    p, d, bg = theme["primary"], theme["dark"], theme["bg"]
    white, black = (255, 255, 255), (20, 20, 20)

    img = Image.new("RGB", (LW, LH), bg)
    draw = ImageDraw.Draw(img)

    if topic_image and os.path.exists(topic_image):
        try:
            ti = Image.open(topic_image).convert("RGB").resize((LW, LH))
            overlay = Image.new("RGB", (LW, LH), bg)
            img = Image.blend(ti, overlay, 0.85)
            draw = ImageDraw.Draw(img)
        except Exception as e:
            print(f"  BG error: {e}")

    # Top channel banner — auto-sized to fit CHANNEL_NAME
    cn_font = load_latin_font(38)
    name_w = int(draw.textlength(CHANNEL_NAME, font=cn_font)) + 46
    draw.rounded_rectangle([40, 30, 40+name_w, 110], radius=30, fill=(0, 0, 0))
    draw.text((63, 70), CHANNEL_NAME, font=cn_font, fill=white, anchor="lm")

    # Chapter badge
    draw.rounded_rectangle([LW-340, 30, LW-40, 110], radius=30, fill=p)
    draw.text((LW-190, 70), f"Chapter {chapter_num}/{total_chapters}",
             font=load_latin_font(30), fill=white, anchor="mm")

    # ── Split layout: heading card (left) + visual (right) ──
    content_y1, content_y2 = 150, LH-110
    mid_x = int(LW * 0.44)

    # Left: heading card + mascot
    draw.rounded_rectangle([60, content_y1, mid_x-20, content_y2], radius=28, fill=white)
    lines = wrap_mixed(heading, 56, mid_x-60-60, draw)
    ty = (content_y1+content_y2)//2 - len(lines)*36
    for line in lines:
        draw_mixed_text(draw, (60+(mid_x-20-60)//2, ty), line, 56, p, anchor="mm")
        ty += 72
    mascot_poses = ["wave", "point", "happy", "idle"]
    draw_mascot(draw, mid_x-110, content_y1+95, 110,
               mascot_poses[chapter_num % len(mascot_poses)], theme)

    # Right: visual (icon / comparison / flow)
    draw.rounded_rectangle([mid_x+20, content_y1, LW-60, content_y2], radius=28, fill=(250,250,250), outline=p, width=5)
    vcx = (mid_x+20 + LW-60) // 2
    vcy = (content_y1 + content_y2) // 2
    vw  = (LW-60 - mid_x-20) * 0.72
    vh  = (content_y2 - content_y1) * 0.72
    draw_point_visual(draw, vcx, vcy, vw, vh, visual_spec, heading, theme)

    # Disclaimer bar
    disclaimer_short, _ = get_disclaimer(topic)
    draw.rectangle([0, LH-70, LW, LH], fill=(170, 15, 15))
    draw.text((LW//2, LH-35), disclaimer_short, font=load_latin_font(28), fill=white, anchor="mm")

    return img

# ══════════════════════════════════════════════════════════
#  LONG-FORM VOICEOVER (per-chapter, chained)
# ══════════════════════════════════════════════════════════
def generate_long_voiceover(chapters, temp_dir, lang="hi"):
    audio_paths, durations = [], []
    for i, ch in enumerate(chapters):
        path = str(temp_dir / f"chapter_{i+1}.mp3")
        text = ch.get("narration", "")
        tts = gTTS(text=text, lang=lang, slow=False, tld="co.in")
        tts.save(path)
        audio = AudioFileClip(path)
        durations.append(audio.duration)
        audio.close()
        audio_paths.append(path)
        print(f"  Chapter {i+1} voiceover: {durations[-1]:.1f}s")
    return audio_paths, durations

# ══════════════════════════════════════════════════════════
#  LONG-FORM VIDEO ASSEMBLY
# ══════════════════════════════════════════════════════════
def create_long_video(script_data, theme, output_path, topic=None):
    chapters = script_data["chapters"]
    topic_image = get_topic_image(topic or "finance")

    temp_dir = OUTPUT_DIR / "long_temp"
    temp_dir.mkdir(exist_ok=True, parents=True)

    audio_paths, durations = generate_long_voiceover(chapters, temp_dir, lang=LANGUAGE)

    clips = []
    for i, (ch, dur) in enumerate(zip(chapters, durations)):
        frame_img = build_long_frame(
            theme, i+1, len(chapters), ch.get("heading", f"Chapter {i+1}"),
            topic_image=topic_image, topic=topic, visual_spec=ch.get("visual")
        )
        frame_path = str(temp_dir / f"frame_{i+1}.jpg")
        frame_img.save(frame_path, "JPEG", quality=92)
        clip = ImageClip(frame_path).set_duration(dur)
        audio_clip = AudioFileClip(audio_paths[i])
        clip = clip.set_audio(audio_clip)
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")
    video.write_videofile(output_path, fps=FPS, codec="libx264",
                         audio_codec="aac", threads=4, logger=None)
    total_dur = sum(durations)
    print(f"  Long video: {output_path} | Total: {total_dur/60:.1f} min")

    # cleanup temp audio/frames
    for p in audio_paths:
        try: os.remove(p)
        except OSError: pass
    for i in range(len(chapters)):
        try: os.remove(str(temp_dir / f"frame_{i+1}.jpg"))
        except OSError: pass

    return topic_image, total_dur

# ══════════════════════════════════════════════════════════
#  LONG-FORM THUMBNAIL (16:9)
# ══════════════════════════════════════════════════════════
def generate_long_thumbnail(script_data, theme, output_path, topic_image=None, topic=None):
    TW, TH = 1280, 720
    p = theme["primary"]
    white = (255, 255, 255)

    img = Image.new("RGB", (TW, TH), theme["bg"])
    draw = ImageDraw.Draw(img)

    if topic_image and os.path.exists(topic_image):
        try:
            ti = Image.open(topic_image).convert("RGB").resize((TW, TH))
            img = Image.blend(ti, Image.new("RGB", (TW, TH), theme["bg"]), 0.55)
            draw = ImageDraw.Draw(img)
        except Exception:
            pass

    draw.rectangle([0, 0, TW, 90], fill=p)
    draw.text((TW//2, 45), CHANNEL_HANDLE, font=load_latin_font(38), fill=white, anchor="mm")

    # ── Character panel (right side) — AI image if available, else
    # our reliable hand-drawn character as fallback ──
    char_x1 = TW - 380
    _, disclaimer_line = get_disclaimer(topic or "")
    is_insurance = disclaimer_line == IRDAI_DISCLAIMER
    pose_desc = generate_thumbnail_scene(
        topic or script_data.get("title", ""), script_data.get("hook", ""), is_insurance
    )
    ai_char_path = get_ai_character_image(pose_desc, seed=random.randint(1000, 9999))
    if ai_char_path and os.path.exists(ai_char_path):
        try:
            ci = Image.open(ai_char_path).convert("RGB")
            cw, ch = TW-char_x1-40, TH-130
            cr = ci.width / ci.height
            br = cw / ch
            if cr > br:
                nh, nw = ch, int(ch*cr)
            else:
                nw, nh = cw, int(cw/cr)
            ci = ci.resize((nw, nh), Image.LANCZOS)
            left = (nw-cw)//2
            top  = max(0, (nh-ch)//3)
            ci = ci.crop((left, top, left+cw, top+ch))
            img.paste(ci, (char_x1+20, 110))
            draw = ImageDraw.Draw(img)
        except Exception as e:
            print(f"  Long thumbnail AI char paste failed ({e}), using hand-drawn")
            ai_char_path = None
    if not ai_char_path:
        draw.rounded_rectangle([char_x1, 110, TW-40, TH-40], radius=24, fill=(250,250,250), outline=p, width=4)
        pose = "happy_arms" if is_insurance else "point_up"
        draw_person(draw, char_x1+170, 400, 320, pose, theme, 0)

    text_right_edge = char_x1 - 20
    title = script_data.get("thumbnail_title",
            script_data.get("hook", "Finance Guide"))[:35]
    draw.rounded_rectangle([40, 110, text_right_edge, TH-40], radius=24, fill=white, outline=p, width=5)
    lines = wrap_mixed(title, 56, text_right_edge-160, draw)
    ty = (TH+70 - len(lines)*62)//2
    for line in lines:
        draw_mixed_text(draw, ((40+text_right_edge)//2, ty), line, 56, p, anchor="mm")
        ty += 68

    img.save(output_path, "JPEG", quality=95)

# ══════════════════════════════════════════════════════════
#  LONG-FORM UPLOAD (no #Shorts, Education category)
# ══════════════════════════════════════════════════════════
def upload_long_to_youtube(yt, video_path, thumb_path, script_data, topic=''):
    lang = script_data.get("_lang", "hi")
    title = script_data["title"][:100]
    is_insurance = script_data.get("_category") == "Insurance"

    desc = script_data.get("description", "")
    if not desc:
        _, disclaimer_line = get_disclaimer(topic)
        chapters = script_data.get("chapters", [])
        chapter_lines = "\n".join(f"{i+1}. {c.get('heading','')}" for i, c in enumerate(chapters))
        desc = (
            f"{CHANNEL_NAME} — Paisa Samjho, Future Sanwaro\n\n"
            f"इस वीडियो में:\n{chapter_lines}\n\n"
            f"Follow करें: {CHANNEL_HANDLE}\n\n{disclaimer_line}"
        )

    base_tags = (
        ["insurance guide hindi", "capital insurance investments", "term insurance explained",
         "irdai", "insurance deep dive", "insurance India"]
        if is_insurance else
        ["finance guide hindi", "capital insurance investments", "sip explained",
         "personal finance india", "investment deep dive", "finance India"]
    )
    chapter_headings = [c.get("heading","") for c in script_data.get("chapters", [])]
    dynamic_tags = extract_dynamic_tags(topic, chapter_headings)
    tags = (base_tags + dynamic_tags)[:20]

    body = {
        "snippet": {
            "title": title,
            "description": desc[:5000],
            "tags": tags,
            "categoryId": "27",  # Education
            "defaultLanguage": lang,
            "defaultAudioLanguage": lang,
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
            "madeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = req.next_chunk()
        if status:
            print(f"  Upload: {int(status.progress()*100)}%")

    video_id = response.get("id")
    print(f"  Live: https://youtube.com/watch?v={video_id}")

    try:
        yt.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumb_path, mimetype="image/jpeg")
        ).execute()
        print("  Thumbnail OK")
    except Exception as e:
        print(f"  Thumbnail: {e}")

    comment = script_data.get("pinned_comment", "")
    if not comment:
        comment = f"Video kaisa laga? Comment karke batao 👇\n{CHANNEL_NAME} ko Follow karna na bhoolein! 🔔"
    try:
        yt.commentThreads().insert(
            part="snippet",
            body={"snippet": {
                "videoId": video_id,
                "topLevelComment": {"snippet": {"textOriginal": comment}}
            }}
        ).execute()
        print("  Comment posted")
    except Exception as e:
        print(f"  Comment: {e}")

    # Add to category playlist (Finance / Insurance) — helps discoverability
    playlist_title = "Insurance Guide 🛡️" if is_insurance else "Finance & Investment Tips 📈"
    playlist_id = get_or_create_playlist(
        yt, playlist_title,
        f"{CHANNEL_NAME} — sabhi related videos ek jagah."
    )
    add_video_to_playlist(yt, playlist_id, video_id)

    return video_id

# ══════════════════════════════════════════════════════════
#  LONG-FORM PIPELINE
# ══════════════════════════════════════════════════════════
def run_long_pipeline():
    import hashlib
    OUTPUT_DIR.mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    yt = get_youtube_client()
    topic = get_next_long_topic(yt=yt)

    topic_hash = int(hashlib.md5(topic.encode()).hexdigest(), 16)
    theme = THEMES[topic_hash % len(THEMES)]

    print(f"\n{'='*55}")
    print(f"  LONG VIDEO (15 min) | Topic: {topic}")
    print(f"  Theme : {theme['name']}")
    print(f"{'='*55}")

    video_path = str(OUTPUT_DIR / f"long_{ts}.mp4")
    thumb_path = str(OUTPUT_DIR / f"long_thumb_{ts}.jpg")

    try:
        print("\n1/4: Generating deep-dive script (6 chapters)...")
        data = generate_long_script(topic, lang=LANGUAGE)

        print("\n2/4: Building long-form video (voiceover + chapters)...")
        topic_image, total_dur = create_long_video(data, theme, video_path, topic=topic)
        print(f"  Total video length: {total_dur/60:.1f} minutes")

        print("\n3/4: Thumbnail...")
        generate_long_thumbnail(data, theme, thumb_path, topic_image=topic_image, topic=topic)

        print("\n3.5/4: QA check before upload...")
        qa_ok, qa_reason = run_qa_checks(video_path, min_duration=240, max_duration=1400)
        if not qa_ok:
            print(f"  ❌ QA CHECK FAILED: {qa_reason}")
            print("  Skipping upload — a broken video will NOT go live. "
                  "Check the files in output_videos/ to debug, then re-run.")
            return None

        print("\n4/4: Uploading to YouTube...")
        vid = upload_long_to_youtube(yt, video_path, thumb_path, data, topic=topic)

        log_upload(topic, vid, data["title"], theme["name"] + "-long")

        if os.path.exists(thumb_path):
            os.remove(thumb_path)

        print(f"\n🎉 Long video Done! https://youtube.com/watch?v={vid}")
        return vid

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback; traceback.print_exc()
        raise

# ══════════════════════════════════════════════════════════
#  SCHEDULER
# ══════════════════════════════════════════════════════════
POST_TIMES = ["08:00", "13:00", "20:00"]
LONG_POST_TIME = "10:00"
_last_run  = None
_last_long_run = None

def safe_run():
    global _last_run
    now = datetime.datetime.now()
    if _last_run and (now-_last_run).total_seconds() < 3600:
        return
    _last_run = now
    run_pipeline()

def safe_run_long():
    global _last_long_run
    now = datetime.datetime.now()
    if _last_long_run and (now-_last_long_run).total_seconds() < 3600*12:
        return
    _last_long_run = now
    run_long_pipeline()

def start_scheduler(times=None, long_time=None):
    times = times or POST_TIMES
    for t in times:
        schedule.every().day.at(t).do(safe_run)
    long_time = long_time or LONG_POST_TIME
    schedule.every().day.at(long_time).do(safe_run_long)
    print(f"{CHANNEL_NAME} Bot Active | Shorts: {times} | Long: {long_time}")
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        print("Stopped.")

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if not args:
        run_pipeline()
    elif args[0] == "--long":
        run_long_pipeline()
    elif args[0] == "--schedule":
        start_scheduler(args[1:] or None)
    elif args[0] == "--log":
        if LOG_FILE.exists():
            with open(LOG_FILE, encoding="utf-8") as f:
                log = json.load(f)
            today = datetime.date.today().isoformat()
            t = [e for e in log if e["date"].startswith(today)]
            print(f"Today: {len(t)} uploads")
            for e in t:
                print(f"  {e['date'][11:16]} | {e['theme']:8} | {e['title'][:50]}")
        else:
            print("No uploads yet.")
