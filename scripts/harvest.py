#!/usr/bin/env python3
"""
Harvest Tamil epigraphy / inscription / archaeology / rock-art / hero-stone books
from public library APIs. Runs on GitHub Actions (needs open internet).

Sources:
  ia   Internet Archive (incl. Tamil Digital Library, Roja Muthiah (RMRL), DLI,
       Tamil Heritage Foundation, Noolaham mirrors) - advancedsearch scrape API
  ol   Open Library search API
  gb   Google Books API
  loc  Library of Congress JSON API
  nl   Noolaham digital library (MediaWiki API)

Writes data/harvest/<source>.json (normalised records) and data/harvest/log.txt.
Each source is isolated: one failing source never stops the others.
"""
import gzip, io, json, os, re, signal, sys, time, traceback, unicodedata, urllib.parse, urllib.request, urllib.robotparser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "harvest"
OUT.mkdir(parents=True, exist_ok=True)
SAMPLES = OUT / "samples"
SAMPLES.mkdir(exist_ok=True)
LOG = []
UA = "TamilEpigraphyBibliography/1.0 (https://github.com/Udhayan26/tamil-epigraphy-archaeology-bibliography)"


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.append(s)


BROWSER_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def get(url, tries=4, as_json=True, sleep=0.4, data=None, ua=None):
    last = None
    for i in range(tries):
        try:
            body = urllib.parse.urlencode(data).encode() if data else None
            req = urllib.request.Request(url, data=body, headers={"User-Agent": ua or UA, "Accept": "application/json, text/html;q=0.9, */*;q=0.8"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read().decode("utf-8", "replace")
            time.sleep(sleep)
            return json.loads(data) if as_json else data
        except Exception as e:  # noqa
            last = e
            code = getattr(e, "code", None)
            time.sleep(min(60, (2 ** i) * (5 if code == 429 else 1.5)))
    raise last


def sample(name, obj):
    try:
        (SAMPLES / f"{name}.json").write_text(json.dumps(obj, ensure_ascii=False, indent=1)[:60000], encoding="utf-8")
    except Exception:
        pass


def s(v, sep="; "):
    if v is None:
        return ""
    if isinstance(v, list):
        return sep.join(s(x) for x in v if x not in (None, ""))
    return re.sub(r"\s+", " ", str(v)).strip()


def year_of(v):
    m = re.search(r"(1[6-9]\d\d|20[0-3]\d)", s(v))
    return m.group(1) if m else ""


# ---------------------------------------------------------------- search terms
TAMIL_TERMS = [
    "கல்வெட்டு", "கல்வெட்டுகள்", "கல்வெட்டுக்கள்", "கல்வெட்டியல்", "செப்பேடு", "செப்பேடுகள்",
    "நடுகல்", "நடுகற்கள்", "வீரக்கல்", "தொல்லியல்", "தொல்பொருள்", "அகழாய்வு", "அகழ்வாய்வு",
    "அகழ்வைப்பகம்", "பாறை ஓவியம்", "பாறை ஓவியங்கள்", "குகை ஓவியங்கள்", "தமிழ்-பிராமி",
    "தமிழ் பிராமி", "தமிழி", "வட்டெழுத்து", "பட்டயம்", "சாசனம்", "சாசனங்கள்", "நாணயவியல்",
    "பழங்காசுகள்", "பெருங்கற்காலம்", "முதுமக்கள் தாழி", "கீழடி", "ஆதிச்சநல்லூர்", "கொடுமணல்",
    "சிவகளை", "பொருந்தல்", "அழகன்குளம்", "பூம்புகார் அகழாய்வு", "தொல்லெழுத்தியல்",
]
ROMAN_TERMS = [
    "kalvettu", "kalvettukal", "kalvettukkal", "kalvettugal", "kalvetukal", "kalvettiyal",
    "kalveddukal", "seppedu", "seppedugal", "seppedukal", "ceppetu", "ceppetukal", "nadukal",
    "nadukarkal", "natukal", "natukarkal", "tholliyal", "tolliyal", "tholporul", "agazhaivu",
    "akalayvu", "akazhaivu", "akalvaippakam", "paarai oviyangal", "tamil pirami", "tamili",
    "vatteluttu", "vattezhuthu", "sasanam", "pattayam",
]
EN_TERMS = [
    "Tamil inscriptions", "inscriptions Tamil Nadu", "Tamilnadu inscriptions", "Tamil epigraphy",
    "South Indian inscriptions", "South Indian epigraphy", "Epigraphia Indica", "annual report epigraphy",
    "topographical list inscriptions", "district inscriptions Tamil", "temple inscriptions Tamil",
    "Chola inscriptions", "Pandya inscriptions", "Pallava inscriptions", "Pallava copper plates",
    "Chola copper plates", "Pandya copper plates", "copper plates Tamil", "Tamil Brahmi",
    "Tamil-Brahmi inscriptions", "Vatteluttu", "South Indian palaeography", "hero stones Tamil",
    "hero stones Tamil Nadu", "memorial stones South India", "rock art Tamil Nadu",
    "rock paintings Tamil Nadu", "prehistoric rock art South India", "excavations Tamil Nadu",
    "archaeology Tamil Nadu", "archaeology Tamilnadu", "Tamil Nadu archaeology department",
    "megalithic Tamil Nadu", "megaliths South India", "urn burials Tamil Nadu", "Keeladi", "Keezhadi",
    "Adichanallur", "Arikamedu", "Kodumanal", "Porunthal", "Alagankulam", "Kaveripattinam excavation",
    "Poompuhar archaeology", "Sivagalai", "Tamil coins Sangam", "Pudukkottai inscriptions",
    "Travancore archaeological series", "Madras Presidency antiquities", "Kanyakumari inscriptions",
    "Jaina inscriptions Tamil Nadu", "Tamil graffiti potsherds", "Sri Lanka Tamil inscriptions",
    "Annual Report on Indian Epigraphy", "Annual Report on South Indian Epigraphy", "Annual report on epigraphy Madras",
    "Report on epigraphy", "Madras epigraphy", "Government Epigraphist Madras", "Epigraphia Indica",
    "Indian Antiquary", "Epigraphia Carnatica", "South Indian Inscriptions volume", "Pudukkottai State inscriptions",
    "Travancore Archaeological Series", "Archaeological Survey of Southern India", "antiquarian remains Madras",
    "Madras Government Museum bulletin", "Ancient India bulletin", "Indian Archaeology a review",
    "Annual report archaeological department southern circle", "Mackenzie collection", "Tamil Nadu State Department of Archaeology",
    "Madras district gazetteer antiquities", "Vijayanagara inscriptions Tamil", "Nayak inscriptions", "Sethupathi copper plates",
    "Maratha Tanjore inscriptions", "Kongu inscriptions", "Jain inscriptions Tamil", "Buddhist Tamil inscriptions",
    "Grantha script", "Tamil script evolution", "Thanjavur Brihadisvara inscriptions", "Chidambaram inscriptions",
    "Srirangam inscriptions", "Kanchipuram inscriptions", "Tirumalai Tirupati inscriptions", "Madurai inscriptions",
]
SUBJECTS = [
    "Inscriptions, Tamil", "Tamil language--Inscriptions", "Inscriptions--India--Tamil Nadu",
    "Tamil Nadu (India)--Antiquities", "Excavations (Archaeology)--India--Tamil Nadu",
    "Hero stones", "Memorial stones", "Rock paintings--India--Tamil Nadu", "Petroglyphs--India--Tamil Nadu",
    "Copper plates--India", "Brahmi inscriptions", "Coins, Tamil", "Megalithic monuments--India--Tamil Nadu",
    "Inscriptions, Dravidian", "Inscriptions--India, South", "Paleography, Tamil",
]

# ---------------------------------------------------------------- relevance
TA_KW = re.compile(r"(கல்வெட்டு|கல்வெட்டி|செப்பேடு|நடுக(ல்|ற்)|வீரக்கல்|தொல்லியல்|தொல்பொருள்|அகழாய்வு|அகழ்வாய்வு|அகழ்வைப்பக|பாறை ஓவிய|குகை ஓவிய|பிராமி|தமிழி|வட்டெழுத்து|பட்டய|சாசன|நாணய|பழங்காசு|காசுகள்|பெருங்கற்|முதுமக்கள்|தாழி|கீழடி|ஆதிச்சநல்லூர்|கொடுமணல்|சிவகளை|பொருந்தல்|அழகன்குளம்|தொல்லெழுத்|தொல்பழங்கால)")
RO_KW = re.compile(r"(kal[vw]e[td]+[ui]|kalved+u|kalvettiyal|[sc]h?ep+[ae][dt]u|natukal|nadukal|natukar|nadukar|t?hol+iyal|tolliyal|tholporul|agazh|akazh|akal[aā]yvu|akalvaip|vat+e[lz]h?ut+u|pattayam|sasan|sāsan|pirami|piraami)", re.I)
EN_KW = re.compile(r"(inscri|epigraph|palaeograph|paleograph|copper[- ]?plate|hero[- ]?stone|memorial stone|rock art|rock[- ]paint|petroglyph|cave paint|excavat|archaeolog|antiquit|antiquarian|megalith|prehistor|neolithic|palaeolith|urn[- ]burial|dolmen|cairn|brahmi|graffiti|numismat|\bcoins?\b|keeladi|keezhadi|adichanallur|arikamedu|kodumanal|porunthal|alagankulam|kaveripattinam|poompuhar|sivagalai|mangulam|epigraphia|copper plates)", re.I)
CTX = re.compile(r"(tamil|tamizh|madras|south india|southern india|dravid|chola|cola|pandya|pandiya|pallava|chera|pudukkottai|tanjore|thanjavur|madurai|kanchi|tirunelveli|coimbatore|kongu|salem|trichy|tiruchirappalli|vellore|arcot|chingleput|chengalpattu|kanyakumari|travancore|nilgiri|dharmapuri|krishnagiri|ramanathapuram|sivaganga|thoothukudi|tuticorin|pondicherry|puducherry|vijayanagar|nayak|sri lanka|ceylon|jaffna|keeladi|keezhadi|adichanallur|arikamedu|kodumanal|porunthal|alagankulam|kaveripattinam|poompuhar|sivagalai|south indian|uraiyur|korkai|kanchipuram|kanchi|mamallapuram|mahabalipuram|chidambaram|kumbakonam|karur|erode|tiruvannamalai|villupuram|cuddalore|nagapattinam|tiruvarur|virudhunagar|theni|dindigul|namakkal|perambalur|ariyalur|karaikal|gingee|senji|uttaramerur|uttiramerur|tirumalai|tirupati|sittannavasal|kalugumalai|kazhugumalai|vellalur|paiyampalli|attirampakkam|pallavaram|tirukkoyilur|tiruchendur|rameswaram|nilgiris|kerala|malabar|vatteluttu|grantha|kongu|nanjil|chingleput|tamilaham|tamilakam|sangam)", re.I)
NOISE = re.compile(r"(kashmir|bengal|assam|orissa|odisha|nepal|tibet|burma|myanmar|persian|arabic|egypt|greek|rome\b|roman empire|babylon|maya|mesopotam|china|chinese|japan|korea|europe|britain|england|scotland|ireland|america|mexico|africa|cambodia|java|indonesia|bihar|bundelkhand|kalinga|maharashtra|gujarat|rajasthan|punjab|sindh|harappa|mohenjo|mathura|gandhara|afghan|iran|israel|palestine|bible|biblical|assyria|hittite|aegean|etrusc|viking|anglo|celtic|norse|canaan|phoenic|crete|turkey|syria)", re.I)
TAMIL_SCRIPT = re.compile(r"[஀-௿]")


SERIES = re.compile(r"(south[- ]indian inscriptions|epigraphia indica|annual reports? (on|of) (the )?(south[- ]indian |indian )?epigraphy|report on (south[- ]indian |indian )?epigraphy|madras epigraph|government epigraphist|indian antiquary|travancore archaeological|inscriptions of the pudukkottai|pudukkottai state|archaeological survey of southern india|antiquarian remains in the presidency of madras|lists? of inscriptions .*madras|topographical list of (the )?inscriptions|annual report.{0,40}archaeolog.{0,40}(madras|southern circle|south(ern)? india)|madras government museum|bulletin of the madras|ancient india[:,]? bulletin|indian archaeology[ ,:-]+a review|epigraphia carnatica|south indian temple inscriptions|tirumalai.tirupati devasthanam inscriptions)", re.I)


def fold(t):
    """Strip Latin diacritics (ṭ->t, ḷ->l, ā->a) but keep Tamil vowel signs."""
    out = []
    for ch in unicodedata.normalize("NFKD", t or ""):
        if unicodedata.combining(ch) and out and out[-1].isascii():
            continue
        out.append(ch)
    return unicodedata.normalize("NFC", "".join(out)).replace("ḻ", "l").replace("ḷ", "l")


def relevant(title, subjects="", extra=""):
    t = fold(s(title))
    blob = fold(f"{t} {s(subjects)} {s(extra)}")
    if SERIES.search(t) or TA_KW.search(blob) or RO_KW.search(t):
        return True
    if EN_KW.search(blob) and CTX.search(blob) and not NOISE.search(t):
        return True
    return False


def rec(source, sid, title, url, authors="", publisher="", year="", language="", place="",
        subjects="", alt_title="", extra=None):
    r = {"source": source, "source_id": sid, "title": s(title)[:400], "alt_title": s(alt_title)[:300],
         "authors": s(authors)[:300], "publisher": s(publisher)[:200], "place": s(place)[:100],
         "year": year_of(year), "language": s(language)[:40], "subjects": s(subjects)[:400], "url": url,
         "access": "catalogue", "read_url": "", "download_url": ""}
    if extra:
        r.update(extra)
    return r


LIVE = {}


def live(name):
    LIVE[name] = []
    return LIVE[name]


def save(name, rows):
    seen, out = set(), []
    for r in rows:
        k = r["source_id"]
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    (OUT / f"{name}.json").write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")
    log(f"[{name}] saved {len(out)} records")
    return out


# ---------------------------------------------------------------- Internet Archive
def harvest_ia():
    fields = "identifier,title,creator,publisher,date,year,language,subject,collection,description"
    hits = {}
    queries = []
    for t in TAMIL_TERMS:
        queries.append(f'(title:("{t}") OR subject:("{t}"))')
    for t in ROMAN_TERMS:
        queries.append(f"title:({t}*)" if " " not in t else f'title:("{t}")')
    for t in EN_TERMS:
        queries.append(f'(title:("{t}") OR subject:("{t}"))' if len(t.split()) <= 2 else f"title:({t})")
    for t in SUBJECTS:
        queries.append(f'subject:("{t.split("--")[0]}")')
    # whole collections known to be relevant
    for col in ["tamildigitallibrary", "digitallibraryindia", "rmrl", "rojamuthiahlibrary",
                "tamilheritagefoundation", "noolaham", "TamilVirtualAcademy"]:
        queries.append(f"collection:({col}) AND (title:(inscriptions OR epigraphy OR archaeology OR excavation OR copper OR \"hero stone\" OR brahmi OR கல்வெட்டு OR கல்வெட்டுகள் OR தொல்லியல் OR நடுகல் OR செப்பேடு OR அகழாய்வு))")
    for qi, q in enumerate(queries):
        cursor, n, pages = None, 0, 0
        while True:
            params = {"q": f"({q}) AND mediatype:(texts)", "fields": fields, "count": 1000}
            if cursor:
                params["cursor"] = cursor
            url = "https://archive.org/services/search/v1/scrape?" + urllib.parse.urlencode(params)
            try:
                j = get(url, sleep=0.3)
            except Exception as e:
                log("[ia] ERR", q[:60], e)
                break
            if qi == 0 and pages == 0:
                sample("ia_search", j)
            for it in j.get("items", []):
                it["_q"] = q
                hits.setdefault(it["identifier"], it)
                n += 1
            cursor = j.get("cursor")
            pages += 1
            if not cursor or pages >= 20:
                break
        log(f"[ia] {n:5d}  {q[:90]}")
    log(f"[ia] raw unique hits: {len(hits)}")

    rows = live("ia")
    for ident, it in hits.items():
        title = s(it.get("title"))
        if not relevant(title, it.get("subject"), ""):
            continue
        rows.append(rec("Internet Archive", ident, title, f"https://archive.org/details/{ident}",
                        authors=it.get("creator"), publisher=it.get("publisher"),
                        year=it.get("year") or it.get("date"), language=it.get("language"),
                        subjects=it.get("subject"),
                        extra={"collection": s(it.get("collection"))[:200],
                               "description": s(it.get("description"))[:600]}))
    log(f"[ia] relevant: {len(rows)}")

    # enrich every item from the per-item metadata API: author/publisher/year + open-access file links
    BORROW = re.compile(r"(inlibrary|printdisabled|lendinglibrary|browserlending|china_inlibrary)", re.I)
    for r in rows:
        r["access"] = "borrow" if BORROW.search(r.get("collection", "")) else "open"
        r["read_url"] = r["url"] if r["access"] == "open" else ""
    log(f"[ia] enriching {len(rows)} items via metadata API")
    for i, r in enumerate(rows[:9000]):
        try:
            m = get(f"https://archive.org/metadata/{urllib.parse.quote(r['source_id'])}", tries=2, sleep=0.1)
            md = (m or {}).get("metadata", {}) if isinstance(m, dict) else {}
            if i == 0:
                sample("ia_metadata", {k: v for k, v in (m or {}).items() if k != "files"})
            if not r["authors"]:
                for k in ("creator", "author", "editor"):          # NOT 'contributor' (= scanning library)
                    if md.get(k):
                        r["authors"] = s(md[k])[:300]
                        break
            if not r["publisher"] and md.get("publisher"):
                r["publisher"] = s(md["publisher"])[:200]
            if not r["year"]:
                r["year"] = year_of(md.get("year") or md.get("date") or "")
            if not r.get("description") and md.get("description"):
                r["description"] = re.sub(r"<[^>]+>", " ", s(md["description"]))[:600]
            for k in ("isbn", "call_number", "imagecount", "title_alt_script", "alternate_title"):
                if md.get(k):
                    r[k] = s(md[k])[:200]
            restricted = str(md.get("access-restricted-item", "")).lower() == "true" or (m or {}).get("is_dark")
            if restricted or BORROW.search(s(md.get("collection"))):
                r["access"], r["read_url"] = "borrow", ""
            else:
                r["access"], r["read_url"] = "open", r["url"]
                pdfs = [f["name"] for f in (m or {}).get("files", []) if f.get("name", "").lower().endswith(".pdf")]
                pdfs.sort(key=lambda n: (n.endswith("_text.pdf"), len(n)))
                if pdfs:
                    r["download_url"] = f"https://archive.org/download/{urllib.parse.quote(r['source_id'])}/{urllib.parse.quote(pdfs[0])}"
        except Exception as e:
            if i < 5:
                log("[ia] meta ERR", r["source_id"], e)
        if i and i % 500 == 0:
            log(f"[ia] enriched {i}")
    return save("ia", rows)


# ---------------------------------------------------------------- Open Library
def harvest_ol():
    rows = live("ol")
    fl = "key,title,subtitle,author_name,publisher,publish_place,first_publish_year,publish_year,language,subject,isbn,ia,ebook_access"
    qs = [("q", t) for t in ROMAN_TERMS + EN_TERMS + TAMIL_TERMS] + [("subject", t.split("--")[0]) for t in SUBJECTS]
    for kind, t in qs:
        page = 1
        while page <= 5:
            url = "https://openlibrary.org/search.json?" + urllib.parse.urlencode({kind: t, "fields": fl, "limit": 1000, "page": page})
            try:
                j = get(url, sleep=1.0)
            except Exception as e:
                log("[ol] ERR", t, e)
                break
            if not rows and page == 1:
                sample("ol_search", j)
            docs = j.get("docs", [])
            for d in docs:
                title = s(d.get("title")) + (": " + s(d.get("subtitle")) if d.get("subtitle") else "")
                if not relevant(title, d.get("subject", [])[:40]):
                    continue
                ia = d.get("ia") or []
                rows.append(rec("Open Library", d.get("key"), title, "https://openlibrary.org" + s(d.get("key")),
                                authors=d.get("author_name"), publisher=(d.get("publisher") or [])[:3],
                                place=(d.get("publish_place") or [])[:2],
                                year=d.get("first_publish_year") or min(d.get("publish_year") or [0]) or "",
                                language=d.get("language"), subjects=(d.get("subject") or [])[:12],
                                extra={"isbn": s((d.get("isbn") or [])[:2]),
                                       "full_text": f"https://archive.org/details/{ia[0]}" if ia else ""}))
                ea = d.get("ebook_access", "")
                if ia and ea == "public":
                    rows[-1].update(access="open", read_url=f"https://archive.org/details/{ia[0]}")
                elif ia and ea in ("borrowable", "printdisabled"):
                    rows[-1].update(access="borrow")
            log(f"[ol] {kind}={t}: page {page} docs {len(docs)}")
            if len(docs) < 1000:
                break
            page += 1
    return save("ol", rows)


# ---------------------------------------------------------------- Google Books
def harvest_gb():
    rows = live("gb")
    qs = [t for t in ROMAN_TERMS + EN_TERMS + TAMIL_TERMS] + [f'subject:"{t.split("--")[0]}"' for t in SUBJECTS]
    for t in qs:
        for start in range(0, 400, 40):
            url = "https://www.googleapis.com/books/v1/volumes?" + urllib.parse.urlencode(
                {"q": t, "maxResults": 40, "startIndex": start, "printType": "books"})
            try:
                j = get(url, sleep=1.2)
            except Exception as e:
                log("[gb] ERR", t, e)
                break
            if not rows and start == 0:
                sample("gb_search", j)
            items = j.get("items", []) or []
            for it in items:
                v = it.get("volumeInfo", {})
                title = s(v.get("title")) + (": " + s(v.get("subtitle")) if v.get("subtitle") else "")
                if not relevant(title, v.get("categories"), v.get("description", "")[:300]):
                    continue
                isbn = ";".join(x.get("identifier", "") for x in v.get("industryIdentifiers", []) or [])
                rows.append(rec("Google Books", it.get("id"), title,
                                v.get("infoLink") or f"https://books.google.com/books?id={it.get('id')}",
                                authors=v.get("authors"), publisher=v.get("publisher"), year=v.get("publishedDate"),
                                language=v.get("language"), subjects=v.get("categories"),
                                extra={"isbn": isbn, "pages": s(v.get("pageCount")),
                                       "description": s(v.get("description"))[:600]}))
                ai = it.get("accessInfo", {}) or {}
                si = it.get("saleInfo", {}) or {}
                if si.get("buyLink"):
                    rows[-1]["buy_url"] = si["buyLink"]
                if ai.get("viewability") == "ALL_PAGES" or ai.get("publicDomain"):
                    rows[-1].update(access="open", read_url=ai.get("webReaderLink") or rows[-1]["url"],
                                    download_url=(ai.get("pdf") or {}).get("downloadLink", "") or (ai.get("epub") or {}).get("downloadLink", ""))
                elif ai.get("viewability") == "PARTIAL":
                    rows[-1].update(access="preview", read_url=ai.get("webReaderLink") or "")
            if len(items) < 40:
                break
        log(f"[gb] {t}: total so far {len(rows)}")
    return save("gb", rows)


# ---------------------------------------------------------------- Library of Congress
def parse_imprint(cp):
    cp = s(cp)
    place, pub = "", ""
    m = re.match(r"\s*([^:]+?)\s*:\s*([^,]+)", cp)
    if m:
        place, pub = m.group(1).strip(" [].,"), m.group(2).strip(" [].,")
    return place, pub


def harvest_loc():
    rows = live("loc")
    qs = ROMAN_TERMS + EN_TERMS
    for t in qs:
        for sp in range(1, 11):
            url = "https://www.loc.gov/books/?" + urllib.parse.urlencode({"q": t, "fo": "json", "c": 100, "sp": sp})
            try:
                j = get(url, sleep=3.0)
            except Exception as e:
                log("[loc] ERR", t, e)
                break
            if not rows and sp == 1:
                sample("loc_search", j)
            res = j.get("results", []) or []
            for it in res:
                title = s(it.get("title"))
                item = it.get("item") or {}
                subj = it.get("subject") or item.get("subjects") or []
                if not relevant(title, subj, s(it.get("description"))[:300]):
                    continue
                cp = item.get("created_published") or ""
                place, pub = parse_imprint(cp[0] if isinstance(cp, list) and cp else cp)
                authors = it.get("contributor") or item.get("contributors") or []
                rows.append(rec("Library of Congress", s(it.get("id") or it.get("url")), title, s(it.get("url") or it.get("id")),
                                authors=authors, publisher=pub, place=place, year=it.get("date"),
                                language=it.get("language"), subjects=subj[:12],
                                extra={"imprint": s(cp)[:200]}))
                fmts = s(it.get("online_format")).lower()
                if any(x in fmts for x in ("pdf", "image", "online text")):
                    pdf = ""
                    for res_ in it.get("resources") or []:
                        if isinstance(res_, dict) and res_.get("pdf"):
                            pdf = res_["pdf"]; break
                    rows[-1].update(access="open", read_url=rows[-1]["url"], download_url=pdf)
            pag = j.get("pagination") or {}
            if not pag.get("next") or not res:
                break
        log(f"[loc] {t}: total so far {len(rows)}")
    return save("loc", rows)


# ---------------------------------------------------------------- Noolaham
NL_API = "https://noolaham.org/wiki/api.php"


def parse_template(text):
    out = {}
    for m in re.finditer(r"\|\s*([^=|\n]{1,40}?)\s*=\s*([^|\n}]*)", text or ""):
        k, v = m.group(1).strip(), m.group(2).strip()
        v = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", v)
        if v and k not in out:
            out[k] = v
    return out


def harvest_nl():
    titles = {}
    for t in TAMIL_TERMS + ["epigraphy", "inscriptions", "archaeology", "excavation", "hero stone", "Brahmi"]:
        off = 0
        while off < 2000:
            url = NL_API + "?" + urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": t,
                                                         "srlimit": 50, "sroffset": off, "format": "json", "srnamespace": 0})
            try:
                j = get(url, sleep=0.6)
            except Exception as e:
                log("[nl] ERR", t, e)
                break
            if not titles:
                sample("nl_search", j)
            res = j.get("query", {}).get("search", [])
            for r in res:
                titles[r["title"]] = 1
            if "continue" not in j or not res:
                break
            off = j["continue"].get("sroffset", off + 50)
        log(f"[nl] {t}: titles so far {len(titles)}")
    tl = list(titles)
    rows = live("nl")
    log(f"[nl] fetching content of {len(tl)} pages")
    for i in range(0, len(tl), 20):
        batch = tl[i:i + 20]
        try:
            j = get(NL_API, sleep=0.6, data={"action": "query", "prop": "revisions", "rvprop": "content",
                                             "rvslots": "main", "titles": "|".join(batch), "format": "json",
                                             "formatversion": 2})
        except Exception as e:
            log("[nl] content ERR", e)
            continue
        if i == 0:
            sample("nl_content", j)
        for p in j.get("query", {}).get("pages", []):
            revs = p.get("revisions") or []
            if not revs:
                continue
            txt = revs[0].get("slots", {}).get("main", {}).get("content") or revs[0].get("content", "")
            if "{{" not in txt:
                continue
            f = parse_template(txt.split("}}")[0])
            title = f.get("தலைப்பு") or p["title"]
            kind = f.get("வகை", "")
            if not relevant(title, kind, f.get("குறிப்பு", "")):
                continue
            rows.append(rec("Noolaham", p["title"], title,
                            "https://noolaham.org/wiki/index.php/" + urllib.parse.quote(p["title"].replace(" ", "_")),
                            authors=f.get("ஆசிரியர்", ""), publisher=f.get("பதிப்பகம்", ""),
                            year=f.get("பதிப்பு", ""), language=f.get("மொழி", "Tamil"), subjects=kind,
                            extra={"pages": f.get("பக்கங்கள்", "")}))
            pdf = re.search(r"https?://[^\s\]|<>\"']+\.pdf", txt)
            rows[-1].update(access="open", read_url=rows[-1]["url"], download_url=pdf.group(0) if pdf else "")
    return save("nl", rows)


