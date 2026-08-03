"""
Regression test: custom rules' "risk" field must drive FileClassifier's
risk classification, not just their "category" label.

Previously _classify_risk() only matched hardcoded category names, so files
caught by config/defaults.py's default rules (*.log, *.tmp, __pycache__/,
*.pyc, node_modules/ - all declared "risk": "safe") fell through to
RiskLevel.CONFIRM_NEEDED instead.
"""

from diskcleaner.core.classifier import FileClassifier, RiskLevel
from diskcleaner.core.scanner import FileInfo


def _file(name):
    return FileInfo(path=f"mock/{name}", name=name, size=10, mtime=0.0, is_dir=False, is_link=False)


def test_default_log_rule_is_safe():
    classifier = FileClassifier()
    result = classifier.classify([_file("app.log")])
    assert any(f.name == "app.log" for f in result["by_risk"][RiskLevel.SAFE.value])


def test_default_tmp_rule_is_safe():
    classifier = FileClassifier()
    result = classifier.classify([_file("scratch.tmp")])
    assert any(f.name == "scratch.tmp" for f in result["by_risk"][RiskLevel.SAFE.value])


def test_custom_rule_confirm_needed_risk_is_honored():
    from diskcleaner.config import Config

    config = Config.load()
    config.set("rules", [{"pattern": "*.mystery", "category": "Mystery", "risk": "confirm_needed"}])
    classifier = FileClassifier(config=config)

    result = classifier.classify([_file("thing.mystery")])
    assert any(f.name == "thing.mystery" for f in result["by_risk"][RiskLevel.CONFIRM_NEEDED.value])
