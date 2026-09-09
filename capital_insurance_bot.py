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
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
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

# Logo path — tries multiple locations
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
LOGO_PATHS = [
    os.path.join(SCRIPT_DIR, "channel_logo.png"),
    "channel_logo.png",
    os.path.join(os.getcwd(), "channel_logo.png"),
]

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

def get_illustration_kind(text):
    """Maps a topic/tip string to one of our original flat-design
    illustration categories (no external images, no copyright risk)."""
    t = (text or "").lower()
    checks = [
        (("sip","निवेश","invest","mutual fund","म्यूचुअल","index fund","शेयर","stock","बाजार","market"), "growth"),
        (("टैक्स","tax","80c","elss"), "tax"),
        (("बजट","budget","50-30-20"), "budget"),
        (("इमरजेंसी","emergency"), "emergency"),
        (("क्रेडिट कार्ड","credit card"), "creditcard"),
        (("रिटायरमेंट","retirement","nps"), "retirement"),
        (("गोल्ड","gold"), "gold"),
        (("फिक्स्ड डिपॉजिट","fixed deposit"," fd","बैंक"), "bank"),
        (("लोन","loan","कर्ज"), "loan"),
        (("क्रेडिट स्कोर","credit score"), "creditscore"),
        (("नॉमिनी","nominee"), "nominee"),
        (("क्लेम","claim","दस्तावेज","document"), "document"),
        (("फैमिली","family","चाइल्ड","child"), "family"),
        (("टर्म","term","हेल्थ इंश्योरेंस","health insurance","health cover",
          "एंडोमेंट","endowment","ulip","यूलिप","प्रीमियम","premium",
          "क्रिटिकल इलनेस","critical illness","इंश्योरेंस","insurance"), "shield"),
    ]
    for keys, kind in checks:
        if any(k in t for k in keys):
            return kind
    return "growth"


