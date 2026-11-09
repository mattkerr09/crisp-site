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
    "bundle": ("Alle drei Apps, Crisp, Docket SEO und Outlier. {bundle_copy} Einzeln ab {future}: {apart}."),
    "more": "Was Pro zusätzlich bietet, die Lizenzbedingungen und Antworten auf die üblichen Fragen finden Sie auf der <a href=\"/de/\">Startseite</a>.",
}

FOOTER = {
    "line": ("<strong style=\"color:var(--text-mid)\">Crisp</strong>: Offline-KI zum Hochskalieren und Schneiden: Videos und Fotos "
             "auf dem Mac, Videos unter Windows."),
    "about": "Über uns",
    "made_by": "Von Kerr &amp; Company",
}
