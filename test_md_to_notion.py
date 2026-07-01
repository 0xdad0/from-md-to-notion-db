"""Smallest checks for the non-trivial bits. Run: python test_md_to_notion.py"""
from md_to_notion import to_values, build_properties, md_to_blocks, parse_map


def test_values():
    assert to_values(["a", "b"]) == ["a", "b"]
    assert to_values("a, b c") == ["a", "b", "c"]
    assert to_values(None) == []


def test_map():
    assert parse_map(["platform=os", "env = environment"]) == {
        "platform": "os", "env": "environment"}


def test_properties():
    meta = {"title": "T", "platform": "android", "tags": ["a", "b"]}
    props = build_properties(meta, "T", {"platform": "os"})
    assert props["Name"]["title"][0]["text"]["content"] == "T"
    assert props["os"]["multi_select"] == [{"name": "android"}]
    assert props["Type"]["multi_select"] == [{"name": "a"}, {"name": "b"}]


def test_blocks():
    b = md_to_blocks("# H1\n- item\n\npara\n```\ncode\n```")
    types = [x["type"] for x in b]
    assert types == ["heading_1", "bulleted_list_item", "paragraph", "code"], types


if __name__ == "__main__":
    test_values()
    test_map()
    test_properties()
    test_blocks()
    print("ok")
