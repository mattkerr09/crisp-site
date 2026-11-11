"""German text for crispvideo.app/de/ (written by the Crisp session, 2026-11-08; formal "Sie", plain sentences).

Only WORDS live here. Every fact (prices, the founding price and its end, the code, the Windows version, the macOS floor, the
refund days, the free cap) is a {placeholder} that the site's generators fill from the same sources the English pages use
(llms_txt.facts(), landing_pages.py), so a German page can never say an older price or version than its English twin.

Rules for this text (approved 2026-11-07): "Sie"; one line saying the app itself is in English; no Impressum and no postal
address, only the Kontakt block; prices in US dollars, written the German way ("19 $"), with the line that checkout shows
the buyer's currency and any local tax; nothing typed by hand that a generator knows.
"""

# a money amount, German style: 19 $ / 14,50 $
def money(d) -> str:
    s = f"{d:.2f}".replace(".", ",")
    if s.endswith(",00"):
        s = s[:-3]
    return f"{s} $"


# Facts arrive in English from llms_txt.facts() ("macOS 14.0 or later", "Apple Silicon (M1 or later)"); only these phrases change.
def fact_de(text: str) -> str:
    return fact(text)


SPLIT = "oder 4 × {amount}"   # pay in four, when a price is high enough for it

APP_LANGUAGE = "Die App selbst ist auf Englisch; diese Seiten erklären sie auf Deutsch."
NAV_DOWNLOAD = "Download"
CURRENCY = "Preise in US-Dollar. An der Kasse sehen Sie Ihre Währung und gegebenenfalls die Steuer Ihres Landes."
KONTAKT_H = "Kontakt"

BOX = {
    "name": "<strong>Crisp Video</strong> stellt Videos wieder her, entfernt Rauschen und skaliert sie auf 4K hoch, offline auf Ihrem Mac oder PC.",
    "once": "einmalig",
    # {now}, {price} are money(); {code} the founding code; {ends} the last day of the offer, e.g. "30. November"
    "found": "Einführungspreis, bis {ends}. Ab {future}: {price}. Über den Kauf-Button wird der Code <strong>{code}</strong> an der Kasse automatisch eingelöst.",
    "buy": "Crisp Pro kaufen",
    "download_mac": "Kostenlos für den Mac herunterladen",
    "windows_q": "Windows 10 oder 11, 64 Bit?",
    "windows_dl": "Crisp {win_version} für Windows herunterladen",
    "windows_gpu": "Voraussetzung ist eine Grafikkarte mit Vulkan-Unterstützung; die haben die meisten PCs ab 2016.",
    # {cap} seconds of the free cap; {os} the macOS floor; {chip} the chip line; {refund_days}
    "fine": ("Kostenlos nutzbar: KI-Exporte (Hochskalieren, Wiederherstellen, Farblooks) bis {cap} Sekunden, alles andere in voller Länge, "
             "Video- und GIF-Exporte mit einem kleinen &bdquo;crispvideo.app&ldquo;-Wasserzeichen · {os} · {chip} · "
             "{refund_days} Tage Geld zurück, ohne Angabe von Gründen."),
}

DOWNLOAD = {
    "title": "Crisp für den Mac herunterladen",
    "meta": ("Crisp Video für den Mac: {os}, {chip}. Kostenlos nutzbar: KI-Exporte bis {cap} Sekunden, alles andere in "
             "voller Länge."),
    "h1": "Crisp für den Mac herunterladen",
    "lede": ("Die aktuelle Version, von Apple geprüft (notarisiert): {os}, {chip}. Kostenlos nutzbar: KI-Exporte (Hochskalieren, "
             "Wiederherstellen, Farblooks) bis {cap} Sekunden, alles andere in voller Länge, Video- und GIF-Exporte mit einem kleinen "
             "&bdquo;crispvideo.app&ldquo;-Wasserzeichen. Pro entfernt das Wasserzeichen und die Grenze."),
    "speed_h": "Wie schnell Crisp auf Ihrer macOS-Version läuft",
    "speed_p": "Crisp ist für macOS 14 entwickelt und auf macOS 14 und 26 getestet. Welcher Hochskalierer läuft, hängt von Ihrem macOS ab:",
    "speed_15": "<strong>macOS 15 Sequoia oder neuer:</strong> Core ML auf dem Grafikprozessor Ihres Macs. Volle Geschwindigkeit.",
    "speed_14": ("<strong>macOS 14:</strong> ein anderer Hochskalierer, die ncnn-Engine von Crisp, ebenfalls auf dem Grafikprozessor Ihres Macs. "
                 "Das Hochskalieren dauert etwa 1,5-mal so lange."),
    "speed_same": "Das Ergebnis ist in beiden Fällen gleich; nur die Wartezeit ändert sich.",
    "speed_measured": ("Gemessen auf einem Mac Studio (M1 Ultra) im Oktober 2026: Ein 3-Sekunden-Clip, auf 720p verdoppelt, brauchte "
                       "3,4 Sekunden mit Core ML und 5,0 Sekunden mit dem ncnn-Hochskalierer, den macOS 14 nutzt. Das ist der "
                       "macOS-14-Hochskalierer, gemessen auf einem neueren macOS; auf einem Mac mit macOS 14 selbst wurde er noch nicht gemessen."),
    "more": "Was Pro zusätzlich bietet, die Lizenzbedingungen und Antworten auf die üblichen Fragen finden Sie auf der <a href=\"/de/\">Startseite</a>.",
}

