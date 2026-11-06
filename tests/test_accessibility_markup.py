import unittest
from collections import Counter
from pathlib import Path

from lxml import html


PAGE = html.fromstring(
    (Path(__file__).parents[1] / "src/app/static/index.html").read_bytes()
)


def has_accessible_name(element) -> bool:
    if element.get("aria-label") or element.get("aria-labelledby"):
        return True
    if element.text_content().strip():
        return True
    element_id = element.get("id")
    if element_id and PAGE.xpath('//label[@for=$id]', id=element_id):
        return True
    parent = element.getparent()
    while parent is not None:
        if parent.tag == "label" and parent.text_content().strip():
            return True
        parent = parent.getparent()
    return False


class AccessibilityMarkupTests(unittest.TestCase):
    def test_interactive_controls_have_accessible_names(self) -> None:
        controls = PAGE.xpath(
            "//button | //a | //input[not(@type='hidden')] | //select | //textarea"
        )
        unnamed = [
            (element.tag, element.get("id"), element.get("type"))
            for element in controls
            if not has_accessible_name(element)
        ]
        self.assertEqual(unnamed, [])

    def test_aria_references_resolve_to_existing_ids(self) -> None:
        missing = []
        for attribute in ("aria-labelledby", "aria-describedby"):
            for element in PAGE.xpath(f"//*[@{attribute}]"):
                for reference in element.get(attribute).split():
                    if not PAGE.xpath('//*[@id=$id]', id=reference):
                        missing.append((element.tag, element.get("id"), reference))
        self.assertEqual(missing, [])

    def test_ids_are_unique_and_fieldsets_have_legends(self) -> None:
        ids = PAGE.xpath("//@id")
        duplicates = [value for value, count in Counter(ids).items() if count > 1]
        missing_legends = [
            fieldset.get("id")
            for fieldset in PAGE.xpath("//fieldset")
            if not fieldset.xpath("./legend")
        ]
        self.assertEqual(duplicates, [])
        self.assertEqual(missing_legends, [])

    def test_images_have_alt_attributes(self) -> None:
        missing_alt = PAGE.xpath("//img[not(@alt)]")
        self.assertEqual(missing_alt, [])


if __name__ == "__main__":
    unittest.main()
