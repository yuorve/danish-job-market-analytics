"""
Normalization helpers for Danish entities, text cleaning, and HTML stripping.
"""

import html
import re
from typing import Optional, Tuple

CITY_MAPPING = {
    "københavn": "Copenhagen",
    "kobenhavn": "Copenhagen",
    "cph": "Copenhagen",
    "aarhus": "Aarhus",
    "århus": "Aarhus",
    "odense": "Odense",
    "aalborg": "Aalborg",
    "ålborg": "Aalborg",
    "hillerød": "Hillerød",
    "hillerod": "Hillerød",
    "roskilde": "Roskilde",
    "lyngby": "Lyngby",
    "kgs. lyngby": "Lyngby",
    "kongens lyngby": "Lyngby",
    "ballerup": "Ballerup"
}

REGION_MAPPING = {
    "Copenhagen": "Hovedstaden",
    "Lyngby": "Hovedstaden",
    "Ballerup": "Hovedstaden",
    "Hillerød": "Hovedstaden",
    "Roskilde": "Sjælland",
    "Aarhus": "Midtjylland",
    "Odense": "Syddanmark",
    "Aalborg": "Nordjylland"
}

# Danish legal company suffix patterns: A/S, ApS, IVS, P/S, filial, Denmark, Danmark
COMPANY_LEGAL_SUFFIXES = re.compile(
    r"\b(a/s|aps|ivs|p/s|denmark|danmark|filial|group|holding)\b",
    re.IGNORECASE
)

HTML_TAG_PATTERN = re.compile(r"<[^>]+>")

def strip_html(text: Optional[str]) -> str:
    """Remove HTML tags and decode HTML entities."""
    if not text:
        return ""
    unescaped = html.unescape(text)
    clean_text = HTML_TAG_PATTERN.sub(" ", unescaped)
    return re.sub(r"\s+", " ", clean_text).strip()

def normalize_city(city: Optional[str]) -> Tuple[str, str]:
    """Normalize city name and return (normalized_city, region)."""
    if not city:
        return "Copenhagen", "Hovedstaden"
    clean = city.strip().lower()
    norm_city = CITY_MAPPING.get(clean, city.strip().title())
    region = REGION_MAPPING.get(norm_city, "Hovedstaden")
    return norm_city, region

def normalize_company_name(name: Optional[str]) -> str:
    """Strip Danish legal corporate abbreviations and normalize whitespace."""
    if not name:
        return "Confidential Employer"
    cleaned = COMPANY_LEGAL_SUFFIXES.sub("", name)
    cleaned = re.sub(r"[,.\-/\\]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned if cleaned else name.strip()

def normalize_title(title: Optional[str]) -> str:
    """Normalize job title casing and common Danish/English variations."""
    if not title:
        return "Software Professional"
    cleaned = strip_html(title)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned
