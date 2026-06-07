"""Data access layer for institutions, KPIs, and related entities."""
from typing import List, Optional

import pandas as pd
from sqlalchemy import delete
from sqlalchemy.orm import Session

from database.models import Institution, InstitutionKPI, MLPrediction, Recommendation, User


class InstitutionRepository:
    @staticmethod
    def get_all(session: Session) -> List[Institution]:
        return session.query(Institution).order_by(Institution.institution_name).all()

    @staticmethod
    def get_by_id(session: Session, institution_id: int) -> Optional[Institution]:
        return session.query(Institution).filter(Institution.id == institution_id).first()

    @staticmethod
    def get_by_name(session: Session, name: str) -> Optional[Institution]:
        return session.query(Institution).filter(Institution.institution_name == name).first()

    @staticmethod
    def count(session: Session) -> int:
        return session.query(Institution).count()

    @staticmethod
    def bulk_upsert_from_dataframe(session: Session, df: pd.DataFrame) -> int:
        count = 0
        for _, row in df.iterrows():
            name = str(row["institution_name"]).strip()
            existing = InstitutionRepository.get_by_name(session, name)
            data = {
                "institution_name": name,
                "student_enrollment": int(row.get("student_enrollment", 0)),
                "faculty_count": int(row.get("faculty_count", 0)),
                "placement_percentage": float(row.get("placement_percentage", 0)),
                "research_publications": int(row.get("research_publications", 0)),
                "infrastructure_score": float(row.get("infrastructure_score", 0)),
                "accreditation_grade": str(row.get("accreditation_grade", "NA")),
                "nirf_rank": int(row.get("nirf_rank", 0)),
                "state": str(row.get("state", "Unknown")),
            }
            if existing:
                for key, val in data.items():
                    setattr(existing, key, val)
            else:
                session.add(Institution(**data))
            count += 1
        session.flush()
        return count

    @staticmethod
    def to_dataframe(session: Session) -> pd.DataFrame:
        records = InstitutionRepository.get_all(session)
        if not records:
            return pd.DataFrame()
        return pd.DataFrame([
            {
                "id": r.id,
                "institution_name": r.institution_name,
                "student_enrollment": r.student_enrollment,
                "faculty_count": r.faculty_count,
                "placement_percentage": r.placement_percentage,
                "research_publications": r.research_publications,
                "infrastructure_score": r.infrastructure_score,
                "accreditation_grade": r.accreditation_grade,
                "nirf_rank": r.nirf_rank,
                "state": r.state,
            }
            for r in records
        ])


class KPIRepository:
    @staticmethod
    def clear_all(session: Session) -> None:
        session.execute(delete(InstitutionKPI))

    @staticmethod
    def bulk_save(session: Session, kpi_records: List[dict]) -> int:
        KPIRepository.clear_all(session)
        for rec in kpi_records:
            session.add(InstitutionKPI(**rec))
        session.flush()
        return len(kpi_records)

    @staticmethod
    def to_dataframe(session: Session) -> pd.DataFrame:
        records = session.query(InstitutionKPI).order_by(InstitutionKPI.institution_rank).all()
        if not records:
            return pd.DataFrame()
        return pd.DataFrame([
            {
                "institution_id": r.institution_id,
                "institution_name": r.institution_name,
                "academic_score": r.academic_score,
                "research_score": r.research_score,
                "placement_score": r.placement_score,
                "infrastructure_score_kpi": r.infrastructure_score_kpi,
                "faculty_score": r.faculty_score,
                "accreditation_score": r.accreditation_score,
                "overall_performance_index": r.overall_performance_index,
                "composite_rank_score": r.composite_rank_score,
                "institution_rank": r.institution_rank,
                "ranking_category": r.ranking_category,
            }
            for r in records
        ])


class MLRepository:
    @staticmethod
    def clear_all(session: Session) -> None:
        session.execute(delete(MLPrediction))

    @staticmethod
    def bulk_save(session: Session, predictions: List[dict]) -> int:
        MLRepository.clear_all(session)
        for pred in predictions:
            session.add(MLPrediction(**pred))
        session.flush()
        return len(predictions)

    @staticmethod
    def to_dataframe(session: Session) -> pd.DataFrame:
        records = session.query(MLPrediction).all()
        if not records:
            return pd.DataFrame()
        return pd.DataFrame([
            {
                "institution_id": r.institution_id,
                "institution_name": r.institution_name,
                "predicted_performance_score": r.predicted_performance_score,
                "accreditation_readiness": r.accreditation_readiness,
                "ranking_category_pred": r.ranking_category_pred,
            }
            for r in records
        ])


class RecommendationRepository:
    @staticmethod
    def clear_all(session: Session) -> None:
        session.execute(delete(Recommendation))

    @staticmethod
    def bulk_save(session: Session, recommendations: List[dict]) -> int:
        RecommendationRepository.clear_all(session)
        for rec in recommendations:
            session.add(Recommendation(**rec))
        session.flush()
        return len(recommendations)

    @staticmethod
    def get_for_institution(session: Session, institution_id: int) -> List[Recommendation]:
        return (
            session.query(Recommendation)
            .filter(Recommendation.institution_id == institution_id)
            .order_by(Recommendation.priority)
            .all()
        )

    @staticmethod
    def to_dataframe(session: Session) -> pd.DataFrame:
        records = session.query(Recommendation).all()
        if not records:
            return pd.DataFrame()
        return pd.DataFrame([
            {
                "institution_id": r.institution_id,
                "institution_name": r.institution_name,
                "category": r.category,
                "message": r.message,
                "priority": r.priority,
            }
            for r in records
        ])


class UserRepository:
    @staticmethod
    def user_to_dict(user: User) -> dict:
        """Convert ORM User to plain dict while session is still open."""
        return {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "password_hash": user.password_hash,
            "linked_institution": user.linked_institution,
        }

    @staticmethod
    def get_by_username(session: Session, username: str) -> Optional[User]:
        return session.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_dict_by_username(session: Session, username: str) -> Optional[dict]:
        user = UserRepository.get_by_username(session, username)
        if user is None:
            return None
        return UserRepository.user_to_dict(user)

    @staticmethod
    def create_user(session: Session, username: str, password_hash: str, role: str, linked_institution: str = None) -> User:
        user = User(
            username=username,
            password_hash=password_hash,
            role=role,
            linked_institution=linked_institution,
        )
        session.add(user)
        session.flush()
        return user

    @staticmethod
    def seed_default_users(session: Session, default_users: dict, hash_fn) -> None:
        for username, info in default_users.items():
            if not UserRepository.get_by_username(session, username):
                UserRepository.create_user(
                    session,
                    username=username,
                    password_hash=hash_fn(info["password"]),
                    role=info["role"],
                    linked_institution=info.get("institution"),
                )