# ---------------------------------------------------------------- OpenAlex (scholarly books worldwide)
def harvest_oa():
    rows = live("oa")
    for t in EN_TERMS + ROMAN_TERMS:
        cursor = "*"
        for _ in range(5):
            url = "https://api.openalex.org/works?" + urllib.parse.urlencode({
                "search": t, "filter": "type:book|monograph|edited-book|reference-book|report", "per-page": 200,
                "cursor": cursor, "mailto": "bibliography@users.noreply.github.com"})
            try:
                j = get(url, sleep=0.3)
            except Exception as e:
                # older filter syntax fallback
                try:
                    j = get(url.replace("type%3Abook%7Cmonograph%7Cedited-book%7Creference-book%7Creport", "type%3Abook"), sleep=0.3)
                except Exception as e2:
                    log("[oa] ERR", t, e2)
                    break
            if not rows and cursor == "*":
                sample("oa_search", j)
            for w in j.get("results", []) or []:
                title = s(w.get("display_name") or w.get("title"))
                concepts = [c.get("display_name", "") for c in (w.get("concepts") or w.get("topics") or [])][:10]
                if not relevant(title, concepts):
                    continue
                authors = [a.get("author", {}).get("display_name", "") for a in w.get("authorships") or []]
                loc = w.get("primary_location") or {}
                src = loc.get("source") or {}
                pub = src.get("host_organization_name") or w.get("publisher") or ""
                oa = w.get("open_access") or {}
                best = w.get("best_oa_location") or {}
                r = rec("OpenAlex", w.get("id"), title, w.get("doi") or loc.get("landing_page_url") or w.get("id"),
                        authors=authors, publisher=pub, year=w.get("publication_year"), language=w.get("language"),
                        subjects=concepts)
                if oa.get("is_oa"):
                    r.update(access="open", read_url=oa.get("oa_url") or best.get("landing_page_url") or "",
                             download_url=best.get("pdf_url") or "")
                rows.append(r)
            cursor = (j.get("meta") or {}).get("next_cursor")
            if not cursor or not j.get("results"):
                break
        log(f"[oa] {t}: total so far {len(rows)}")
    return save("oa", rows)


