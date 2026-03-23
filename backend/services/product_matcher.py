import logging
import re

logger = logging.getLogger("vinted_intelligence")

# Storage patterns to extract from titles
STORAGE_PATTERN = re.compile(r"(\d+)\s*(GB|TB)", re.IGNORECASE)
COLOR_PATTERN = re.compile(
    r"\b(nero|bianco|blu|rosso|verde|viola|giallo|arancione|rosa|grigio|titanio|"
    r"black|white|blue|red|green|purple|yellow|orange|pink|gray|grey|titanium|"
    r"silver|gold|space\s*gray|space\s*grey|midnight|starlight|natural)\b",
    re.IGNORECASE,
)

# Noise words to remove from titles for cleaner search queries
NOISE_WORDS = [
    "vendo",
    "vendi",
    "vendesi",
    "come nuovo",
    "come nuova",
    "perfetto",
    "perfetta",
    "stato",
    "ottime condizioni",
    "usato",
    "usata",
    "poco usato",
    "poco usata",
    "originale",
    "originali",
    "garanzia",
    "con scatola",
    "box",
    "completo",
    "completa",
    "accessori",
    "inclusi",
    "spedizione",
    "gratis",
    "gratuita",
    "regalo",
    "affare",
    "urgente",
    "prezzo trattabile",
    "no perditempo",
]

# Apple model patterns for normalization
IPHONE_PATTERN = re.compile(
    r"iPhone\s*(\d{2})\s*(Pro\s*Max|Pro|Plus|mini)?", re.IGNORECASE
)
MACBOOK_PATTERN = re.compile(
    r"MacBook\s*(Pro|Air)\s*(\d{2})?[\"\"]?\s*(M[1-4]\s*(Pro|Max|Ultra)?)?",
    re.IGNORECASE,
)
IPAD_PATTERN = re.compile(
    r"iPad\s*(Pro|Air|mini)?\s*(M[1-4])?\s*(\d{2,4})?", re.IGNORECASE
)
WATCH_PATTERN = re.compile(
    r"Apple\s*Watch\s*(Ultra\s*\d?|Series\s*\d+|SE\s*\d?)?", re.IGNORECASE
)
AIRPODS_PATTERN = re.compile(r"AirPods?\s*(Pro\s*\d?|Max)?", re.IGNORECASE)
MAC_MINI_PATTERN = re.compile(
    r"Mac\s*Mini\s*(\d{4})?\s*(M[1-4]\w+)?\s*([A-Za-z0-9]+)?", re.IGNORECASE
)


def _extract_storage(text: str) -> str | None:
    """Extract storage capacity from text."""
    match = STORAGE_PATTERN.search(text)
    if match:
        amount = int(match.group(1))
        unit = match.group(2).upper()
        return f"{amount}{unit}"
    return None


def _extract_model(text: str) -> str | None:
    """Try to extract a normalized Apple model name from text."""
    for pattern, prefix in [
        (IPHONE_PATTERN, "iPhone"),
        (MACBOOK_PATTERN, "MacBook"),
        (IPAD_PATTERN, "iPad"),
        (WATCH_PATTERN, "Apple Watch"),
        (AIRPODS_PATTERN, "AirPods"),
        (MAC_MINI_PATTERN, "Mac Mini"),
    ]:
        match = pattern.search(text)
        if match:
            parts = [prefix]
            for group in match.groups():
                if group:
                    parts.append(group.strip())
            return " ".join(parts)
    return None


def _clean_title(title: str) -> str:
    """Remove noise from a listing title."""
    clean = title
    for noise in NOISE_WORDS:
        clean = re.sub(re.escape(noise), "", clean, flags=re.IGNORECASE)
    # Remove extra whitespace
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean
