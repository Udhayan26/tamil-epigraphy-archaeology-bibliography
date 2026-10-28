# Tamil Epigraphy, Inscriptions, Archaeology, Rock Art & Hero Stones — Books

**தமிழ்க் கல்வெட்டியல், கல்வெட்டுகள், தொல்லியல், பாறை ஓவியங்கள், நடுகற்கள் — நூல் பட்டியல் (1820 – இன்று)**

A categorized, searchable bibliography of books on Tamil inscriptions, epigraphy, archaeology, rock art and hero stones by writers around the world, in Tamil and English, from about 1820 to today. It covers books, inscription volumes, excavation reports and journals.

Each entry has:

- **Title** in Tamil script and in English or exact romanised form (ISO 15919)
- **Author / editor**, **publisher**, place, **year**, language, ISBN and pages where known
- **Category** (15 subject groups, below)
- **Source record URL**, plus extra record URLs where the same book appears in several catalogues
- **Read online / Download PDF** links when the book is freely available

🌐 **Website:** https://udhayan26.github.io/tamil-epigraphy-archaeology-bibliography/ (Settings → Pages → `main` / root)

## Automatic updates

- **Every day at 02:47 IST** – quick search of catalogues, open-access collections and your listed sources.
- **Every Saturday at 01:17 IST** – full deep search (old/colonial catalogue, ~90 scholars by name, all catalogues).
- Each book keeps a **permanent ID** (`TB-000123`) and the **date it was first added**; duplicates (same title in Tamil script / romanised, or same ISBN) are merged into one entry.
- New finds of the last 30 days: [`data/new_books.csv`](data/new_books.csv), or on the website choose **Newly added**.

## Add your own sources (Google Drive, blogs, government sites)

Edit [`data/extra_sources.txt`](data/extra_sources.txt) on GitHub and add one link per line (optionally `| label`).
Public Google Drive folders (with sub-folders), Blogger blogs (all posts) and any page listing books or PDFs are supported.
They are searched on every daily run.

## No duplicates

- The same book from different libraries, in Tamil script or romanised, with or without subtitle, or with the same ISBN, is one entry.
- Every scan of the same volume of South Indian Inscriptions, Epigraphia Indica, Annual Report on Epigraphy, Indian Antiquary, Travancore Archaeological Series and Epigraphia Carnatica is one entry, with the extra scans listed as *Copy 2, Copy 3…*

## Links for each book

- **Read online / Download PDF** – when the book is freely available
- **Buy** – store link where known, otherwise search links (Panuval and Commonfolks for Tamil books, Amazon.in)
- **Source record** – the catalogue page the details came from


## What's inside

| File | Contents |
|---|---|
| [`index.html`](index.html) | Searchable website: filter by category, language, period, link status |
| [`BIBLIOGRAPHY.md`](BIBLIOGRAPHY.md) | Full list as Markdown tables, grouped by category |
| [`data/bibliography.csv`](data/bibliography.csv) | Spreadsheet (UTF-8, opens in Excel): title_ta, title_en, authors, publisher, year, access, read_url, download_url, source_url… |
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
| NUM | Numismatics (Coins) | நாணயவியல் |
| PLM | Palm-leaf Manuscripts & Manuscriptology | ஓலைச்சுவடிகள், சுவடியியல் |
| SEA | Seals, Rock-cut Caves & Jain Beds | முத்திரைகள், குடைவரைகள், சமணப் படுகைகள் |
| REF | Reference: Catalogues, Lists & Glossaries | பட்டியல்கள், சொல்லகராதிகள் |
| JOU | Journals & Periodicals | இதழ்கள் |
| ONL | Online Resources & Digital Libraries | இணைய வளங்கள் |

## How records are gathered

- A hand-checked core list (`data/records.txt`)
- Automatic weekly harvest from public catalogues and open-access collections (`scripts/harvest.py`)
- Records of the same book from different catalogues are merged, including Tamil-script and romanised copies of the same title
- Single photo or artefact records (not books) are kept apart in `data/heritage_records.csv`

## Notes & limitations

- Years left blank are not confirmed; volume series show the full span (e.g. `1891-1913`).
- The Tamil Nadu State Department of Archaeology alone has issued 285–300+ titles; this list includes the key ones and is meant to grow.

## Adding a book

Add one line to `data/records.txt`:

```
category|language|year|title|alt_title|authors|publisher|place|type|series|notes|url
```

then run `python3 scripts/build.py`.

## License

Bibliographic data released under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). Linked works belong to their respective publishers.