PRICES = {
    "title": "Crisp-Preise: kostenlos ausprobieren, Pro einmal kaufen",
    "meta": ("Kostenlos nutzbar: KI-Exporte bis {cap} Sekunden, alles andere in voller Länge, mit einem kleinen Wasserzeichen. "
             "{price_short}"),
    "h1": "Crisp: Preise",
    "free": ("Kostenlos: der ganze Editor und die ganze Vorschau. KI-Exporte (Hochskalieren, Wiederherstellen, Farblooks) enden nach {cap} "
             "Sekunden; alles andere, etwa Umwandeln, Stummschalten, Komprimieren und Endlosschleife, läuft in voller Länge. Jeder kostenlose "
             "Videoexport trägt ein kleines &bdquo;crispvideo.app&ldquo;-Wasserzeichen."),
    "pro": ("{price_copy} Kein Abo. Pro entfernt das Wasserzeichen und die {cap}-Sekunden-Grenze und bietet die "
            "Stapelverarbeitung, auf dem Mac auch die Wiederherstellungsstufe &bdquo;Max&ldquo;. Eine Lizenz gilt für bis zu drei Computer gleichzeitig, Mac oder "
            "Windows. Alle Updates der Version 1.x sind enthalten, und Sie bekommen {refund_days} Tage lang Ihr Geld zurück, ohne Angabe "
            "von Gründen."),
    # the bundle: {bundle} regular, {apart} the three apps bought separately, {bundle_now} the November price
    "bundle": ("Alle drei Apps, Crisp, Check Engine SEO und Outlier. {bundle_copy} Einzeln ab {future}: {apart}."),
    "more": "Was Pro zusätzlich bietet, die Lizenzbedingungen und Antworten auf die üblichen Fragen finden Sie auf der <a href=\"/de/\">Startseite</a>.",
}

FOOTER = {
    "line": ("<strong style=\"color:var(--text-mid)\">Crisp</strong>: Offline-KI zum Hochskalieren und Schneiden: Videos und Fotos "
             "auf dem Mac, Videos unter Windows."),
    "about": "Über uns",
    "made_by": "Von Kerr &amp; Company",
}

# Locale data shared by the generator, gate and site-wide chrome.
LANGUAGE_NAME = "German"
PAGE_COUNT = "seven"
ROUTES = (
    ("/", "/de/"),
    ("/download/", "/de/download/"),
    ("/pricing/", "/de/preise/"),
    ("/free-vs-pro/", "/de/kostenlos-oder-pro/"),
    ("/how-to/upscale-video-on-mac/", "/de/anleitung/video-hochskalieren-mac/"),
    ("/how-to/restore-old-home-videos-mac/", "/de/vhs-digitalisieren-und-verbessern/"),
    ("/legal/privacy/", "/de/datenschutz/"),
)
GENERATED_ROUTES = ("/download/", "/pricing/")
GENERATOR_COMMENT = "<!-- Generated by _tools/de_pages.py. Edit the generator, not this page. -->"
MONTHS = ("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
          "September", "Oktober", "November", "Dezember")
SHORT_MONTHS = tuple(month[:3] for month in MONTHS)
DATE_FORMAT = "{day}. {month}"
SHORT_DATE_FORMAT = "{day}. {month}."
PRICE_ONCE = "{price} einmalig."
PRICE_COPY = "Einführungspreis: {now} einmalig, bis {ends}. Ab {future}: {price}."
PRICE_SHORT = "Einführungspreis {now} bis {ends}, dann {price}."
BUNDLE_FULL_PRICE = "Alle drei Apps, Crisp, Check Engine SEO und Outlier. {price} einmalig."
CONTACT_CLASS = "kontakt"
CONTACT = ('<section class="kontakt"><h2>' + KONTAKT_H + '</h2><p>Kerr &amp; Company LLC<br>'
           'E-Mail: <a href="mailto:support@crispvideo.app">support@crispvideo.app</a><br>'
           'Web: <a href="https://crispvideo.app/">crispvideo.app</a></p></section>')
