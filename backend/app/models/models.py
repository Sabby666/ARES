# backend/app/models/models.py
"""SQLAlchemy ORM models for ARES prototype."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.database.engine import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    assessments = relationship("Assessment", back_populates="project", cascade="all, delete-orphan")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(String, primary_key=True, default=_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    target = Column(String(512), nullable=False)
    scope = Column(String(512), default="")
    description = Column(Text, default="")
    status = Column(String(50), default="CREATED")
    # CREATED | POLICY_CHECK | RECON | ANALYSIS | LLM_REASONING | VALIDATION | EVIDENCE | REPORTING | COMPLETED | BLOCKED | FAILED
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    recon_data = Column(JSON, nullable=True)
    analysis_data = Column(JSON, nullable=True)
    reasoning_data = Column(JSON, nullable=True)
    report_html = Column(Text, nullable=True)
    report_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    project = relationship("Project", back_populates="assessments")
    findings = relationship("Finding", back_populates="assessment", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="assessment", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="assessment", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="assessment", cascade="all, delete-orphan")
    attack_surfaces = relationship("AttackSurface", back_populates="assessment", cascade="all, delete-orphan")
    pentest_actions = relationship("PentestAction", back_populates="assessment", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(String, primary_key=True, default=_uuid)
    assessment_id = Column(String, ForeignKey("assessments.id"), nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(String(100), default="")
    severity = Column(String(50), default="Info")  # Critical, High, Medium, Low, Info
    confidence = Column(Float, default=0.0)
    endpoint = Column(String(512), default="")
    description = Column(Text, default="")
    reasoning = Column(Text, default="")
    recommendation = Column(Text, default="")
    status = Column(String(50), default="CANDIDATE")  # OBSERVED | HYPOTHESIS | CANDIDATE | VALIDATING | PROVEN | NOT_PROVEN | INCONCLUSIVE | REJECTED
    agent = Column(String(100), default="")
    finding_signature = Column(String(512), unique=True, nullable=True)
    evidence_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    assessment = relationship("Assessment", back_populates="findings")
    evidence = relationship("Evidence", back_populates="finding", cascade="all, delete-orphan", foreign_keys="[Evidence.finding_id]")
    pentest_actions = relationship("PentestAction", back_populates="finding", cascade="all, delete-orphan")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String, primary_key=True, default=_uuid)
    assessment_id = Column(String, ForeignKey("assessments.id"), nullable=False)
    finding_id = Column(String, ForeignKey("findings.id"), nullable=True)
    agent = Column(String(100), default="")
    action = Column(String(255), default="")
    evidence_type = Column(String(100), default="")  # recon, analysis, validation, tool_output
    content = Column(Text, default="")
    source = Column(String(255), default="")
    source_type = Column(String(50), default="REAL")  # REAL, MOCK
    timestamp = Column(DateTime, default=_now)

    assessment = relationship("Assessment", back_populates="evidence")
    finding = relationship("Finding", back_populates="evidence", foreign_keys=[finding_id])


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(String, primary_key=True, default=_uuid)
    assessment_id = Column(String, ForeignKey("assessments.id"), nullable=False)
    agent = Column(String(100), default="")
    message = Column(Text, default="")
    log_type = Column(String(50), default="info")  # info, success, warning, error
    timestamp = Column(DateTime, default=_now)

    assessment = relationship("Assessment", back_populates="activity_logs")


class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=_uuid)
    assessment_id = Column(String, ForeignKey("assessments.id"), nullable=False)
    report_type = Column(String(50), default="html")  # html, json
    content = Column(Text, default="")
    findings_count = Column(Integer, default=0)
    generated_at = Column(DateTime, default=_now)

    assessment = relationship("Assessment", back_populates="reports")


class AttackSurface(Base):
    __tablename__ = "attack_surfaces"

    id = Column(String, primary_key=True, default=_uuid)
    assessment_id = Column(String, ForeignKey("assessments.id"), nullable=False)
    origin = Column(String(255), default="")
    path = Column(String(512), nullable=False)
    method = Column(String(20), default="GET")
    parameters = Column(JSON, nullable=True)
    forms = Column(JSON, nullable=True)
    form_fields = Column(JSON, nullable=True)
    input_fields = Column(JSON, nullable=True)
    authentication_required = Column(String(20), default="False") # keeping boolean as string for sqlite flexibility, or use Integer/Boolean
    authentication_state = Column(String(50), default="UNAUTHENTICATED")
    session_context_id = Column(String(255), nullable=True)
    csrf_state = Column(JSON, nullable=True)
    response_status = Column(Integer, nullable=True)
    response_headers = Column(JSON, nullable=True)
    response_metadata = Column(JSON, nullable=True)
    technologies = Column(JSON, nullable=True)
    candidate_classes = Column(JSON, nullable=True)
    observations = Column(JSON, nullable=True)
    evidence_refs = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    assessment = relationship("Assessment", back_populates="attack_surfaces")


class PentestAction(Base):
    __tablename__ = "pentest_actions"

    id = Column(String, primary_key=True, default=_uuid)
    assessment_id = Column(String, ForeignKey("assessments.id"), nullable=False)
    finding_id = Column(String, ForeignKey("findings.id"), nullable=True)
    target = Column(String(512), nullable=False)
    endpoint = Column(String(512), nullable=True)
    method = Column(String(20), default="GET")
    capability = Column(String(100), nullable=False)
    tool = Column(String(100), nullable=True)
    objective = Column(Text, default="")
    hypothesis = Column(Text, default="")
    reason = Column(Text, default="")
    expected_observation = Column(Text, default="")
    validation_goal = Column(String(255), nullable=True)
    policy_requirements = Column(JSON, nullable=True)
    risk = Column(String(50), default="Low")
    stop_condition = Column(Text, nullable=True)
    status = Column(String(50), default="PENDING")  # PENDING | EXECUTING | COMPLETED | FAILED | BLOCKED
    result_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    assessment = relationship("Assessment", back_populates="pentest_actions")
    finding = relationship("Finding", back_populates="pentest_actions")

