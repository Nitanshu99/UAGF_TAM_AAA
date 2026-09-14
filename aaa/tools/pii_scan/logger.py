"""Part 1 of the former ``pii_scan`` module (auto-split)."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

#: A Presidio result below this confidence is not a detection. Without the floor,
#: per-cell analysis surfaces regex guesses such as US_BANK_NUMBER at 0.05 on every
#: numeric sensor column and US_DRIVER_LICENSE at 0.01-0.3 on language-level codes.
MIN_ENTITY_SCORE = 0.5

#: A column carries an entity only when at least this share of its sampled,
#: non-empty cells do — the column-level threshold AWS Glue's sensitive-data
#: detection applies ("percentage of rows that contain the PII entity").
MIN_COLUMN_RATE = 0.10

#: Seed for the row sample, so a scan is reproducible; presidio-structured uses 123.
SAMPLE_SEED = 123


_SPECIAL_CATEGORY_ENTITIES: dict[str, str] = {
    "MEDICAL_LICENSE": "health_data",
    "US_ITIN": "health_data",          # often tied to health insurance
    "POLITICAL_OPINION": "political_opinions",
    "TRADE_UNION_MEMBERSHIP": "trade_union_membership",
    "GENETIC": "genetic_data",
    "BIOMETRIC": "biometric_data",
    "HEALTH": "health_data",
    "RELIGION": "religious_beliefs",
    "SEXUAL_ORIENTATION": "sex_life_or_orientation",
    "CRIMINAL": "criminal_convictions",
    "RACE": "racial_or_ethnic_origin",
    "ETHNIC_GROUP": "racial_or_ethnic_origin",
}


#: Entities that may carry an Art. 9 category but cannot say which, if any.
#: Presidio's NRP is spaCy's NORP — "a nationality, religious or political group" —
#: and spaCy also gives that label to language names: every NRP match in case 05's
#: CVs was "german" or "english" in "fluent in german and english". It used to map
#: to racial_or_ethnic_origin, which is none of the three, and so recorded special-
#: category data the provider had correctly declared absent (T-20260913-096). Such
#: a mention is kept with its matched terms for a reader to resolve; it asserts no
#: category.
_UNRESOLVED_ENTITIES: dict[str, str] = {
    "NRP": ("mentions a nationality, religious or political group; the entity does not "
            "say which, and nationality is not a GDPR Art. 9 category"),
}


_HIGH_SEVERITY_ENTITIES = {
    "MEDICAL_LICENSE", "BIOMETRIC", "HEALTH", "GENETIC",
    "POLITICAL_OPINION", "CRIMINAL", "RACE", "ETHNIC_GROUP",
    "SEXUAL_ORIENTATION", "TRADE_UNION_MEMBERSHIP",
}


_KEYWORD_PATTERNS: list[tuple[str, str, str]] = [
    # (pattern, entity_type, severity)
    (r"health|diagnosis|disease|medication|prescription", "HEALTH", "high"),
    (r"race|ethnic|national.?origin", "RACE", "high"),
    (r"biometric|fingerprint|iris|retina|face.?id", "BIOMETRIC", "critical"),
    (r"religion|faith|church|mosque|synagogue", "RELIGION", "high"),
    (r"politic|party|vote|union|union.?member", "POLITICAL_OPINION", "high"),
    (r"sex.?orient|gender.?ident|lgbtq", "SEXUAL_ORIENTATION", "high"),
    (r"criminal|conviction|arrest|offence", "CRIMINAL", "high"),
    (r"genetic|dna|genome", "GENETIC", "critical"),
    (r"email|e.?mail", "EMAIL_ADDRESS", "medium"),
    (r"phone|mobile|tel", "PHONE_NUMBER", "medium"),
    (r"ssn|social.?security|national.?id|passport|id.?number", "US_SSN", "high"),
    (r"credit.?card|card.?number|cvv", "CREDIT_CARD", "high"),
    (r"address|street|postcode|zip.?code", "LOCATION", "low"),
    (r"name|first.?name|last.?name|surname", "PERSON", "low"),
    (r"ip.?address|ipv4|ipv6", "IP_ADDRESS", "medium"),
]
