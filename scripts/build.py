#!/usr/bin/env python3
"""
Merge the curated list (data/records.txt) with harvested records (data/harvest/*.json),
classify, de-duplicate and write:
  data/bibliography.json / .csv / .js   (books, journals, reports)
  data/heritage_records.csv             (single photo/artefact records, not books)
  BIBLIOGRAPHY.md                       (category-wise Markdown tables)
"""
import csv, json, re, sys, unicodedata
from collections import Counter, OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
HARVEST = DATA / "harvest"

CATEGORIES = OrderedDict([
    ("EPG", ("Epigraphy: Manuals, Palaeography & Studies", "கல்வெட்டியல்: கையேடுகள், எழுத்தியல், ஆய்வுகள்")),
    ("ASI", ("Inscription Corpora: ASI, Epigraphia & Colonial Series", "கல்வெட்டுத் தொகுதிகள்: இந்தியத் தொல்லியல் துறை")),
    ("TNS", ("Inscription Corpora: Tamil Nadu State, District & Temple", "தமிழ்நாட்டுக் கல்வெட்டுத் தொகுதிகள்")),
    ("CPP", ("Copper Plates & Charters", "செப்பேடுகள், பட்டயங்கள்")),
    ("TBR", ("Tamil-Brahmi, Vatteluttu & Early Writing", "தமிழ்-பிராமி, வட்டெழுத்து")),
    ("HER", ("Hero Stones & Memorial Stones", "நடுகற்கள்")),
    ("ROC", ("Rock Art & Paintings", "பாறை ஓவியங்கள்")),
    ("EXC", ("Archaeology: Excavation Reports & Sites", "அகழாய்வு அறிக்கைகள்")),
    ("PRE", ("Archaeology: Prehistory & Megaliths", "தொல்பழங்காலம், பெருங்கற்காலம்")),
    ("ARC", ("Archaeology: General, Surveys & Museums", "தொல்லியல்: பொது, அகழ்வைப்பகங்கள்")),
    ("HIS", ("History from Inscriptions", "கல்வெட்டு வழி வரலாறு")),
    ("NUM", ("Numismatics (Coins)", "நாணயவியல்")),
    ("REF", ("Reference: Catalogues, Lists & Glossaries", "பட்டியல்கள், சொல்லகராதிகள்")),
    ("JOU", ("Journals & Periodicals", "இதழ்கள்")),
    ("ONL", ("Online Resources & Digital Libraries", "இணைய வளங்கள்")),
])
FIELDS = ["category", "language", "year", "title", "alt_title", "authors", "publisher",
          "place", "type", "series", "notes", "url"]

