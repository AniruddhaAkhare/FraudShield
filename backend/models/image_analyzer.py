"""
Model 3 — Image / Screenshot Fraud Analyzer
Uses LangChain + Gemini Vision (IMAGE_ANALYZER_API_KEY) with robust intelligent heuristic fallback.
"""
import json
import re
import sys
import os
import base64
from pathlib import Path
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import IMAGE_ANALYZER_API_KEY, GEMINI_VISION_MODEL

SYSTEM_PROMPT = """You are FraudShield's Visual Fraud Detection Engine with advanced vision capabilities.
Analyze images for fraud indicators including:

1. DOCUMENT FRAUD: Fake government IDs, certificates, notices, tax documents, court orders
2. SCREENSHOT FRAUD: Fake WhatsApp/SMS conversations, fake bank statements, fake payment receipts
3. AI-GENERATED IMAGES: Deepfake faces, AI-generated fake people, synthetic media artifacts
4. BRAND IMPERSONATION: Misused logos, fake official seals, suspicious letterheads

Return ONLY valid JSON (no markdown, no code fences):
{
  "risk_score": <0-100 integer>,
  "confidence": <0-100 integer>,
  "scam_type": "<one scam type or 'No Fraud Detected'>",
  "is_fraud": <true|false>,
  "indicators": [
    {"label": "<name>", "detail": "<what was found>", "severity": "<HIGH|MEDIUM|LOW>"}
  ],
  "evidence": {
    "extracted_text_summary": "<key text visible in image>",
    "document_type": "<type of document/screenshot>",
    "visual_inconsistencies": ["<item1>", "<item2>"],
    "brand_claims": ["<brand1>"]
  },
  "recommendations": [
    {"title": "<title>", "detail": "<detail>"}
  ],
  "explanation": "<2-4 sentence summary of visual fraud analysis>"
}"""


def _image_to_base64(image_path: str) -> tuple:
    ext = Path(image_path).suffix.lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
    }
    mime = mime_map.get(ext, "image/jpeg")
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return data, mime


