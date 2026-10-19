#!/usr/bin/env python3
"""Build JSON / CSV / Markdown outputs from data/records.txt."""
import csv, json, re, sys
from pathlib import Path
from urllib.parse import quote, quote_plus

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "records.txt"

CATEGORIES = {
    "EPG": ("Epigraphy: Manuals, Palaeography & Script", "கல்வெட்டியல்: கையேடுகள், எழுத்தியல்"),
    "ASI": ("Inscription Corpora: ASI & Colonial Series", "கல்வெட்டுத் தொகுதிகள்: இந்தியத் தொல்லியல் துறை"),
    "TNS": ("Inscription Corpora: Tamil Nadu State, District & Temple", "தமிழ்நாட்டுக் கல்வெட்டுத் தொகுதிகள்"),
    "CPP": ("Copper Plates & Charters", "செப்பேடுகள்"),
    "TBR": ("Tamil-Brahmi, Early Writing & Graffiti", "தமிழ்-பிராமி, கீறல் குறியீடுகள்"),
    "HER": ("Hero Stones & Memorial Stones", "நடுகற்கள்"),
    "ROC": ("Rock Art & Paintings", "பாறை ஓவியங்கள்"),
    "EXC": ("Archaeology: Excavation Reports", "அகழாய்வு அறிக்கைகள்"),
    "PRE": ("Archaeology: Prehistory & Megaliths", "தொல்பழங்காலம், பெருங்கற்காலம்"),
    "ARC": ("Archaeology: General, Surveys & Museums", "தொல்லியல்: பொது, அகழ்வைப்பகங்கள்"),
    "HIS": ("History from Inscriptions", "கல்வெட்டு வழி வரலாறு"),
    "NUM": ("Numismatics (Inscribed Coins)", "நாணயவியல்"),
    "REF": ("Reference: Catalogues, Lists & Glossaries", "பட்டியல்கள், சொல்லகராதிகள்"),
    "JOU": ("Journals & Periodicals", "இதழ்கள்"),
    "ONL": ("Online Resources & Digital Libraries", "இணைய வளங்கள்"),
}
FIELDS = ["category", "language", "year", "title", "alt_title", "authors", "publisher",
          "place", "type", "series", "notes", "url"]


def period(year: str) -> str:
    m = re.match(r"(\d{4})", year or "")
    if not m:
        return "Undated"
    y = int(m.group(1))
    if y < 1900: return "1820–1899 (Colonial, early)"
    if y < 1947: return "1900–1946 (Colonial, late)"
    if y < 1991: return "1947–1990 (Post-independence)"
    if y < 2011: return "1991–2010"
    return "2011–2026 (Recent)"


def search_links(title, authors):
    q = title if len(title) < 120 else title[:120]
    qa = f"{q} {authors.split(';')[0]}".strip() if authors else q
    return {
        "archive_org": "https://archive.org/search?query=" + quote_plus(q),
        "tamil_digital_library": "https://www.google.com/search?q=" + quote_plus(f"site:tamildigitallibrary.in {q}"),
        "open_library": "https://openlibrary.org/search?q=" + quote_plus(qa),
        "worldcat": "https://search.worldcat.org/search?q=" + quote_plus(qa),
        "google_books": "https://www.google.com/search?tbm=bks&q=" + quote_plus(qa),
    }


def load():
    recs, errors = [], []
    counters = {}
    for n, line in enumerate(SRC.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("|")
        if len(parts) != len(FIELDS):
            errors.append(f"line {n}: {len(parts)} fields")
            continue
        r = dict(zip(FIELDS, [p.strip() for p in parts]))
        if r["category"] not in CATEGORIES:
            errors.append(f"line {n}: bad category {r['category']}")
            continue
        counters[r["category"]] = counters.get(r["category"], 0) + 1
        r["id"] = f"{r['category']}-{counters[r['category']]:03d}"
        r["category_name"], r["category_name_ta"] = CATEGORIES[r["category"]]
        r["period"] = period(r["year"])
        if r["url"]:
            r["url"] = quote(r["url"], safe=":/?=&%#-_.~+,()'")
        r["link_status"] = "verified" if r["url"] else "search-only"
        r["search"] = search_links(r["alt_title"] if (r["language"] == "Tamil" and r["alt_title"]) else r["title"], r["authors"])
        recs.append(r)
    if errors:
        sys.exit("\n".join(errors))
    return recs


def main():
    recs = load()
    (ROOT / "data").mkdir(exist_ok=True)
    order = ["id", "category", "category_name", "category_name_ta", "title", "alt_title", "authors",
             "year", "period", "language", "publisher", "place", "type", "series", "notes", "url", "link_status"]
    json.dump({"generated": "2026-10-19", "count": len(recs),
               "categories": {k: {"en": v[0], "ta": v[1]} for k, v in CATEGORIES.items()},
               "records": [{**{k: r[k] for k in order}, "search": r["search"]} for r in recs]},
              open(ROOT / "data" / "bibliography.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(ROOT / "data" / "bibliography.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(order + ["search_archive_org", "search_tamil_digital_library", "search_open_library", "search_worldcat"])
        for r in recs:
            s = r["search"]
            w.writerow([r[k] for k in order] + [s["archive_org"], s["tamil_digital_library"], s["open_library"], s["worldcat"]])

    # Markdown list by category
    md = ["# Bibliography by Category / வகைவாரிப் பட்டியல்", "",
          f"Total records: **{len(recs)}**. ✅ = verified direct link (full text, catalogue record or info page); 🔎 = search links only.", ""]
    for code, (en, ta) in CATEGORIES.items():
        rs = sorted([r for r in recs if r["category"] == code], key=lambda r: (r["year"] or "9999", r["title"]))
        if not rs: continue
        md += [f"## {en} — {ta} ({len(rs)})", "",
               "| ID | Year | Title | Author / Editor | Publisher | Lang | Link |", "|---|---|---|---|---|---|---|"]
        for r in rs:
            t = r["title"] + (f"<br><sub>{r['alt_title']}</sub>" if r["alt_title"] else "")
            link = f"[✅ Open]({r['url']})" if r["url"] else f"[🔎 Archive]({r['search']['archive_org']}) · [🔎 WorldCat]({r['search']['worldcat']})"
            cells = [r["id"], r["year"] or "—", t, r["authors"] or "—", r["publisher"] or "—", r["language"], link]
            md.append("| " + " | ".join(c.replace("|", "/") for c in cells) + " |")
        md.append("")
    (ROOT / "BIBLIOGRAPHY.md").write_text("\n".join(md), encoding="utf-8")

    stats = {}
    for r in recs:
        stats.setdefault(r["category"], 0); stats[r["category"]] += 1
    print(len(recs), "records;", sum(1 for r in recs if r["url"]), "verified links")
    print(stats)


if __name__ == "__main__":
    main()


def write_js():
    data = (ROOT / "data" / "bibliography.json").read_text(encoding="utf-8")
    (ROOT / "data" / "bibliography.js").write_text("window.BIB = " + data + ";\n", encoding="utf-8")


write_js()
