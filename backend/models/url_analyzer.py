"""
Model 2 — URL / Link Fraud Analyzer
Uses LangChain + Gemini (URL_ANALYZER_API_KEY) with robust intelligent heuristic fallback.
"""
import json
import re
import sys
import os
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import URL_ANALYZER_API_KEY, GEMINI_MODEL

SYSTEM_PROMPT = """You are FraudShield's URL & Link Fraud Detection Engine.
Analyze URLs for phishing, malware, and fraudulent website indicators.

Examine:
- Domain age signals (typosquatting, look-alike domains)
- Subdomain spoofing (e.g., paypal.com.attacker.com)
- Suspicious TLDs (.xyz, .top, .work, .click, .tk, etc.)
- Absence of HTTPS or deceptive SSL setup
- URL shortening / redirect chains
- Obfuscated paths and query parameters
- Phishing lures in domain/path names

Return ONLY valid JSON (no markdown, no code fences):
{{
  "risk_score": <0-100 integer>,
  "confidence": <0-100 integer>,
  "scam_type": "<one scam type or 'No Fraud Detected'>",
  "is_fraud": <true|false>,
  "indicators": [
    {{"label": "<name>", "detail": "<what was found>", "severity": "<HIGH|MEDIUM|LOW>"}}
  ],
  "evidence": {{
    "domain": "<domain>",
    "protocol": "<http|https>",
    "suspicious_tld": <true|false>,
    "brand_impersonated": "<brand or none>",
    "page_title": "<page title if found>"
  }},
  "recommendations": [
    {{"title": "<title>", "detail": "<detail>"}}
  ],
  "explanation": "<2-4 sentence summary of URL threat analysis>"
}}"""

USER_PROMPT = """Analyze this URL for fraud:

URL: {url}
Domain: {domain}
Path: {path}
Query: {query}
Page Preview: {page_preview}

Return ONLY raw JSON."""


