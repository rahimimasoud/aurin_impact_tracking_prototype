"""
Shared constants for the Research Trend Monitor sections:
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

# Generic academic / research stopwords that carry no field-specific signal
KEYWORD_STOPWORDS: set = {
    # Research / study framing
    "australia", "australian", "case study", "study", "studies", "research", "paper", "article", "review", "analysis",
    "analysis", "analyses", "approach", "approaches", "method", "methods", "literature", "literature review", "meta-analysis", "systematic review",
    "methodology", "framework", "frameworks", "model", "models", "modelling", "platform", "platforms", "tool", "tools", "technique", "techniques", "application", "applications",
    "modeling", "theory", "theories", "concept", "concepts", "perspective",
    "perspectives", "overview", "survey", "surveys", "investigation",
    # Findings / results
    "result", "results", "finding", "findings", "outcome", "outcomes",
    "evidence", "observation", "observations", "conclusion", "conclusions",
    "insight", "insights",
    # Generic descriptors
    "effect", "effects", "impact", "impacts", "factor", "factors",
    "role", "roles", "relationship", "relationships", "association",
    "associations", "influence", "influences", "implication", "implications",
    "issue", "issues", "challenge", "challenges", "problem", "problems",
    "solution", "solutions", "strategy", "strategies", "mechanism",
    "mechanisms", "process", "processes", "pattern", "patterns",
    "context", "contexts", "condition", "conditions", "aspect", "aspects",
    "feature", "features", "dimension", "dimensions", "component",
    "components", "element", "elements", "variable", "variables",
    "parameter", "parameters", "indicator", "indicators",
    # Data / methods
    "data", "dataset", "datasets", "sample", "samples", "case", "cases",
    "example", "examples", "experiment", "experiments", "test", "tests",
    "measure", "measures", "measurement", "measurements", "assessment",
    "assessments", "evaluation", "evaluations", "comparison", "comparisons",
    "simulation", "simulations", "algorithm", "algorithms",
    # Generic actions
    "use", "uses", "using", "used", "based", "proposed", "proposed",
    "provide", "provides", "identify", "identifies", "show", "shows",
    "present", "presents", "discuss", "discusses", "examine", "examines",
    "explore", "explores", "investigate", "investigates", "develop",
    "develops", "development", "improve", "improves", "improvement",
    "increase", "increases", "reduce", "reduces", "reduction", "apply",
    "applies", "application", "applications", "consider", "considers",
    "include", "includes", "require", "requires", "suggest", "suggests",
    # Generic nouns
    "system", "systems", "area", "areas", "field", "fields", "domain",
    "domains", "section", "sections", "type", "types", "form", "forms",
    "level", "levels", "scale", "scales", "range", "scope", "focus",
    "number", "numbers", "set", "sets", "group", "groups", "unit", "units",
    "structure", "structures", "network", "networks", "environment",
    "environments", "region", "regions", "location", "locations",
    "space", "spaces", "time", "times", "period", "periods", "year", "years",
    "rate", "rates", "value", "values", "size", "sizes", "change", "changes",
    "trend", "trends", "performance", "performances",
    # Common adjectives / adverbs
    "new", "novel", "current", "recent", "existing", "different", "various",
    "multiple", "large", "small", "high", "low", "significant", "important",
    "key", "main", "major", "general", "specific", "global", "local",
    "national", "international", "social", "economic", "political",
    "potential", "possible", "effective", "efficient", "complex", "simple",
    # Stopwords that slip through short-length filter
    "the", "and", "for", "that", "with", "this", "from", "are", "was",
    "has", "have", "had", "its", "not", "but", "can", "all", "one",
    "also", "both", "well", "than", "more", "less", "most", "such",
    "other", "these", "those", "their", "each", "been", "will", "would",
    "may", "might", "could", "should", "into", "over", "under", "within",
    "between", "across", "through", "about", "while", "where", "when",
    "how", "what", "which",
}