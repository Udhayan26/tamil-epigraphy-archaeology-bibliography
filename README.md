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

The list is rebuilt automatically every week by `scripts/harvest.py` (GitHub Actions), which searches public library catalogues and open-access book collections by subject keywords (Tamil, romanised and English), by the names of Tamil epigraphists and archaeologists, and by specialist publishers.

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
| NUM | Numismatics (Inscribed Coins) | நாணயவியல் |
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
