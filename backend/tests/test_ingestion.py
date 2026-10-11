import pytest
from app.services.ingestion import read_csv_stream, normalize_text, compute_content_hash


def test_normalize_and_hash():
    t1 = "  Slow response   time on checkout! "
    t2 = "slow response time on checkout!"
    assert normalize_text(t1) == "Slow response time on checkout!"
    assert compute_content_hash(t1) == compute_content_hash(t2)


def test_csv_ingestion_with_bom_and_aliases():
    csv_bytes = (
        "\ufeffreview,category\n"
        "\"App crashed during payment\",Operational Issues\n"
        "\"Support never replied\",Customer Service\n"
        "\"\",Empty Category\n"
    ).encode("utf-8")

    headers, mapping, unmapped, valid_rows, rejected_rows, sha256 = read_csv_stream(csv_bytes)
    assert "review" in headers
    assert "text" in mapping
    assert len(valid_rows) == 2
    assert len(rejected_rows) == 1
    assert valid_rows[0]["source_category"] == "Operational Issues"