# ---------------------------------------------------------------- DOAB (open-access academic books)
def harvest_doab():
    rows = live("doab")
    for t in EN_TERMS[:40] + ["Tamil", "Tamil Nadu archaeology", "South India epigraphy", "Chola", "Pallava", "Pandya"]:
        j = None
        for host in ("https://directory.doabooks.org", "https://library.oapen.org"):
            url = host + "/rest/search?" + urllib.parse.urlencode({"query": t, "expand": "metadata,bitstreams", "limit": 100})
            try:
                j = get(url, sleep=0.8, ua=BROWSER_UA, tries=2)
                break
            except Exception as e:
                log("[doab] ERR", host[8:30], t, e)
        if j is None:
            continue
        if not rows:
            sample("doab_search", j[:3] if isinstance(j, list) else j)
        for it in j if isinstance(j, list) else []:
            md = {}
            for m in it.get("metadata", []) or []:
                md.setdefault(m.get("key", ""), []).append(m.get("value", ""))
            pick = lambda *ks: next((md[k] for k in ks if md.get(k)), [])
            title = s(pick("dc.title"))
            if not relevant(title, pick("dc.subject.other", "dc.subject.classification", "dc.subject"), s(pick("dc.description.abstract"))[:400]):
                continue
            handle = it.get("handle", "")
            dl = s(pick("oapen.identifier.downloadUrl", "dc.identifier.uri"))
            rows.append(rec("DOAB", handle or title, title, f"https://directory.doabooks.org/handle/{handle}" if handle else dl,
                            authors=pick("dc.contributor.author", "dc.contributor.editor", "dc.creator"),
                            publisher=pick("publisher.name", "dc.publisher", "oapen.relation.isPublishedBy"),
                            year=s(pick("dc.date.issued")), language=s(pick("dc.language")),
                            subjects=pick("dc.subject.other"),
                            extra={"access": "open", "read_url": f"https://directory.doabooks.org/handle/{handle}" if handle else dl,
                                   "download_url": dl if dl.lower().endswith(".pdf") or "download" in dl.lower() else "",
                                   "isbn": s(pick("oapen.identifier.isbn", "dc.identifier.isbn"))}))
        log(f"[doab] {t}: total so far {len(rows)}")
    return save("doab", rows)