FACT_REPLACEMENTS = ((" or later", " oder neuer"),)
TODO_NOTICE = "TODO-DE: one sentence that the app itself is in English"
FORBIDDEN_WORDS = ("impressum",)
FORBIDDEN_WORD_MESSAGE = "forbidden heading or link: Impressum"
POSTAL_ADDRESS_PATTERN = (r"\b\d+\s+[A-Za-z ]+\s+(?:Street|Road|Avenue|Boulevard)\b|"
                          r"\b\w+(?:straße|strasse)\s+\d+\b")
SENTENCE_EXCEPTIONS = ("Crisp.", "Pro.", "Max.", "Mac.", "Windows.", "USD.", "GIF.", "MP4.", "AI.")


def fact(text: str) -> str:
    for source, target in FACT_REPLACEMENTS:
        text = text.replace(source, target)
    return text


# Locale-specific mutation fixtures keep the shared gate free of German phrases.
GATE_WINDOWS_VERSION_PATTERN = r"Crisp (1\.0\.\d+) f"


def gate_cases(generator, origin, lastmod, win_version, en_desc):
    words = generator.words
    ORIGIN = origin
    CONTACT = words.CONTACT
    _DE_LASTMOD, _WIN_VERSION, _EN_DESC = lastmod, win_version, en_desc
    return [
        ("missing page", "de/download/index.html", None, None, "No such file", True),
        ("wrong language", "de/index.html", 'lang="de"', 'lang="en"', "lang=de", True),
        ("wrong canonical", "de/index.html", 'rel="canonical" href="' + ORIGIN + '/de/"', 'rel="canonical" href="' + ORIGIN + '/"', "canonical must", True),
        ("German hreflang", "de/index.html", 'hreflang="de"', 'hreflang="fr"', "hreflang", True),
        ("English hreflang", "index.html", 'hreflang="en"', 'hreflang="fr"', "hreflang", True),
        ("default hreflang", "de/preise/index.html", 'hreflang="x-default"', 'hreflang="fr"', "hreflang", True),
        ("missing stylesheet", "de/download/index.html", '<link rel="stylesheet" href="/style.css">', '', "generated German page is stale", True),
        ("changed stylesheet", "de/download/index.html", 'href="/style.css"', 'href="/other.css"', "generated German page is stale", True),
        ("changed Plausible", "de/index.html", 'src="https://plausible.io/js/script.js"', 'src="/wrong.js"', "script src must preserve", True),
        ("missing title marker", "de/index.html", '<title>TODO-DE:', '<title>', "unmarked English", True),
        ("missing description marker", "de/index.html", 'content="TODO-DE: ' + _EN_DESC, 'content="' + _EN_DESC, "unmarked English", True),
        ("changed reference", "de/download/index.html", words.DOWNLOAD['h1'], 'TODO-DE: Wrong reference', "TODO-DE markers", True),
        ("changed nav", "de/download/index.html", '>' + words.NAV_DOWNLOAD + '</a>', '>Wrong</a>', "generated German page is stale", True),
        ("footer removed", "de/download/index.html", '<footer>', '', "generated German page is stale", True),
        ("missing contact", "de/download/index.html", CONTACT, '', "exact contact", True),
        ("changed contact email", "de/download/index.html", CONTACT, CONTACT.replace('support@', 'other@'), "exact contact", True),
        ("contact in footer", "de/download/index.html", CONTACT + '\n<footer>', '<footer>' + CONTACT, "above the footer", True),
        ("missing app notice", "de/download/index.html", '<p class="app-language">' + words.APP_LANGUAGE + '</p>', '', "app-language", True),
        ("wrong app notice", "de/download/index.html", words.APP_LANGUAGE, 'TODO-DE: different notice', "required sentence", True),
        ("app notice below the bar's tag and other content", "de/datenschutz/index.html", '<p class="app-language">',
         '<p>Seite</p>\n<p class="app-language">', "top of body", True),
        ("unmapped nav link", "de/download/index.html", ORIGIN + '/de/download/?src=nav-download', ORIGIN + '/download/?src=nav-download', "generated German page is stale", True),
        ("unmapped home link", "de/download/index.html", 'href="/de/"', 'href="/"', "generated German page is stale", True),
        ("altered download", "de/download/index.html", 'Crisp.dmg', 'Other.dmg', "generated German page is stale", True),
        ("changed price", "de/preise/index.html", 'data-full-price="19 $"', 'data-full-price="30 $"', "generated German page is stale", True),
        ("changed JSON price", "de/index.html", '"price": "14.50"', '"price": "30"', "fixed value", True),
        ("unmarked JSON prose", "de/index.html", '"name": "TODO-DE: Crisp Video"', '"name": "Crisp Video"', "unmarked English", True),
        ("invalid JSON", "de/index.html", '"@context": "https://schema.org",', '"@context": ,', "invalid JSON-LD", True),
        ("changed schema type", "de/index.html", '"@type": "Organization"', '"@type": "Thing"', "fixed value", True),
        ("wrong schema language", "de/index.html", '"inLanguage": "de"', '"inLanguage": "en"', "must be de", True),
        ("written page without schema language", "de/vhs-digitalisieren-und-verbessern/index.html", '"inLanguage": "de",', '', "must be de (inLanguage)", True),
        ("graph node without schema language", "de/index.html", '"inLanguage": "de"', '"inLanguage": "en"', "must be de (inLanguage)", True),
        ("forbidden word", "de/download/index.html", '</body>', '<!-- iMpReSsUm --></body>', "forbidden heading", True),
        ("encoded forbidden word", "de/download/index.html", '</body>', '<!-- &#73;mpressum --></body>', "forbidden heading", True),
        ("postal markup", "de/download/index.html", '</body>', '<address>123 Example Street</address></body>', "postal address", True),
        ("plain postal address", "de/download/index.html", words.DOWNLOAD['h1'] + '</h1>', '123 Example Street</h1>', "postal addresses", True),
        ("phone link", "de/download/index.html", 'href="mailto:support@crispvideo.app"', 'href="tel:+15555550123"', "telephone links", True),
        ("plain phone", "de/download/index.html", words.DOWNLOAD['h1'] + '</h1>', '+1 555 555 0123</h1>', "phone numbers", True),
        ("missing sitemap URL", "sitemap.xml", '<loc>' + ORIGIN + '/de/</loc>', '<loc>' + ORIGIN + '/other/</loc>', "one entry", True),
        ("invalid lastmod", "sitemap.xml", '<loc>' + ORIGIN + '/de/</loc><lastmod>' + _DE_LASTMOD, '<loc>' + ORIGIN + '/de/</loc><lastmod>2026-02-30', "valid YYYY-MM-DD", True),
        ("invalid sitemap XML", "sitemap.xml", '</urlset>', '', "invalid XML", True),
        ("final markers", "de/download/index.html", words.DOWNLOAD['h1'], 'TODO-DE: Wrong reference', "TODO-DE markers", False),
        ("English sentence", "de/download/index.html", words.DOWNLOAD['speed_same'], 'The picture comes out the same either way; only the wait changes.', "generated German page is stale", False),
        ("sentence across inline tags", "de/index.html", 'TODO-DE: Crisp Video restores, denoises and upscales footage to 4K <strong>TODO-DE: offline</strong>TODO-DE: , then lets you edit it on a real timeline.', 'Crisp Video restores, denoises and upscales footage to 4K <strong>offline</strong>, then lets you edit it on a real timeline.', "English sentence remains", False),
        ("stale Windows version", "de/download/index.html", 'Crisp ' + _WIN_VERSION, 'Crisp 1.0.1', "generated German page is stale", True),
        ("stale code", "de/preise/index.html", 'FOUNDINGCRISP', 'WRONGCODE', "generated German page is stale", True),
        ("stale bundle price", "de/preise/index.html", '49,50 $', '48,50 $', "generated German page is stale", True),
        ("stale macOS floor", "de/download/index.html", 'macOS 14.0', 'macOS 13.0', "generated German page is stale", True),
        ("unmarked homepage price", "de/index.html", '$14.50 once', '$13.50 once', "prices differ", True),
        ("unmarked homepage code", "de/index.html", 'TODO-DE: FOUNDINGCRISP', 'WRONGCODE', "codes differ", True),
        ("stale generated box", "de/datenschutz/index.html", '14,50 $', '13,50 $', "generated German box is stale", True),
        ("missing box expiry", "de/datenschutz/index.html", generator.EXPIRY_SCRIPT, '', "generated German box is stale", True),
    ]
