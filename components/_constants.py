"""
Shared constants across all trend monitor components:
FOR tier definitions, badge styles, momentum colours, and keyword stopwords.
"""
import os
from typing import Dict

from dotenv import load_dotenv

load_dotenv()
_ENV_DIMENSIONS: str = os.getenv('DIMENSIONS_API_KEY', '')
_ENV_OPENROUTER: str = os.getenv('OPENROUTER_API_KEY', '')
_ENV_SERPAPI: str = os.getenv('SERPAPI_KEY', '')

# ANZSRC 2020 FOR codes — urban research domain, structured by relevance tier
FOR_TIERS: Dict[str, Dict] = {
    # ── Core ─────────────────────────────────────────────────────────────────
    # Urban and regional planning (3304)
    "3304":   {"name": "Urban and regional planning",                          "tier": "Core"},
    "330401": {"name": "Community planning",                                   "tier": "Core"},
    "330403": {"name": "Housing markets, development and management",          "tier": "Core"},
    "330404": {"name": "Land use and environmental planning",                  "tier": "Core"},
    "330405": {"name": "Public participation and community engagement",        "tier": "Core"},
    "330406": {"name": "Regional analysis and development",                    "tier": "Core"},
    "330408": {"name": "Strategic, metropolitan and regional planning",        "tier": "Core"},
    "330409": {"name": "Transport planning",                                   "tier": "Core"},
    "330410": {"name": "Urban analysis and development",                       "tier": "Core"},
    "330411": {"name": "Urban design",                                         "tier": "Core"},
    "330412": {"name": "Urban informatics",                                    "tier": "Core"},
    "330413": {"name": "Urban planning and health",                            "tier": "Core"},
    "330499": {"name": "Urban and regional planning NEC",                      "tier": "Core"},
    # Demography (4403)
    "4403":   {"name": "Demography",                                           "tier": "Core"},
    "440302": {"name": "Fertility",                                            "tier": "Core"},
    "440303": {"name": "Migration (demography)",                               "tier": "Core"},
    "440305": {"name": "Population trends and policies",                       "tier": "Core"},
    # Human geography (4406) — urban/regional subcodes
    "4406":   {"name": "Human geography",                                      "tier": "Core"},
    "440602": {"name": "Development geography",                                "tier": "Core"},
    "440603": {"name": "Economic geography",                                   "tier": "Core"},
    "440604": {"name": "Environmental geography",                              "tier": "Core"},
    "440605": {"name": "Health geography",                                     "tier": "Core"},
    "440607": {"name": "Population geography",                                 "tier": "Core"},
    "440609": {"name": "Rural and regional geography",                         "tier": "Core"},
    "440610": {"name": "Social geography",                                     "tier": "Core"},
    "440611": {"name": "Transport geography",                                  "tier": "Core"},
    "440612": {"name": "Urban geography",                                      "tier": "Core"},
    # Policy and administration (4407) — urban policy subcodes
    "4407":   {"name": "Policy and administration",                            "tier": "Core"},
    "440703": {"name": "Economic development policy",                          "tier": "Core"},
    "440704": {"name": "Environment policy",                                   "tier": "Core"},
    "440706": {"name": "Health policy",                                        "tier": "Core"},
    "440707": {"name": "Housing policy",                                       "tier": "Core"},
    "440709": {"name": "Public policy",                                        "tier": "Core"},
    "440712": {"name": "Social policy",                                        "tier": "Core"},
    "440714": {"name": "Urban policy",                                         "tier": "Core"},
    # Spatial data and geomatics
    "4013":   {"name": "Geomatic engineering",                                 "tier": "Core"},
    "401302": {"name": "Geospatial information systems and geospatial data modelling", "tier": "Core"},
    "401304": {"name": "Photogrammetry and remote sensing",                    "tier": "Core"},
    "460106": {"name": "Spatial data and applications",                        "tier": "Core"},
    "490507": {"name": "Spatial statistics",                                   "tier": "Core"},
    # Urban sociology and community
    "441016": {"name": "Urban sociology and community studies",                "tier": "Core"},
    "440408": {"name": "Urban community development",                          "tier": "Core"},
    "440405": {"name": "Poverty, inclusivity and wellbeing",                   "tier": "Core"},
    # Indigenous urban/regional (Australia-specific)
    "450527": {"name": "Aboriginal and Torres Strait Islander urban and regional planning", "tier": "Core"},
    "450513": {"name": "Aboriginal and Torres Strait Islander human geography and demography", "tier": "Core"},
    "450505": {"name": "Aboriginal and Torres Strait Islander community and regional development", "tier": "Core"},

    # ── Related ───────────────────────────────────────────────────────────────
    # Climate change
    "3702":   {"name": "Climate change science",                               "tier": "Related"},
    "370201": {"name": "Climate change processes",                             "tier": "Related"},
    "4101":   {"name": "Climate change impacts and adaptation",                "tier": "Related"},
    "410103": {"name": "Human impacts of climate change and human adaptation", "tier": "Related"},
    "410102": {"name": "Ecological impacts of climate change and adaptation",  "tier": "Related"},
    "410101": {"name": "Carbon sequestration science",                         "tier": "Related"},
    "370903": {"name": "Natural hazards",                                      "tier": "Related"},
    "370705": {"name": "Urban hydrology",                                      "tier": "Related"},
    "370102": {"name": "Air pollution processes and air quality measurement",  "tier": "Related"},
    # Energy transition
    "400803": {"name": "Electrical energy generation (incl. renewables)",      "tier": "Related"},
    "400804": {"name": "Electrical energy storage",                            "tier": "Related"},
    "400805": {"name": "Electrical energy transmission, networks and systems", "tier": "Related"},
    "400404": {"name": "Electrochemical energy storage and conversion",        "tier": "Related"},
    "401102": {"name": "Environmentally sustainable engineering",              "tier": "Related"},
    # Urban economics and transport
    "380118": {"name": "Urban and regional economics",                         "tier": "Related"},
    "380117": {"name": "Transport economics",                                  "tier": "Related"},
    "3509":   {"name": "Commerce and transport",                               "tier": "Related"},
    "350906": {"name": "Public transport",                                     "tier": "Related"},
    "400512": {"name": "Transport engineering",                                "tier": "Related"},
    # Environmental management
    "4104":   {"name": "Environmental management",                             "tier": "Related"},
    "410401": {"name": "Conservation and biodiversity",                        "tier": "Related"},
    "410402": {"name": "Environmental assessment and monitoring",              "tier": "Related"},
    "410404": {"name": "Environmental management",                             "tier": "Related"},
    "410405": {"name": "Environmental rehabilitation and restoration",         "tier": "Related"},
    # Public and community health
    "4205":   {"name": "Health (community care)",                              "tier": "Related"},
    "420606": {"name": "Social determinants of health",                        "tier": "Related"},
    "420305": {"name": "Health and community services",                        "tier": "Related"},
    "420203": {"name": "Environmental epidemiology",                           "tier": "Related"},
    # Migration and social change
    "441013": {"name": "Sociology of migration, ethnicity and multiculturalism", "tier": "Related"},
    "441004": {"name": "Social change",                                        "tier": "Related"},
    "441012": {"name": "Sociology of inequalities",                            "tier": "Related"},
    "441001": {"name": "Applied sociology and social impact assessment",       "tier": "Related"},
    "440406": {"name": "Rural community development",                          "tier": "Related"},
    # Development studies and economics
    "4404":   {"name": "Development studies",                                  "tier": "Related"},
    "380105": {"name": "Environment and resource economics",                   "tier": "Related"},
    # Infrastructure
    "400508": {"name": "Infrastructure engineering and asset management",      "tier": "Related"},
    "400513": {"name": "Water resources engineering",                          "tier": "Related"},
    "401106": {"name": "Waste management, reduction, reuse and recycling",     "tier": "Related"},
    # Informatics for sustainability
    "460907": {"name": "Information systems for sustainable development",      "tier": "Related"},
    "461010": {"name": "Social and community informatics",                     "tier": "Related"},

    # ── Contextual ────────────────────────────────────────────────────────────
    # Architecture and building
    "3301":   {"name": "Architecture",                                         "tier": "Contextual"},
    "3302":   {"name": "Building",                                             "tier": "Contextual"},
    "330106": {"name": "Architecture for disaster relief",                     "tier": "Contextual"},
    "330110": {"name": "Sustainable architecture",                             "tier": "Contextual"},
    "330314": {"name": "Sustainable design",                                   "tier": "Contextual"},
    "330313": {"name": "Social design",                                        "tier": "Contextual"},
    # History, law, and governance
    "330402": {"name": "History and theory of the built environment",          "tier": "Contextual"},
    "480202": {"name": "Climate change law",                                   "tier": "Contextual"},
    "480204": {"name": "Mining, energy and natural resources law",             "tier": "Contextual"},
    "480704": {"name": "Migration, asylum and refugee law",                    "tier": "Contextual"},
    # Economics (broader)
    "389902": {"name": "Ecological economics",                                 "tier": "Contextual"},
    "350201": {"name": "Environment and climate finance",                      "tier": "Contextual"},
    "400402": {"name": "Chemical and thermal processes in energy and combustion", "tier": "Contextual"},
    # Rural and remote
    "441003": {"name": "Rural sociology",                                      "tier": "Contextual"},
    "441002": {"name": "Environmental sociology",                              "tier": "Contextual"},
    "420321": {"name": "Rural and remote health services",                     "tier": "Contextual"},
    # Ageing and education
    "520106": {"name": "Psychology of ageing",                                 "tier": "Contextual"},
    "390410": {"name": "Multicultural education",                              "tier": "Contextual"},
    "520501": {"name": "Community psychology",                                 "tier": "Contextual"},
    # Migration history
    "430319": {"name": "Migration history",                                    "tier": "Contextual"},
    # Broader Indigenous studies
    "4505":   {"name": "Indigenous studies",                                   "tier": "Contextual"},
    "4511":   {"name": "Maori studies",                                        "tier": "Contextual"},
    "4503":   {"name": "Aboriginal and Torres Strait Islander environmental knowledges", "tier": "Contextual"},
    # Civil engineering (broader)
    "4005":   {"name": "Civil engineering",                                    "tier": "Contextual"},
    "401103": {"name": "Global and planetary environmental engineering",       "tier": "Contextual"},
    # Energy (less urban-specific)
    "460606": {"name": "Energy-efficient computing",                           "tier": "Contextual"},
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
    "analyses", "approach", "approaches", "method", "methods", "literature", "literature review", "meta-analysis", "systematic review",
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
    "use", "uses", "using", "used", "based", "proposed",
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
