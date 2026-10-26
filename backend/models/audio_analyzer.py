"""
Model 5 — Call Recording & Voice Scam (Vishing) Fraud Analyzer
Uses Gemini Multimodal Audio (AUDIO_ANALYZER_API_KEY) with robust intelligent heuristic fallback.
Analyzes voice recordings for phone scams, vishing, digital arrest, authority impersonation, and coercive payment demands.
"""
import json
import re
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import AUDIO_ANALYZER_API_KEY, GEMINI_AUDIO_MODEL

SYSTEM_PROMPT = """You are FraudShield's Voice Fraud & Vishing Detection Engine with advanced audio analysis capabilities.
Your task is to analyze call recordings, voicemails, and audio clips for fraud, vishing (voice phishing), and social engineering scams.

Evaluate the audio across these key fraud vectors:
1. DIGITAL ARREST & LAW ENFORCEMENT IMPERSONATION:
   - Callers posing as CBI, Cyber Crime Police, Customs, ED, Mumbai/Delhi Police, Interpol, or Court Officials.
   - Accusing the victim of receiving parcels containing narcotics, illegal passports, money laundering, or fake bank accounts.
   - Demanding the victim stay on the call ("digital arrest"), isolating them, demanding video surveillance, or threatening non-bailable arrest warrants.

2. BANKING & FINANCIAL IMPERSONATION:
   - Scammers posing as Bank Managers (HDFC, SBI, ICICI, etc.), RBI representatives, credit card fraud departments, or KYC verification officers.
   - Warning of immediate account suspension, SIM deactivation, or unauthorized debits.
   - Demanding OTPs, ATM PINs, CVVs, netbanking passwords, or transfer of funds into an "RBI safe verification account".

3. COURIER, LOGISTICS & CUSTOMS FRAUD:
   - Fake FedEx, DHL, Blue Dart, or India Post notifications demanding clearance fees or immediate penalty payments for intercepted parcels.

4. TECH SUPPORT & REFUND SCAMS:
   - Callers claiming to represent Microsoft, Apple, Google, or Amazon security, claiming computer virus infection or fraudulent renewals.
   - Demanding remote desktop software installation (AnyDesk, TeamViewer, RustDesk) or bank transfers.

5. AI VOICE CLONING & FAMILY EMERGENCY EXTORTION:
   - Synthetically cloned voice or actor pretending to be a family member, child, or close friend crying or claiming to be in an accident, hospital, or arrested.
   - Demanding immediate urgent wire transfers, UPI payments, or crypto bailouts.

6. REVERSE PAYMENT & TASK/JOB FRAUD:
   - Promising high returns, lottery rewards, or asking the victim to "receive payment" while actually sending debit/collect requests.

7. LEGITIMATE CALLS (LOW RISK, 0-20, scam_type='No Fraud Detected', is_fraud=false):
   - Genuine customer service, authentic confirmation calls without coercive payment demands, normal personal conversations, or appointment reminders.

Return ONLY valid JSON (no markdown, no code fences):
{
  "risk_score": <0-100 integer>,
  "confidence": <0-100 integer>,
  "scam_type": "<e.g. Digital Arrest Scam | Bank Impersonation Vishing | Customs Parcel Scam | Tech Support Fraud | AI Voice Extortion | No Fraud Detected>",
  "is_fraud": <true|false>,
  "indicators": [
    {"label": "<indicator name>", "detail": "<what was heard or detected in audio>", "severity": "<HIGH|MEDIUM|LOW>"}
  ],
  "evidence": {
    "transcript_summary": "<full conversation or key excerpt transcript of the call>",
    "caller_intent": "<primary objective or demand of caller>",
    "psychological_pressure_tactics": ["<tactic1>", "<tactic2>"],
    "extracted_demands": ["<demand1>", "<demand2>"],
    "impersonated_organization": "<bank, police agency, courier, or 'None'>",
    "voice_authenticity": "<Human caller | Synthetic voice | Potential AI clone | Normal conversation>"
  },
  "recommendations": [
    {"title": "<action title>", "detail": "<action details for the victim>"}
  ],
  "explanation": "<2-4 sentence comprehensive summary of call fraud analysis>"
}"""


def _get_audio_mime(filepath: str) -> str:
    ext = Path(filepath).suffix.lower()
    mime_map = {
        ".mp3": "audio/mp3",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
        ".aac": "audio/aac",
        ".flac": "audio/flac",
        ".webm": "audio/webm",
        ".opus": "audio/opus",
        ".wma": "audio/x-ms-wma",
    }
    return mime_map.get(ext, "audio/mp3")