# ---------------------------------------------------------------- Tamil Wikisource scanned books (Index pages)
def harvest_ws():
    rows_en = []
    api_en = "https://en.wikisource.org/w/api.php"
    for t in ["South Indian Inscriptions", "Epigraphia Indica", "Indian Antiquary", "Tamil inscriptions", "Madras epigraphy", "Pudukkottai inscriptions", "Travancore Archaeological Series"]:
        for ns in (0, 106):
            try:
                j = get(api_en + "?" + urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": t, "srnamespace": ns, "srlimit": 50, "format": "json"}), sleep=0.4)
            except Exception as e:
                log("[ws-en] ERR", t, e); continue
            for r in j.get("query", {}).get("search", []):
                ti = r["title"]; book = re.sub(r"\.(pdf|djvu)$", "", ti.split(":", 1)[-1], flags=re.I)
                if relevant(book):
                    u = "https://en.wikisource.org/wiki/" + urllib.parse.quote(ti.replace(" ", "_"))
                    rows_en.append(rec("English Wikisource", ti, book, u, extra={"access": "open", "read_url": u}))
    api = "https://ta.wikisource.org/w/api.php"
    titles = {}
    for t in TAMIL_TERMS + ["inscriptions", "epigraphy", "archaeology"]:
        for ns in (0, 252, 250):  # main, Index (அட்டவணை), Page
            url = api + "?" + urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": t, "srnamespace": ns,
                                                      "srlimit": 50, "format": "json"})
            try:
                j = get(url, sleep=0.4)
            except Exception as e:
                log("[ws] ERR", t, e)
                continue
            if not titles:
                sample("ws_search", j)
            for r in j.get("query", {}).get("search", []):
                ti = r["title"]
                if ns == 250:   # Page:Book.pdf/123 -> Index:Book.pdf
                    ti = "அட்டவணை:" + ti.split(":", 1)[-1].split("/")[0]
                titles[ti] = 1
    rows = []
    for ti in titles:
        name = ti.split(":", 1)[-1]
        book = re.sub(r"\.(pdf|djvu)$", "", name, flags=re.I)
        if not relevant(book):
            continue
        u = "https://ta.wikisource.org/wiki/" + urllib.parse.quote(ti.replace(" ", "_"))
        rows.append(rec("Tamil Wikisource", ti, book, u, language="Tamil",
                        extra={"access": "open", "read_url": u}))
    return save("ws", rows + rows_en)


