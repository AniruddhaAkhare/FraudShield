from config import RISK_THRESHOLDS


def compute_risk_level(score: float) -> str:
    """Convert a numeric risk score 0-100 into a label."""
    if score >= RISK_THRESHOLDS["CRITICAL"]:
        return "CRITICAL"
    elif score >= RISK_THRESHOLDS["HIGH"]:
        return "HIGH"
    elif score >= RISK_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    else:
        return "LOW"


def is_fraud_verdict(risk_score: float, confidence: float) -> bool:
    """Return True when the analysis indicates fraud."""
    # Flag as fraud if risk is medium+ AND confidence is reasonable
    return risk_score >= 40 and confidence >= 50


def parse_score_from_text(text: str, key: str = "risk_score") -> float:
    """Extract a numeric value from an LLM response (fallback parser)."""
    import re
    patterns = [
        rf'"{key}"\s*:\s*(\d+(?:\.\d+)?)',
        rf"'{key}'\s*:\s*(\d+(?:\.\d+)?)",
        rf"{key}\s*[=:]\s*(\d+(?:\.\d+)?)",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return min(float(m.group(1)), 100.0)
    return 0.0


def build_summary(result: dict) -> dict:
    """Add computed fields to the raw analysis result."""
    score = float(result.get("risk_score", 0))
    conf = float(result.get("confidence", 0))
    result["risk_level"] = compute_risk_level(score)
    result["is_fraud"] = is_fraud_verdict(score, conf)
    return result