RULES = [
    ("JOU", r"(^இதழ்|\bjournal\b|bulletin|quarterly|காலாண்டு|சிறப்பிதழ்|\bmagazine\b|ஆவணம் :|^kalvettu[- ]?(april|jan|jul|oct|magazine)|^கல்வெட்டு\s*(ஏப்ரல்|ஜனவரி|சனவரி|ஜூலை|சூலை|அக்டோபர்|ஆகஸ்டு|சித்திரை|தை|ஐப்பசி|\d)|acl-arch|indian archaeology.{0,5}a review|ancient india|puratattva|indian antiquary)"),
    ("HER", r"(நடுக(ல்|ற்)|வீரக்கல்|nadukal|natukal|nadukar|natukar|hero[- ]?stone|memorial stone|sati stone|virakal|veerakal)"),
    ("ROC", r"(பாறை ஓவிய|குகை ஓவிய|ஓவியங்கள்|rock[- ]?art|rock[- ]paint|petroglyph|cave paint|pictograph|mural|paintings? in tamil|oviya)"),
    ("TBR", r"(பிராமி|தமிழி\b|வட்டெழுத்து|brahmi|tamili\b|vatteluttu|vattezhuthu|graffiti|potsherd|early writing|script)"),
    ("CPP", r"(செப்பேடு|பட்டய|copper[- ]?plates?|ceppe|seppe|cheppe|pattayam|charter)"),
    ("NUM", r"(நாணய|காசு|\bcoins?\b|numismat)"),
    ("EXC", r"(அகழாய்வு|அகழ்வாய்வு|excavat|keeladi|keezhadi|கீழடி|adichanallur|ஆதிச்சநல்லூர்|arikamedu|kodumanal|கொடுமணல்|porunthal|பொருந்தல்|alagankulam|அழகன்குளம்|kaveripattinam|poompuhar|பூம்புகார்|sivagalai|சிவகளை|uraiyur|korkai|mangulam|modur|vasavasamudram|akalayvu|agazhaivu)"),
    ("PRE", r"(பெருங்கற்|முதுமக்கள்|தாழி|தொல்பழங்கால|megalith|prehistor|palaeolith|paleolith|neolith|urn burial|dolmen|cairn|stone age|pandoo|pandukal)"),
    ("REF", r"(topographical list|அகராதி|அகரமுதலி|glossary|dictionary|concordance|catalogue|catalog\b|அடைவு|index of|bibliography|lists? of (inscriptions|antiquarian))"),
    ("ASI", r"(south indian inscriptions|epigraphia|annual report.{0,25}epigraph|report on .{0,20}epigraph|travancore archaeological|pudukkottai state|tirumalai.tirupati|ttd inscriptions|archaeological survey of (india|southern india)|memoirs of the archaeological|hultzsch)"),
    ("TNS", r"(கல்வெட்டுகள்|கல்வெட்டுக்கள்|kalvettuk|kalvettug|kalveddukal|kalvetukal|district inscriptions|temple inscriptions|inscriptions of (the )?\w+ (district|temple|state)|select(ed)? (tamil )?inscriptions|inscriptions (texts )?of|inscriptions in|\binscriptions\b)"),
    ("EPG", r"(கல்வெட்டியல்|தொல்லெழுத்|எழுத்தியல்|epigraphy|palaeograph|paleograph|கல்வெட்டு|kalvettu|kalvettiyal|inscription|சாசன|sasan)"),
    ("HIS", r"(history|வரலாறு|chola|cola|pandya|pallava|சோழ|பாண்டிய|பல்லவ|kingdom|administration|society|agrarian|temple)"),
    ("ARC", r"(தொல்லியல்|தொல்பொருள்|அகழ்வைப்பக|archaeolog|antiquit|antiquarian|museum|monument|tholliyal|tolliyal)"),
]
RULES = [(c, re.compile(p, re.I)) for c, p in RULES]
TAMIL = re.compile(r"[஀-௿]")


def classify(title, subjects=""):
    t = f"{title}"
    for code, rx in RULES:
        if rx.search(t):
            return code
    for code, rx in RULES:
        if rx.search(subjects or ""):
            return code
    return None


def period(year):
    m = re.match(r"(\d{4})", year or "")
    if not m:
        return "Undated"
    y = int(m.group(1))
    if y < 1900: return "1800–1899 (Colonial, early)"
    if y < 1947: return "1900–1946 (Colonial, late)"
    if y < 1991: return "1947–1990 (Post-independence)"
    if y < 2011: return "1991–2010"
    return "2011–2026 (Recent)"


def lang_of(title, raw, source):
    raw = (raw or "").lower()
    has_ta = bool(TAMIL.search(title or ""))
    has_en = "eng" in raw or raw.strip() in ("en", "english")
    if has_ta and re.search(r"[A-Za-z]{4,}", re.sub(r"\(.*?\)", "", title or "")) and has_en:
        return "Tamil-English"
    if has_ta or "tam" in raw or raw.strip() == "ta":
        return "Tamil"
    if has_en:
        return "English"
    if source in ("Noolaham",):
        return "Tamil"
    return "English" if re.search(r"[A-Za-z]", title or "") and not raw else (raw.title() or "Unknown")


def norm(t):
    t = (t or "").lower()
    t = re.sub(r"^(நூல்|இதழ்)\s*-\s*", "", t)
    t = re.sub(r"tva[ _-]?(bok|prl)[ _-]?\d+", "", t)
    out = []
    for ch in unicodedata.normalize("NFKD", t):
        if unicodedata.combining(ch) and out and out[-1].isascii():
            continue
        out.append(ch)
    t = "".join(out)
    return re.sub(r"[\s\W_]+", "", t)


def clean_title(t):
    t = re.sub(r"^\s*(நூல்|இதழ்)\s*-\s*", "", t or "").strip()
    t = re.sub(r"^TVA (BOK|PRL) \d+\s*", "", t).strip()
    return t


def heritage_record(r):
    """Tamil Digital Library single photo/artefact records mirrored on IA (not books)."""
    sid = r.get("source_id", "")
    if r["source"] == "Internet Archive" and re.match(r"^tdl\.(tdl_[0-9a-f]+|\d{3,5})-", sid):
        if not re.search(r"-(nuul|itlll)-", sid) and "நூல்" not in r["title"] and "இதழ்" not in r["title"]:
            return True
    return False


