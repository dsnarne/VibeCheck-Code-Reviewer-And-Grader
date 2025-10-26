"""
Database schema definitions and Pydantic models for VibeCheck.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    email: str = Field(..., description="User email address")
    name: Optional[str] = Field(None, description="User's full name")
    github_username: Optional[str] = Field(None, description="GitHub username")


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = None
    github_username: Optional[str] = None


class User(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RepoBase(BaseModel):
    user_id: UUID = Field(..., description="User who owns this repository")
    owner: str = Field(..., description="Repository owner")
    name: str = Field(..., description="Repository name")
    full_name: str = Field(..., description="Full repository name (owner/repo)")
    description: Optional[str] = Field(None, description="Repository description")
    html_url: str = Field(..., description="Repository HTML URL")
    clone_url: Optional[str] = Field(None, description="Repository clone URL")
    default_branch: str = Field("main", description="Default branch name")
    language: Optional[str] = Field(None, description="Primary programming language")
    stars_count: int = Field(0, description="Number of stars")
    forks_count: int = Field(0, description="Number of forks")
    size_bytes: int = Field(0, description="Repository size in bytes")
    window_days: int = Field(3650, description="Analysis window in days")
    max_commits: int = Field(500, description="Maximum commits to analyze")
    languages: Optional[Dict[str, Any]] = Field(None, description="Language analysis data")
    team_data: Optional[Dict[str, Any]] = Field(None, description="Team contribution analysis")
    commits_data: Optional[Dict[str, Any]] = Field(None, description="Commit analysis data")
    raw_analysis: Optional[Dict[str, Any]] = Field(None, description="Complete analysis results")
    file_storage_base_path: Optional[str] = Field(None, description="Base path for stored files")
    file_count: int = Field(0, description="Number of files stored")
    files_ready_for_embedding: bool = Field(False, description="Whether files are ready for vector embedding")
    file_metadata: List[Dict[str, Any]] = Field(default_factory=list, description="File metadata as JSONB array")


class RepoCreate(RepoBase):
    pass


class RepoUpdate(BaseModel):
    description: Optional[str] = None
    stars_count: Optional[int] = None
    forks_count: Optional[int] = None
    size_bytes: Optional[int] = None


class Repo(RepoBase):
    id: UUID
    analysis_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# File metadata is now stored as JSONB in the repos table
class FileMetadata(BaseModel):
    relative_path: str = Field(..., description="File path relative to repository root")
    storage_path: str = Field(..., description="Full storage path in Supabase")
    public_url: str = Field(..., description="Public URL to access the file")
    size_bytes: int = Field(..., description="File size in bytes")
    file_extension: Optional[str] = Field(None, description="File extension")
    content_type: Optional[str] = Field(None, description="MIME content type")


# API Request/Response models
class AnalyzeRequest(BaseModel):
    repo_url: str = Field(..., description="GitHub repository URL")
    window_days: int = Field(3650, description="Analysis window in days")
    max_commits: int = Field(500, description="Maximum commits to analyze")
    download_zipball: bool = Field(True, description="Whether to download and extract files")


class AnalyzeWithStorageRequest(BaseModel):
    repo_url: str = Field(..., description="GitHub repository URL")
    user_id: UUID = Field(..., description="User ID for storage")
    window_days: int = Field(3650, description="Analysis window in days")
    max_commits: int = Field(500, description="Maximum commits to analyze")
    download_zipball: bool = Field(True, description="Whether to download and extract files")


class UserRequest(BaseModel):
    email: str = Field(..., description="User email address")
    name: Optional[str] = Field(None, description="User's full name")
    github_username: Optional[str] = Field(None, description="GitHub username")


class AnalysisResponse(BaseModel):
    repo: str = Field(..., description="Repository name")
    limits: Optional[Dict[str, Any]] = Field(None, description="Analysis limits")
    languages: Optional[Dict[str, Any]] = Field(None, description="Language analysis")
    team: Optional[Dict[str, Any]] = Field(None, description="Team analysis")
    commits: Optional[Dict[str, Any]] = Field(None, description="Commit analysis")
    file_storage: Optional[Dict[str, Any]] = Field(None, description="File storage info")
    repo_id: Optional[str] = Field(None, description="Database repository ID")
    stored_in_db: bool = Field(False, description="Whether stored in database")
    files_stored: bool = Field(False, description="Whether files were stored")
    file_count: Optional[int] = Field(None, description="Number of files stored")
    warning: Optional[str] = Field(None, description="Warning message")
    error: Optional[str] = Field(None, description="Error message")
    suggestion: Optional[str] = Field(None, description="Suggestion for error resolution")


class PaginatedResponse(BaseModel):
    count: int = Field(..., description="Number of items returned")
    limit: int = Field(..., description="Maximum items per page")
    offset: int = Field(..., description="Number of items skipped")
