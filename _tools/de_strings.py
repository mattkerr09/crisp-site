"""German text for crispvideo.app/de/ (written by the Crisp session, 2026-11-08; formal "Sie", plain sentences).

Only WORDS live here. Every fact (prices, the founding price and its end, the code, the Windows version, the macOS floor, the
refund days, the free cap) is a {placeholder} that the site's generators fill from the same sources the English pages use
(llms_txt.facts(), landing_pages.py), so a German page can never say an older price or version than its English twin.

Rules for this text (approved 2026-11-07): "Sie"; one line saying the app itself is in English; no Impressum and no postal
address, only the Kontakt block; prices in US dollars, written the German way ("29 $"), with the line that checkout shows
the buyer's currency and any local tax; nothing typed by hand that a generator knows.
"""

# a money amount, German style: 29 $ / 14,50 $
def money(d) -> str:
    s = f"{d:.2f}".replace(".", ",")
    if s.endswith(",00"):
        s = s[:-3]
    return f"{s} $"


# Facts arrive in English from llms_txt.facts() ("macOS 14.0 or later", "Apple Silicon (M1 or later)"); only these phrases change.
def fact_de(text: str) -> str:
    return text.replace(" or later", " oder neuer")


SPLIT = "oder 4 × {amount}"   # pay in four, when a price is high enough for it

APP_LANGUAGE = "Die App selbst ist auf Englisch; diese Seiten erklären sie auf Deutsch."
NAV_DOWNLOAD = "Download"
CURRENCY = "Preise in US-Dollar. An der Kasse sehen Sie Ihre Währung und gegebenenfalls die Steuer Ihres Landes."
KONTAKT_H = "Kontakt"

BOX = {
    "name": "<strong>Crisp Video</strong> stellt Videos wieder her, entfernt Rauschen und skaliert sie auf 4K, auf Ihrem Mac oder PC, offline.",
    "once": "einmalig",
    # {now}, {price} are money(); {code} the founding code; {ends} the last day of the offer, e.g. "30. November"
    "found": "Black-Friday-Preis <strong>{now}</strong> für alle bis {ends}, danach {price}. Der Kauf-Button wendet <strong>{code}</strong> an der Kasse an.",
    "buy": "Crisp Pro kaufen",
    "download_mac": "Kostenlos für den Mac laden",
    "windows_q": "Windows 10 oder 11, 64 Bit?",
    "windows_dl": "Crisp {win_version} für Windows laden",
    "windows_gpu": "Dafür braucht es eine Grafik mit Vulkan; die meisten PCs ab 2016 haben sie.",
    # {cap} seconds of the free cap; {os} the macOS floor; {chip} the chip line; {refund_days}
    "fine": ("Kostenlos nutzbar: Hochskalieren, Wiederherstellen und Farbexporte bis {cap} Sekunden, alles andere in voller Länge, "
             "Video- und GIF-Exporte mit einem kleinen &bdquo;crispvideo.app&ldquo;-Zeichen · {os} · {chip} · "
             "{refund_days} Tage Geld zurück, ohne Angabe von Gründen."),
}

DOWNLOAD = {
    "title": "Crisp für den Mac herunterladen",
    "meta": ("Crisp Video für den Mac: {os}, {chip}. Kostenlos nutzbar: verbesserte Exporte bis {cap} Sekunden, alles andere in "
             "voller Länge."),
    "h1": "Crisp für den Mac herunterladen",
    "lede": ("Die aktuelle Version, von Apple notariell beglaubigt: {os}, {chip}. Kostenlos nutzbar: Hochskalieren, Wiederherstellen "
             "und Farbexporte bis {cap} Sekunden, alles andere in voller Länge, Video- und GIF-Exporte mit einem kleinen "
             "&bdquo;crispvideo.app&ldquo;-Zeichen. Pro entfernt das Zeichen und die Grenze."),
    "speed_h": "Wie schnell es auf Ihrem macOS läuft",
    "speed_p": "Crisp ist für macOS 14 gebaut und auf macOS 14 und 26 getestet. Welcher Hochskalierer läuft, hängt von Ihrem macOS ab:",
    "speed_15": "<strong>macOS 15 Sequoia oder neuer:</strong> Core ML auf der Grafik Ihres Macs. Volle Geschwindigkeit.",
    "speed_14": ("<strong>macOS 14:</strong> ein anderer Hochskalierer, die ncnn-Engine von Crisp, ebenfalls auf der Grafik Ihres Macs. "
                 "Das Hochskalieren dauert etwa anderthalbmal so lange."),
    "speed_same": "Das Bild wird in beiden Fällen gleich; nur die Wartezeit ändert sich.",
    "speed_measured": ("Gemessen auf einem Mac Studio (M1 Ultra) im Oktober 2026: Ein 3-Sekunden-Clip, auf 720p verdoppelt, brauchte "
                       "3,4 Sekunden mit Core ML und 5,0 Sekunden mit dem ncnn-Hochskalierer, den macOS 14 nutzt. Das ist der "
                       "macOS-14-Hochskalierer, gemessen auf einem neueren macOS; auf einem Mac mit macOS 14 selbst ist er noch nicht gemessen."),
    "more": "Was Pro dazugibt, die Lizenzbedingungen und Antworten auf die üblichen Fragen finden Sie auf der <a href=\"/de/\">Startseite</a>.",
}

PRICES = {
    "title": "Crisp: Preise. Kostenlos ausprobieren, Pro für {price} einmalig",
    "meta": ("Kostenlos nutzbar: verbesserte Exporte bis {cap} Sekunden, alles andere in voller Länge, mit einem kleinen Zeichen. "
             "Pro kostet {price} einmalig, kein Abo."),
    "h1": "Crisp: Preise",
    "free": ("Kostenlos: der ganze Editor und die ganze Vorschau. Hochskalieren, Wiederherstellen und Farbexporte enden nach {cap} "
             "Sekunden; alles andere, etwa Umwandeln, Stummschalten, Komprimieren und Schleife, läuft in voller Länge. Jeder kostenlose "
             "Videoexport trägt ein kleines &bdquo;crispvideo.app&ldquo;-Zeichen."),
    "pro": ("Crisp Pro kostet {price} einmalig, kein Abo. Pro entfernt das Zeichen und die {cap}-Sekunden-Grenze und bringt die "
            "Stapelverarbeitung, auf dem Mac auch die Max-Wiederherstellung. Eine Lizenz gilt für 3 Computer gleichzeitig, Mac oder "
            "Windows. Alle Updates der Version 1.x sind enthalten, und Sie bekommen {refund_days} Tage lang Ihr Geld zurück, ohne Angabe "
            "von Gründen."),
    # the bundle: {bundle} regular, {apart} the three apps bought separately, {bundle_now} the November price
    "bundle": ("Alle drei Apps, Crisp, Docket SEO und Outlier: einzeln {apart}, zusammen {bundle} einmalig"
               "<span data-until=\"{ends_iso}\">, bis {ends} {bundle_now}</span>."),
    "more": "Was Pro dazugibt, die Lizenzbedingungen und Antworten auf die üblichen Fragen finden Sie auf der <a href=\"/de/\">Startseite</a>.",
}

FOOTER = {
    "line": ("<strong style=\"color:var(--text-mid)\">Crisp</strong>: Offline-KI zum Hochskalieren und Schneiden von Videos und Fotos "
             "für den Mac, und zum Hochskalieren und Schneiden von Videos für Windows."),
    "about": "Über uns",
    "made_by": "Von Kerr &amp; Company",
}
