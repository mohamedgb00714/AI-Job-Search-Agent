"""This module defines Pydantic models for this project.

These models are used mainly for the structured tool and LLM outputs.
Resources:
- https://docs.pydantic.dev/latest/concepts/models/
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class JobPreferences(BaseModel):
    location: str = Field(..., description="Preferred job location")
    job_types: List[str] = Field(default=["full-time"], description="Types of employment")
    salary_range: Optional[Dict[str, float]] = Field(None, description="Desired salary range")
    remote_preference: str = Field(default="hybrid", description="Remote work preference: 'remote', 'hybrid', 'onsite'")
    industries: Optional[List[str]] = Field(None, description="Preferred industries")
    experience_level: str = Field(default="mid-level", description="Experience level: 'entry', 'mid-level', 'senior'")


class JobMatch(BaseModel):
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    url: str = Field(..., description="Job posting URL")
    match_score: float = Field(..., description="Match score between 0 and 1")
    salary_range: Optional[str] = Field(None, description="Salary range if available")
    key_requirements: List[str] = Field(default_factory=list, description="Key job requirements")
    skill_matches: List[str] = Field(default_factory=list, description="Matching skills from resume")
    missing_skills: List[str] = Field(default_factory=list, description="Required skills not found in resume")
    job_description: str = Field(..., description="Brief job description")
    posting_date: Optional[str] = Field(None, description="When the job was posted")


class AgentStructuredOutput(BaseModel):
    """Structured output for the ReAct agent."""
    matches: List[JobMatch] = Field(..., description="List of matching jobs")
    summary: str = Field(..., description="Summary of job search results")
    recommended_actions: List[str] = Field(..., description="Recommended next steps")
    total_matches: int = Field(..., description="Total number of matches found")
    average_match_score: float = Field(..., description="Average match score across all jobs")