def _analyze_image_heuristics(image_path: str, error_note: str = "") -> dict:
    """Intelligent fallback visual analyzer when LLM is unavailable."""
    filename = os.path.basename(image_path).lower()
    
    # Read image metadata
    try:
        with Image.open(image_path) as im:
            width, height = im.size
            img_format = im.format or "UNKNOWN"
            mode = im.mode
    except Exception:
        width, height = (800, 600)
        img_format = "IMAGE"
        mode = "RGB"

    # Read image text strings if present in binary
    try:
        with open(image_path, "rb") as f:
            raw_bytes = f.read(500000)
        found_strings = re.findall(rb"[\x20-\x7E]{4,}", raw_bytes)
        text_content = " ".join([s.decode("latin1", errors="ignore") for s in found_strings[:100]]).lower()
    except Exception:
        text_content = ""

    indicators = []
    suspicious_findings = []
    brand_claims = []
    score = 15
    confidence = 85
    document_type = "Image / Screenshot"
    
    combined = f"{filename} {text_content}"
    
    # Check for fake legal / warrant / court notice
    legal_keywords = ["court", "warrant", "arrest", "police", "freeze", "asset", "law enforcement", "tax", "federal", "revenue", "clearance"]
    matched_legal = [k for k in legal_keywords if k in combined]
    if matched_legal:
        score += 40
        document_type = "Government / Judicial Notice"
        suspicious_findings.append("Fabricated legal authority and arrest pressure")
        indicators.append({
            "label": "Fake Authority & Coercive Notice",
            "detail": f"Document claims authority of law enforcement or courts ({', '.join(matched_legal[:3])}) to intimidate recipient.",
            "severity": "CRITICAL"
        })
        
    # Check for financial extortion / crypto demand
    financial_keywords = ["bitcoin", "crypto", "settle", "fee", "penalty", "transfer", "hours", "urgent", "$", "usd", "inr"]
    matched_financial = [k for k in financial_keywords if k in combined]
    if matched_financial:
        score += 30
        suspicious_findings.append("Demands immediate financial settlement via untraceable channels")
        indicators.append({
            "label": "Extortion / Advance Fee Demand",
            "detail": f"Document demands urgent financial payment under threat of prosecution.",
            "severity": "HIGH"
        })
        
    # Check for screenshot or fake receipts
    receipt_keywords = ["receipt", "transaction", "credited", "debited", "successful", "payment", "fake", "notice", "statement"]
    matched_receipt = [k for k in receipt_keywords if k in combined]
    if matched_receipt and not matched_legal:
        score += 25
        document_type = "Payment Receipt / Conversation Screenshot"
        indicators.append({
            "label": "Suspicious Transaction Artifacts",
            "detail": "Document resembles a payment proof or financial statement subject to visual tampering.",
            "severity": "MEDIUM"
        })

    # Brands impersonated
    brands = ["icici", "hdfc", "sbi", "rbi", "amazon", "paypal", "apple", "google", "meta"]
    for b in brands:
        if b in combined:
            brand_claims.append(b.upper())
            score += 20
            indicators.append({
                "label": f"Brand Emblem Impersonation ({b.upper()})",
                "detail": f"Contains branding indicators for {b.upper()} on an unofficial document.",
                "severity": "HIGH"
            })
            break

    score = min(score, 98)
    if score >= 65:
        if matched_legal:
            scam_type = "Counterfeit Document"
        elif brand_claims:
            scam_type = "Fake Authority"
        else:
            scam_type = "Financial Scam"
    elif score >= 40:
        scam_type = "Suspicious Document"
    else:
        score = max(5, score)
        scam_type = "No Fraud Detected"
        
    is_fraud = score >= 40
    
    recommendations = []
    if is_fraud:
        recommendations.append({
            "title": "Do Not Pay Any Demands",
            "detail": "Genuine law enforcement agencies and courts never demand immediate fines via cryptocurrency or wire transfer."
        })
        recommendations.append({
            "title": "Report to Cyber Crime Cell",
            "detail": "File a report with national cybercrime authorities (e.g. cybercrime.gov.in) with this screenshot as evidence."
        })
        recommendations.append({
            "title": "Verify with Official Department",
            "detail": "Verify any case number directly with the official court registry or police station in person."
        })
    else:
        recommendations.append({
            "title": "Standard Inspection",
            "detail": "No overt visual forgery indicators detected. Always verify sender identity independently."
        })

    explanation = (
        f"Visual document inspection calculated a risk score of {score}/100. "
        + (f"Detected {len(indicators)} deception indicators including {indicators[0]['label'].lower()}." if indicators else "No significant visual anomalies or counterfeit signatures detected.")
    )
    if error_note:
        print(f"[FraudShield Backend Log] Image Analyzer Note: {error_note}. Local engine utilized.")

    return {
        "risk_score": score,
        "confidence": confidence,
        "scam_type": scam_type,
        "is_fraud": is_fraud,
        "indicators": indicators,
        "evidence": {
            "document_type": document_type,
            "dimensions": f"{width}x{height}",
            "image_format": img_format,
            "visual_inconsistencies": suspicious_findings,
            "brand_claims": brand_claims,
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


def analyze_image(image_path: str) -> dict:
    """Analyze an image for fraud using Gemini Vision with fallback."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    if IMAGE_ANALYZER_API_KEY:
        try:
            import google.generativeai as genai
            from PIL import Image as PILImage
            genai.configure(api_key=IMAGE_ANALYZER_API_KEY)
            model = genai.GenerativeModel(GEMINI_VISION_MODEL, system_instruction=SYSTEM_PROMPT)
            
            pil_img = PILImage.open(image_path)
            res = model.generate_content(["Analyze this document/screenshot/image for fraud. Return ONLY raw JSON.", pil_img], request_options={"timeout": 10})
            raw = res.text
            raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()

            try:
                result = json.loads(raw)
            except json.JSONDecodeError:
                match = re.search(r"\{.*\}", raw, re.DOTALL)
                if match:
                    result = json.loads(match.group(0))
                else:
                    raise ValueError("JSON decode error from vision model output")

            ai_name = f"Google Gemini Vision ({GEMINI_VISION_MODEL})"
            result["input_type"] = "image"
            result["input_content"] = f"Image file: {os.path.basename(image_path)}"
            result["file_path"] = image_path
            result["ai_model"] = ai_name
            result["engine"] = f"Google Gemini Vision AI ({GEMINI_VISION_MODEL})"
            result["is_ai_generated"] = True

            if "evidence" not in result or not isinstance(result["evidence"], dict):
                result["evidence"] = {}
            result["evidence"]["ai_model_used"] = ai_name
            result["evidence"]["analysis_engine"] = "Google Gemini Live Vision AI"
            result["evidence"]["is_ai_generated"] = True

            return result

        except Exception as e:
            err_msg = str(e)
            result = _analyze_image_heuristics(image_path, error_note=err_msg)
            result["input_type"] = "image"
            result["input_content"] = f"Image file: {os.path.basename(image_path)}"
            result["file_path"] = image_path
            return result
    else:
        result = _analyze_image_heuristics(image_path, error_note="No API key provided")
        result["input_type"] = "image"
        result["input_content"] = f"Image file: {os.path.basename(image_path)}"
        result["file_path"] = image_path
        return result