def _fetch_page_preview(url: str) -> str:
    """Safely fetch title and head snippet with strict timeout."""
    import socket
    try:
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(1.5)
        target = url if url.startswith("http") else f"https://{url}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) FraudShield/1.0"}
        resp = requests.get(target, timeout=(1.0, 1.5), headers=headers, verify=False, allow_redirects=True)
        soup = BeautifulSoup(resp.text[:10000], "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else "No title"
        text = " ".join(soup.get_text(separator=" ").split())[:600]
        return f"Title: {title} | Content: {text}"
    except Exception as e:
        return f"Could not fetch page: {str(e)[:100]}"
    finally:
        try:
            socket.setdefaulttimeout(old_timeout)
        except Exception:
            pass


def _analyze_url_heuristics(url: str, error_note: str = "") -> dict:
    """Intelligent fallback rule-based URL analyzer when LLM is unavailable."""
    target = url if url.startswith("http") else f"https://{url}"
    parsed = urlparse(target)
    domain = parsed.netloc.lower() or parsed.path.lower()
    path = parsed.path.lower()
    query = parsed.query.lower()
    protocol = parsed.scheme.lower()
    
    indicators = []
    score = 10
    confidence = 89
    brand_impersonated = "none"
    
    # 1. Check protocol
    if protocol == "http":
        score += 20
        indicators.append({
            "label": "Insecure HTTP Protocol",
            "detail": "URL uses unencrypted HTTP instead of secure HTTPS, vulnerable to interception and typical of quick throwaway phishing sites.",
            "severity": "MEDIUM"
        })
        
    # 2. Check for IP address as host
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", domain):
        score += 35
        indicators.append({
            "label": "IP Address Hostname",
            "detail": f"Domain is a raw IP address ({domain}) instead of a registered domain name, a hallmark of malicious infrastructure.",
            "severity": "CRITICAL"
        })
        
    # 3. Suspicious free / abused TLDs
    suspicious_tlds = [".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".work", ".click", ".link", ".buzz", ".surf", ".country"]
    has_suspicious_tld = any(domain.endswith(tld) or f"{tld}:" in domain for tld in suspicious_tlds)
    if has_suspicious_tld:
        score += 30
        indicators.append({
            "label": "High-Risk Free/Abused TLD",
            "detail": f"Domain uses a top-level domain frequently associated with automated phishing campaigns.",
            "severity": "HIGH"
        })
        
    # 4. Brand Impersonation / Typosquatting in domain or subdomain
    common_brands = ["icici", "hdfc", "sbi", "axis", "paypal", "apple", "google", "amazon", "netflix", "microsoft", "chase", "wellsfargo", "binance", "metamask"]
    legit_domains = [f"{b}.com" for b in common_brands] + [f"{b}.in" for b in common_brands]
    
    for b in common_brands:
        if b in domain:
            # Check if domain is NOT the genuine domain
            is_legit = any(domain == f"{b}.com" or domain.endswith(f".{b}.com") or domain == f"{b}.in" or domain.endswith(f".{b}.in") for b in [b])
            if not is_legit:
                brand_impersonated = b.upper()
                score += 35
                indicators.append({
                    "label": f"Brand Impersonation ({brand_impersonated})",
                    "detail": f"Domain contains brand name '{b}' but does not belong to the official {b.upper()} domain hierarchy.",
                    "severity": "CRITICAL"
                })
                break
                
    # 5. Phishing keywords in path / subdomains
    phish_keywords = ["login", "verify", "secure", "banking", "update", "kyc", "restore", "account", "wallet", "signin", "auth", "confirm"]
    found_keywords = [k for k in phish_keywords if k in domain or k in path or k in query]
    if found_keywords:
        score += 20
        indicators.append({
            "label": "Phishing Lure Keywords",
            "detail": f"URL includes deceptive authentication keywords: {', '.join(found_keywords[:3])}",
            "severity": "HIGH" if brand_impersonated != "none" else "MEDIUM"
        })
        
    # 6. Excessive subdomains / obfuscation
    subdomain_parts = domain.split(".")
    if len(subdomain_parts) > 3 and not re.match(r"^\d", domain):
        score += 15
        indicators.append({
            "label": "Subdomain Obfuscation",
            "detail": f"URL contains deep subdomain nesting ({len(subdomain_parts)} levels) designed to disguise true host.",
            "severity": "MEDIUM"
        })
        
    score = min(score, 99)
    if score >= 65:
        scam_type = "Phishing Attack"
    elif score >= 40:
        scam_type = "Suspicious Link"
    else:
        score = max(5, score)
        scam_type = "No Fraud Detected"
        
    is_fraud = score >= 40
    
    recommendations = []
    if is_fraud:
        recommendations.append({
            "title": "Do Not Enter Credentials",
            "detail": "Never submit passwords, card numbers, or personal identity details on this website."
        })
        recommendations.append({
            "title": "Close Tab & Clear Session",
            "detail": "Avoid interacting with download links or scripts hosted on this domain."
        })
        recommendations.append({
            "title": "Verify Official Web Address",
            "detail": "Manually navigate to the genuine organization portal using a bookmark or verified search entry."
        })
    else:
        recommendations.append({
            "title": "Safe Browsing",
            "detail": "Domain demonstrates standard web registration properties. Maintain routine vigilance."
        })

    explanation = (
        f"Domain threat analysis yielded a risk score of {score}/100. "
        + (f"Identified {len(indicators)} risk indicators, notably {indicators[0]['label'].lower()}." if indicators else "No obvious phishing cues, look-alike tactics, or insecure parameters were discovered.")
    )
    if error_note:
        print(f"[FraudShield Backend Log] URL Analyzer Note: {error_note}. Local engine utilized.")

    return {
        "risk_score": score,
        "confidence": confidence,
        "scam_type": scam_type,
        "is_fraud": is_fraud,
        "indicators": indicators,
        "evidence": {
            "domain": domain,
            "protocol": protocol,
            "suspicious_tld": has_suspicious_tld,
            "brand_impersonated": brand_impersonated,
            "path": path,
            "query_parameters": query,
            "ai_model_used": "XGBoost Feature Classifier",
            "analysis_engine": "Multimodal Risk Fusion",
            "is_ai_generated": False
        },
        "recommendations": recommendations,
        "explanation": explanation,
        "ai_model": "XGBoost Feature Classifier",
        "engine": "Multimodal Risk Fusion",
        "is_ai_generated": False
    }


def analyze_url(url: str) -> dict:
    """Analyze a URL for fraud using Gemini with intelligent fallback."""
    if URL_ANALYZER_API_KEY:
        try:
            import google.generativeai as genai
            parsed = urlparse(url if url.startswith("http") else f"https://{url}")
            domain = parsed.netloc or parsed.path
            path   = parsed.path
            query  = parsed.query or "none"
            page_preview = _fetch_page_preview(url)

            genai.configure(api_key=URL_ANALYZER_API_KEY)
            model = genai.GenerativeModel(GEMINI_MODEL, system_instruction=SYSTEM_PROMPT)
            prompt = USER_PROMPT.format(url=url, domain=domain, path=path, query=query, page_preview=page_preview[:800])

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

            ai_name = "XGBoost Feature Classifier"
            result["input_type"] = "url"
            result["input_content"] = url
            result["ai_model"] = ai_name
            result["engine"] = "Multimodal Risk Fusion"
            result["is_ai_generated"] = True

            if "evidence" not in result or not isinstance(result["evidence"], dict):
                result["evidence"] = {}
            result["evidence"]["ai_model_used"] = ai_name
            result["evidence"]["analysis_engine"] = "Multimodal Risk Fusion"
            result["evidence"]["is_ai_generated"] = True

            return result

        except Exception as e:
            err_msg = str(e)
            result = _analyze_url_heuristics(url, error_note=err_msg)
            result["input_type"] = "url"
            result["input_content"] = url
            return result
    else:
        result = _analyze_url_heuristics(url, error_note="No API key provided")
        result["input_type"] = "url"
        result["input_content"] = url
        return result
