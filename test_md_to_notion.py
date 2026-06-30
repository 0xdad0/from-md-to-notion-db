"""Smallest checks for the non-trivial bits. Run: python test_md_to_notion.py"""
from md_to_notion import normalize_tags, md_to_blocks


def test_tags():
    assert normalize_tags({"tags": ["a", "b"]}) == ["a", "b"]
    assert normalize_tags({"tags": "a, b c"}) == ["a", "b", "c"]
    assert normalize_tags({}) == []


def test_blocks():
    b = md_to_blocks("# H1\n- item\n\npara\n```\ncode\n```")
    types = [x["type"] for x in b]
    assert types == ["heading_1", "bulleted_list_item", "paragraph", "code"], types


if __name__ == "__main__":
    test_tags()
    test_blocks()
    print("ok")
