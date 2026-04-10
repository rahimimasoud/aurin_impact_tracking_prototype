"""
Shared constants for the Grant Trend Monitor sections:
FOR tier definitions, badge styles, and momentum colours.
"""
from typing import Dict

# ANZSRC 2020 FOR codes — urban research domain, structured by relevance tier
FOR_TIERS: Dict[str, Dict] = {
    # Core — highest relevance to AURIN
    "3304": {"name": "Urban and regional planning",      "tier": "Core"},
    "3301": {"name": "Architecture",                     "tier": "Core"},
    "3302": {"name": "Building",                         "tier": "Core"},
    "4013": {"name": "Geomatic engineering",             "tier": "Core"},
    "4005": {"name": "Civil engineering",                "tier": "Core"},
    "4406": {"name": "Human geography",                  "tier": "Core"},
    "4403": {"name": "Demography",                       "tier": "Core"},
    "4407": {"name": "Policy and administration",        "tier": "Core"},
    "4410": {"name": "Sociology",                        "tier": "Core"},
    "4404": {"name": "Development studies",              "tier": "Core"},
    # Related — secondary relevance
    "3702": {"name": "Earth sciences (climate/hazards)", "tier": "Related"},
    "3801": {"name": "Economics (urban/transport)",      "tier": "Related"},
    "3509": {"name": "Commerce and transport",           "tier": "Related"},
    "4101": {"name": "Environmental studies",            "tier": "Related"},
    "4205": {"name": "Health (community care)",          "tier": "Related"},
    # Contextual — background relevance
    "4505": {"name": "Indigenous studies",               "tier": "Contextual"},
    "4511": {"name": "Maori studies",                    "tier": "Contextual"},
}

TIER_BADGE = {
    "Core":       {"fg": "#1a56db", "bg": "#e8f0fe"},
    "Related":    {"fg": "#0e9f6e", "bg": "#def7ec"},
    "Contextual": {"fg": "#6b7280", "bg": "#f3f4f6"},
}

MOMENTUM_COLOR = {
    "high":    "#22c55e",
    "medium":  "#f59e0b",
    "low":     "#3b82f6",
    "decline": "#ef4444",
}
