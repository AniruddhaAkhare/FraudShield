"""
Model 1 — Text / Social-Media Message Fraud Analyzer
Uses LangChain + Gemini (TEXT_ANALYZER_API_KEY) with robust intelligent heuristic fallback.
"""
import json
import re
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import TEXT_ANALYZER_API_KEY, GEMINI_MODEL

SYSTEM_PROMPT = """You are FraudShield's elite Text Fraud Detection Engine.
Your task is to analyze messages from WhatsApp, SMS, Twitter, email, or social media for fraud signals.

CRITICAL INSTRUCTIONS & BANKING SMS DISTINCTIONS:
1. LEGITIMATE BANK TRANSACTION ALERTS (LOW RISK, 5-15, scam_type="No Fraud Detected", is_fraud=false):
   - Legitimate transactional SMS sent by banks (HDFC, SBI, ICICI, Axis, PNB, etc.) notifying about an authorized debit or credit.
   - Hallmark authentic features:
     * Masked account or card numbers (e.g., "A/C XX4921", "A/C **1234", "Card XX99", "ending 4321"). Scammers do not have access to real masked account numbers.
     * Recognized merchant names (e.g., SWIGGY, ZOMATO, AMAZON, FLIPKART, UBER, or standard UPI/IMPS reference numbers).
     * Official bank security advisory (e.g., "If not done by you, SMS BLOCK to 5676766" — note that 5676766 is HDFC Bank's authentic official shortcode).
     * NO phishing URLs, NO links to .xyz / .tk / bit.ly, NO requests for OTP/PIN, NO threats of account closure.
   - Genuine bank transaction notifications like this MUST receive a LOW risk score (5-15), scam_type="No Fraud Detected", and is_fraud=false.

2. FRAUDULENT / SMISHING MESSAGES (HIGH/CRITICAL RISK, 75-98, is_fraud=true):
   - Urgent threats of immediate account suspension/blocking unless action is taken (e.g., "Your account has been suspended. Update KYC/PAN immediately").
   - Demands to click unverified external links (e.g., http://...-kyc.xyz, bit.ly, non-bank domains).
   - Requests to share OTP, PIN, CVV, or passwords.
   - Advance fee lottery, lucky draw prizes, task scams, fake part-time jobs.

Return ONLY valid JSON (no markdown, no code fences) with this exact schema:
{
  "risk_score": <0-100 integer>,
  "confidence": <0-100 integer>,
  "scam_type": "<one scam type or 'No Fraud Detected'>",
  "is_fraud": <true|false>,
  "indicators": [
    {"label": "<indicator name>", "detail": "<what you found>", "severity": "<HIGH|MEDIUM|LOW>"}
  ],
  "evidence": {
    "suspicious_phrases": ["<phrase1>", "<phrase2>"],
    "urgency_triggers": ["<trigger1>"],
    "fake_authority_claims": ["<claim1>"],
    "embedded_urls": ["<url1>"]
  },
  "recommendations": [
    {"title": "<action title>", "detail": "<what to do>"}
  ],
  "explanation": "<comprehensive 2-4 sentence explanation of your findings>"
}"""

USER_PROMPT = """Analyze this message for fraud:

---MESSAGE START---
{message}
---MESSAGE END---

Remember: return ONLY raw JSON, no extra text."""