def draw_illustration(draw, cx, cy, w, h, kind, theme):
    """Original flat-design vector illustration — hand-coded shapes,
    no external assets, drawn fresh for this bot."""
    p, d, light = theme["primary"], theme["dark"], theme["light"]
    white, black = (255,255,255), (30,30,30)
    s = min(w, h)

    if kind == "growth":
        base_y = cy + s*0.28
        heights = [0.18, 0.30, 0.44, 0.60]
        bar_w = s*0.13
        start_x = cx - s*0.34
        for i, hh in enumerate(heights):
            bx = start_x + i*(bar_w+s*0.06)
            by = base_y - s*hh
            col = p if i < len(heights)-1 else d
            draw.rounded_rectangle([bx, by, bx+bar_w, base_y], radius=8, fill=col)
        ax1, ay1 = start_x-10, base_y - s*heights[0] - 20
        ax2, ay2 = start_x + 3*(bar_w+s*0.06) + bar_w + 20, base_y - s*heights[-1] - s*0.22
        draw.line([ax1,ay1,ax2,ay2], fill=d, width=10)
        ang = 28
        import math
        rad = math.radians(20)
        dx, dy = math.cos(rad)*26, math.sin(rad)*26
        draw.polygon([(ax2,ay2),(ax2-dx-14,ay2+dy-8),(ax2-dx+8,ay2+dy+14)], fill=d)

    elif kind == "tax":
        cw, ch = s*0.62, s*0.62
        draw.rounded_rectangle([cx-cw/2, cy-ch/2, cx+cw/2, cy+ch/2], radius=18, fill=white, outline=p, width=6)
        for r in range(4):
            for c in range(3):
                bx = cx-cw/2+18+c*(cw-36)/2
                by = cy-ch/2+18+r*(ch-36)/3.6
                draw.rounded_rectangle([bx,by,bx+ (cw-56)/3, by+18], radius=6, fill=light if (r+c)%2 else p)
        draw.ellipse([cx+s*0.1, cy+s*0.05, cx+s*0.42, cy+s*0.37], fill=d)
        f = load_latin_font(int(s*0.16))
        draw.text((cx+s*0.26, cy+s*0.21), "%", font=f, fill=white, anchor="mm")

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
        hw, hh = s*0.5, s*0.36
        draw.polygon([(cx, cy-s*0.4),(cx-hw/2-14, cy-s*0.1),(cx+hw/2+14, cy-s*0.1)], fill=d)
        draw.rectangle([cx-hw/2, cy-s*0.1, cx+hw/2, cy-s*0.1+hh], fill=p)
        draw.rectangle([cx-hw*0.12, cy-s*0.1+hh*0.4, cx+hw*0.12, cy-s*0.1+hh], fill=white)
        f = load_latin_font(int(s*0.14))
        draw.ellipse([cx+s*0.16, cy+s*0.02, cx+s*0.42, cy+s*0.28], fill=(230,180,40), outline=white, width=4)
        draw.text((cx+s*0.29, cy+s*0.15), "₹", font=f, fill=white, anchor="mm")

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
        positions = [(-s*0.22, 0.85, p), (0, 1.0, d), (s*0.22, 0.7, p)]
        for off, scale, col in positions:
            hx = cx+off
            rr = s*0.08*scale
            draw.ellipse([hx-rr, cy-s*0.3*scale, hx+rr, cy-s*0.3*scale+2*rr], fill=col)
            draw.rounded_rectangle([hx-rr*1.6, cy-s*0.14*scale, hx+rr*1.6, cy+s*0.28*scale],
                                   radius=14, fill=col)

    else:  # "shield" — default for insurance topics
        sw, sh = s*0.5, s*0.6
        draw.polygon([
            (cx, cy-sh/2), (cx+sw/2, cy-sh/2+sh*0.18),
            (cx+sw/2, cy+sh*0.08), (cx, cy+sh/2),
            (cx-sw/2, cy+sh*0.08), (cx-sw/2, cy-sh/2+sh*0.18),
        ], fill=p, outline=d, width=5)
        draw.line([cx-sw*0.18, cy-sh*0.02, cx-sw*0.02, cy+sh*0.14], fill=white, width=12)
        draw.line([cx-sw*0.02, cy+sh*0.14, cx+sw*0.22, cy-sh*0.16], fill=white, width=12)


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
                point_image=None, point_text=None):
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
    for lp in LOGO_PATHS + ["channel_logo.png"]:
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

        # ── Large point image ──────────────────────────────
        img_y1 = badge_y + 84
        footer_h = 175
        footer_y = H - 285 - footer_h - 18
        img_y2 = footer_y - 15

        draw.rounded_rectangle([26, img_y1+6, W-26, img_y2+6],
                               radius=26, fill=(140,140,140))
        # Card background for the illustration
        draw.rounded_rectangle([26, img_y1, W-26, img_y2],
                               radius=26, fill=(250,250,250))
        illus_kind = get_illustration_kind(point_text)
        icx = (26 + (W-26)) // 2
        icy = (img_y1 + img_y2) // 2
        iw  = (W-52) * 0.72
        ih  = (img_y2 - img_y1) * 0.72
        draw_illustration(draw, icx, icy, iw, ih, illus_kind, theme)
        draw.rounded_rectangle([26, img_y1, W-26, img_y2],
                               radius=26, outline=p, width=6)

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
    #  MODE 2: INTRO TEASER (screen 0) — hook only, tips
    #  are NOT revealed yet (kept for the step-by-step reveal)
    # ══════════════════════════════════════════════════════
    elif screen_num == 0:
        ty = banner_h + 60
        th = 420
        draw.rounded_rectangle([34, ty+5, W-24, ty+th+5],
                               radius=26, fill=(180,180,180))
        draw.rounded_rectangle([28, ty, W-28, ty+th],
                               radius=26, fill=white, outline=p, width=6)
        tlines = wrap_mixed(title, 62, W-140, draw)
        t_y = ty + th//2 - len(tlines)*36 - 40
        for line in tlines:
            draw_mixed_text(draw, (W//2+2, t_y+2), line, 62, light, anchor="mm")
            draw_mixed_text(draw, (W//2, t_y), line, 62, p, anchor="mm")
            t_y += 74

        # Teaser row — hints 3 points are coming, without revealing them
        draw.text((W//2, ty+th-70), "3 जरूरी पॉइंट्स आगे",
                 font=pick_font("3 जरूरी पॉइंट्स आगे", 34), fill=d, anchor="mm")
        for i in range(3):
            cx = W//2 - 90 + i*90
            cy = ty + th - 20
            draw.ellipse([cx-28, cy-28, cx+28, cy+28],
                        fill=white, outline=p, width=4)
            draw.text((cx, cy), str(i+1), font=load_latin_font(34),
                     fill=p, anchor="mm")

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
def generate_thumbnail(script_data, theme, output_path, topic_image=None):
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

    # Title
    title = script_data.get("thumbnail_title",
            script_data.get("hook", "Finance Tips"))[:42]
    draw.rounded_rectangle([28, 115, TW-28, 300],
                           radius=20, fill=white, outline=p, width=4)
    tlines = wrap_mixed(title, 68, TW-110, draw)
    ty = 208 - len(tlines)*36
    for line in tlines:
        draw_mixed_text(draw, (TW//2, ty), line, 68, p, anchor="mm")
        ty += 74

    # Tips
    tips = script_data.get("key_points", [])[:3]
    tip_y = 315
    for i, tip in enumerate(tips):
        draw.rounded_rectangle([28, tip_y, TW-28, tip_y+90],
                               radius=18, fill=white, outline=p, width=2)
        draw.rounded_rectangle([28, tip_y, 82, tip_y+90],
                               radius=18, fill=p)
        draw.text((55, tip_y+45), str(i+1),
                 font=load_latin_font(44), fill=white, anchor="mm")
        draw_mixed_text(draw, (100, tip_y+45), tip[:50], 44, black, anchor="lm")
        tip_y += 105

    img.save(output_path, "JPEG", quality=95)

# ══════════════════════════════════════════════════════════
#  VOICEOVER
# ══════════════════════════════════════════════════════════
def generate_voiceover(script_text, output_path, lang="hi"):
    tts = gTTS(text=script_text, lang=lang, slow=False, tld="co.in")
    tts.save(output_path)
    audio = AudioFileClip(output_path)
    dur = audio.duration
    audio.close()
    print(f"  Voiceover: {dur:.1f}s")
    return dur

# ══════════════════════════════════════════════════════════
#  VIDEO
# ══════════════════════════════════════════════════════════
def create_short_video(script_data, audio_path, audio_duration,
                       theme, output_path, topic=None):
    tips  = script_data.get("key_points", ["Tip 1","Tip 2","Tip 3"])
    hook  = script_data.get("hook", "Finance Tips")[:42]
    title = script_data.get("thumbnail_title", hook)[:42]

    topic_image = get_topic_image(topic or "finance")

    # Timing — 2 minute video
    intro = audio_duration * 0.12
    t1    = audio_duration * 0.27
    t2    = audio_duration * 0.27
    t3    = audio_duration * 0.26
    outro = audio_duration * 0.08

    print(f"  Timing: {audio_duration:.1f}s total | intro={intro:.1f} tip1={t1:.1f} tip2={t2:.1f} tip3={t3:.1f} outro={outro:.1f}")

    # Build frames — one point revealed at a time, each with its own image
    f_intro = build_frame(theme, 0, title, tips, total=5,
                          topic_image=topic_image, topic=topic)
    f_t1 = build_frame(theme, 1, title, tips, total=5, topic=topic, point_text=tips[0])
    f_t2 = build_frame(theme, 2, title, tips, total=5, topic=topic, point_text=tips[1])
    f_t3 = build_frame(theme, 3, title, tips, total=5, topic=topic, point_text=tips[2])
    f_outro = build_frame(theme, 4, f"Yaad Rakho! {CHANNEL_NAME}", tips, total=5,
                          topic_image=topic_image, topic=topic)

    clips = [
        ImageClip(f_intro).set_duration(intro),
        ImageClip(f_t1).set_duration(t1),
        ImageClip(f_t2).set_duration(t2),
        ImageClip(f_t3).set_duration(t3),
        ImageClip(f_outro).set_duration(outro),
    ]

    video = concatenate_videoclips(clips, method="compose")
    audio = AudioFileClip(audio_path)
    video = video.set_audio(audio)
    video.write_videofile(output_path, fps=FPS, codec="libx264",
                         audio_codec="aac", threads=4, logger=None)
    print(f"  Video: {output_path}")
    return topic_image

# ══════════════════════════════════════════════════════════
#  SEO SCRIPT GENERATOR
# ══════════════════════════════════════════════════════════
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

    prompt = (
        "You are a VIRAL Hindi YouTube Finance & Insurance content creator for Indian audience.\n"
        f"Channel: {CHANNEL_NAME} — Paisa Samjho, Future Sanwaro\n"
        f"Category: {category}\n"
        "Topic: " + topic + "\n\n"
        "Create a VIRAL finance/insurance video script. Return ONLY valid JSON:\n"
        "{\n"
        "  \"title\": \"VIRAL Hindi title 55-65 chars — use numbers, emotions, curiosity — must end with #Shorts\",\n"
        "  \"description\": \"SEO description 400-500 chars. Line1: hook. Line2-3: what viewers learn. Line4: CTA. Then 20 hashtags mix Hindi+English\",\n"
        "  \"hook\": \"Shocking opening line MAX 38 chars\",\n"
        f"  \"script\": \"Natural Hindi speech 280-300 words for 2 minute video. Start dramatic. Explain each point in detail with real examples. End with {CHANNEL_NAME} follow karo\",\n"
        "  \"key_points\": [\n"
        "    \"Short powerful Hindi point 1 MAX 38 chars\",\n"
        "    \"Short powerful Hindi point 2 MAX 38 chars\",\n"
        "    \"Short powerful Hindi point 3 MAX 38 chars\"\n"
        "  ],\n"
        "  \"thumbnail_title\": \"Bold Hindi text MAX 32 chars\",\n"
        "  \"pinned_comment\": \"Engaging question for viewers in Hindi\"\n"
        "}\n\n"
        "SEO RULES:\n"
        "1. Title must have: number OR emotion word (चौंकाने वाला/जरूरी/खतरनाक/समझदारी भरा)\n"
        "2. key_points: exactly 3, MAX 38 chars, action-oriented\n"
        f"3. Description hashtags: {hashtag_set}\n"
        "4. script: 280-300 words, conversational Hindi, factually careful (no guaranteed-return claims for finance, no false claim-approval promises for insurance)\n"
        f"5. At the very end of the script, naturally mention: \"{disclaimer_line}\"\n"
        "6. Return ONLY JSON, no other text"
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
    return data

# ══════════════════════════════════════════════════════════
#  TOPIC MANAGEMENT
# ══════════════════════════════════════════════════════════
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

def upload_to_youtube(yt, video_path, thumb_path, script_data, topic=''):
    lang  = script_data.get("_lang","hi")
    raw_title = script_data["title"]
    # Add #Shorts if not present
    if "#Shorts" not in raw_title and "#shorts" not in raw_title:
        raw_title = raw_title[:60] + " | #Shorts"
    title = raw_title[:100]
    is_insurance = script_data.get("_category") == "Insurance"
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

    tags = (
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
        comment = f"क्या आप भी ये टिप्स अपनाते हैं? नीचे comment करें 👇\n{CHANNEL_NAME} को Follow करना न भूलें! 🔔"
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
    log.append({
        "date": datetime.datetime.now().isoformat(),
        "topic": topic, "video_id": video_id,
        "title": title, "theme": theme_name,
        "url": f"https://youtube.com/shorts/{video_id}",
    })
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

# ══════════════════════════════════════════════════════════
#  MAIN PIPELINE
# ══════════════════════════════════════════════════════════
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
        generate_thumbnail(data, theme, thumb_path, topic_image=topic_image)

        print("\n5/5: Uploading to YouTube...")
        yt = get_youtube_client()
        vid = upload_to_youtube(yt, video_path, thumb_path, data, topic=topic)

        log_upload(topic, vid, data["title"], theme["name"])

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
        '    {"heading":"Chapter title MAX 40 chars","narration":"350-420 words natural Hindi speech, explain with real examples and numbers"}\n'
        "    // exactly 6 such chapter objects\n"
        "  ],\n"
        '  "thumbnail_title": "Bold Hindi text MAX 35 chars",\n'
        '  "pinned_comment": "Engaging Hindi question for viewers"\n'
        "}\n\n"
        "RULES:\n"
        "1. Chapter 1 = Hook + Problem statement, Chapters 2-5 = deep explanation with examples/numbers/comparisons, "
        f"Chapter 6 = Summary + CTA to follow {CHANNEL_NAME}\n"
        "2. Total narration across all 6 chapters must be ~2200-2400 words (~15 minutes spoken Hindi)\n"
        "3. Be factually careful — no guaranteed-return claims for finance topics, "
        "no guaranteed-claim-approval promises for insurance topics\n"
        f"4. In the final chapter, naturally mention this disclaimer: \"{disclaimer_line}\"\n"
        "5. Return ONLY the JSON object, no other text, no markdown fences"
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
    data["chapters"] = chapters

    title = str(data.get("title", topic)).strip()
    data["title"] = title[:100]

    print(f"  Category: {category} | Chapters: {len(chapters)}")
    print(f"  Title: {data['title']}")
    return data

# ══════════════════════════════════════════════════════════
#  LONG-FORM LANDSCAPE FRAME BUILDER
# ══════════════════════════════════════════════════════════
def build_long_frame(theme, chapter_num, total_chapters, heading, topic_image=None, topic=None):
    p, d, bg = theme["primary"], theme["dark"], theme["bg"]
    white, black = (255, 255, 255), (20, 20, 20)

    img = Image.new("RGB", (LW, LH), bg)
    draw = ImageDraw.Draw(img)

    if topic_image and os.path.exists(topic_image):
        try:
            ti = Image.open(topic_image).convert("RGB").resize((LW, LH))
            overlay = Image.new("RGB", (LW, LH), bg)
            img = Image.blend(ti, overlay, 0.75)
            draw = ImageDraw.Draw(img)
        except Exception as e:
            print(f"  BG error: {e}")

    # Top channel banner
    draw.rounded_rectangle([40, 30, 560, 110], radius=30, fill=(0, 0, 0))
    draw.text((60, 70), CHANNEL_NAME, font=load_latin_font(38), fill=white, anchor="lm")

    # Chapter badge
    draw.rounded_rectangle([LW-340, 30, LW-40, 110], radius=30, fill=p)
    draw.text((LW-190, 70), f"Chapter {chapter_num}/{total_chapters}",
             font=load_latin_font(30), fill=white, anchor="mm")

    # Heading card (centered)
    lines = wrap_mixed(heading, 72, LW-320, draw)
    card_h = 140 + len(lines)*90
    card_y = (LH - card_h)//2
    draw.rounded_rectangle([150, card_y, LW-150, card_y+card_h], radius=30, fill=white)
    ty = card_y + 70
    for line in lines:
        draw_mixed_text(draw, (LW//2, ty), line, 72, p, anchor="mm")
        ty += 90

    # Disclaimer bar
    disclaimer_short, _ = get_disclaimer(topic)
    draw.rectangle([0, LH-70, LW, LH], fill=(170, 15, 15))
    draw.text((LW//2, LH-35), disclaimer_short, font=load_font(28), fill=white, anchor="mm")

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
            topic_image=topic_image, topic=topic
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
def generate_long_thumbnail(script_data, theme, output_path, topic_image=None):
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

    title = script_data.get("thumbnail_title",
            script_data.get("hook", "Finance Guide"))[:35]
    draw.rounded_rectangle([40, 110, TW-40, TH-40], radius=24, fill=white, outline=p, width=5)
    lines = wrap_mixed(title, 64, TW-160, draw)
    ty = (TH+70 - len(lines)*70)//2
    for line in lines:
        draw_mixed_text(draw, (TW//2, ty), line, 64, p, anchor="mm")
        ty += 76

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

    tags = (
        ["insurance guide hindi", "capital insurance investments", "term insurance explained",
         "irdai", "insurance deep dive", "insurance India"]
        if is_insurance else
        ["finance guide hindi", "capital insurance investments", "sip explained",
         "personal finance india", "investment deep dive", "finance India"]
    )

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
        generate_long_thumbnail(data, theme, thumb_path, topic_image=topic_image)

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
