"""
Skill and Technology Extraction engine for Danish Job Market Analytics.
Extracts programming languages, data engineering tools, cloud platforms, and AI frameworks
using compiled regex patterns with word boundary handling.
Loads rules from config/skills.json / config/skills.yaml.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

class SkillExtractor:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else None
        self.skills_by_category: Dict[str, List[Dict[str, Any]]] = {}
        self.compiled_rules: List[Tuple[str, str, re.Pattern]] = []
        self._load_config()

    def _load_config(self) -> None:
        """Load skills catalog from json or yaml with fallback."""
        loaded = False
        paths_to_try = [
            self.config_path,
            Path("config/skills.json"),
            Path("config/skills.yaml"),
        ]

        for p in paths_to_try:
            if p and p.exists():
                try:
                    if p.suffix == ".json":
                        with open(p, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            self.skills_by_category = data.get("categories", {})
                            loaded = True
                            break
                    elif p.suffix == ".yaml" or p.suffix == ".yml":
                        # Parse simple YAML structure without requiring PyYAML
                        self.skills_by_category = self._parse_simple_yaml(p)
                        if self.skills_by_category:
                            loaded = True
                            break
                except Exception as e:
                    logger.warning(f"Could not load config from {p}: {e}")

        if not loaded:
            self._load_default_skills()

        self._compile_patterns()

    def _parse_simple_yaml(self, path: Path) -> Dict[str, List[Dict[str, Any]]]:
        """Simple YAML fallback parser for skills config."""
        categories: Dict[str, List[Dict[str, Any]]] = {}
        current_cat = None
        current_skill = None

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if line.startswith("  ") and not line.startswith("    ") and stripped.endswith(":"):
                    current_cat = stripped[:-1].strip()
                    categories[current_cat] = []
                elif stripped.startswith("- name:") and current_cat:
                    name = stripped.split(":", 1)[1].strip().strip('"').strip("'")
                    current_skill = {"name": name, "pattern": f"\\b{re.escape(name)}\\b"}
                    categories[current_cat].append(current_skill)
                elif stripped.startswith("pattern:") and current_skill:
                    pattern = stripped.split(":", 1)[1].strip().strip('"').strip("'")
                    current_skill["pattern"] = pattern

        return categories

    def _load_default_skills(self) -> None:
        """Built-in fallback catalog if no config files found."""
        self.skills_by_category = {
            "Programming": [
                {"name": "Python", "pattern": r"\bpython\b|\bpy3?\b"},
                {"name": "Java", "pattern": r"\bjava\b(?!script)"},
                {"name": "JavaScript", "pattern": r"\bjavascript\b|\bjs\b"},
                {"name": "TypeScript", "pattern": r"\btypescript\b|\bts\b"},
                {"name": "C#", "pattern": r"(?:\bc#|\bcsharp\b)(?=[,\s\.\)/;]|\b|$)"},
                {"name": "C++", "pattern": r"(?:\bc\+\+|\bcpp\b)(?=[,\s\.\)/;]|\b|$)"},
                {"name": "Go", "pattern": r"(?:\bgolang\b|\bgo\b(?=[,\s\.\)/;]|\b|$))"},
                {"name": "Rust", "pattern": r"\brust\b"}
            ],
            "Data": [
                {"name": "SQL", "pattern": r"\bsql\b|\bt-sql\b|\bpl/sql\b"},
                {"name": "Pandas", "pattern": r"\bpandas\b"},
                {"name": "Apache Spark", "pattern": r"\bspark\b|\bpyspark\b|\bapache\s+spark\b"},
                {"name": "Databricks", "pattern": r"\bdatabricks\b"},
                {"name": "Microsoft Fabric", "pattern": r"\bmicrosoft\s+fabric\b|\bms\s+fabric\b|\bfabric\b"},
                {"name": "Power BI", "pattern": r"\bpower\s*bi\b|\bpbi\b"},
                {"name": "Snowflake", "pattern": r"\bsnowflake\b"},
                {"name": "Apache Airflow", "pattern": r"\bairflow\b"},
                {"name": "dbt", "pattern": r"\bdbt\b|\bdata\s+build\s+tool\b"}
            ],
            "Cloud": [
                {"name": "Azure", "pattern": r"\bazure\b"},
                {"name": "AWS", "pattern": r"\baws\b|\bamazon\s+web\s+services\b"},
                {"name": "GCP", "pattern": r"\bgcp\b|\bgoogle\s+cloud\b"},
                {"name": "Docker", "pattern": r"\bdocker\b"},
                {"name": "Kubernetes", "pattern": r"\bkubernetes\b|\bk8s\b"},
                {"name": "Terraform", "pattern": r"\bterraform\b"}
            ],
            "AI": [
                {"name": "Machine Learning", "pattern": r"\bmachine\s+learning\b|\bml\b"},
                {"name": "LLM", "pattern": r"\bllm[s]?\b|\blarge\s+language\s+model[s]?\b"},
                {"name": "Generative AI", "pattern": r"\bgenerative\s+ai\b|\bgenai\b"},
                {"name": "RAG", "pattern": r"\brag\b|\bretrieval\s+augmented\s+generation\b"}
            ],
            "Development": [
                {"name": "React", "pattern": r"\breact(?:\.js)?\b"},
                {"name": "Node.js", "pattern": r"\bnode(?:\\.js)?\b"},
                {"name": ".NET", "pattern": r"(?<!\w)(?:\.net\b|\bdotnet\b|\basp\.net\b)"},
                {"name": "FastAPI", "pattern": r"\bfastapi\b"}
            ]
        }

    def _compile_patterns(self) -> None:
        self.compiled_rules = []
        for cat, skills in self.skills_by_category.items():
            for item in skills:
                name = item["name"]
                pat_str = item.get("pattern", rf"\b{re.escape(name)}\b")
                try:
                    compiled = re.compile(pat_str, re.IGNORECASE)
                    self.compiled_rules.append((name, cat, compiled))
                except re.error as e:
                    logger.error(f"Invalid regex for {name}: {e}")

    def extract_skills(self, text: str, explicit_skills: Optional[List[str]] = None) -> List[Dict[str, str]]:
        """
        Extract unique skills from text content and reconcile with any explicit tags.
        Returns list of dicts: [{'name': 'Python', 'category': 'Programming'}, ...]
        """
        found_map: Dict[str, str] = {}
        combined_text = (text or "").lower()

        # Check regex rules
        for name, category, pattern in self.compiled_rules:
            if pattern.search(combined_text):
                found_map[name] = category

        # Reconcile explicit tags if present
        if explicit_skills:
            for exp in explicit_skills:
                exp_clean = exp.strip()
                for name, category, pattern in self.compiled_rules:
                    if exp_clean.lower() == name.lower() or pattern.search(exp_clean.lower()):
                        found_map[name] = category

        return [{"name": k, "category": v} for k, v in sorted(found_map.items())]
