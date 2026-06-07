"""SQLAlchemy ORM models."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    institution_name = Column(String(255), unique=True, nullable=False, index=True)
    student_enrollment = Column(Integer, default=0)
    faculty_count = Column(Integer, default=0)
    placement_percentage = Column(Float, default=0.0)
    research_publications = Column(Integer, default=0)
    infrastructure_score = Column(Float, default=0.0)
    accreditation_grade = Column(String(10), default="NA")
    nirf_rank = Column(Integer, default=0)
    state = Column(String(100), default="Unknown")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InstitutionKPI(Base):
    __tablename__ = "institution_kpis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    institution_id = Column(Integer, nullable=False, index=True)
    institution_name = Column(String(255), nullable=False)
    academic_score = Column(Float, default=0.0)
    research_score = Column(Float, default=0.0)
    placement_score = Column(Float, default=0.0)
    infrastructure_score_kpi = Column(Float, default=0.0)
    faculty_score = Column(Float, default=0.0)
    accreditation_score = Column(Float, default=0.0)
    overall_performance_index = Column(Float, default=0.0)
    composite_rank_score = Column(Float, default=0.0)
    institution_rank = Column(Integer, default=0)
    ranking_category = Column(String(20), default="")
    calculated_at = Column(DateTime, default=datetime.utcnow)


class MLPrediction(Base):
    __tablename__ = "ml_predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    institution_id = Column(Integer, nullable=False, index=True)
    institution_name = Column(String(255), nullable=False)
    predicted_performance_score = Column(Float, default=0.0)
    accreditation_readiness = Column(String(30), default="")
    ranking_category_pred = Column(String(30), default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    institution_id = Column(Integer, nullable=False, index=True)
    institution_name = Column(String(255), nullable=False)
    category = Column(String(50), default="")
    message = Column(Text, default="")
    priority = Column(String(20), default="medium")
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="institution_user")
    linked_institution = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