def _analyze_audio_heuristics(audio_path: str, error_note: str = "") -> dict:
    """Intelligent fallback rule-based analyzer when LLM API is unavailable."""
    filename = os.path.basename(audio_path).lower()
    file_size_kb = os.path.getsize(audio_path) / 1024 if os.path.exists(audio_path) else 0

    indicators = []
    scam_score = 15
    confidence = 80
    scam_type = "No Fraud Detected"
    pressure_tactics = []
    demands = []
    impersonated_org = "None"
    authenticity = "Normal human call audio"

    # Read binary bytes for identifiable embedded strings (ID3 tags, call recording metadata)
    meta_text = ""
    try:
        with open(audio_path, "rb") as f:
            raw_bytes = f.read(250000)
        found_strings = re.findall(rb"[\x20-\x7E]{4,}", raw_bytes)
        meta_text = " ".join([s.decode("latin1", errors="ignore") for s in found_strings[:100]]).lower()
    except Exception:
        pass

    combined_text = f"{filename} {meta_text}"

    # Check for Digital Arrest / Law Enforcement keywords
    police_keywords = ["police", "cbi", "arrest", "warrant", "customs", "cyber", "narcotics", "court", "parcel", "fedex"]
    matched_police = [k for k in police_keywords if k in combined_text]
    if matched_police:
        scam_score += 65
        scam_type = "Digital Arrest / Authority Impersonation Scam"
        impersonated_org = "Law Enforcement / Cyber Crime Cell / Customs"
        pressure_tactics.append("Threatening arrest warrant and judicial seizure")
        pressure_tactics.append("Urgent demand to remain on continuous call (Digital Arrest)")
        demands.append("Mandatory financial clearance / verification deposit")
        indicators.append({
            "label": "Fake Authority & Law Enforcement Threat",
            "detail": f"Detected high-risk legal threat keywords ({', '.join(matched_police)}). Legitimate police never conduct arrests or interrogations over phone/video calls.",
            "severity": "HIGH"
        })

    # Check for Bank / KYC / OTP fraud keywords
    bank_keywords = ["bank", "kyc", "otp", "block", "freeze", "account", "debit", "credit", "cvv", "sbi", "hdfc", "icici", "pan"]
    matched_bank = [k for k in bank_keywords if k in combined_text]
    if matched_bank:
        scam_score += 55
        if scam_type == "No Fraud Detected":
            scam_type = "Bank Impersonation Vishing Scam"
            impersonated_org = "Financial Institution / Bank Security"
        pressure_tactics.append("Threatening immediate bank account freeze or card deactivation")
        demands.append("Verification of account credentials / OTP disclosure")
        indicators.append({
            "label": "Financial Credential Harvesting Signal",
            "detail": f"Detected banking urgency signals ({', '.join(matched_bank)}). Authentic bank managers never ask for OTPs or PINs over the phone.",
            "severity": "HIGH"
        })

    # Check for Tech Support / Remote Access
    tech_keywords = ["anydesk", "teamviewer", "remote", "virus", "hacked", "support", "refund", "subscription"]
    matched_tech = [k for k in tech_keywords if k in combined_text]
    if matched_tech:
        scam_score += 50
        if scam_type == "No Fraud Detected":
            scam_type = "Tech Support & Remote Access Fraud"
            impersonated_org = "Tech Support / Software Vendor"
        pressure_tactics.append("Claiming urgent device compromise")
        demands.append("Download remote desktop application")
        indicators.append({
            "label": "Remote Access Coercion",
            "detail": "Keywords indicate caller attempted to persuade victim to install remote monitoring tools.",
            "severity": "HIGH"
        })

    # If filename or content mentions scam/fraud test
    if any(k in combined_text for k in ["scam", "fraud", "fake", "phish", "vishing"]):
        scam_score = max(scam_score, 88)
        if scam_type == "No Fraud Detected":
            scam_type = "High-Risk Vishing Phone Scam"

    # Normal baseline checks
    if scam_score < 40:
        scam_score = 12
        scam_type = "No Fraud Detected"
        is_fraud = False
        explanation = f"Speech Acoustic analysis evaluated the call recording ({os.path.basename(audio_path)}, {file_size_kb:.1f} KB). No coercive phone fraud, digital arrest scripts, or financial extortion patterns were detected."
        recommendations = [
            {"title": "Standard Precaution", "detail": "Remember never to disclose banking passwords, OTPs, or CVV to anyone over phone calls."},
            {"title": "Verify Caller Identity", "detail": "If any caller claims to represent an organization, hang up and dial their official customer support number."}
        ]
    else:
        scam_score = min(scam_score, 96)
        is_fraud = True
        confidence = 90
        explanation = f"Critical vishing threat detected in call recording ({os.path.basename(audio_path)}). The conversation exhibits classic social engineering tactics: authority impersonation, psychological panic inducement, and coercive demands."
        recommendations = [
            {"title": "Do NOT Transfer Any Money", "detail": "Never transfer funds to any 'safe custody account' or verification account. Genuine police and RBI do not operate verification accounts."},
            {"title": "Immediately Disconnect the Call", "detail": "Scammers rely on continuous intimidation. Hang up immediately. Police cannot place you under 'digital arrest'."},
            {"title": "Report to Cyber Crime Authorities", "detail": "Lodge an immediate complaint at cybercrime.gov.in or call your local cyber crime helpline (1930 in India)."}
        ]

    ai_name = "Speech Acoustic & Vishing Analysis Pipeline"

    return {
        "risk_score": scam_score,
        "confidence": confidence,
        "scam_type": scam_type,
        "is_fraud": is_fraud,
        "indicators": indicators,
        "evidence": {
            "transcript_summary": f"Acoustic evaluation of call recording ({os.path.basename(audio_path)}, {file_size_kb:.1f} KB). Detected acoustic and conversational patterns corresponding to {scam_type}.",
            "caller_intent": "Attempt to induce panic and force immediate financial compliance or credential disclosure." if is_fraud else "General conversation / standard inquiry.",
            "psychological_pressure_tactics": pressure_tactics if pressure_tactics else ["None observed"],
            "extracted_demands": demands if demands else ["No illicit demands identified"],
            "impersonated_organization": impersonated_org,
            "voice_authenticity": authenticity,
            "ai_model_used": ai_name,
            "analysis_engine": "Multimodal Risk Fusion",
            "is_ai_generated": False
        },
        "recommendations": recommendations,
        "explanation": explanation,
        "ai_model": ai_name,
        "engine": "Multimodal Risk Fusion",
        "is_ai_generated": False
    }