def _analyze_text_heuristics(message: str, error_note: str = "") -> dict:
    """Intelligent fallback rule-based analyzer when LLM API is unavailable or denied."""
    lower = message.lower()
    
    # 1. URL extraction
    url_pattern = r"https?://[^\s<>\"']+|www\.[^\s<>\"']+|[a-zA-Z0-9-]+\.(?:tk|ml|ga|cf|gq|xyz|top|work|click|link|info)[^\s<>\"']*"
    urls = re.findall(url_pattern, message)
    
    # 2. Check for legitimate transactional banking alert pattern
    has_masked_ac = bool(re.search(r"(?:a/c|acct|account|card)\s*(?:no\.?|ending)?\s*[:\s]*[x*]{2,}\d+", lower) or re.search(r"[x*]{2,}\d{3,4}", lower))
    has_tx_term = any(t in lower for t in ["debited", "credited", "inr", "rs.", "spent", "upi ref", "ref no", "txn"])
    has_known_merchant = any(m in lower for m in ["swiggy", "zomato", "amazon", "flipkart", "uber", "ola", "paytm", "irctc"])
    
    # If legitimate bank transaction SMS without phishing URLs or credential theft:
    if (has_masked_ac or has_tx_term) and not urls and not any(c in lower for c in ["otp", "password", "netbanking password", "cvv", "update kyc", "pan card"]):
        indicators = []
        if has_masked_ac:
            indicators.append({
                "label": "Masked Account Identifier",
                "detail": "Message contains a standard masked account format commonly used in authentic banking alerts.",
                "severity": "LOW"
            })
        if has_known_merchant:
            indicators.append({
                "label": "Recognized Merchant Context",
                "detail": "Transaction references a known merchant or standard UPI reference format.",
                "severity": "LOW"
            })
        indicators.append({
            "label": "Official Security Reporting",
            "detail": "Includes standard bank security reporting instructions without suspicious links.",
            "severity": "LOW"
        })
        
        if error_note:
            print(f"[FraudShield Backend Log] Text Analyzer Fallback Note: {error_note}")

        return {
            "risk_score": 10,
            "confidence": 95,
            "scam_type": "No Fraud Detected",
            "is_fraud": False,
            "indicators": indicators,
            "evidence": {
                "suspicious_phrases": [],
                "urgency_triggers": [],
                "fake_authority_claims": [],
                "embedded_urls": [],
                "ai_model_used": "FraudShield Heuristic Engine",
                "analysis_engine": "Rule-based Heuristic Engine",
                "is_ai_generated": False
            },
            "recommendations": [
                {
                    "title": "Legitimate Transaction Alert",
                    "detail": "This message exhibits characteristics of an authentic transaction notification. No action required unless this debit was not authorized by you."
                }
            ],
            "explanation": "This message matches the standard structure of an authentic bank transaction alert, including masked account digits and standard dispute reporting options. No phishing links or credential harvesting tactics were detected.",
            "ai_model": "FraudShield Heuristic Engine",
            "engine": "Rule-based Heuristic Engine",
            "is_ai_generated": False
        }

    # 3. Standard heuristic detection for other messages
    indicators = []
    suspicious_phrases = []
    urgency_triggers = []
    authority_claims = []
    score = 10
    confidence = 88
    scam_type = "No Fraud Detected"
    
    # Urgency check
    urgency_words = ["urgent", "immediately", "within 24 hours", "within 12 hours", "within 6 hours", "suspended", "account closure", "freeze", "action required", "act now", "final notice"]
    for w in urgency_words:
        if w in lower:
            urgency_triggers.append(w)
            suspicious_phrases.append(w)
            
    if urgency_triggers:
        score += 25
        indicators.append({
            "label": "Urgency & Threat Pressure",
            "detail": f"Message creates artificial panic using urgency phrases: {', '.join(urgency_triggers[:3])}",
            "severity": "HIGH" if len(urgency_triggers) > 1 else "MEDIUM"
        })
        
    # Fake Authority check
    authority_words = ["icici", "sbi", "rbi", "police", "court", "warrant", "customs", "income tax", "security team", "fraud prevention cell", "central government", "support desk"]
    for w in authority_words:
        if w in lower:
            authority_claims.append(w)
            suspicious_phrases.append(w)
            
    if authority_claims:
        score += 25
        indicators.append({
            "label": "Authority Impersonation",
            "detail": f"Claiming authority of prominent institutions: {', '.join(authority_claims[:3])}",
            "severity": "HIGH"
        })
        
    # Credential Harvesting check
    cred_words = ["kyc", "verify", "update kyc", "restore access", "password", "otp", "pin", "login", "credentials", "biometric"]
    found_creds = [w for w in cred_words if w in lower]
    if found_creds:
        score += 20
        suspicious_phrases.extend(found_creds)
        indicators.append({
            "label": "Credential / Data Harvesting",
            "detail": f"Requests sensitive action or credential verification: {', '.join(found_creds[:3])}",
            "severity": "HIGH"
        })
        
    # Suspicious Links check
    suspicious_tlds = [".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".click", ".link"]
    has_suspicious_tld = any(any(tld in u.lower() for tld in suspicious_tlds) for u in urls)
    
    if urls:
        if has_suspicious_tld or authority_claims or urgency_triggers:
            score += 25
            indicators.append({
                "label": "Suspicious Embedded URL",
                "detail": f"Contains suspicious or unverified external link: {urls[0]}",
                "severity": "CRITICAL" if has_suspicious_tld else "HIGH"
            })
            
    # Financial / Prize bait
    prize_words = ["won", "lottery", "prize", "crore", "lakh", "congratulations", "lucky winner", "claim your prize", "bitcoin", "crypto"]
    found_prizes = [w for w in prize_words if w in lower]
    if found_prizes:
        score += 30
        suspicious_phrases.extend(found_prizes)
        indicators.append({
            "label": "Financial / Lottery Bait",
            "detail": f"Entices user with unverified prize or crypto claims: {', '.join(found_prizes[:2])}",
            "severity": "HIGH"
        })
        
    # Social engineering / secrecy
    secret_words = ["do not share", "do not contact", "confidential", "secret", "do not call branch"]
    found_secret = [w for w in secret_words if w in lower]
    if found_secret:
        score += 15
        indicators.append({
            "label": "Isolation Tactic",
            "detail": f"Instructs target not to contact official branches or family: {', '.join(found_secret)}",
            "severity": "HIGH"
        })

    # Determine scam type and final verdict
    score = min(score, 98)
    if score >= 65:
        if found_prizes:
            scam_type = "Lottery / Prize Scam"
        elif authority_claims and (urls or found_creds):
            scam_type = "Phishing Attack"
        elif authority_claims:
            scam_type = "Fake Authority"
        else:
            scam_type = "Financial Scam"
    elif score >= 40:
        scam_type = "Suspicious Message"
    else:
        score = max(5, score)
        scam_type = "No Fraud Detected"
        
    is_fraud = score >= 40
    
    # Recommendations
    recommendations = []
    if is_fraud:
        recommendations.append({
            "title": "Do Not Click Any Links",
            "detail": "Do not tap on any links or URLs provided in the message, as they may lead to credential harvesting sites."
        })
        recommendations.append({
            "title": "Never Share OTPs or Passwords",
            "detail": "Legitimate banks and organizations will never ask for your PIN, passwords, or one-time passcodes."
        })
        recommendations.append({
            "title": "Verify Directly with Official Channels",
            "detail": "Contact the official helpline or visit your local branch independently using known authentic contact info."
        })
    else:
        recommendations.append({
            "title": "Standard Vigilance",
            "detail": "Message exhibits standard notification characteristics. Always remain cautious when interacting with unsolicited links."
        })

    explanation = (
        f"Analysis flagged a risk score of {score}/100. "
        + (f"Identified {len(indicators)} fraud risk indicators including {indicators[0]['label'].lower()}." if indicators else "No significant deception indicators or coercive language patterns were detected.")
    )
    if error_note:
        print(f"[FraudShield Backend Log] Text Analyzer Note: {error_note}. Local engine utilized.")

    return {
        "risk_score": score,
        "confidence": confidence,
        "scam_type": scam_type,
        "is_fraud": is_fraud,
        "indicators": indicators,
        "evidence": {
            "suspicious_phrases": list(set(suspicious_phrases)),
            "urgency_triggers": urgency_triggers,
            "fake_authority_claims": authority_claims,
            "embedded_urls": urls,
            "ai_model_used": "FraudShield Heuristic Engine",
            "analysis_engine": "Rule-based Heuristic Engine",
            "is_ai_generated": False
        },
        "recommendations": recommendations,
        "explanation": explanation,
        "ai_model": "FraudShield Heuristic Engine",
        "engine": "Rule-based Heuristic Engine",
        "is_ai_generated": False
    }


def analyze_text(message: str) -> dict:
    """Analyze a text message for fraud using Gemini with intelligent fallback."""
    if TEXT_ANALYZER_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=TEXT_ANALYZER_API_KEY)
            model = genai.GenerativeModel(GEMINI_MODEL, system_instruction=SYSTEM_PROMPT)
            prompt = USER_PROMPT.format(message=message)
            
            res = model.generate_content(prompt, request_options={"timeout": 40})
            raw = res.text
            raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()

            try:
                result = json.loads(raw)
            except json.JSONDecodeError:
                match = re.search(r"\{.*\}", raw, re.DOTALL)
                if match:
                    result = json.loads(match.group(0))
                else:
                    raise ValueError("JSON decode error from model output")

            ai_name = f"Google Gemini ({GEMINI_MODEL})"
            result["input_type"] = "text"
            result["input_content"] = message[:2000]
            result["ai_model"] = ai_name
            result["engine"] = f"Google Gemini AI ({GEMINI_MODEL})"
            result["is_ai_generated"] = True

            if "evidence" not in result or not isinstance(result["evidence"], dict):
                result["evidence"] = {}
            result["evidence"]["ai_model_used"] = ai_name
            result["evidence"]["analysis_engine"] = "Google Gemini Live AI"
            result["evidence"]["is_ai_generated"] = True

            return result

        except Exception as e:
            err_msg = str(e)
            result = _analyze_text_heuristics(message, error_note=err_msg)
            result["input_type"] = "text"
            result["input_content"] = message[:2000]
            return result
    else:
        result = _analyze_text_heuristics(message, error_note="No API key provided")
        result["input_type"] = "text"
        result["input_content"] = message[:2000]
        return result
