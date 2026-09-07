from droidfoundry.properties import metadata_from_props, parse_prop_text


def test_parse_prop_text_ignores_comments():
    props = parse_prop_text("""
# comment
ro.product.device=sweet
ro.build.version.release=15
invalid
""")
    assert props["ro.product.device"] == "sweet"
    assert props["ro.build.version.release"] == "15"
    assert "invalid" not in props


def test_metadata_fallbacks():
    meta = metadata_from_props(
        {
            "ro.product.vendor.brand": "xiaomi",
            "ro.product.vendor.device": "sweet",
            "ro.product.vendor.model": "Redmi Note 10 Pro",
        }
    )
    assert meta.brand == "xiaomi"
    assert meta.device == "sweet"
    assert meta.model == "Redmi Note 10 Pro"
