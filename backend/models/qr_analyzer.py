"""
Model 4 — QR Code Fraud Analyzer
Uses pyzbar and OpenCV to decode QR codes, with Gemini Vision and intelligent heuristic fallback.
"""
import json
import re
import sys
import os
import base64
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import QR_ANALYZER_API_KEY, GEMINI_VISION_MODEL

SYSTEM_PROMPT = """You are FraudShield's QR Code Fraud Detection Engine.
You receive a QR code image and its decoded content (if successfully decoded).

Analyze for:
1. PAYMENT QR FRAUD: Malicious UPI/bank QR codes designed to steal money
2. PHISHING REDIRECTS: QR codes leading to credential-harvesting phishing pages
3. MALWARE DELIVERY: Direct links to APK, EXE, or payload downloads
4. REVERSE PAYMENT TRICK: Scammer sends QR claiming "scan to receive payment" (when it actually debits)
5. BRAND IMPERSONATION: QR framed with fake brand/bank logos
6. SUSPICIOUS SCHEMES: bitcoin:, tel:, smsto:, javascript:, intent:

Return ONLY valid JSON (no markdown, no code fences):
{
  "risk_score": <0-100 integer>,
  "confidence": <0-100 integer>,
  "scam_type": "<one scam type or 'No Fraud Detected'>",
  "is_fraud": <true|false>,
  "indicators": [
    {"label": "<name>", "detail": "<detail>", "severity": "<HIGH|MEDIUM|LOW>"}
  ],
  "evidence": {
    "qr_decoded_data": "<the raw decoded QR content>",
    "qr_data_type": "<URL|Payment|Contact|Text|WiFi|Email|Other>",
    "destination_url": "<if URL type, the destination>",
    "payment_details": "<if payment type, payee/amount details>",
    "suspicious_patterns": ["<pattern1>"],
    "visual_qr_anomalies": ["<anomaly1>"]
  },
  "recommendations": [
    {"title": "<action>", "detail": "<detail>"}
  ],
  "explanation": "<2-4 sentence comprehensive QR fraud analysis>"
}"""


def _decode_qr(image_path: str) -> tuple[str, str]:
    """Decode QR code using pyzbar with OpenCV fallback."""
    # 1. Try pyzbar
    try:
        from pyzbar.pyzbar import decode as pyzbar_decode
        from PIL import Image
        img = Image.open(image_path)
        decoded = pyzbar_decode(img)
        if decoded:
            data = decoded[0].data.decode("utf-8", errors="replace").strip()
            return data, _classify_data_type(data)
    except Exception:
        pass

    # 2. Try OpenCV QRCodeDetector fallback
    try:
        import cv2
        cv_img = cv2.imread(image_path)
        if cv_img is not None:
            detector = cv2.QRCodeDetector()
            val, pts, st = detector.detectAndDecode(cv_img)
            if val and val.strip():
                data = val.strip()
                return data, _classify_data_type(data)
    except Exception:
        pass

    return "No QR code could be decoded from this image.", "Unknown"


def _classify_data_type(data: str) -> str:
    """Classify the payload type of a decoded QR code."""
    d = data.lower()
    if d.startswith(("http://", "https://")):
        return "URL"
    elif d.startswith(("upi://", "paytm://", "phonepe://", "gpay://", "bhim://")):
        return "Payment"
    elif d.startswith("begin:vcard"):
        return "Contact"
    elif d.startswith(("wifi:", "WIFI:")):
        return "WiFi"
    elif d.startswith("mailto:"):
        return "Email"
    elif d.startswith(("tel:", "smsto:")):
        return "Telephony"
    elif d.startswith("bitcoin:") or "crypto" in d:
        return "Crypto"
    else:
        return "Text"


def _image_to_base64(image_path: str) -> tuple[str, str]:
    ext = Path(image_path).suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".png": "image/png", ".gif": "image/gif",
                ".bmp": "image/bmp", ".webp": "image/webp"}
    mime = mime_map.get(ext, "image/jpeg")
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return data, mime