# ---------------------------------------------------------------- HathiTrust (full catalogue file; old colonial & govt volumes)
HT_COLS = ["htid", "access", "rights", "ht_bib_key", "description", "source", "source_bib_num", "oclc_num", "isbn", "issn",
           "lccn", "title", "imprint", "rights_reason_code", "rights_timestamp", "us_gov_doc_flag", "rights_date_used",
           "pub_place", "lang", "bib_fmt", "collection_code", "content_provider_code", "responsible_entity_code",
           "digitization_agent_code", "access_profile_code", "author"]
HT_PRE = re.compile(r"(inscri|epigraph|kalvet|kalvett|natukal|nadukal|ceppet|seppe|tolliyal|tholliyal|tolporul|akalayvu|archaeolog|antiquit|antiquar|excavat|copper.?plate|hero.?stone|memorial stone|rock (art|paint)|petroglyph|megalith|prehistor|brahmi|vatteluttu|palaeograph|paleograph|numismat|coins|indian antiquary|tamil|madras|chola|cola|pandya|pallava|pudukkottai|travancore)", re.I)
HT_PUB = re.compile(r"(dept\.? of archaeology|department of archaeology|tolliyal|tholliyal|tolporul|archaeological survey|government epigraphist|superintendent,? government press|govt\.? press)", re.I)


def harvest_ht():
    rows = live("ht")
    lst = get("https://www.hathitrust.org/files/hathifiles/hathi_file_list.json")
    sample("ht_filelist", lst[:5] if isinstance(lst, list) else lst)
    fulls = sorted([f for f in lst if f.get("full") in (True, "true", 1) or "full" in f.get("filename", "")],
                   key=lambda f: f.get("filename", ""))
    f = fulls[-1]
    url = f.get("url") or ("https://www.hathitrust.org/files/hathifiles/" + f["filename"])
    log(f"[ht] streaming {url} ({f.get('size')} bytes)")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    n = 0
    with urllib.request.urlopen(req, timeout=300) as resp:
        gz = gzip.GzipFile(fileobj=resp)
        for raw in io.TextIOWrapper(gz, encoding="utf-8", errors="replace"):
            n += 1
            if n % 2000000 == 0:
                log(f"[ht] scanned {n:,} lines, kept {len(rows)}")
            if not HT_PRE.search(raw):
                continue
            c = raw.rstrip("\n").split("\t")
            if len(c) < 26:
                continue
            d = dict(zip(HT_COLS, c))
            title, imprint = d["title"], d["imprint"]
            ftitle, fimp = fold(title), fold(imprint)
            if not (relevant(title, "", d["description"]) or
                    (HT_PUB.search(fimp) and (RO_KW.search(ftitle) or EN_KW.search(ftitle)) and
                     re.search(r"(madras|tamil|chennai|thanjavur|tanjore|pudukkottai|trivandrum|madurai)", fimp + " " + ftitle, re.I))):
                continue
            place, pub = "", ""
            m = re.match(r"\s*([^:;]+?)\s*[:;]\s*(.+?)(,\s*\[?c?\d{4}.*)?$", imprint)
            if m:
                place, pub = m.group(1).strip(" [].,"), m.group(2).strip(" [].,")
            else:
                pub = re.sub(r",?\s*\[?\d{4}.*$", "", imprint).strip(" [].,")
                parts = pub.split(",", 1)
                if len(parts) == 2 and len(parts[0].split()) <= 2:
                    place, pub = parts[0].strip(), parts[1].strip()
            title = title.strip(" /:;,.")
            vol = d["description"].strip()
            rights = d["rights"]
            open_ = d["access"] == "allow" and rights not in ("pdus",)
            r = rec("HathiTrust", d["htid"], title + (f" — {vol}" if vol else ""),
                    f"https://catalog.hathitrust.org/Record/{d['ht_bib_key']}",
                    authors=d["author"].strip(" ,."), publisher=pub, place=place,
                    year=d["rights_date_used"] if d["rights_date_used"] not in ("", "9999") else imprint,
                    language=d["lang"], extra={"isbn": d["isbn"], "series": vol, "imprint": imprint[:200]})
            if d["access"] == "allow":
                r.update(access="open" if open_ else "open-us", read_url=f"https://babel.hathitrust.org/cgi/pt?id={d['htid']}")
            else:
                r.update(access="catalogue")
            rows.append(r)
    log(f"[ht] scanned {n:,} lines total")
    return save("ht", rows)