# ------------------------------------------------------------ Tamil -> Latin (ISO 15919)
_V = {"அ": "a", "ஆ": "ā", "இ": "i", "ஈ": "ī", "உ": "u", "ஊ": "ū", "எ": "e", "ஏ": "ē", "ஐ": "ai", "ஒ": "o", "ஓ": "ō", "ஔ": "au", "ஃ": "ḵ"}
_C = {"க": "k", "ங": "ṅ", "ச": "c", "ஞ": "ñ", "ட": "ṭ", "ண": "ṇ", "த": "t", "ந": "n", "ப": "p", "ம": "m", "ய": "y", "ர": "r",
      "ல": "l", "வ": "v", "ழ": "ḻ", "ள": "ḷ", "ற": "ṟ", "ன": "ṉ", "ஜ": "j", "ஷ": "ṣ", "ஸ": "s", "ஹ": "h", "ஶ": "ś"}
_S = {"ா": "ā", "ி": "i", "ீ": "ī", "ு": "u", "ூ": "ū", "ெ": "e", "ே": "ē", "ை": "ai", "ொ": "o", "ோ": "ō", "ௌ": "au", "்": ""}


def translit(text):
    text = text or ""
    out, i = [], 0
    while i < len(text):
        ch = text[i]
        if ch in _C:
            nxt = text[i + 1] if i + 1 < len(text) else ""
            if nxt in _S:
                out.append(_C[ch] + _S[nxt]); i += 2; continue
            out.append(_C[ch] + "a")
        elif ch in _V:
            out.append(_V[ch])
        elif ch in _S:
            out.append(_S[ch])
        else:
            out.append(ch)
        i += 1
    res = "".join(out)
    # capitalise first letter of each word that came from Tamil
    return re.sub(r"(^|[\s(\-–:])([a-zāīūēōṅñṭṇḻḷṟṉś])", lambda m: m.group(1) + m.group(2).upper(), res) if TAMIL.search(text) else res


_ROMAN = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9, "x": 10, "xi": 11, "xii": 12,
          "xiii": 13, "xiv": 14, "xv": 15, "xvi": 16, "xvii": 17, "xviii": 18, "xix": 19, "xx": 20}


def skeleton(title):
    """Script- and spelling-independent key so Tamil-script and romanised copies of a book merge."""
    t = translit(clean_title(title or "")).lower()
    t = "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))
    t = re.sub(r"\b(vol(ume)?|part|pt|no|tokuti|thogudi|thokuthi|thougudi|pakuti|pakudi|bhag)\b\.?", " ", t)
    t = re.sub(r"\b([ivx]{1,5})\b", lambda m: str(_ROMAN.get(m.group(1), m.group(1))), t)
    for a, b in (("zh", "l"), ("sh", "s"), ("ch", "c"), ("th", "t"), ("dh", "t"), ("kh", "k"), ("bh", "p"), ("gh", "k"), ("ph", "p"),
                 ("ng", "n"), ("nj", "n"), ("w", "v"), ("d", "t"), ("g", "k"), ("b", "p"), ("s", "c"), ("j", "c"), ("z", "l"), ("q", "k"), ("f", "p")):
        t = t.replace(a, b)
    t = re.sub(r"[aeiouyh]", "", t)
    t = re.sub(r"[^a-z0-9]", "", t)
    return re.sub(r"(.)\1+", r"\1", t)


