import csv
import io
import re
import unicodedata
import hashlib
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

# Alias table for column mapping
COLUMN_ALIASES = {
    "text": [
        "text", "review", "feedback", "comment", "body", "content", "message",
        "description", "transcript", "complaint", "verbatim"
    ],
    "category": [
        "category", "topic", "label", "cluster", "department", "tag", "sentiment_category"
    ],
    "created_at": [
        "created_at", "date", "timestamp", "datetime", "time", "submitted_at", "created"
    ],
    "source": [
        "source", "channel", "platform", "origin", "type"
    ],
    "rating": [
        "rating", "score", "stars", "csat", "nps"
    ],
    "product": [
        "product", "item", "service", "sku"
    ],
    "language": [
        "language", "lang", "locale"
    ]
}


def normalize_text(text: str) -> str:
    """Normalize text with Unicode NFKC and whitespace collapse."""
    if not text:
        return ""
    # Normalize unicode
    text = unicodedata.normalize("NFKC", str(text))
    # Replace control characters with space
    text = "".join(ch if unicodedata.category(ch)[0] != "C" else " " for ch in text)
    # Collapse multiple whitespaces
    return " ".join(text.split()).strip()


def compute_content_hash(text: str) -> str:
    """Compute deterministic SHA-256 hash of casefolded normalized text."""
    normalized = normalize_text(text).casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def detect_column_mapping(headers: List[str]) -> Tuple[Dict[str, str], List[str]]:
    """
    Map input CSV headers to canonical schema fields:
    Returns (canonical_to_input_mapping, unmapped_headers)
    """
    mapping = {}
    unmapped = []
    
    cleaned_headers = {h.strip(): h.strip().lower().replace("_", "").replace("-", "").replace(" ", "") for h in headers}

    for canonical, aliases in COLUMN_ALIASES.items():
        found = False
        for original, clean in cleaned_headers.items():
            for alias in aliases:
                clean_alias = alias.replace("_", "").replace("-", "").replace(" ", "")
                if clean == clean_alias:
                    mapping[canonical] = original
                    found = True
                    break
            if found:
                break

    mapped_originals = set(mapping.values())
    for h in headers:
        if h.strip() not in mapped_originals:
            unmapped.append(h.strip())

    return mapping, unmapped


def parse_date(val: str) -> Optional[datetime]:
    if not val or not val.strip():
        return None
    cleaned = val.strip()[:19]
    formats = (
        "%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
        "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%d/%m/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M:%S", "%Y/%m/%d"
    )
    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            pass
    return None


def read_csv_stream(
    content_bytes: bytes,
    explicit_mapping: Optional[Dict[str, str]] = None
) -> Tuple[List[str], Dict[str, str], List[str], List[Dict[str, Any]], List[Dict[str, Any]], str]:
    """
    Parse CSV bytes with encoding detection, dialect sniffing, row limits and validation.
    Returns:
    - original_headers
    - column_mapping (canonical -> input_col)
    - unmapped_columns
    - valid_rows (parsed dicts)
    - rejected_rows (error dicts)
    - file_sha256
    """
    file_sha256 = hashlib.sha256(content_bytes).hexdigest()

    # Encoding detection fallback
    text_content = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            text_content = content_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue

    if text_content is None:
        raise ValueError("Unable to decode CSV file. Please ensure file is valid UTF-8 or text encoded.")

    # Check for binary/NUL characters
    if "\x00" in text_content:
        raise ValueError("Invalid file content: binary NUL byte detected.")

    lines = [line for line in text_content.splitlines() if line.strip()]
    if not lines:
        raise ValueError("Uploaded CSV file is completely empty.")

    reader = csv.reader(lines)
    try:
        header_row = next(reader)
    except StopIteration:
        raise ValueError("CSV file missing header row.")

    headers = [h.strip() for h in header_row if h.strip()]
    if not headers:
        raise ValueError("CSV header row contains only blank column names.")

    mapping, unmapped = detect_column_mapping(headers)
    if explicit_mapping:
        for k, v in explicit_mapping.items():
            if v in headers:
                mapping[k] = v

    if "text" not in mapping:
        raise ValueError(
            f"Could not map a customer feedback text column from headers: {headers}. "
            "Please provide a column named 'review', 'text', 'feedback', or 'comment'."
        )

    text_col = mapping["text"]
    cat_col = mapping.get("category")
    date_col = mapping.get("created_at")
    source_col = mapping.get("source")
    rating_col = mapping.get("rating")
    prod_col = mapping.get("product")
    lang_col = mapping.get("language")

    header_indices = {h: i for i, h in enumerate(headers)}
    text_idx = header_indices[text_col]
    cat_idx = header_indices.get(cat_col) if cat_col else None
    date_idx = header_indices.get(date_col) if date_col else None
    source_idx = header_indices.get(source_col) if source_col else None
    rating_idx = header_indices.get(rating_col) if rating_col else None
    prod_idx = header_indices.get(prod_col) if prod_col else None
    lang_idx = header_indices.get(lang_col) if lang_col else None

    valid_rows = []
    rejected_rows = []

    for row_idx, row in enumerate(reader, start=2):
        if not row or not any(x.strip() for x in row):
            continue

        if len(row) <= text_idx:
            rejected_rows.append({
                "row_number": row_idx,
                "reason": "Missing text column cell in row",
                "raw": ",".join(row)
            })
            continue

        raw_text = row[text_idx]
        norm_text = normalize_text(raw_text)
        if not norm_text:
            rejected_rows.append({
                "row_number": row_idx,
                "reason": "Feedback text is empty or contains only whitespace",
                "raw": ",".join(row)
            })
            continue

        if len(norm_text) > 10000:
            rejected_rows.append({
                "row_number": row_idx,
                "reason": "Feedback text exceeds maximum allowed length of 10,000 characters",
                "raw": ",".join(row)[:200]
            })
            continue

        # Optional fields
        cat_val = row[cat_idx].strip() if cat_idx is not None and len(row) > cat_idx else None
        source_val = row[source_idx].strip() if source_idx is not None and len(row) > source_idx else None
        prod_val = row[prod_idx].strip() if prod_idx is not None and len(row) > prod_idx else None
        lang_val = row[lang_idx].strip() if lang_idx is not None and len(row) > lang_idx else None
        
        rating_val = None
        if rating_idx is not None and len(row) > rating_idx:
            try:
                rating_val = float(row[rating_idx].strip())
            except ValueError:
                pass

        date_val = None
        if date_idx is not None and len(row) > date_idx:
            date_val = parse_date(row[date_idx])

        # Extra unmapped fields preserved in dictionary
        extra_data = {}
        for unmapped_col in unmapped:
            idx = header_indices.get(unmapped_col)
            if idx is not None and len(row) > idx and row[idx].strip():
                extra_data[unmapped_col] = row[idx].strip()

        valid_rows.append({
            "external_ref": f"row-{row_idx}",
            "original_text": raw_text,
            "normalized_text": norm_text,
            "content_hash": compute_content_hash(norm_text),
            "source_category": cat_val,
            "source": source_val,
            "rating": rating_val,
            "product": prod_val,
            "language": lang_val,
            "created_at": date_val,
            "extra": extra_data
        })

    return headers, mapping, unmapped, valid_rows, rejected_rows, file_sha256