def _analyze_qr_heuristics(decoded_content: str, data_type: str, image_path: str, error_note: str = "") -> dict:
    """Intelligent fallback rule-based QR code analyzer."""
    lower = decoded_content.lower()
    indicators = []
    suspicious_patterns = []
    score = 10
    confidence = 90
    destination_url = decoded_content if data_type == "URL" else "none"
    payment_details = "none"

    if data_type == "Unknown" or "no qr code could be decoded" in lower:
        return {
            "risk_score": 25,
            "confidence": 70,
            "scam_type": "Unreadable QR Code",
            "is_fraud": False,
            "indicators": [{
                "label": "QR Decode Failure",
                "detail": "Could not identify or decode a standard QR matrix from the submitted image. Ensure the image is clear and well-lit.",
                "severity": "LOW"
            }],
            "evidence": {
                "qr_decoded_data": decoded_content,
                "qr_data_type": data_type,
                "destination_url": "none",
                "payment_details": "none",
                "suspicious_patterns": [],
                "visual_qr_anomalies": ["Low contrast or unreadable matrix"]
            },
            "recommendations": [{
                "title": "Upload Clear Image",
                "detail": "Retake a well-lit photo or screenshot of the QR code squarely without glare."
            }],
            "explanation": "No readable QR matrix was decoded from the image file."
        }

    # 1. URL Analysis for QR
    if data_type == "URL":
        parsed = urlparse(decoded_content if decoded_content.startswith("http") else f"https://{decoded_content}")
        domain = parsed.netloc.lower() or parsed.path.lower()

        # Suspicious free / abused TLD
        suspicious_tlds = [".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".work", ".click", ".link"]
        if any(domain.endswith(t) for t in suspicious_tlds):
            score += 35
            suspicious_patterns.append(f"Suspicious high-risk TLD in QR payload: {domain}")
            indicators.append({
                "label": "High-Risk QR Destination TLD",
                "detail": f"QR redirects to high-risk free/disposable top-level domain ({domain}).",
                "severity": "CRITICAL"
            })

        # Brand spoofing in QR
        brands = ["icici", "hdfc", "sbi", "paypal", "paytm", "gpay", "phonepe", "amazon"]
        for b in brands:
            if b in domain:
                is_legit = domain == f"{b}.com" or domain.endswith(f".{b}.com") or domain == f"{b}.in"
                if not is_legit:
                    score += 35
                    suspicious_patterns.append(f"Brand spoofing of {b.upper()}")
                    indicators.append({
                        "label": f"QR Brand Impersonation ({b.upper()})",
                        "detail": f"QR encodes a deceptive domain mimicking {b.upper()}: {domain}",
                        "severity": "CRITICAL"
                    })
                    break

        # Insecure HTTP
        if decoded_content.startswith("http://"):
            score += 20
            indicators.append({
                "label": "Insecure HTTP Protocol",
                "detail": "QR encodes an unencrypted HTTP link rather than HTTPS.",
                "severity": "MEDIUM"
            })

        # Phishing keywords in destination
        if any(k in lower for k in ["login", "verify", "kyc", "restore", "token", "suspended"]):
            score += 25
            indicators.append({
                "label": "Phishing Authentication Intent",
                "detail": "QR points directly to an authentication/credential harvesting form.",
                "severity": "HIGH"
            })

    # 2. Payment QR Analysis
    elif data_type == "Payment":
        payment_details = decoded_content
        # Check for preset amounts or suspicious handles
        if "am=" in lower or "pn=" in lower:
            score += 25
            indicators.append({
                "label": "Direct Payment Transfer Request",
                "detail": "QR directly triggers a debit transfer from the scanner's banking/UPI app.",
                "severity": "HIGH"
            })
            
    # 3. Telephony or SMS QR
    elif data_type == "Telephony":
        score += 30
        indicators.append({
            "label": "Automated Dialer / SMS QR Trigger",
            "detail": f"QR triggers an automatic phone call or SMS transmission ({decoded_content}).",
            "severity": "HIGH"
        })

    score = min(score, 99)
    if score >= 65:
        scam_type = "Phishing Redirect via QR" if data_type == "URL" else "Payment QR Fraud"
    elif score >= 40:
        scam_type = "Suspicious QR Code"
    else:
        score = max(5, score)
        scam_type = "No Fraud Detected"

    is_fraud = score >= 40

    recommendations = []
    if is_fraud:
        recommendations.append({
            "title": "Do Not Open Link or Authorize Payment",
            "detail": "Scanning this QR code will direct your browser to a deceptive web address or trigger an unauthorized payment."
        })
        recommendations.append({
            "title": "Never Enter PIN to 'Receive' Money",
            "detail": "Scammers frequently claim scanning a QR will credit your account. You NEVER need to enter your UPI PIN to receive money."
        })
        recommendations.append({
            "title": "Inspect Destination Host",
            "detail": f"Verified destination: {destination_url} — verify this matches the legitimate vendor portal."
        })
    else:
        recommendations.append({
            "title": "Safe QR Code",
            "detail": "Decoded payload displays expected structure. Verify the destination matches your intent."
        })

    explanation = (
        f"QR payload analysis computed a risk score of {score}/100 for payload type [{data_type}]. "
        + (f"Identified {len(indicators)} risk indicators, notably {indicators[0]['label'].lower()}." if indicators else "QR content appears legitimate with standard routing characteristics.")
    )
    if error_note:
        print(f"[FraudShield Backend Log] QR Analyzer Note: {error_note}. Local engine utilized.")

    return {
        "risk_score": score,
        "confidence": confidence,
        "scam_type": scam_type,
        "is_fraud": is_fraud,
        "indicators": indicators,
        "evidence": {
            "qr_decoded_data": decoded_content,
            "qr_data_type": data_type,
            "destination_url": destination_url,
            "payment_details": payment_details,
            "suspicious_patterns": suspicious_patterns,
            "visual_qr_anomalies": [],
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


def analyze_qr(image_path: str) -> dict:
    """Analyze a QR code image for fraud with dual decoder and AI fallback."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    decoded_content, data_type = _decode_qr(image_path)

    if QR_ANALYZER_API_KEY:
        try:
            import google.generativeai as genai
            from PIL import Image as PILImage
            genai.configure(api_key=QR_ANALYZER_API_KEY)
            model = genai.GenerativeModel(GEMINI_VISION_MODEL, system_instruction=SYSTEM_PROMPT)
            
            prompt_text = f"Analyze this QR code for fraud.\nDecoded content: {decoded_content}\nData type: {data_type}\nFilename: {os.path.basename(image_path)}\nReturn ONLY raw JSON."
            pil_img = PILImage.open(image_path)
            res = model.generate_content([prompt_text, pil_img], request_options={"timeout": 40})
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
            if "evidence" not in result or not isinstance(result["evidence"], dict):
                result["evidence"] = {}
            result["evidence"]["qr_decoded_data"] = decoded_content
            result["evidence"]["qr_data_type"] = data_type
            result["evidence"]["ai_model_used"] = ai_name
            result["evidence"]["analysis_engine"] = "Google Gemini Live Vision AI"
            result["evidence"]["is_ai_generated"] = True

            result["input_type"] = "qr"
            result["input_content"] = decoded_content[:500]
            result["file_path"] = image_path
            result["ai_model"] = ai_name
            result["engine"] = f"Google Gemini Vision AI ({GEMINI_VISION_MODEL})"
            result["is_ai_generated"] = True
            return result

        except Exception as e:
            err_msg = str(e)
            result = _analyze_qr_heuristics(decoded_content, data_type, image_path, error_note=err_msg)
            result["input_type"] = "qr"
            result["input_content"] = decoded_content[:500]
            result["file_path"] = image_path
            return result
    else:
        result = _analyze_qr_heuristics(decoded_content, data_type, image_path, error_note="No API key provided")
        result["input_type"] = "qr"
        result["input_content"] = decoded_content[:500]
        result["file_path"] = image_path
        return result
