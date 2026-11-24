#!/usr/bin/env python3
"""Render the 24 November 2026 world-news front page.

A dense cream newspaper page summing up Tuesday 24 November 2026:
39 verified stories across 7 regions, 3 illustrated hero panels,
8 numbers-first medium panels (3 with mini-scenes, so 6 illustrated
panels in total), 4 small stories, a 24-item ALSO list, a small world
map, a UTC strip and a DATE CHECK box flagging re-reported news.

Facts were verified against the day's wires on 24 Nov 2026 (see
stories-20261124.md in the parent workspace). Two stories were
re-verified for this edition: the US Treasury sanctions on Iranian
shadow banking (primary source: home.treasury.gov) and the Ulleung
island alert (Reuters, 24 Nov). The Wong speech was confirmed
delivered on Tuesday (ACS Information Age). Where sources disagree
(Cikande missing 30 vs 34; Manipur toll 17 vs 18; Thai-Cambodia
ceasefire dates) the majority figure is used and the dispute is
noted in DATE CHECK. Nothing here is a photograph; every picture
and the map are drawn in code with PIL.

Run from the entry directory:
    python3 render24.py
writes entry.jpg next to this file (1024x1024, under 1 MiB).
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "entry.jpg")

W = H = 1024
MARGIN = 14
RIGHT = W - MARGIN

# ---- Colours -------------------------------------------------------------
PAPER = (247, 242, 231)
PANEL = (238, 232, 216)
NAVY = (20, 38, 74)
INK = (26, 26, 26)
RED = (166, 30, 34)
RULE = (120, 110, 92)
FAINT = (105, 98, 82)
WHITE = (255, 255, 255)
GOLD = (255, 197, 61)
TEAL = (38, 166, 154)
SEA = (16, 42, 74)
SKY = (108, 180, 238)

REGION_FILL = {
    "EUROPE": (27, 58, 107),
    "MIDDLE EAST": (166, 30, 34),
    "AMERICAS": (15, 118, 110),
    "ASIA-PACIFIC": (194, 87, 26),
    "AFRICA": (46, 125, 50),
    "OCEANIA": (106, 76, 147),
    "WORLD": (85, 85, 85),
}

# Badge colours cycle for the ALSO numbers 16-39 and the map pins.
BADGES = [(255, 197, 61), (229, 72, 77), (38, 166, 154), (240, 123, 45),
          (245, 166, 35), (66, 103, 226), (233, 92, 162), (139, 124, 246),
          (62, 189, 110), (108, 180, 238)]

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


class Sheet:
    """The page plus a font cache and small text helpers."""

    def __init__(self):
        self.page = Image.new("RGB", (W, H), PAPER)
        self.d = ImageDraw.Draw(self.page)
        self._fonts = {}

    def f(self, path, size):
        key = (path, size)
        if key not in self._fonts:
            self._fonts[key] = ImageFont.truetype(path, size)
        return self._fonts[key]

    def width(self, text, path, size):
        return self.d.textlength(text, font=self.f(path, size))

    def put(self, x, y, text, path, size, fill):
        self.d.text((x, y), text, font=self.f(path, size), fill=fill)

    def centred(self, y, text, path, size, fill):
        tw = self.width(text, path, size)
        self.d.text(((W - tw) / 2, y), text, font=self.f(path, size), fill=fill)

    def wrap(self, text, path, size, max_w):
        """Greedy wrap; returns a list of lines that fit max_w."""
        out, cur = [], ""
        for word in text.split():
            trial = (cur + " " + word).strip()
            if self.width(trial, path, size) <= max_w:
                cur = trial
            else:
                if cur:
                    out.append(cur)
                cur = word
        if cur:
            out.append(cur)
        return out

    def block(self, x, y, text, path, size, fill, max_w, lead, limit=None):
        """Draw a wrapped paragraph; return the y below its last line."""
        lines = self.wrap(text, path, size, max_w)
        if limit is not None:
            lines = lines[:limit]
        for line in lines:
            self.put(x, y, line, path, size, fill)
            y += lead
        return y

    def rule(self, y, fill=RULE, width=1):
        self.d.line([(MARGIN, y), (RIGHT, y)], fill=fill, width=width)

    def disc(self, x, y, r, fill):
        self.d.ellipse([x, y, x + 2 * r, y + 2 * r], fill=fill)

    def numdot(self, x, y, num, r=10, fill=RED):
        self.disc(x, y, r, fill)
        lab = str(num)
        fnt = self.f(SANS_B, 12 if r >= 10 else 9)
        tw = self.d.textlength(lab, font=fnt)
        self.d.text((x + r - tw / 2, y + r - (7 if r >= 10 else 5)),
                    lab, font=fnt, fill=WHITE)

    def tagline(self, x, y, src, tag):
        """'(Source) · TAG' source line; returns nothing."""
        self.put(x, y, "(%s)" % src, SANS, 8, FAINT)
        w = self.width("(%s)" % src, SANS, 8)
        self.put(x + w + 4, y, "· " + tag, SANS_B, 8,
                 RED if tag == "CLAIM" else NAVY)


# ---- The 39 stories ------------------------------------------------------
# Display numbers follow the page order: heroes 1-3, mediums 4-11,
# smalls 12-15, ALSO 16-39. lon/lat place each story on the map.

HEROES = [
    dict(n=1, region="EUROPE", place="ANTALYA, TURKEY", beat="CLIMATE",
         head="Climate talks collapse with no fossil-fuel deal",
         deck="The EU and about 130 countries reject a pact that never "
              "mentions fossil fuels — the first climate-summit collapse "
              "since Copenhagen in 2009.",
         src="Reuters", tag="REPORTED", banner="NO DEAL",
         banner_col=(166, 30, 34), scene="cop31", lon=30.7, lat=36.9),
    dict(n=2, region="ASIA-PACIFIC", place="CIKANDE, INDONESIA", beat="FIRE",
         head="Factory fire kills 24; around 30 still missing",
         deck="Monday's toll jumps from 3 as searchers work the ruins of "
              "the Milkita candy plant; around 30 are missing and DNA "
              "IDs may take weeks.",
         src="Reuters", tag="REPORTED", banner="24 DEAD",
         banner_col=(166, 30, 34), scene="fire", lon=106.2, lat=-6.3),
    dict(n=3, region="AMERICAS", place="WALL STREET", beat="MARKETS",
         head="Nvidia brings back Huang; shares soar 31%",
         deck="Eleven days after quitting in scandal, Jensen Huang is "
              "reinstated as CEO; shares add about $952bn in a day and "
              "Asian markets leap.",
         src="CNN", tag="REPORTED", banner="+31.5%",
         banner_col=(15, 118, 110), scene="chip", lon=-122.0, lat=37.4),
]

# Mediums: big opening figure/word first; the first three carry a
# small filled mini-scene beside the figure (6 illustrated panels
# in total across the page: 3 heroes + these 3).
MEDIUMS = [
    dict(n=4, region="MIDDLE EAST", place="KHAN YOUNIS, GAZA", beat="WAR",
         big="3", big_col=RED, scene="gaza",
         head="Three killed in strike on a Gaza police post",
         deck="An Israeli strike hits a volunteer police post in Khan "
              "Younis; five more are wounded, medics say.",
         src="Reuters", tag="REPORTED", lon=34.45, lat=31.35),
    dict(n=5, region="ASIA-PACIFIC", place="TOKYO", beat="MARKETS",
         big="+4.6%", big_col=(15, 118, 110), scene="chart",
         head="Asian shares leap as Nvidia revives the AI trade",
         deck="MSCI's Asia-Pacific index climbs 4.6% from an eight-month "
              "low after Wall Street's relief rally.",
         src="Reuters", tag="REPORTED", lon=139.7, lat=35.7),
    dict(n=6, region="EUROPE", place="BRUSSELS", beat="SANCTIONS",
         big="60", big_col=NAVY, scene="bank",
         head="EU unveils its 22nd Russia sanctions package",
         deck="Brussels proposes a ban on 60 Russian banks from SWIFT, "
              "more shadow-fleet ships and a visa ban for ex-combatants.",
         src="European Commission", tag="REPORTED", lon=4.35, lat=50.85),
    dict(n=7, region="EUROPE", place="DYMER, UKRAINE", beat="WAR",
         big="11", big_col=RED, scene=None,
         head="Boy, 7, saved after 14 hours under rubble",
         deck="The final toll reaches 11 dead after a drone hits a block "
              "of flats; a 79-year-old woman is freed after 22 hours.",
         src="SOFX", tag="REPORTED", lon=30.3, lat=50.8),
    dict(n=8, region="ASIA-PACIFIC", place="MANIPUR, INDIA", beat="HEALTH",
         big="17", big_col=RED, scene=None,
         head="Tainted alcohol kills 17; hundreds screened",
         deck="More than 200 people are in hospital after suspect liquor; "
              "nine are arrested and 4,600 litres seized.",
         src="People", tag="REPORTED", lon=93.9, lat=24.8),
    dict(n=9, region="AFRICA", place="BENGHAZI, LIBYA", beat="WAR",
         big="SUNK", big_col=NAVY, scene=None,
         head="Ukraine claims it sank a Russian warship",
         deck="Kyiv says sea drones sank the corvette Merkury 2,400 km "
              "from the front line; satellite images show it submerged.",
         src="AP", tag="CLAIM", lon=20.1, lat=32.1),
    dict(n=10, region="AMERICAS", place="LAS VEGAS", beat="SPORT",
         big="75", big_col=(15, 118, 110), scene=None,
         head="Verstappen wins a chaotic Las Vegas Grand Prix",
         deck="His 75th career win, by 0.639 seconds, after 35 lead "
              "changes and 352 overtakes on the Strip.",
         src="Formula 1", tag="REPORTED", lon=-115.2, lat=36.1),
    dict(n=11, region="AMERICAS", place="WASHINGTON", beat="POLITICS",
         big="258", big_col=NAVY, scene=None,
         head="Democrats hit 258 House seats, most since 1992",
         deck="A recount confirms Chuck Hubbard's North Carolina win; "
              "Democrats now hold 258 seats to the Republicans' 173.",
         src="The Times", tag="REPORTED", lon=-77.0, lat=38.9),
]

SMALLS = [
    dict(n=12, region="EUROPE", place="MANCHESTER, UK", beat="ARENA",
         head="12,000 evacuated as fumes fill arena",
         deck="Police declare a major incident at the Co-op Live show; 89 "
              "show symptoms, one woman in hospital.",
         src="CNN", tag="REPORTED", lon=-2.24, lat=53.48),
    dict(n=13, region="AMERICAS", place="GUASAVE, MEXICO", beat="JUSTICE",
         head="‘El Chapo Isidro’ captured in Sinaloa",
         deck="Mexican special forces seize the FBI most-wanted drug lord; "
              "at least 21 die in the operation. A US extradition order exists.",
         src="Reuters", tag="REPORTED", lon=-108.5, lat=25.6),
    dict(n=14, region="ASIA-PACIFIC", place="SEOUL", beat="POLITICS",
         head="South Korea names its first woman spy chief",
         deck="President Lee reshuffles his cabinet, nominating Kang "
              "Kum-sil to lead the intelligence service; four ministers replaced.",
         src="Reuters", tag="REPORTED", lon=127.0, lat=37.5),
    dict(n=15, region="ASIA-PACIFIC", place="WELLINGTON", beat="CRICKET",
         head="New Zealand bat out a draw against India",
         deck="Mitchell and Phillips defy India for 120 overs to save the "
              "first Test; India declared at 720 for 9.",
         src="ICC", tag="REPORTED", lon=174.8, lat=-41.3),
]

# ALSO 16-39: one line each: (number, place, line, source, tag, lon, lat)
ALSO = [
    (16, "SEATTLE", "ICE seizes father and daughter on a jet bridge",
     "CNN", "REPORTED", -122.3, 47.6),
    (17, "BRAZIL", "Storm wrecks 8,000 homes; 5 dead, 20,000 homeless",
     "Channels TV", "REPORTED", -53.9, -29.0),
    (18, "COLORADO", "First Gen Z woman heads to Congress at 29",
     "NPR", "REPORTED", -105.0, 39.0),
    (19, "WASHINGTON", "US sanctions 24+ Iranian shadow banks",
     "US Treasury", "REPORTED", -77.0, 38.9),
    (20, "NEW DELHI", "India stays Asia's No. 3 power; Modi rated No. 2",
     "Lowy Institute", "REPORTED", 77.2, 28.6),
    (21, "THAI BORDER", "Ceasefire reported holding after 3 weeks of fighting",
     "Gazette", "REPORTED", 103.0, 13.5),
    (22, "HIMALAYAS", "8 trekkers missing as snow halts the search",
     "PTI", "REPORTED", 78.9, 31.0),
    (23, "ULLEUNG", "Jets scrambled as Russian planes near island; alert lifted",
     "Reuters", "REPORTED", 130.9, 37.5),
    (24, "BENGHAZI", "Libya's east asks the UN to probe the naval attack",
     "Libya Review", "REPORTED", 20.1, 32.1),
    (25, "KHARTOUM", "Drones hit a UN building; 4 killed",
     "UN", "REPORTED", 32.5, 15.6),
    (26, "DR CONGO", "Fighting traps Ebola teams in Ituri hospital",
     "WHO", "REPORTED", 29.5, 1.5),
    (27, "HARARE", "Preacher Uebert Angel arrested mid-sermon",
     "News Hour", "REPORTED", 31.0, -17.8),
    (28, "CANBERRA", "Wong: AI is now a core foreign-policy challenge",
     "Reuters", "REPORTED", 149.1, -35.3),
    (29, "WELLINGTON", "Tickner out of 2nd Test with hamstring injury",
     "Reuters", "REPORTED", 174.8, -41.3),
    (30, "BARBADOS", "UN chief: agree global AI rules within a year",
     "AFP", "REPORTED", -59.6, 13.1),
    (31, "LONDON", "Oil slides to a 3-month low as Libyan pipeline reopens",
     "Reuters", "REPORTED", -0.1, 51.5),
    (32, "MOSCOW", "Report: Russia may orbit a nuclear weapon by year's end",
     "SZ/WDR/NDR", "CLAIM", 37.6, 55.8),
    (33, "MOSCOW", "Medvedev warns of a ‘preventive’ nuclear strike",
     "Fox News", "CLAIM", 37.6, 55.8),
    (34, "PARIS", "Macron weighs a ‘golden rule’ on spending",
     "Le Monde", "REPORTED", 2.35, 48.85),
    (35, "ZAPORIZHZHIA", "Overnight attack kills 2, wounds 22",
     "Reuters", "REPORTED", 35.2, 47.8),
    (36, "GULF", "Iran vows to use ‘all tools’ against the US blockade",
     "TBS", "REPORTED", 50.3, 29.2),
    (37, "TAIZ", "80 civilians killed in 20 days of shelling",
     "Yemen Monitor", "CLAIM", 44.0, 13.6),
    (38, "N. IRAQ", "PKK quits 14 mountain bases as peace talks advance",
     "TRT", "REPORTED", 44.5, 36.8),
    (39, "BERLIN", "Hoax bomb emails hit 450 schools; police say carry on",
     "Reuters", "REPORTED", 13.4, 52.5),
]

REGIONS = [("EUROPE", 9), ("MIDDLE EAST", 4), ("AMERICAS", 8),
           ("ASIA-PACIFIC", 9), ("AFRICA", 5), ("OCEANIA", 2), ("WORLD", 2)]

STATS = [
    ("90", "COUNTRIES IN THE 35-BY-35 PLEDGE AFTER COP31"),
    ("24", "DEAD IN THE CIKANDE FACTORY FIRE"),
    ("+31.5%", "NVIDIA'S ONE-DAY SHARE JUMP"),
    ("3", "KILLED IN TUESDAY'S GAZA STRIKE"),
    ("2", "KILLED IN ZAPORIZHZHIA OVERNIGHT"),
    ("258", "DEMOCRATS' HOUSE SEATS"),
]

# Six moments, all genuinely tied to Tuesday 24 Nov (times as reported;
# "NIGHT" / "TUE" where no exact hour was published).
CLOCK = [
    ("00:00", "ASIA MARKETS LEAP"),
    ("~01:00", "GAZA STRIKE: 3 KILLED"),
    ("07:52 KST", "ULLEUNG ALERT"),
    ("NIGHT", "ZAPORIZHZHIA: 2 DEAD"),
    ("TUE", "WONG: AI IS FOREIGN POLICY"),
    ("TUE", "8 TREKKERS MISSING"),
]

DATE_CHECK = (
    "Left out as other days’ news: COP31’s collapse was Sunday 22 Nov — "
    "only the fallout is today’s news · the Cikande fire was Saturday "
    "21 Nov; Monday’s toll of 24 is the new fact · the Dymer strike was "
    "Sunday 22 Nov · the Libya warship attack was Sunday 22 Nov · the "
    "Democrats were elected 3 Nov; the 258-seat milestone was confirmed "
    "22–23 Nov · Thai–Cambodia ceasefire dates are disputed in reports "
    "(21 Nov vs a December timeline) · the ICJ Myanmar ruling was 19 Nov · "
    "the Prajwal Revanna sentence was August 2025, not November 2026.")

# ---- Code-drawn scenes ---------------------------------------------------
# Six illustrated panels: 3 heroes + 3 medium mini-scenes. Each painter
# draws a full little scene (filled background + several elements) in
# the box it is given; nothing is a photo or a stretched flat object.

def _stamp(sheet, x, y, text, size=11, col=RED):
    """A small red rubber-stamp label, tilted, on its own layer."""
    layer = Image.new("RGBA", (220, 40), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    fnt = sheet.f(SANS_B, size)
    tw = ld.textlength(text, font=fnt)
    ld.rectangle([2, 2, tw + 12, 30], outline=col, width=3)
    ld.text((8, 8), text, font=fnt, fill=col)
    layer = layer.rotate(8, expand=True, resample=Image.BICUBIC)
    sheet.page.paste(layer, (x, y), layer)


def paint_cop31(sheet, x, y, w, h):
    d = sheet.d
    d.rectangle([x, y, x + w, y + h], fill=(23, 92, 96))
    d.rectangle([x, y, x + w, y + int(h * 0.42)], fill=(31, 122, 126))
    # low sun + skyline through the hall window
    d.ellipse([x + w - 52, y + 8, x + w - 22, y + 38], fill=GOLD)
    d.rectangle([x, y + int(h * 0.42), x + w, y + int(h * 0.42) + 3],
                fill=(18, 64, 70))
    # long negotiating table
    ty = y + int(h * 0.55)
    d.rectangle([x + 14, ty, x + w - 14, ty + 16], fill=(92, 58, 30))
    d.rectangle([x + 14, ty + 16, x + w - 14, ty + 20], fill=(70, 44, 22))
    # five seated delegates (one chair empty) + papers
    for i in range(5):
        cx = x + 34 + i * int((w - 68) / 4)
        if i == 3:
            # empty chair
            d.rectangle([cx - 9, ty - 12, cx + 9, ty], outline=WHITE, width=2)
            continue
        d.ellipse([cx - 9, ty - 34, cx + 9, ty - 16], fill=(244, 214, 180))
        d.rectangle([cx - 13, ty - 16, cx + 13, ty], fill=NAVY if i % 2 else (90, 30, 40))
        d.rectangle([cx - 8, ty - 8, cx + 8, ty - 2], fill=WHITE)
    d.rectangle([x + w // 2 - 26, ty - 6, x + w // 2 + 26, ty + 2],
                fill=WHITE)
    # draft document standing on the table
    d.rectangle([x + w - 78, ty - 30, x + w - 40, ty], fill=WHITE)
    d.line([(x + w - 72, ty - 24), (x + w - 46, ty - 24)], fill=INK, width=1)
    d.line([(x + w - 72, ty - 18), (x + w - 46, ty - 18)], fill=INK, width=1)
    d.line([(x + w - 72, ty - 12), (x + w - 56, ty - 12)], fill=INK, width=1)
    _stamp(sheet, x + 10, y + h - 46, "NOT ADOPTED", size=11)
    d.text((x + w - 96, y + h - 16), "COP31 · ANTALYA",
           font=sheet.f(SANS_B, 9), fill=WHITE)


def paint_fire(sheet, x, y, w, h):
    d = sheet.d
    d.rectangle([x, y, x + w, y + h], fill=(58, 22, 18))
    d.rectangle([x, y, x + w, y + int(h * 0.35)], fill=(120, 52, 28))
    # smoke
    for cx, cy, r in [(70, 18, 12), (92, 10, 15), (150, 20, 11),
                      (210, 12, 13), (250, 22, 10)]:
        d.ellipse([x + cx - r, y + cy - r, x + cx + r, y + cy + r],
                  fill=(90, 84, 78))
    # factory with a sawtooth roof
    by = y + h
    d.rectangle([x + 16, by - 52, x + w - 16, by - 14], fill=(74, 74, 74))
    for i in range(4):
        px = x + 16 + i * int((w - 32) / 4)
        d.polygon([(px, by - 52), (px + int((w - 32) / 8), by - 66),
                   (px + int((w - 32) / 4), by - 52)], fill=(58, 58, 58))
    d.rectangle([x + 26, by - 44, x + 44, by - 30], fill=GOLD)
    d.rectangle([x + 56, by - 44, x + 74, by - 30], fill=GOLD)
    # flames licking from the roof
    for cx, fh in [(110, 26), (150, 34), (195, 24), (240, 30)]:
        d.polygon([(x + cx - 12, by - 60), (x + cx, by - 60 - fh),
                   (x + cx + 12, by - 60)], fill=(240, 123, 45))
        d.polygon([(x + cx - 6, by - 60), (x + cx, by - 60 - fh + 12),
                   (x + cx + 6, by - 60)], fill=(255, 197, 61))
    # fire truck + short ladder leaning on the roof's left edge
    d.rectangle([x + 18, by - 14, x + 74, by - 2], fill=(166, 30, 34))
    d.rectangle([x + 58, by - 24, x + 74, by - 14], fill=(166, 30, 34))
    d.line([(x + 66, by - 22), (x + 102, by - 60)], fill=WHITE, width=3)
    d.line([(x + 72, by - 22), (x + 108, by - 60)], fill=WHITE, width=3)
    for k in range(3):
        lx = x + 70 + k * 12
        ly = by - 30 - k * 11
        d.line([(lx, ly), (lx + 6, ly)], fill=WHITE, width=2)
    for cx in (150, 170):
        d.ellipse([x + cx - 5, by - 22, x + cx + 5, by - 12], fill=(244, 214, 180))
        d.rectangle([x + cx - 6, by - 12, x + cx + 6, by - 2], fill=(245, 166, 35))
    d.text((x + w - 108, y + h - 14), "MILKITA · CIKANDE",
           font=sheet.f(SANS_B, 9), fill=WHITE)


def paint_chip(sheet, x, y, w, h):
    d = sheet.d
    d.rectangle([x, y, x + w, y + h], fill=(13, 32, 54))
    # circuit dots
    for cx, cy in [(24, 18), (60, 30), (w - 30, 16), (w - 66, 34),
                   (30, h - 18), (w - 40, h - 22)]:
        d.ellipse([x + cx - 3, y + cy - 3, x + cx + 3, y + cy + 3],
                  fill=(60, 130, 110))
    # green chip, centre-left
    cw, ch = 92, 64
    cx0, cy0 = x + 22, y + int(h / 2) - ch // 2
    d.rectangle([cx0, cy0, cx0 + cw, cy0 + ch], fill=(20, 160, 90))
    d.rectangle([cx0 + 8, cy0 + 8, cx0 + cw - 8, cy0 + ch - 8],
                outline=(255, 255, 255), width=2)
    for i in range(4):
        d.line([(cx0 - 10, cy0 + 12 + i * 14), (cx0, cy0 + 12 + i * 14)],
               fill=(20, 160, 90), width=3)
        d.line([(cx0 + cw, cy0 + 12 + i * 14), (cx0 + cw + 10, cy0 + 12 + i * 14)],
               fill=(20, 160, 90), width=3)
    d.text((cx0 + 24, cy0 + 22), "NVDA", font=sheet.f(SANS_B, 13), fill=WHITE)
    # gold rising arrow across the right side
    pts = [(x + 130, y + h - 26), (x + 175, y + h - 52),
           (x + 205, y + h - 40), (x + 255, y + h - 70),
           (x + w - 18, y + 22)]
    d.line(pts, fill=GOLD, width=4)
    d.polygon([(x + w - 30, y + 16), (x + w - 8, y + 18),
               (x + w - 20, y + 36)], fill=GOLD)
    d.text((x + 130, y + 8), "WALL STREET", font=sheet.f(SANS_B, 9), fill=WHITE)


def paint_gaza(sheet, x, y, w, h):
    """Mini-scene for medium 4: damaged building + smoke."""
    d = sheet.d
    d.rectangle([x, y, x + w, y + h], fill=(226, 220, 205))
    d.rectangle([x + 8, y + 12, x + w - 26, y + h - 2], fill=(120, 116, 108))
    d.rectangle([x + 14, y + 18, x + 26, y + 26], fill=(240, 200, 90))
    d.rectangle([x + 32, y + 18, x + 44, y + 26], fill=(60, 58, 54))
    d.polygon([(x + 8, y + 12), (x + 30, y + 4), (x + 52, y + 12)],
              fill=(90, 88, 82))
    for cx, cy, r in [(w - 16, 8, 7), (w - 8, 14, 5), (w - 24, 4, 5)]:
        d.ellipse([x + cx - r, y + cy - r, x + cx + r, y + cy + r],
                  fill=(150, 146, 138))
    for px, pw in [(8, 14), (26, 10), (40, 16)]:
        d.polygon([(x + px, y + h - 2), (x + px + pw // 2, y + h - 12),
                   (x + px + pw, y + h - 2)], fill=(96, 92, 86))


def paint_chart(sheet, x, y, w, h):
    """Mini-scene for medium 5: rising market chart."""
    d = sheet.d
    d.rectangle([x, y, x + w, y + h], fill=(226, 220, 205))
    d.line([(x + 8, y + h - 8), (x + w - 6, y + h - 8)], fill=INK, width=1)
    d.line([(x + 8, y + 6), (x + 8, y + h - 8)], fill=INK, width=1)
    pts = [(x + 10, y + h - 14), (x + 28, y + h - 22), (x + 44, y + h - 18),
           (x + 62, y + h - 30), (x + 80, y + 12), (x + w - 8, y + 8)]
    d.line(pts, fill=(15, 118, 110), width=3)
    for px, py in pts[1:-1]:
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(15, 118, 110))
    d.polygon([(x + w - 16, y + 6), (x + w - 4, y + 8), (x + w - 12, y + 18)],
              fill=(15, 118, 110))


def paint_bank(sheet, x, y, w, h):
    """Mini-scene for medium 6: bank facade + sanction document."""
    d = sheet.d
    d.rectangle([x, y, x + w, y + h], fill=(226, 220, 205))
    d.polygon([(x + 6, y + 12), (x + 34, y + 4), (x + 62, y + 12)],
              fill=NAVY)
    for cx in (12, 26, 40, 54):
        d.rectangle([x + cx, y + 14, x + cx + 5, y + h - 8], fill=NAVY)
    d.rectangle([x + 6, y + h - 8, x + 62, y + h - 4], fill=NAVY)
    d.rectangle([x + 70, y + 8, x + w - 6, y + h - 6], fill=WHITE,
                outline=RULE)
    for i in range(3):
        d.line([(x + 76, y + 14 + i * 7), (x + w - 12, y + 14 + i * 7)],
               fill=INK, width=1)
    d.ellipse([x + w - 22, y + h - 18, x + w - 10, y + h - 6], fill=RED)


SCENES = {"cop31": paint_cop31, "fire": paint_fire, "chip": paint_chip,
          "gaza": paint_gaza, "chart": paint_chart, "bank": paint_bank}


# ---- Small world map -----------------------------------------------------
# Rough continent outlines (lon, lat), equirectangular. Deliberately
# coarse: the panel is 304x116 and only needs to read as a world map.
CONTINENTS = [
    [(-168, 66), (-140, 70), (-125, 71), (-110, 68), (-95, 69), (-85, 66),
     (-80, 73), (-70, 62), (-60, 55), (-55, 47), (-65, 44), (-75, 38),
     (-80, 32), (-85, 29), (-90, 21), (-97, 16), (-94, 17), (-86, 13),
     (-83, 9), (-79, 9), (-90, 14), (-97, 16), (-105, 20), (-110, 23),
     (-117, 33), (-125, 40), (-124, 48), (-135, 58), (-150, 60), (-165, 60)],
    [(-79, 9), (-72, 11), (-62, 10), (-52, 5), (-50, 0), (-44, -3),
     (-35, -8), (-40, -20), (-48, -28), (-58, -35), (-65, -41), (-70, -50),
     (-74, -54), (-70, -30), (-72, -18), (-77, -12), (-81, -5), (-80, 1)],
    [(-17, 15), (-10, 31), (-5, 35), (10, 37), (20, 32), (30, 31), (35, 28),
     (40, 15), (43, 11), (48, 11), (51, 12), (44, 2), (40, -5), (36, -18),
     (32, -29), (26, -34), (19, -35), (15, -27), (12, -18), (9, -1),
     (9, 4), (-8, 5), (-13, 8), (-17, 15)],
    [(-10, 36), (-9, 43), (-2, 48), (-4, 50), (0, 51), (5, 53), (8, 57),
     (10, 59), (18, 56), (21, 55), (24, 59), (30, 60), (28, 65), (25, 70),
     (20, 70), (15, 68), (12, 64), (8, 62), (5, 58), (0, 52), (-5, 50),
     (-9, 43), (-10, 36)],
    [(30, 60), (40, 68), (60, 69), (70, 72), (90, 75), (110, 74), (130, 72),
     (150, 70), (170, 66), (178, 65), (170, 60), (162, 56), (156, 51),
     (142, 50), (140, 45), (135, 43), (130, 38), (127, 35), (122, 32),
     (120, 28), (115, 22), (109, 20), (105, 10), (100, 8), (97, 15),
     (92, 21), (89, 22), (85, 19), (80, 13), (76, 9), (72, 20), (66, 25),
     (60, 25), (57, 27), (52, 28), (48, 29), (44, 29), (40, 31), (36, 36),
     (30, 36), (28, 40), (26, 40), (23, 40), (20, 45), (18, 50), (15, 55),
     (12, 58), (10, 59)],
    [(114, -22), (114, -30), (115, -35), (120, -34), (124, -33), (129, -32),
     (132, -32), (136, -35), (140, -38), (145, -38), (150, -37), (153, -32),
     (153, -27), (150, -22), (146, -19), (142, -15), (142, -11), (137, -12),
     (135, -15), (132, -12), (130, -13), (126, -14), (122, -17), (118, -20),
     (114, -22)],
]


def project(lon, lat, x0, y0, w, h):
    """Equirectangular: lon -180..180, lat 75..-60 -> panel coords."""
    px = x0 + (lon + 180.0) / 360.0 * w
    py = y0 + (75.0 - lat) / 135.0 * h
    return px, py


def draw_map(sheet, x0, y0, w, h):
    d = sheet.d
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=(11, 26, 41))
    for gx in range(-150, 181, 30):
        px, _ = project(gx, 0, x0, y0, w, h)
        d.line([(px, y0), (px, y0 + h)], fill=(26, 50, 70), width=1)
    for gy in (-30, 0, 30, 60):
        _, py = project(0, gy, x0, y0, w, h)
        d.line([(x0, py), (x0 + w, py)], fill=(26, 50, 70), width=1)
    for poly in CONTINENTS:
        pts = [project(lon, lat, x0, y0, w, h) for lon, lat in poly]
        d.polygon(pts, fill=(44, 96, 104), outline=(74, 138, 145))
    # pins 1-13 numbered, dots 14-39; nudge pins that would collide.
    placed = []
    all_stories = HEROES + MEDIUMS + SMALLS
    for st in all_stories:
        px, py = project(st["lon"], st["lat"], x0, y0, w, h)
        dx = dy = 0
        for qx, qy in placed:
            if abs(px + dx - qx) < 13 and abs(py + dy - qy) < 13:
                dx += 11
                dy -= 8
        placed.append((px + dx, py + dy))
        col = BADGES[(st["n"] - 1) % len(BADGES)]
        cx, cy = px + dx, py + dy
        d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=col,
                  outline=WHITE, width=1)
        fnt = sheet.f(SANS_B, 7)
        lab = str(st["n"])
        tw = d.textlength(lab, font=fnt)
        d.text((cx - tw / 2, cy - 5), lab, font=fnt, fill=WHITE)
    for (num, _pl, _tx, _src, _tag, lon, lat) in ALSO:
        px, py = project(lon, lat, x0, y0, w, h)
        d.ellipse([px - 2.5, py - 2.5, px + 2.5, py + 2.5], fill=WHITE)

# ---- Page sections -------------------------------------------------------
# Each takes the sheet and the current y, draws its band, and returns
# the y where the next section starts. Heights are measured from the
# wrapped text so nothing can overflow the 1024 canvas silently:
# main() prints every section end and the final y.

def masthead(sheet):
    sheet.centred(8, "THE WORLD IN ONE DAY", SANS_B, 13, RED)
    sheet.centred(25, "Tuesday, 24 November 2026", SERIF_B, 40, INK)
    y = 25 + 42
    sheet.rule(y, fill=INK, width=2)
    y += 4
    sheet.centred(y, "39 STORIES · 7 REGIONS · THE DAY’S NEWS, "
                  "REPORTED 23–24 NOV 2026", SANS_B, 10, INK)
    y += 16
    sheet.centred(y, "COP31 ends with no deal · Cikande fire kills 24 · "
                  "Nvidia’s $1 trillion comeback", SERIF, 15, RED)
    return y + 20


def stats_strip(sheet, y):
    col_w = 996 / 6
    for i, (num, label) in enumerate(STATS):
        cx = MARGIN + i * col_w
        if i > 0:
            sheet.d.line([(cx, y + 2), (cx, y + 48)], fill=RULE, width=1)
        nw = sheet.width(num, SANS_B, 24)
        sheet.put(cx + (col_w - nw) / 2, y, num, SANS_B, 24, RED)
        sheet.block(cx + 6, y + 28, label, SANS, 8, INK, col_w - 12, 10,
                    limit=2)
    y += 54
    sheet.rule(y)
    return y + 4


def region_tabs(sheet, y):
    tab_w = 996 / 7
    for i, (name, count) in enumerate(REGIONS):
        x0 = MARGIN + i * tab_w
        sheet.d.rectangle([x0 + 1, y, x0 + tab_w - 1, y + 18],
                          fill=REGION_FILL[name])
        label = "%s %d" % (name, count)
        tw = sheet.width(label, SANS_B, 10)
        sheet.put(x0 + (tab_w - tw) / 2, y + 3, label, SANS_B, 10, WHITE)
    return y + 22


def clock_strip(sheet, y):
    sheet.d.rectangle([MARGIN, y, RIGHT, y + 22], fill=NAVY)
    lab = "THE DAY IN UTC"
    lw = sheet.width(lab, SANS_B, 9)
    sheet.d.rectangle([MARGIN, y, MARGIN + lw + 12, y + 22], fill=RED)
    sheet.put(MARGIN + 6, y + 6, lab, SANS_B, 9, WHITE)
    cell_x = MARGIN + lw + 12
    cell_w = (RIGHT - cell_x) / 6
    for i, (t, txt) in enumerate(CLOCK):
        cx = cell_x + i * cell_w
        if i > 0:
            sheet.d.line([(cx, y + 4), (cx, y + 18)], fill=(58, 110, 128),
                         width=1)
        sheet.put(cx + 6, y + 6, t, SANS_B, 9, GOLD)
        tw = sheet.width(t, SANS_B, 9)
        sheet.put(cx + 6 + tw + 4, y + 6, txt, SANS, 8, (240, 244, 246))
    return y + 27


def heroes(sheet, y):
    col_w = 324
    panel_h = 118
    # measure the tallest hero card first so all three align
    tallest = 0
    for st in HEROES:
        hh = 24 + panel_h + 4
        hh += len(sheet.wrap(st["head"], SANS_B, 14, col_w)[:2]) * 17 + 3
        hh += len(sheet.wrap(st["deck"], SANS, 10, col_w)[:3]) * 12 + 4 + 10
        tallest = max(tallest, hh)
    for i, st in enumerate(HEROES):
        x = MARGIN + i * (col_w + 12)
        sheet.numdot(x, y, st["n"], r=10)
        sheet.put(x + 26, y + 4, "%s · %s" % (st["place"], st["beat"]),
                  SANS_B, 9, RED)
        # banner word across the top of the picture, scene below it
        sheet.d.rectangle([x, y + 24, x + col_w, y + 48], fill=st["banner_col"])
        bw = sheet.width(st["banner"], SANS_B, 15)
        sheet.put(x + (col_w - bw) / 2, y + 28, st["banner"], SANS_B, 15, WHITE)
        SCENES[st["scene"]](sheet, x, y + 48, col_w, panel_h - 24)
        sheet.d.rectangle([x, y + 24, x + col_w, y + 24 + panel_h],
                          outline=RULE, width=1)
        yy = y + 24 + panel_h + 4
        yy = sheet.block(x, yy, st["head"], SANS_B, 14, INK, col_w, 17, limit=2)
        yy = sheet.block(x, yy + 3, st["deck"], SANS, 10, INK, col_w, 12,
                         limit=3)
        sheet.tagline(x, yy + 4, st["src"], st["tag"])
    y += tallest
    sheet.rule(y + 2)
    return y + 8


def _big_panel(sheet, x, y, w, h, st):
    """Numbers-first opener: big figure left, mini-scene right (4-6)
    or the figure alone (7-11)."""
    sheet.d.rectangle([x, y, x + w, y + h], fill=PANEL, outline=RULE)
    big = st["big"]
    size = 30 if len(big) <= 2 else (24 if len(big) <= 3 else 20)
    if st["scene"]:
        scene_w = 118
        tw = sheet.width(big, SANS_B, size)
        sheet.put(x + 8, y + (h - size) // 2 - 2, big, SANS_B, size,
                  st["big_col"])
        SCENES[st["scene"]](sheet, x + w - scene_w - 4, y + 3,
                            scene_w - 4, h - 6)
    else:
        tw = sheet.width(big, SANS_B, size)
        sheet.put(x + (w - tw) / 2, y + (h - size) // 2 - 2, big, SANS_B,
                  size, st["big_col"])


def mediums(sheet, y):
    col_w = 996 // 4
    step = 249
    panel_h = 42
    for row in range(2):
        cards = MEDIUMS[row * 4:(row + 1) * 4]
        row_h = 0
        for st in cards:
            rh = panel_h + 4 + 16
            rh += len(sheet.wrap(st["head"], SANS_B, 11, col_w - 7)[:2]) * 13 + 2
            rh += len(sheet.wrap(st["deck"], SANS, 8, col_w - 7)[:2]) * 10 + 2 + 10
            row_h = max(row_h, rh)
        for j, st in enumerate(cards):
            x = MARGIN + j * step
            _big_panel(sheet, x, y, col_w - 7, panel_h, st)
            yy = y + panel_h + 4
            sheet.numdot(x, yy, st["n"], r=7)
            sheet.put(x + 18, yy + 3, "%s · %s" % (st["place"], st["beat"]),
                      SANS_B, 8, RED)
            yy += 16
            yy = sheet.block(x, yy, st["head"], SANS_B, 11, INK, col_w - 7,
                             13, limit=2)
            yy = sheet.block(x, yy + 2, st["deck"], SANS, 8, INK, col_w - 7,
                             10, limit=2)
            sheet.tagline(x, yy + 2, st["src"], st["tag"])
        y += row_h
        if row == 0:
            y += 8
    sheet.rule(y + 2)
    return y + 8


def smalls(sheet, y):
    col_w = 996 // 4
    step = 249
    tallest = 0
    for st in SMALLS:
        sh = 15
        sh += len(sheet.wrap(st["head"], SANS_B, 10, col_w - 7)[:2]) * 12 + 1
        sh += len(sheet.wrap(st["deck"], SANS, 8, col_w - 7)[:2]) * 10 + 1 + 10
        tallest = max(tallest, sh)
    for i, st in enumerate(SMALLS):
        x = MARGIN + i * step
        sheet.put(x, y, "%d  %s · %s" % (st["n"], st["place"], st["beat"]),
                  SANS_B, 8, RED)
        yy = sheet.block(x, y + 15, st["head"], SANS_B, 10, INK, col_w - 7,
                         12, limit=2)
        yy = sheet.block(x, yy + 1, st["deck"], SANS, 8, INK, col_w - 7, 10,
                         limit=2)
        sheet.put(x, yy + 1, "(%s) · %s" % (st["src"], st["tag"]), SANS, 8,
                  FAINT)
    y += tallest
    sheet.rule(y + 2)
    return y + 8


def _trim_line(sheet, text, max_w):
    """Shorten an ALSO line with an ellipsis until it fits."""
    if sheet.width(text, SANS, 8) <= max_w:
        return text
    words = text.split()
    while len(words) > 4:
        words = words[:-1]
        trial = " ".join(words) + " …"
        if sheet.width(trial, SANS, 8) <= max_w:
            return trial
    return " ".join(words) + " …"


def bottom_band(sheet, y):
    map_w = 304
    sheet.put(MARGIN, y, "WHERE IT HAPPENED", SANS_B, 9, INK)
    sheet.put(MARGIN, y + 11, "pins = story 1–13 · dots = story 14–39",
              SANS, 8, FAINT)
    draw_map(sheet, MARGIN, y + 22, map_w, 116)
    sheet.put(MARGIN, y + 142, "EUROPE 9 · MIDDLE EAST 4 · AMERICAS 8 "
              "· ASIA-PACIFIC 9", SANS, 8, FAINT)
    sheet.put(MARGIN, y + 152, "AFRICA 5 · OCEANIA 2 · WORLD 2", SANS, 8,
              FAINT)
    ax = MARGIN + map_w + 12
    aw = RIGHT - ax
    sheet.put(ax, y, "ALSO ON TUESDAY 24 NOVEMBER — 24 MORE STORIES",
              SANS_B, 11, INK)
    sheet.d.line([(ax, y + 16), (RIGHT, y + 16)], fill=RULE, width=1)
    col_w = (aw - 12) // 2
    yy = y + 20
    for col in range(2):
        xx = ax + col * (col_w + 12)
        ycol = yy
        for (num, place, text, src, tag, _lon, _lat) in ALSO[col * 12:(col + 1) * 12]:
            colour = BADGES[(num - 16) % len(BADGES)]
            cx, cy = xx + 6, ycol + 4
            sheet.d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=colour,
                            outline=WHITE, width=1)
            fnt = sheet.f(SANS_B, 7)
            lab = str(num)
            tw = sheet.d.textlength(lab, font=fnt)
            sheet.d.text((cx - tw / 2, cy - 4), lab, font=fnt, fill=WHITE)
            line = _trim_line(sheet, "%s — %s (%s)" % (place, text, src),
                              col_w - 15)
            sheet.put(xx + 15, ycol, line, SANS, 8, INK)
            if tag == "CLAIM":
                lw = sheet.width(line, SANS, 8)
                sheet.put(xx + 15 + lw + 3, ycol, "· CLAIM", SANS_B, 8, RED)
            ycol += 11
    y = yy + 12 * 11
    sheet.rule(y + 2)
    return y + 8


def date_check(sheet, y):
    lab = "DATE CHECK — "
    lab_w = sheet.width(lab, SANS_B, 8)
    lines = sheet.wrap(DATE_CHECK, SANS, 8, RIGHT - (MARGIN + 6 + lab_w + 4))
    # reflow: first line shares its row with the label, the rest are full
    first = []
    rest_words = DATE_CHECK.split()
    cur = ""
    for w in rest_words:
        trial = (cur + " " + w).strip()
        if sheet.width(trial, SANS, 8) <= RIGHT - (MARGIN + 6 + lab_w + 4):
            cur = trial
        else:
            break
    first_line = cur
    used = len(first_line.split())
    rest = sheet.wrap(" ".join(rest_words[used:]), SANS, 8,
                      RIGHT - MARGIN - 12)
    lines = [first_line] + rest[:2]
    box_h = 4 + len(lines) * 10 + 4
    sheet.d.rectangle([MARGIN, y, RIGHT, y + box_h], outline=RED, width=1)
    sheet.put(MARGIN + 6, y + 4, lab, SANS_B, 8, RED)
    yy = y + 4
    for li, line in enumerate(lines):
        xx = MARGIN + 6 + lab_w + 4 if li == 0 else MARGIN + 6
        sheet.put(xx, yy, line, SANS, 8, INK)
        yy += 10
    return y + box_h + 4


def footer(sheet, y):
    sheet.centred(y, "Sources: Reuters, AP, CNN, US Treasury, The Times, "
                  "Le Monde, ICC, UN News, WHO, European Commission and "
                  "the wires named with each story. Pictures and maps "
                  "original, drawn in code.", SANS, 8, FAINT)
    y += 10
    sheet.centred(y, "CERTAINTY: REPORTED = carried by the day’s wires · "
                  "CLAIM = one side’s account, labelled as such · "
                  "FORECAST = still to happen when drawn.", SANS, 8, FAINT)
    return y + 10


def main():
    sheet = Sheet()
    y = masthead(sheet)
    print("masthead ends y =", y)
    y = stats_strip(sheet, y)
    print("stats ends y =", y)
    y = region_tabs(sheet, y)
    print("tabs ends y =", y)
    y = clock_strip(sheet, y)
    print("clock ends y =", y)
    y = heroes(sheet, y)
    print("heroes ends y =", y)
    y = mediums(sheet, y)
    print("mediums ends y =", y)
    y = smalls(sheet, y)
    print("smalls ends y =", y)
    y = bottom_band(sheet, y)
    print("bottom band ends y =", y)
    y = date_check(sheet, y)
    print("date check ends y =", y)
    y = footer(sheet, y)
    print("FINAL y =", y, "(canvas 1024)")

    quality = 88
    sheet.page.save(OUT, "JPEG", quality=quality, optimize=True)
    size = os.path.getsize(OUT)
    while size > 1048576 and quality > 60:
        quality -= 6
        sheet.page.save(OUT, "JPEG", quality=quality, optimize=True)
        size = os.path.getsize(OUT)
    print("wrote", OUT, size, "bytes at quality", quality)
    if size > 1048576:
        sys.exit("entry.jpg still over 1 MiB")


if __name__ == "__main__":
    main()
