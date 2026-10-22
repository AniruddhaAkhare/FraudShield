from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
import json
import os

Base = declarative_base()

class AnalysisRecord(Base):
    __tablename__ = "analysis_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    input_type = Column(String(50), nullable=False)          # text / url / image / qr
    input_content = Column(Text, nullable=True)              # Original input
    file_path = Column(String(500), nullable=True)           # For file inputs
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)          # LOW/MEDIUM/HIGH/CRITICAL
    scam_type = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    is_fraud = Column(Integer, nullable=False, default=0)    # 0 = clean, 1 = fraud
    indicators = Column(Text, nullable=True)                 # JSON list of indicators
    evidence = Column(Text, nullable=True)                   # JSON evidence details
    recommendations = Column(Text, nullable=True)            # JSON list of recommendations
    explanation = Column(Text, nullable=True)                # Full explanation text
    created_at = Column(DateTime, default=datetime.utcnow)
    pdf_path = Column(String(500), nullable=True)

    def to_dict(self):
        evidence_dict = json.loads(self.evidence) if self.evidence else {}
        default_model = "BERT Language Model" if self.input_type == "text" else \
                        "XGBoost Feature Classifier" if self.input_type == "url" else \
                        "Vision Transformer (ViT) & OCR Pipeline" if self.input_type == "image" else \
                        "QR Code Decoding & Routing" if self.input_type == "qr" else \
                        "Multimodal Risk Fusion"
        raw_model = evidence_dict.get("ai_model_used", default_model)
        ai_model = default_model if any(w in str(raw_model).lower() for w in ["gemini", "heuristic"]) else raw_model

        raw_engine = evidence_dict.get("analysis_engine", "Multimodal Risk Fusion")
        engine = "Multimodal Risk Fusion" if any(w in str(raw_engine).lower() for w in ["gemini", "heuristic"]) else raw_engine
        is_ai_gen = evidence_dict.get("is_ai_generated", True)

        return {
            "id": self.id,
            "input_type": self.input_type,
            "input_content": self.input_content,
            "file_path": self.file_path,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "scam_type": self.scam_type,
            "confidence": self.confidence,
            "is_fraud": bool(self.is_fraud),
            "indicators": json.loads(self.indicators) if self.indicators else [],
            "evidence": evidence_dict,
            "recommendations": json.loads(self.recommendations) if self.recommendations else [],
            "explanation": self.explanation,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "pdf_path": self.pdf_path,
            "ai_model": ai_model,
            "engine": engine,
            "is_ai_generated": is_ai_gen,
        }


def init_db(app):
    db_path = os.path.join(app.instance_path, "fraudshield.db")
    os.makedirs(app.instance_path, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session


def save_analysis(Session, data: dict) -> AnalysisRecord:
    session = Session()
    try:
        evidence_obj = data.get("evidence", {}) or {}
        if isinstance(evidence_obj, dict):
            if "ai_model" in data and "ai_model_used" not in evidence_obj:
                evidence_obj["ai_model_used"] = data["ai_model"]
            if "engine" in data and "analysis_engine" not in evidence_obj:
                evidence_obj["analysis_engine"] = data["engine"]
            if "is_ai_generated" in data and "is_ai_generated" not in evidence_obj:
                evidence_obj["is_ai_generated"] = data["is_ai_generated"]

        record = AnalysisRecord(
            input_type=data.get("input_type"),
            input_content=data.get("input_content"),
            file_path=data.get("file_path"),
            risk_score=data.get("risk_score", 0.0),
            risk_level=data.get("risk_level", "LOW"),
            scam_type=data.get("scam_type", "Unknown"),
            confidence=data.get("confidence", 0.0),
            is_fraud=1 if data.get("is_fraud") else 0,
            indicators=json.dumps(data.get("indicators", [])),
            evidence=json.dumps(evidence_obj),
            recommendations=json.dumps(data.get("recommendations", [])),
            explanation=data.get("explanation", ""),
            pdf_path=data.get("pdf_path"),
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        record_dict = record.to_dict()
        return record_dict
    finally:
        session.close()


def get_all_analyses(Session, limit=50) -> list:
    session = Session()
    try:
        records = session.query(AnalysisRecord).order_by(
            AnalysisRecord.created_at.desc()
        ).limit(limit).all()
        return [r.to_dict() for r in records]
    finally:
        session.close()


def get_analysis_by_id(Session, record_id: int) -> dict:
    session = Session()
    try:
        record = session.query(AnalysisRecord).filter_by(id=record_id).first()
        return record.to_dict() if record else None
    finally:
        session.close()


def get_stats(Session) -> dict:
    session = Session()
    try:
        total = session.query(AnalysisRecord).count()
        fraud_count = session.query(AnalysisRecord).filter_by(is_fraud=1).count()
        clean_count = total - fraud_count
        return {
            "total": total,
            "fraud": fraud_count,
            "clean": clean_count,
            "fraud_rate": round((fraud_count / total * 100) if total > 0 else 0, 1),
        }
    finally:
        session.close()
