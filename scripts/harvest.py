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
import json, re, sys, time, traceback, urllib.parse, urllib.request
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


def get(url, tries=4, as_json=True, sleep=0.4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
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


def relevant(title, subjects="", extra=""):
    t = s(title)
    blob = f"{t} {s(subjects)} {s(extra)}"
    if TA_KW.search(blob) or RO_KW.search(t):
        return True
    if EN_KW.search(blob) and CTX.search(blob) and not NOISE.search(t):
        return True
    return False


def rec(source, sid, title, url, authors="", publisher="", year="", language="", place="",
        subjects="", alt_title="", extra=None):
    r = {"source": source, "source_id": sid, "title": s(title)[:400], "alt_title": s(alt_title)[:300],
         "authors": s(authors)[:300], "publisher": s(publisher)[:200], "place": s(place)[:100],
         "year": year_of(year), "language": s(language)[:40], "subjects": s(subjects)[:400], "url": url}
    if extra:
        r.update(extra)
    return r


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

    rows = []
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

    # enrich items missing author/publisher from the per-item metadata API
    need = [r for r in rows if not r["authors"] or not r["publisher"]]
    log(f"[ia] enriching {len(need)} items via metadata API")
    for i, r in enumerate(need[:6000]):
        try:
            m = get(f"https://archive.org/metadata/{urllib.parse.quote(r['source_id'])}/metadata", tries=2, sleep=0.15)
            md = m.get("result", {}) if isinstance(m, dict) else {}
            if i == 0:
                sample("ia_metadata", md)
            for k_src, k_dst in (("creator", "authors"), ("publisher", "publisher")):
                if not r[k_dst] and md.get(k_src):
                    r[k_dst] = s(md[k_src])[:300]
            for k in ("contributor", "author", "editor"):
                if not r["authors"] and md.get(k):
                    r["authors"] = s(md[k])[:300]
            if not r["year"]:
                r["year"] = year_of(md.get("year") or md.get("date") or md.get("publicdate", "")[:0])
            if not r.get("description") and md.get("description"):
                r["description"] = s(md["description"])[:600]
            for k in ("pages", "imagecount", "isbn", "call_number", "subject"):
                if md.get(k) and k not in r:
                    r[k] = s(md[k])[:200]
        except Exception as e:
            if i < 5:
                log("[ia] meta ERR", r["source_id"], e)
        if i and i % 500 == 0:
            log(f"[ia] enriched {i}")
    return save("ia", rows)


# ---------------------------------------------------------------- Open Library
def harvest_ol():
    rows = []
    fl = "key,title,subtitle,author_name,publisher,publish_place,first_publish_year,publish_year,language,subject,isbn,ia"
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
            log(f"[ol] {kind}={t}: page {page} docs {len(docs)}")
            if len(docs) < 1000:
                break
            page += 1
    return save("ol", rows)


# ---------------------------------------------------------------- Google Books
def harvest_gb():
    rows = []
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
    rows = []
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
    rows = []
    for i in range(0, len(tl), 50):
        batch = tl[i:i + 50]
        url = NL_API + "?" + urllib.parse.urlencode({"action": "query", "prop": "revisions", "rvprop": "content",
                                                     "rvslots": "main", "titles": "|".join(batch), "format": "json",
                                                     "formatversion": 2})
        try:
            j = get(url, sleep=0.6)
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
    return save("nl", rows)


SOURCES = {"ia": harvest_ia, "ol": harvest_ol, "gb": harvest_gb, "loc": harvest_loc, "nl": harvest_nl}


def main():
    which = sys.argv[1:] or list(SOURCES)
    t0 = time.time()
    for name in which:
        t = time.time()
        try:
            SOURCES[name]()
        except Exception:
            log(f"[{name}] FAILED\n" + traceback.format_exc())
        log(f"[{name}] took {int(time.time() - t)}s")
    log(f"total {int(time.time() - t0)}s")
    (OUT / f"log_{'_'.join(which)}.txt").write_text("\n".join(LOG) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
