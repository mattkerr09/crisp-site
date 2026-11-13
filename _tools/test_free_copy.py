#!/usr/bin/env python3
"""Offline checks of the shared free/Pro wording and its price expiry."""
from datetime import datetime, timedelta
import html
import json
import re
from unittest.mock import patch

import landing_pages
import llms_txt
from sale_test_facts import sale_engine


def main() -> None:
    with sale_engine():
        facts = llms_txt.facts()
        cap = facts["cap"]
        lists = llms_txt.free_pro_html(cap)
        home = llms_txt.read("/")
        pricing = llms_txt.read("/pricing/")
        free = llms_txt.read("/free-vs-pro/")
        for source in (home, pricing, free):
            assert source.count(lists) == 1, "shared lists must appear once on each page"
            descriptions = re.findall(
                r'<meta (?:name="description"|property="og:description"|name="twitter:description") content="([^"]*)">',
                source)
            assert descriptions and all(len(html.unescape(value)) <= 165 for value in descriptions)
        assert landing_pages.home(home) == home, "home block differs from its generator"
        assert landing_pages.pages()[llms_txt.SITE / "pricing/index.html"] == pricing
        assert home.index('class="lede-price"') < home.index('class="free-pro"') < home.index('windows-download:begin')

        visible = re.search(r'<summary>Is Crisp free\?</summary><p>(.*?)</p>', home).group(1)
        expected_faq = llms_txt.free_faq(cap)
        assert html.unescape(visible) == expected_faq
        schemas = [json.loads(block) for block in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', home, re.S)]
        faq_schema = next(block for block in schemas if block.get("@type") == "FAQPage")
        question = next(item for item in faq_schema["mainEntity"] if item["name"] == "Is Crisp free?")
        assert question["acceptedAnswer"]["text"] == expected_faq
        assert html.escape(expected_faq) in free

        text = llms_txt.build()
        expected_section = ["## Is Crisp free?", ""]
        for title, items in llms_txt.free_pro_lists(cap):
            expected_section.extend([title, "", *(f"- {item}" for item in items), ""])
        lines = text.splitlines()
        summary = next(i for i, line in enumerate(lines) if line.startswith("> "))
        assert lines[summary + 1] == ""
        start = summary + 2
        assert lines[start:start + len(expected_section)] == expected_section
        assert lines[start + len(expected_section)] == "## Product and pricing"

        changed_cap = cap + 1
        assert f"stop at {changed_cap} seconds" in llms_txt.free_pro_html(changed_cap)
        assert f"stop at {changed_cap} seconds" in llms_txt.free_faq(changed_cap)

        end = datetime.fromisoformat(facts["ends"].replace("Z", "+00:00"))
        live = llms_txt.founding_live
        for instant in (end - timedelta(seconds=1), end, end + timedelta(seconds=1)):
            active = instant < end
            with patch.object(llms_txt, "founding_live", side_effect=lambda f: live(f, instant)):
                heading = llms_txt.free_pro_heading(facts)
                plain = re.sub(r"<[^>]+>", "", heading)
                price = facts["now"] if active else facts["price"]
                assert plain == f"Free, or {llms_txt.money(price)} once"
                assert ("data-launch-price" in heading) == active
                if active:
                    assert f'data-full-price="{llms_txt.money(facts["price"])}"' in heading
                else:
                    summary_line = next(line for line in llms_txt.build().splitlines() if line.startswith("> "))
                    assert "Black Friday" not in summary_line
                rendered = landing_pages.pages()[llms_txt.SITE / "pricing/index.html"]
                assert lists in rendered
                _, note = llms_txt.page_meta("/vs/aiarty-video-enhancer-alternative-mac/")
                assert note.endswith(llms_txt.price_copy(facts))

    print("free copy: three pages and llms.txt share the lists, FAQ matches JSON-LD, descriptions fit, price expiry passes")


if __name__ == "__main__":
    main()