# ------------------------------------------------------------ curated
def load_curated():
    recs = []
    for n, line in enumerate((DATA / "records.txt").read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        p = [x.strip() for x in line.split("|")]
        if len(p) != len(FIELDS):
            sys.exit(f"records.txt line {n}: {len(p)} fields")
        r = dict(zip(FIELDS, p))
        recs.append({"source": "Curated", "source_id": f"cur-{n}", "title": r["title"], "alt_title": r["alt_title"],
                     "authors": r["authors"], "publisher": r["publisher"], "place": r["place"],
                     "year": r["year"], "language": r["language"], "subjects": "", "url": r["url"],
                     "category": r["category"], "type": r["type"], "series": r["series"], "notes": r["notes"]})
    return recs


def load_harvest():
    out = []
    for f in sorted(HARVEST.glob("*.json")):
        try:
            out += json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print("skip", f, e)
    return out


SOURCE_RANK = {"Curated": 0, "Tamil Digital Library": 1, "Internet Archive": 2, "Noolaham": 3,
               "Library of Congress": 4, "Open Library": 5, "Google Books": 6}


def main():
    curated, harvested = load_curated(), load_harvest()
    heritage, books = [], []
    for r in harvested:
        sid = r.get("source_id", "")
        r["is_journal"] = bool(RULES[0][1].search(r["title"] or "")) or bool(re.search(r"(-itlll-|aclarch|kalveddu_|tva-prl|kalvettu-magazine|kalvettu-april)", sid, re.I))
        r["title"] = clean_title(r["title"])
        if not r["title"]:
            continue
        (heritage if heritage_record(r) else books).append(r)

    merged = OrderedDict()
    for r in curated + books:
        if r["source"] == "Curated":
            u = r.get("url", "")
            if u.lower().endswith(".pdf"):
                r.update(access="open", download_url=u, read_url=u)
            elif re.search(r"(archive\.org/details|tamildigitallibrary\.in/(Articles|book)|whatisindia\.com|library\.cict\.in)", u):
                r.update(access="open", read_url=u)
            else:
                r.update(access="catalogue" if u else "")
        is_journal_issue = r.get("is_journal", False)
        key = skeleton(r["title"])[:100]
        if is_journal_issue or len(key) < 8:
            key = f"{key}|{r['source']}|{r['source_id']}"
        if key not in merged:
            m = dict(r)
            m["sources"] = [r["source"]]
            m["source_urls"] = [r["url"]] if r.get("url") else []
            m["titles"] = [r["title"]] + ([r["alt_title"]] if r.get("alt_title") else [])
            merged[key] = m
            continue
        m = merged[key]
        if r["source"] not in m["sources"]:
            m["sources"].append(r["source"])
        if r.get("url") and r["url"] not in m["source_urls"]:
            m["source_urls"].append(r["url"])
        for t in (r["title"], r.get("alt_title")):
            if t and t not in m["titles"]:
                m["titles"].append(t)
        for f in ("authors", "publisher", "place", "year", "language", "subjects"):
            if not m.get(f) and r.get(f):
                m[f] = r[f]
        if r.get("found_by") and r["found_by"] not in m.get("found_by", ""):
            m["found_by"] = (m.get("found_by", "") + "; " + r["found_by"]).strip("; ")
        for f in ("isbn", "pages", "description", "full_text"):
            if r.get(f) and not m.get(f):
                m[f] = r[f]
        rank = {"open": 3, "preview": 2, "borrow": 1, "catalogue": 0, "": 0}
        if rank.get(r.get("access", ""), 0) > rank.get(m.get("access", ""), 0):
            m["access"], m["read_url"] = r.get("access"), r.get("read_url", "")
        if r.get("download_url") and not m.get("download_url"):
            m["download_url"] = r["download_url"]

    rows = []
    counters = Counter()
    for m in merged.values():
        if m.get("full_text") and m.get("access") not in ("open",):
            m.setdefault("read_url", m["full_text"])
        titles = m["titles"]
        ta = next((t for t in titles if TAMIL.search(t)), "")
        lat = next((t for t in titles if not TAMIL.search(t) and re.search(r"[A-Za-z]", t)), "")
        title_ta = ta
        title_en = lat or (translit(ta) if ta else "")
        title_en_is_translit = bool(ta and not lat)
        cat = m.get("category") or ("JOU" if m.get("is_journal") else None) or classify(" ".join(titles), m.get("subjects", "")) or ("HIS" if m.get("found_by") else "ARC")
        typ = m.get("type") or ("Journal issue" if cat == "JOU" else "Book")
        counters[cat] += 1
        rows.append({
            "id": "", "category": cat,
            "category_name": CATEGORIES[cat][0], "category_name_ta": CATEGORIES[cat][1],
            "title": m["title"], "title_ta": title_ta, "title_en": title_en,
            "title_en_note": "romanised from Tamil" if title_en_is_translit else "",
            "alt_title": m.get("alt_title", ""),
            "authors": m.get("authors", ""), "authors_roman": translit(m.get("authors", "")) if TAMIL.search(m.get("authors", "")) else "",
            "publisher": m.get("publisher", ""), "publisher_roman": translit(m.get("publisher", "")) if TAMIL.search(m.get("publisher", "")) else "",
            "place": m.get("place", ""), "year": m.get("year", ""), "period": period(m.get("year", "")),
            "language": m["language"] if m["source"] == "Curated" else lang_of(" ".join(titles), m.get("language"), m["source"]),
            "type": typ, "series": m.get("series", ""), "isbn": m.get("isbn", ""), "pages": m.get("pages", ""),
            "notes": m.get("notes") or (m.get("description") or "")[:220],
            "subjects": (m.get("subjects") or "")[:200],
            "access": m.get("access") or ("catalogue" if m["source_urls"] else ""),
            "read_url": m.get("read_url", ""), "download_url": m.get("download_url", ""),
            "source_url": m["source_urls"][0] if m["source_urls"] else "",
            "other_source_urls": m["source_urls"][1:6],
            "sources": m["sources"], "curated": m["source"] == "Curated",
            "scholar": "; ".join(x.split(":", 1)[1] for x in (m.get("found_by") or "").split("; ") if x.startswith("author:")),
        })

    def sort_key(r):
        y = re.match(r"\d{4}", r["year"] or "")
        return (list(CATEGORIES).index(r["category"]), int(y.group()) if y else 9999, r["title"].lower())
    rows.sort(key=sort_key)
    counters = Counter()
    for r in rows:
        counters[r["category"]] += 1
        r["id"] = f"{r['category']}-{counters[r['category']]:04d}"

    src_counts = Counter(s for r in rows for s in r["sources"])
    acc = Counter(r["access"] for r in rows)
    meta = {"generated": __import__("datetime").date.today().isoformat(), "count": len(rows),
            "with_author": sum(1 for r in rows if r["authors"]), "with_publisher": sum(1 for r in rows if r["publisher"]),
            "with_year": sum(1 for r in rows if r["year"]), "open_access": acc.get("open", 0),
            "with_download": sum(1 for r in rows if r["download_url"]), "heritage_records": len(heritage),
            "access": dict(acc), "sources": dict(src_counts),
            "categories": {k: {"en": v[0], "ta": v[1], "count": counters[k]} for k, v in CATEGORIES.items()}}
    doc = {**meta, "records": rows}
    (DATA / "bibliography.json").write_text(json.dumps(doc, ensure_ascii=False, indent=0), encoding="utf-8")
    pub = {k: v for k, v in meta.items() if k != "sources"}
    slim = {**pub, "records": [{k: v for k, v in r.items() if k not in ("subjects", "sources", "category_name", "category_name_ta")} for r in rows]}
    (DATA / "bibliography.js").write_text("window.BIB = " + json.dumps(slim, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")

    cols = ["id", "category", "category_name", "category_name_ta", "type", "title_ta", "title_en", "title_en_note",
            "authors", "authors_roman", "publisher", "publisher_roman", "place", "year", "period", "language", "scholar",
            "series", "isbn", "pages", "access", "read_url", "download_url", "source_url", "other_source_urls", "notes", "subjects"]
    with open(DATA / "bibliography.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow([" ; ".join(r[c]) if isinstance(r[c], list) else r[c] for c in cols])
    with open(DATA / "heritage_records.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["title_ta", "title_en", "category", "source_url"])
        for r in heritage:
            w.writerow([r["title"], translit(r["title"]), classify(r["title"]) or "", r["url"]])

    md = ["# Bibliography by Category / வகைவாரிப் பட்டியல்", "",
          f"Generated {meta['generated']} · **{len(rows)}** books, reports & journal issues · "
          f"{meta['with_author']} with author/editor · {meta['with_publisher']} with publisher · "
          f"{meta['with_year']} with year · {meta['open_access']} open access ({meta['with_download']} with direct download).", ""]
    for code, (en, ta) in CATEGORIES.items():
        rs = [r for r in rows if r["category"] == code]
        if not rs:
            continue
        md += [f"## {en} — {ta} ({len(rs)})", "",
               "| ID | Year | Title (Tamil / English) | Author / Editor | Publisher | Lang | Read / Download | Source |",
               "|---|---|---|---|---|---|---|---|"]
        for r in rs:
            t = " <br>".join(x for x in (r["title_ta"], r["title_en"]) if x) or r["title"]
            rd = " · ".join(x for x in ((f"[Read]({r['read_url']})" if r["read_url"] and r["access"] == "open" else ""),
                                        (f"[PDF]({r['download_url']})" if r["download_url"] else ""))) or "—"
            src = f"[Record]({r['source_url']})" if r["source_url"] else "—"
            cells = [r["id"], r["year"] or "—", t, r["authors"] or "—", ", ".join(x for x in (r["publisher"], r["place"]) if x) or "—", r["language"], rd, src]
            md.append("| " + " | ".join(str(c).replace("|", "/").replace("\n", " ") for c in cells) + " |")
        md.append("")
    (ROOT / "BIBLIOGRAPHY.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({k: v for k, v in meta.items() if k != "categories"}, ensure_ascii=False))
    print({k: counters[k] for k in CATEGORIES})


if __name__ == "__main__":
    main()