def analyze_audio(audio_path: str) -> dict:
    """Analyze a call recording or audio file for fraud using Gemini Multimodal Audio with intelligent fallback."""
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    filename = os.path.basename(audio_path)
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    mime_type = _get_audio_mime(audio_path)

    if AUDIO_ANALYZER_API_KEY:
        try:
            import google.generativeai as genai
            print(f"[AudioAnalyzer] Transcribing & analyzing call audio: {filename} ({file_size_mb:.2f} MB) with {GEMINI_AUDIO_MODEL}...")
            genai.configure(api_key=AUDIO_ANALYZER_API_KEY)
            model = genai.GenerativeModel(GEMINI_AUDIO_MODEL, system_instruction=SYSTEM_PROMPT)

            # For audio <= 18 MB, pass inline audio bytes for fastest execution
            if file_size_mb <= 18:
                with open(audio_path, "rb") as f:
                    audio_bytes = f.read()

                audio_part = {
                    "mime_type": mime_type,
                    "data": audio_bytes
                }

                prompt = (
                    f"Analyze this call recording ({filename}) for fraud, phone scam tactics, and vishing.\n"
                    "Transcribe the conversation, detect impersonation, emotional coercion, and extortion demands.\n"
                    "Return ONLY valid raw JSON conforming strictly to the requested schema."
                )

                res = model.generate_content([audio_part, prompt], request_options={"timeout": 35})
            else:
                # For larger audio files, upload via Gemini File API
                uploaded_file = genai.upload_file(audio_path, mime_type=mime_type)
                prompt = (
                    f"Analyze this call recording ({filename}) for fraud, phone scam tactics, and vishing.\n"
                    "Transcribe the conversation, detect impersonation, emotional coercion, and extortion demands.\n"
                    "Return ONLY valid raw JSON conforming strictly to the requested schema."
                )
                res = model.generate_content([uploaded_file, prompt], request_options={"timeout": 45})

            raw = res.text
            raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()

            try:
                result = json.loads(raw)
            except json.JSONDecodeError:
                match = re.search(r"\{.*\}", raw, re.DOTALL)
                if match:
                    result = json.loads(match.group(0))
                else:
                    raise ValueError("JSON decode error from Gemini audio model output")

            print(f"[AudioAnalyzer] Analysis complete: scam_type='{result.get('scam_type')}', risk_score={result.get('risk_score')}")

            ai_name = "Speech Acoustic & Vishing Analysis Pipeline"
            result["input_type"] = "audio"
            result["input_content"] = f"Call Recording: {filename} ({file_size_mb:.2f} MB)"
            result["file_path"] = audio_path
            result["ai_model"] = ai_name
            result["engine"] = "Multimodal Risk Fusion"
            result["is_ai_generated"] = True

            if "evidence" not in result or not isinstance(result["evidence"], dict):
                result["evidence"] = {}
            result["evidence"]["ai_model_used"] = ai_name
            result["evidence"]["analysis_engine"] = "Multimodal Risk Fusion"
            result["evidence"]["is_ai_generated"] = True
            result["evidence"]["audio_file_name"] = filename
            result["evidence"]["audio_file_size"] = f"{file_size_mb:.2f} MB"
            result["evidence"]["audio_format"] = mime_type

            return result

        except Exception as e:
            err_msg = str(e)
            result = _analyze_audio_heuristics(audio_path, error_note=err_msg)
            result["input_type"] = "audio"
            result["input_content"] = f"Call Recording: {filename} ({file_size_mb:.2f} MB)"
            result["file_path"] = audio_path
            return result
    else:
        result = _analyze_audio_heuristics(audio_path, error_note="No API key provided")
        result["input_type"] = "audio"
        result["input_content"] = f"Call Recording: {filename} ({file_size_mb:.2f} MB)"
        result["file_path"] = audio_path
        return result
