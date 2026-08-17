"""
Research Hub database models.
Projects, notes, bookmarks, and citations.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.engine import Base


class ResearchProject(Base):
    """Research project model."""
    __tablename__ = "research_projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=False, default=list)
    is_archived = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="research_projects")
    notes = relationship("ResearchNote", back_populates="project", cascade="all, delete-orphan")
    bookmarks = relationship("ResearchBookmark", back_populates="project", cascade="all, delete-orphan")
    citations = relationship("ResearchCitation", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ResearchProject {self.title}>"


class ResearchNote(Base):
    """Research note model."""
    __tablename__ = "research_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("research_projects.id"), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    source_url = Column(Text, nullable=True)
    tags = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("ResearchProject", back_populates="notes")
    author = relationship("User", back_populates="research_notes")
    citations = relationship("ResearchCitation", back_populates="note", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ResearchNote {self.title}>"


class ResearchBookmark(Base):
    """Research bookmark model."""
    __tablename__ = "research_bookmarks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("research_projects.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    url = Column(Text, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    project = relationship("ResearchProject", back_populates="bookmarks")
    user = relationship("User", back_populates="research_bookmarks")

    def __repr__(self) -> str:
        return f"<ResearchBookmark {self.title}>"


class ResearchCitation(Base):
    """Research citation model."""
    __tablename__ = "research_citations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("research_projects.id"), nullable=False)
    note_id = Column(UUID(as_uuid=True), ForeignKey("research_notes.id"), nullable=True)
    source_type = Column(String(50), nullable=False)  # web, book, article, paper, other
    title = Column(String(500), nullable=False)
    authors = Column(JSON, nullable=False, default=list)
    publication_date = Column(DateTime, nullable=True)
    url = Column(Text, nullable=True)
    quote = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    project = relationship("ResearchProject", back_populates="citations")
    note = relationship("ResearchNote", back_populates="citations")

    def __repr__(self) -> str:
        return f"<ResearchCitation {self.title}>"