import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Text, DateTime, Date, ForeignKey, UniqueConstraint, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return uuid.uuid4()


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # TUTOR, STUDENT, PARENT
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("Profile", back_populates="user", uselist=False)
    tutor_links = relationship(
        "TutorStudent", foreign_keys="TutorStudent.tutor_id", back_populates="tutor"
    )
    student_links = relationship(
        "TutorStudent", foreign_keys="TutorStudent.student_id", back_populates="student"
    )


class Profile(Base):
    __tablename__ = "profiles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    birth_date = Column(Date, nullable=True)
    consent_152fz_at = Column(DateTime, nullable=False)
    consent_parent_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="profile")


class TutorStudent(Base):
    __tablename__ = "tutor_student"

    tutor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)

    tutor = relationship("User", foreign_keys=[tutor_id], back_populates="tutor_links")
    student = relationship("User", foreign_keys=[student_id], back_populates="student_links")


class StudentParent(Base):
    __tablename__ = "student_parent"

    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)


class InvitationCode(Base):
    __tablename__ = "invitation_codes"

    code = Column(String(50), primary_key=True)
    tutor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    used_by_student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    __table_args__ = (UniqueConstraint("tutor_id", "code", name="uq_tutor_code"),)


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    tenant_id = Column(UUID(as_uuid=True))
    name = Column(String(100), nullable=False)


class Theme(Base):
    __tablename__ = "themes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    parent_theme_id = Column(UUID(as_uuid=True), ForeignKey("themes.id"), nullable=True)
    fipi_code = Column(String(50))
    name = Column(String(255), nullable=False)

    subject = relationship("Subject")
    parent = relationship("Theme", remote_side="Theme.id")
    children = relationship("Theme", back_populates="parent")
    tasks = relationship("Task", back_populates="theme")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    theme_id = Column(UUID(as_uuid=True), ForeignKey("themes.id"), nullable=False)
    type = Column(String(50), nullable=False)  # TEST, ESSAY
    text_content = Column(JSON, nullable=False)
    correct_answer_key = Column(JSON, nullable=True)
    fipi_criteria = Column(JSON, nullable=True)
    source_url = Column(String(500))
    metadata_ = Column("metadata", JSON, default=dict)
    # KIM classification fields
    exam_position = Column(Integer, nullable=True)  # 1-21
    difficulty_level = Column(String(1), nullable=True)  # Б, П, В

    subject = relationship("Subject")
    theme = relationship("Theme", back_populates="tasks")


class Test(Base):
    __tablename__ = "tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    tenant_id = Column(UUID(as_uuid=True))
    tutor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    time_limit_minutes = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tutor = relationship("User")
    tasks = relationship("TestTask", back_populates="test")
    assignments = relationship("TestAssignment", back_populates="test")


class TestTask(Base):
    __tablename__ = "test_tasks"

    test_id = Column(UUID(as_uuid=True), ForeignKey("tests.id"), primary_key=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), primary_key=True)
    order_number = Column(Integer, nullable=False)

    test = relationship("Test", back_populates="tasks")
    task = relationship("Task")


class TestAssignment(Base):
    __tablename__ = "test_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    test_id = Column(UUID(as_uuid=True), ForeignKey("tests.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="ASSIGNED")  # ASSIGNED, IN_PROGRESS, COMPLETED

    test = relationship("Test", back_populates="assignments")
    student = relationship("User")


class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    test_id = Column(UUID(as_uuid=True), ForeignKey("tests.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default="IN_PROGRESS")
    auto_score = Column(Integer, nullable=True)

    test = relationship("Test")
    student = relationship("User")
    answers = relationship("Answer", back_populates="attempt")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    attempt_id = Column(UUID(as_uuid=True), ForeignKey("attempts.id"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    student_input = Column(Text, nullable=True)
    auto_score = Column(Integer, nullable=True)
    manual_score = Column(Integer, nullable=True)
    ai_feedback = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    attempt = relationship("Attempt", back_populates="answers")
    task = relationship("Task")