# ---------------------------------------------------------------- Wikimedia Commons scanned PDFs / DjVu
def harvest_cm():
    rows = live("cm")
    api = "https://commons.wikimedia.org/w/api.php"
    terms = (["South Indian Inscriptions", "Epigraphia Indica", "Annual report epigraphy", "Indian Antiquary",
              "Tamil inscriptions", "Travancore Archaeological Series", "Pudukkottai inscriptions", "Madras archaeology",
              "copper plates Tamil", "Tamil Brahmi", "hero stone Tamil", "Tamil Nadu archaeology", "Archaeological Survey of Southern India"]
             + TAMIL_TERMS)
    seen = {}
    for t in terms:
        for ft in ("pdf", "djvu"):
            off = 0
            while off < 500:
                url = api + "?" + urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": f"{t} filetype:{ft}",
                                                          "srnamespace": 6, "srlimit": 50, "sroffset": off, "format": "json"})
                try:
                    j = get(url, sleep=0.4)
                except Exception as e:
                    log("[cm] ERR", t, e)
                    break
                if not seen:
                    sample("cm_search", j)
                res = j.get("query", {}).get("search", [])
                for r in res:
                    seen[r["title"]] = 1
                if "continue" not in j or not res:
                    break
                off = j["continue"].get("sroffset", off + 50)
        log(f"[cm] {t}: files so far {len(seen)}")
    for ti in seen:
        name = ti.split(":", 1)[-1]
        book = re.sub(r"[_]", " ", re.sub(r"\.(pdf|djvu)$", "", name, flags=re.I))
        if not relevant(book):
            continue
        page = "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(ti.replace(" ", "_"))
        rows.append(rec("Wikimedia Commons", ti, book, page, year=book,
                        extra={"access": "open", "read_url": page,
                               "download_url": "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(name.replace(" ", "_"))}))
    return save("cm", rows)


# ---------------------------------------------------------------- SII / Epigraphia Indica online texts (index pages)
def robots_ok(url):
    try:
        u = urllib.parse.urlparse(url)
        rp = urllib.robotparser.RobotFileParser(f"{u.scheme}://{u.netloc}/robots.txt")
        rp.read()
        return rp.can_fetch(UA, url)
    except Exception:
        return True


def harvest_wi():
    rows = live("wi")
    base = "https://www.whatisindia.com/inscriptions/"
    if not robots_ok(base):
        log("[wi] robots.txt disallows - skipped")
        return save("wi", rows)
    html = ""
    for b in (base, base.replace("https://", "http://"), base.replace("www.", "")):
        try:
            html = get(b, as_json=False, ua=BROWSER_UA, tries=2)
            base = b
            break
        except Exception as e:
            log("[wi] ERR", b, e)
    for href, text in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, flags=re.S | re.I):
        text = re.sub(r"<[^>]+>|\s+", " ", text).strip()
        if not re.search(r"(vol|volume|part|epigraphia|inscriptions)", text + href, re.I):
            continue
        u = urllib.parse.urljoin(base, href)
        if "whatisindia.com/inscriptions/" not in u or u.rstrip("/") == base.rstrip("/"):
            continue
        series = "South Indian Inscriptions" if "south_indian" in u else ("Epigraphia Indica" if "epigraph" in u else "")
        title = f"{series} — {text}" if series and series.lower() not in text.lower() else text
        rows.append(rec("Online text", u, title, u, year=re.search(r"(18|19)\d\d", u).group(0) if re.search(r"(18|19)\d\d", u) else "",
                        extra={"access": "open", "read_url": u, "series": text}))
    return save("wi", rows)


# ---------------------------------------------------------------- user-supplied sources (Drive folders, blogs, govt sites)
BOOK_EXT = re.compile(r"\.(pdf|djvu|epub|doc|docx)(\?|$)", re.I)


def drive_id(url):
    m = re.search(r"/folders/([\w-]{10,})", url) or re.search(r"[?&]id=([\w-]{10,})", url)
    return m.group(1) if m else ""


def harvest_xs():
    rows = live("xs")
    src_file = ROOT / "data" / "extra_sources.txt"
    if not src_file.exists():
        return save("xs", rows)
    entries = []
    for line in src_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        entries.append((parts[0], parts[1] if len(parts) > 1 else ""))
    log(f"[xs] {len(entries)} user sources")

    def drive_folder(fid, label, depth=0, path=""):
        if depth > 4:
            return
        try:
            html = get(f"https://drive.google.com/embeddedfolderview?id={fid}", as_json=False, sleep=0.8)
        except Exception as e:
            log("[xs] drive ERR", fid, e)
            return
        if depth == 0:
            (SAMPLES / f"xs_drive_{fid[:8]}.html").write_text(html[:40000], encoding="utf-8")
        for m in re.finditer(r'<div class="flip-entry" id="entry-([\w-]+)".*?<div class="flip-entry-title">(.*?)</div>', html, flags=re.S):
            eid, name = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
            block = html[m.start(): m.start() + 1500]
            if "/folders/" in block or "embeddedfolderview" in block:
                drive_folder(eid, label, depth + 1, f"{path}/{name}")
                continue
            title = re.sub(r"\.(pdf|djvu|epub|docx?|zip|rar)$", "", name, flags=re.I).replace("_", " ").strip()
            if not title:
                continue
            view = f"https://drive.google.com/file/d/{eid}/view"
            rows.append(rec("Shared drive", eid, title, view, year=title,
                            extra={"access": "open", "read_url": view,
                                   "download_url": f"https://drive.google.com/uc?export=download&id={eid}",
                                   "notes": f"{label} {path}".strip(), "found_by": f"list:{label or 'drive'}"}))

    def page_links(url, label):
        if not robots_ok(url):
            log("[xs] robots.txt disallows", url)
            return
        try:
            html = get(url, as_json=False, sleep=1.0)
        except Exception as e:
            log("[xs] page ERR", url, e)
            return
        page_title = re.sub(r"<[^>]+>|\s+", " ", (re.search(r"<title>(.*?)</title>", html, re.S | re.I) or [None, ""])[1]).strip()
        n = 0
        for href, text in re.findall(r'<a[^>]+href="([^"#]+)"[^>]*>(.*?)</a>', html, flags=re.S | re.I):
            text = re.sub(r"<[^>]+>|\s+", " ", text).strip()
            u = urllib.parse.urljoin(url, href)
            is_file = bool(BOOK_EXT.search(u)) or "drive.google.com/file/" in u or "docs.google.com" in u
            if not text or len(text) < 4:
                text = urllib.parse.unquote(u.rstrip("/").split("/")[-1])
            if not (is_file or relevant(text)):
                continue
            if "drive.google.com" in u and drive_id(u) and "/folders/" in u:
                drive_folder(drive_id(u), label or page_title)
                continue
            title = re.sub(r"\.(pdf|djvu|epub|docx?)$", "", text, flags=re.I).strip()
            r = rec("Listed site", u, title, url, year=title,
                    extra={"notes": (label or page_title)[:120], "found_by": f"list:{label or page_title}"[:120]})
            if is_file:
                r.update(access="open", read_url=u, download_url=u if BOOK_EXT.search(u) else "")
            rows.append(r)
            n += 1
        log(f"[xs] {url}: {n} links")

    for url, label in entries:
        try:
            if "drive.google.com" in url and drive_id(url):
                if "/file/d/" in url:
                    fid = re.search(r"/file/d/([\w-]+)", url).group(1)
                    rows.append(rec("Shared drive", fid, label or fid, url, extra={"access": "open", "read_url": url,
                                    "download_url": f"https://drive.google.com/uc?export=download&id={fid}", "found_by": "list:drive"}))
                else:
                    drive_folder(drive_id(url), label)
            elif ".blogspot." in url or "blogger.com" in url:
                base = re.match(r"(https?://[^/]+)", url).group(1)
                start = 1
                while start < 5000:
                    try:
                        j = get(f"{base}/feeds/posts/default?alt=json&max-results=150&start-index={start}", sleep=1.0)
                    except Exception as e:
                        log("[xs] blogger feed ERR", base, e)
                        break
                    entries_ = j.get("feed", {}).get("entry", []) or []
                    for e in entries_:
                        post_url = next((l["href"] for l in e.get("link", []) if l.get("rel") == "alternate"), base)
                        body = e.get("content", {}).get("$t", "") or e.get("summary", {}).get("$t", "")
                        for href, text in re.findall(r'<a[^>]+href="([^"#]+)"[^>]*>(.*?)</a>', body, flags=re.S | re.I):
                            text = re.sub(r"<[^>]+>|\s+", " ", text).strip()
                            is_file = bool(BOOK_EXT.search(href)) or "drive.google.com" in href
                            if "/folders/" in href and drive_id(href):
                                drive_folder(drive_id(href), label or base)
                                continue
                            if is_file or relevant(text):
                                ptitle = e.get("title", {}).get("$t", "")
                                t = text if len(text) > 5 and not re.match(r"(?i)(download|click here|pdf|link)$", text) else ptitle
                                r = rec("Listed site", href, t, post_url, year=t,
                                        extra={"notes": ptitle[:120], "found_by": f"list:{label or base}"[:120]})
                                if is_file:
                                    r.update(access="open", read_url=href, download_url=href if BOOK_EXT.search(href) else "")
                                rows.append(r)
                    if len(entries_) < 150:
                        break
                    start += 150
                log(f"[xs] blog {base}: total {len(rows)}")
            else:
                page_links(url, label)
        except Exception as e:
            log("[xs] ERR", url, e)
    return save("xs", rows)


# ---------------------------------------------------------------- authors & publishers
# (search names, tokens that must appear in the record's author field)
AUTHORS = [
    (["R. Nagaswamy", "Nagaswamy", "இரா. நாகசாமி", "நாகசாமி"], ["nagasw", "nagasam", "நாகசாமி"]),
    (["Natana Kasinathan", "Natana. Kasinathan", "நடன. காசிநாதன்", "நடன காசிநாதன்"], ["kasinath", "kacinat", "காசிநாதன்"]),
    (["Iravatham Mahadevan", "ஐராவதம் மகாதேவன்"], ["iravatham", "mahadevan, iravatham", "ஐராவதம்"]),
    (["Mayilai Seeni Venkatasamy", "Venkatasami, Mayilai Cini", "மயிலை சீனி. வேங்கடசாமி"], ["venkatasam", "venkatacam", "வேங்கடசாமி"]),
    (["Y. Subbarayalu", "Subbarayalu", "எ. சுப்பராயலு"], ["subbarayalu", "cuppirayalu", "சுப்பராயலு"]),
    (["S. Rajavelu", "சு. இராசவேலு", "சு. ராஜவேலு"], ["rajavelu", "racavelu", "இராசவேலு", "ராஜவேலு"]),
    (["V. Vedachalam", "வெ. வேதாசலம்"], ["vedachalam", "vetacalam", "வேதாசலம்"]),
    (["C. Santhalingam", "சொ. சாந்தலிங்கம்"], ["santhalingam", "cantalinkam", "சாந்தலிங்கம்"]),
    (["K. Rajan archaeology", "கா. ராஜன்"], ["rajan, k", "k. rajan", "k.rajan", "கா. ராஜன்", "கா. இராசன்"]),
    (["Pulavar Se. Rasu", "Se. Rasu", "புலவர் செ. இராசு", "செ. இராசு"], ["se. rasu", "se.rasu", "rasu, se", "செ. இராசு", "செ.இராசு"]),
    (["T. V. Sadasiva Pandarathar", "சதாசிவ பண்டாரத்தார்"], ["pandarathar", "pantarattar", "பண்டாரத்தார்"]),
    (["Kudavayil Balasubramanian", "குடவாயில் பாலசுப்பிரமணியன்"], ["kudavayil", "kutavayil", "குடவாயில்"]),
    (["R. Kalaikkovan", "இரா. கலைக்கோவன்"], ["kalaikkovan", "kalaikovan", "கலைக்கோவன்"]),
    (["R. Poongundran", "இரா. பூங்குன்றன்"], ["poongundran", "poonkuntran", "punkunran", "பூங்குன்றன்"]),
    (["S. Rajagopal epigraphy", "சு. இராசகோபால்"], ["rajagopal, s", "s. rajagopal", "s.rajagopal", "இராசகோபால்"]),
    (["A. Padmavathy", "அ. பத்மாவதி"], ["padmavath", "patmavati", "பத்மாவதி"]),
    (["N. Marxia Gandhi", "ந. மார்க்சியகாந்தி"], ["marxia", "marxiagandhi", "மார்க்சிய"]),
    (["K. Sridharan archaeology", "க. ஸ்ரீதரன்"], ["sridharan, k", "k. sridharan", "k.sridharan", "ஸ்ரீதரன்"]),
    (["T. S. Sridhar", "தி. ஸ்ரீ. ஸ்ரீதர்"], ["t. s. sridhar", "t.s. sridhar", "sridhar, t", "ஸ்ரீதர்"]),
    (["T. N. Subramanian epigraphy", "தி. நா. சுப்பிரமணியன்"], ["t. n. subramanian", "subramanian, t. n", "தி. நா. சுப்பிரமணியன்"]),
    (["R. Sivanantham", "இரா. சிவானந்தம்"], ["sivanantham", "civanantam", "சிவானந்தம்"]),
    (["K. G. Krishnan epigraphy"], ["k. g. krishnan", "krishnan, k. g"]),
    (["K. V. Raman archaeology"], ["k. v. raman", "raman, k. v"]),
    (["A. Ekambaranathan"], ["ekambaranathan"]),
    (["K. A. Nilakanta Sastri"], ["nilakanta"]),
    (["Noboru Karashima"], ["karashima"]),
    (["T. V. Mahalingam"], ["mahalingam, t", "t. v. mahalingam"]),
    (["R. Krishnamurthy coins", "இரா. கிருஷ்ணமூர்த்தி"], ["krishnamurthy, r", "r. krishnamurthy", "கிருஷ்ணமூர்த்தி"]),
    (["Ko. Vijayavenugopal", "கோ. விஜயவேணுகோபால்"], ["vijayavenugopal", "விஜயவேணுகோபால்"]),
    (["K. T. Gandhirajan", "க.த. காந்திராஜன்"], ["gandhirajan", "காந்திராஜன்"]),
    (["Shanti Pappu"], ["pappu, shanti", "shanti pappu"]),
    (["V. Selvakumar archaeology"], ["selvakumar, v", "v. selvakumar"]),
    (["K. Indrapala", "கா. இந்திரபாலா"], ["indrapala", "இந்திரபாலா"]),
    (["S. Pathmanathan", "சி. பத்மநாதன்"], ["pathmanathan", "பத்மநாதன்"]),
    (["P. Pushparatnam", "ப. புஷ்பரட்ணம்"], ["pushparatnam", "puspparatnam", "புஷ்பரட்ணம்", "புஷ்பரத்தினம்"]),
    (["M. Rajamanickam", "மா. இராசமாணிக்கனார்"], ["rajamanick", "இராசமாணிக்க"]),
    (["S. Ramachandran epigraphy", "செ. இராமச்சந்திரன்"], ["s. ramachandran", "இராமச்சந்திரன்"]),
    (["K. S. Sampath", "கே. எஸ். சம்பத்"], ["k.s.sampath", "k. s. sampath", "சம்பத்"]),
    (["E. Hultzsch"], ["hultzsch"]),
    (["V. Venkayya"], ["venkayya"]),
    (["H. Krishna Sastri"], ["krishna sastri"]),
    (["C. Sivaramamurti"], ["sivaramamurti"]),
    (["R. Champakalakshmi"], ["champakalakshmi"]),
    (["Leslie C. Orr"], ["orr, leslie", "leslie c. orr", "leslie orr"]),
    (["James Burgess"], ["burgess, james", "james burgess", "burgess, j"]),
    (["Robert Sewell"], ["sewell, robert", "robert sewell", "sewell, r"]),
    (["A. C. Burnell"], ["burnell"]),
    (["V. Rangacharya"], ["rangacharya", "rangachari"]),
    (["T. A. Gopinatha Rao"], ["gopinatha rao"]),
    (["K. V. Subrahmanya Aiyar"], ["subrahmanya aiyar", "subramanya aiyar", "subrahmanya ayyar"]),
    (["A. S. Ramanatha Ayyar"], ["ramanatha ayyar", "ramanatha aiyar"]),
    (["G. V. Srinivasa Rao"], ["srinivasa rao, g", "g. v. srinivasa rao"]),
    (["K. R. Srinivasan archaeology"], ["srinivasan, k. r", "k. r. srinivasan"]),
    (["S. R. Balasubrahmanyam"], ["balasubrahmanyam", "balasubramanyam"]),
    (["V. Venkatasubba Ayyar"], ["venkatasubba"]),
    (["C. Minakshi"], ["minakshi, c", "c. minakshi"]),
    (["D. C. Sircar"], ["sircar, d", "d. c. sircar", "sircar, dines"]),
    (["N. Subrahmanian"], ["subrahmanian, n", "n. subrahmanian"]),
    (["R. Tirumalai"], ["tirumalai, r", "r. tirumalai"]),
    (["S. Krishnaswami Aiyangar"], ["krishnaswami aiyangar", "krishnaswamy aiyangar"]),
    (["M. Raghava Iyengar", "மு. இராகவையங்கார்"], ["raghava iyengar", "raghava aiyangar", "இராகவையங்கார்"]),
    (["Alexander Rea"], ["rea, alexander", "alexander rea"]),
    (["Robert Bruce Foote"], ["foote, robert", "r. bruce foote", "robert bruce foote"]),
    (["A. H. Longhurst"], ["longhurst"]),
    (["K. V. Soundara Rajan"], ["soundara rajan", "soundararajan, k"]),
    (["T. N. Ramachandran"], ["ramachandran, t. n", "t. n. ramachandran"]),
    (["Gift Siromoney"], ["siromoney"]),
    (["Burton Stein"], ["stein, burton", "burton stein"]),
    (["James Heitzman"], ["heitzman"]),
    (["Whitney Cox"], ["cox, whitney", "whitney cox"]),
    (["Vimala Begley"], ["begley"]),
    (["P. Shanmugam"], ["shanmugam, p", "p. shanmugam"]),
    (["S. Gurumurthy"], ["gurumurthy"]),
    (["Avvai Duraisamy Pillai", "ஔவை துரைசாமிப் பிள்ளை"], ["duraisam", "துரைசாமி"]),
    (["M. Arunachalam", "மு. அருணாசலம்"], ["arunachalam, m", "m. arunachalam", "அருணாசலம்"]),
    (["K. K. Pillay"], ["pillay, k. k", "k. k. pillay"]),
    (["S. Vaiyapuri Pillai", "எஸ். வையாபுரிப் பிள்ளை"], ["vaiyapuri", "வையாபுரி"]),
    (["N. Karashima"], ["karashima"]),
    (["C. Sivaramamurti"], ["sivaramamurti"]),
    (["R. Gopalan"], ["gopalan, r", "r. gopalan"]),
    (["T. Gopalan epigraphy", "தி. கோபாலன்"], ["t. gopalan", "gopalan, t"]),
    (["M. Senthilselvakumaran"], ["senthilselvakumaran"]),
    (["V. Veeraraghavan", "வீரராகவன்"], ["veeraraghavan", "veeraragavan", "வீரராகவன்"]),
    (["Pon. Venkatesan", "பொன். வெங்கடேசன்"], ["venkatesan, pon", "pon venkatesan", "பொன். வெங்கடேசன்"]),
    (["Kalaikkovan", "இரா. கலைக்கோவன்"], ["kalaikkovan", "கலைக்கோவன்"]),
    (["Su. Thiyagarajan archaeology"], ["thiyagarajan"]),
    (["S. Vasanthi archaeology", "சு. வசந்தி"], ["vasanthi", "வசந்தி"]),
    (["R. Vasanthakalyani"], ["vasanthakalyani"]),
    (["Seetharam Gurumurthy", "சீதாராம் குருமூர்த்தி"], ["seetharam", "சீதாராம்"]),
    (["T. Arunraj archaeology"], ["arunraj"]),
    (["Amarnath Ramakrishna"], ["amarnath"]),
]
PUBLISHERS = [
    ("Tamil Nadu State Department of Archaeology", ["archaeology", "tolliyal", "tholliyal", "தொல்லியல்", "தொல்பொருள்"], True),
    ("தமிழ்நாடு அரசு தொல்லியல் துறை", ["தொல்லியல்", "தொல்பொருள்"], True),
    ("Department of Archaeology Government of Tamil Nadu", ["archaeology"], True),
    ("Tamil University Thanjavur", ["tamil university", "tamil univ", "தமிழ்ப் பல்கலைக்கழகம்"], False),
    ("தமிழ்ப் பல்கலைக்கழகம்", ["தமிழ்ப் பல்கலைக்கழகம்"], False),
    ("Pandya Nadu Centre for Historical Research", ["pandya nadu", "pandyanadu", "பாண்டிய நாடு"], True),
    ("Tamilnadu Archaeological Society", ["archaeological society", "தொல்லியல் கழகம்"], True),
    ("தமிழகத் தொல்லியல் கழகம்", ["தொல்லியல் கழகம்"], True),
    ("Tamil Heritage Foundation", ["heritage foundation", "மரபு அறக்கட்டளை"], False),
    ("International Institute of Tamil Studies", ["tamil studies", "தமிழாராய்ச்சி"], False),
    ("Central Institute of Classical Tamil", ["classical tamil", "செம்மொழி"], False),
    ("Institute of Asian Studies Chennai", ["asian studies"], False),
    ("Archaeological Survey of India", ["archaeological survey"], False),
    ("Government Museum Chennai", ["government museum", "museum"], False),
]


def name_match(authors, tokens):
    a = s(authors).lower()
    a2 = re.sub(r"[\s.]+", "", a)
    return any(t.lower() in a or re.sub(r"[\s.]+", "", t.lower()) in a2 for t in tokens)


def harvest_au():
    rows = live("au")

    def add(src, sid, title, url, found_by, **kw):
        rows.append(rec(src, sid, title, url, extra={"found_by": found_by}, **kw))

    def ia_query(q, keep):
        cursor, n = None, 0
        for _ in range(5):
            params = {"q": f"({q}) AND mediatype:(texts)", "fields": "identifier,title,creator,publisher,date,year,language,subject,collection", "count": 1000}
            if cursor:
                params["cursor"] = cursor
            try:
                j = get("https://archive.org/services/search/v1/scrape?" + urllib.parse.urlencode(params), sleep=0.3)
            except Exception as e:
                log("[au/ia] ERR", q, e)
                return n
            for it in j.get("items", []):
                if keep(it):
                    add("Internet Archive", it["identifier"], it.get("title"), f"https://archive.org/details/{it['identifier']}",
                        q, authors=it.get("creator"), publisher=it.get("publisher"), year=it.get("year") or it.get("date"),
                        language=it.get("language"), subjects=it.get("subject"))
                    borrow = re.search(r"(inlibrary|printdisabled|lendinglibrary)", s(it.get("collection")), re.I)
                    rows[-1].update(access="borrow" if borrow else "open", read_url="" if borrow else rows[-1]["url"])
                    n += 1
            cursor = j.get("cursor")
            if not cursor:
                break
        return n

    def ol_query(params, keep, label):
        n = 0
        try:
            j = get("https://openlibrary.org/search.json?" + urllib.parse.urlencode({**params, "limit": 1000,
                    "fields": "key,title,subtitle,author_name,publisher,publish_place,first_publish_year,publish_year,language,subject,isbn,ia,ebook_access"}), sleep=1.0)
        except Exception as e:
            log("[au/ol] ERR", params, e)
            return 0
        for d in j.get("docs", []):
            if keep(d):
                title = s(d.get("title")) + (": " + s(d.get("subtitle")) if d.get("subtitle") else "")
                ia = d.get("ia") or []
                add("Open Library", d.get("key"), title, "https://openlibrary.org" + s(d.get("key")), label,
                    authors=d.get("author_name"), publisher=(d.get("publisher") or [])[:3], place=(d.get("publish_place") or [])[:2],
                    year=d.get("first_publish_year") or "", language=d.get("language"), subjects=(d.get("subject") or [])[:12])
                if ia:
                    rows[-1]["full_text"] = f"https://archive.org/details/{ia[0]}"
                    if d.get("ebook_access") == "public":
                        rows[-1].update(access="open", read_url=rows[-1]["full_text"])
                n += 1
        return n

    def gb_query(q, keep, label):
        n = 0
        for start in range(0, 200, 40):
            try:
                j = get("https://www.googleapis.com/books/v1/volumes?" + urllib.parse.urlencode({"q": q, "maxResults": 40, "startIndex": start}), sleep=1.2)
            except Exception as e:
                log("[au/gb] ERR", q, e)
                break
            items = j.get("items") or []
            for it in items:
                v = it.get("volumeInfo", {})
                d = {"author_name": v.get("authors"), "publisher": [v.get("publisher") or ""], "title": v.get("title"), "subject": v.get("categories")}
                if keep(d):
                    title = s(v.get("title")) + (": " + s(v.get("subtitle")) if v.get("subtitle") else "")
                    add("Google Books", it.get("id"), title, v.get("infoLink") or f"https://books.google.com/books?id={it.get('id')}", label,
                        authors=v.get("authors"), publisher=v.get("publisher"), year=v.get("publishedDate"), language=v.get("language"),
                        subjects=v.get("categories"))
                    rows[-1]["isbn"] = ";".join(x.get("identifier", "") for x in v.get("industryIdentifiers", []) or [])
                    ai = it.get("accessInfo", {}) or {}
                    si = it.get("saleInfo", {}) or {}
                    if si.get("buyLink"):
                        rows[-1]["buy_url"] = si["buyLink"]
                    if ai.get("viewability") == "ALL_PAGES" or ai.get("publicDomain"):
                        rows[-1].update(access="open", read_url=ai.get("webReaderLink") or rows[-1]["url"],
                                        download_url=(ai.get("pdf") or {}).get("downloadLink", ""))
                    n += 1
            if len(items) < 40:
                break
        return n

    for names, tokens in AUTHORS:
        label = f"author:{names[0]}"
        keep_ia = lambda it, t=tokens: name_match(it.get("creator"), t)
        keep_ol = lambda d, t=tokens: name_match(d.get("author_name"), t)
        tot = 0
        for nm in names:
            core = re.sub(r"\s+(archaeology|epigraphy|coins)$", "", nm)
            tot += ia_query(f'creator:("{core}")', keep_ia)
            tot += ol_query({"author": core}, keep_ol, label)
            tot += gb_query(f'inauthor:"{core}"', keep_ol, label)
        log(f"[au] {names[0]}: {tot}")

    for pub, tokens, all_books in PUBLISHERS:
        label = f"publisher:{pub}"
        def keep_pub(pubs, title, subj, t=tokens, all_books=all_books):
            ok = any(x.lower() in s(pubs).lower() for x in t)
            return ok and (all_books or relevant(title, subj))
        tot = ia_query(f'publisher:("{pub}")', lambda it: keep_pub(it.get("publisher"), it.get("title"), it.get("subject")))
        tot += ol_query({"publisher": pub}, lambda d: keep_pub(d.get("publisher"), d.get("title"), (d.get("subject") or [])[:30]), label)
        tot += gb_query(f'inpublisher:"{pub}"', lambda d: keep_pub(d.get("publisher"), d.get("title"), d.get("subject")), label)
        log(f"[au] publisher {pub}: {tot}")
    return save("au", rows)


SOURCES = {"ia": harvest_ia, "ol": harvest_ol, "gb": harvest_gb, "loc": harvest_loc, "nl": harvest_nl, "au": harvest_au, "oa": harvest_oa, "doab": harvest_doab, "ws": harvest_ws, "ht": harvest_ht, "cm": harvest_cm, "wi": harvest_wi, "xs": harvest_xs}


class Deadline(Exception):
    pass


def _alarm(*_):
    raise Deadline()


def main():
    which = sys.argv[1:] or list(SOURCES)
    t0 = time.time()
    max_s = int(os.environ.get("MAX_SECONDS", "0") or 0)
    if max_s:
        signal.signal(signal.SIGALRM, _alarm)
        signal.alarm(max_s)
    for name in which:
        t = time.time()
        try:
            SOURCES[name]()
        except Deadline:
            log(f"[{name}] time budget reached - saving partial results")
            if LIVE.get(name):
                save(name, LIVE[name])
        except Exception:
            log(f"[{name}] FAILED\n" + traceback.format_exc())
            if LIVE.get(name):
                save(name, LIVE[name])
        log(f"[{name}] took {int(time.time() - t)}s")
    log(f"total {int(time.time() - t0)}s")
    (OUT / f"log_{'_'.join(which)}.txt").write_text("\n".join(LOG) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
