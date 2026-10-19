# Tamil Epigraphy, Inscriptions, Archaeology, Rock Art & Hero Stones — Bibliography

**தமிழ்க் கல்வெட்டியல், கல்வெட்டுகள், தொல்லியல், பாறை ஓவியங்கள், நடுகற்கள் — நூல் பட்டியல் (1820கள் – 2026)**

A categorized, searchable bibliography of Tamil and English books, inscription corpora, excavation reports, journals and online resources covering roughly 200 years of scholarship — from the Mackenzie Collection catalogue (1828) and Burnell's *South-Indian Palaeography* (1874) to the Tamil Nadu State Department of Archaeology's 2026 volumes on rock art and inscribed potsherds.

🌐 **Website (search & filter):** enable GitHub Pages for this repo (Settings → Pages → Deploy from branch `main` / root) — the site will be at `https://udhayan26.github.io/<repo-name>/`

## What's inside

| File | Contents |
|---|---|
| [`index.html`](index.html) | Searchable website: filter by category, language, period, link status |
| [`BIBLIOGRAPHY.md`](BIBLIOGRAPHY.md) | Full list as Markdown tables, grouped by category |
| [`data/bibliography.csv`](data/bibliography.csv) | Spreadsheet (UTF-8, opens in Excel / Google Sheets) |
| [`data/bibliography.json`](data/bibliography.json) | Machine-readable data with search links |
| [`data/records.txt`](data/records.txt) | Master source file (edit this to add books) |
| [`scripts/build.py`](scripts/build.py) | Regenerates CSV, JSON, JS and Markdown from the master file |

## Categories / வகைகள்

| Code | Category | தமிழில் |
|---|---|---|
| EPG | Epigraphy: Manuals, Palaeography & Script | கல்வெட்டியல்: கையேடுகள், எழுத்தியல் |
| ASI | Inscription Corpora: ASI & Colonial Series (SII, EI, ARE, TAS, Pudukkottai, TTD) | கல்வெட்டுத் தொகுதிகள்: இந்தியத் தொல்லியல் துறை |
| TNS | Inscription Corpora: Tamil Nadu State, District & Temple | தமிழ்நாட்டுக் கல்வெட்டுத் தொகுதிகள் |
| CPP | Copper Plates & Charters | செப்பேடுகள் |
| TBR | Tamil-Brahmi, Early Writing & Graffiti | தமிழ்-பிராமி, கீறல் குறியீடுகள் |
| HER | Hero Stones & Memorial Stones | நடுகற்கள் |
| ROC | Rock Art & Paintings | பாறை ஓவியங்கள் |
| EXC | Archaeology: Excavation Reports | அகழாய்வு அறிக்கைகள் |
| PRE | Archaeology: Prehistory & Megaliths | தொல்பழங்காலம், பெருங்கற்காலம் |
| ARC | Archaeology: General, Surveys & Museums | தொல்லியல்: பொது, அகழ்வைப்பகங்கள் |
| HIS | History from Inscriptions | கல்வெட்டு வழி வரலாறு |
| NUM | Numismatics (Inscribed Coins) | நாணயவியல் |
| REF | Reference: Catalogues, Lists & Glossaries | பட்டியல்கள், சொல்லகராதிகள் |
| JOU | Journals & Periodicals | இதழ்கள் |
| ONL | Online Resources & Digital Libraries | இணைய வளங்கள் |

## Metadata fields

`id` · `category` · `title` · `alt_title` (Tamil script / transliteration / translation) · `authors` (author or editor) · `year` · `period` · `language` · `publisher` · `place` · `type` (book, report, journal, catalogue…) · `series` (volume / series) · `notes` · `url` · `link_status` · `search` (Internet Archive, Tamil Digital Library, Open Library, WorldCat, Google Books)

**Links:** `verified` means a direct link (full-text PDF, Internet Archive item, Tamil Digital Library record, or catalogue/info page) was checked while compiling. `search-only` records still get ready-made search links for every major library.

## Main sources consulted

- Tamil Virtual Academy — Tamil Digital Library (tamildigitallibrary.in), incl. MARC records of Tamil Nadu State Department of Archaeology books
- Internet Archive (archive.org) — scans of SII, ARE, Tamil Nadu inscription volumes
- Tamil Nadu State Department of Archaeology (tnarch.gov.in) — Department Press, *Kalvettu* journal
- whatisindia.com (South Indian Inscriptions & Epigraphia Indica texts), Open Library, Central Institute of Classical Tamil library
- Standard scholarly bibliographies of South Indian epigraphy and archaeology

## Notes & limitations

- Years left blank are not confirmed; volume series show the full span (e.g. `1891-1913`).
- The Tamil Nadu State Department of Archaeology alone has issued 285–300+ titles; this list includes the key ones and is meant to grow.
- For Sri Lankan Tamil inscriptions see the companion repo [srilanka-tamil-inscriptions-bibliography](https://github.com/Udhayan26/srilanka-tamil-inscriptions-bibliography).

## Adding a book

Add one line to `data/records.txt`:

```
category|language|year|title|alt_title|authors|publisher|place|type|series|notes|url
```

then run `python3 scripts/build.py`.

## License

Bibliographic data released under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). Linked works belong to their respective publishers.
