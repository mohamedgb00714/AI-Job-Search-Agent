"""This module defines the tools used by the agent.

Feel free to modify or add new tools to suit your specific needs.

To learn how to create a new tool, see:
- https://python.langchain.com/docs/concepts/tools/
- https://python.langchain.com/docs/how_to/#tools

Tools for job searching and resume analysis using various job board scrapers.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional, TypedDict
from pydantic import BaseModel, Field

from apify import Actor
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from src.models import JobMatch, JobPreferences


class JobSearchInput(BaseModel):
    """Input schema for job search tools."""
    query: str = Field(..., description="Job title or keywords")
    location: str = Field(default="Remote", description="Job location")


class JobSearchResult(TypedDict):
    """Standardized job search result format."""
    title: str
    company: str
    location: str
    posting_date: str
    employment_type: str
    salary: str
    description: str
    url: str
    is_remote: bool


class ResumeInput(BaseModel):
    resume_text: str


async def base_job_search(
    query: str,
    actor_id: str,
    location: str = "Remote"
) -> List[JobSearchResult]:
    """Base function for job searching across different platforms."""
    try:
        run_input = {
            "query": query.split(',')[0].strip(),
            "location": location if ',' not in query else query.split(',')[1].strip(),
            "limit": 10
        }
        
        run = await Actor.apify_client.actor(actor_id).call(run_input=run_input)
        if not run:
            return []
            
        dataset_items = (await Actor.apify_client.dataset(run["defaultDatasetId"]).list_items()).items
        return format_job_results(dataset_items)
    except Exception as e:
        Actor.log.error(f"Job search failed for {actor_id}: {str(e)}")
        return []


def format_job_results(items: List[Dict[str, Any]]) -> List[JobSearchResult]:
    """Format raw job listings into standardized format."""
    formatted_jobs = []
    for job in items:
        try:
            formatted_job = JobSearchResult(
                title=job.get('title', '').strip(),
                company=job.get('companyName', '').strip(),
                location=job.get('jobLocation', {}).get('displayName', '').strip(),
                posting_date=job.get('postedDate', ''),
                employment_type=job.get('employmentType', ''),
                salary=job.get('salary', 'Not specified'),
                description=job.get('summary', '')[:300] + '...' if job.get('summary') else '',  # Limit description length
                url=job.get('detailsPageUrl', ''),
                is_remote=job.get('isRemote', False)
            )
            formatted_jobs.append(formatted_job)
        except Exception as e:
            Actor.log.error(f"Failed to format job listing: {str(e)}")
            continue
            
    return formatted_jobs[:5]  # Limit to top 5 results


async def _linkedin_search(query: str) -> List[JobSearchResult]:
    """Search for jobs on LinkedIn."""
    return await base_job_search(query, "krandiash/linkedin-jobs-scraper")


# Create LinkedIn search tool
tool_linkedin_search = Tool(
    name="search_linkedin_jobs",
    description="Search for jobs on LinkedIn. Input format: 'job title, location'",
    func=_linkedin_search,
    coroutine=_linkedin_search
)


async def _indeed_search(query: str) -> List[JobSearchResult]:
    """Search for jobs on Indeed."""
    return await base_job_search(query, "krandiash/indeed-scraper")


# Create Indeed search tool
tool_indeed_search = Tool(
    name="search_indeed_jobs",
    description="Search for jobs on Indeed. Input format: 'job title, location'",
    func=_indeed_search,
    coroutine=_indeed_search
)


async def _dice_search(query: str) -> List[JobSearchResult]:
    """Search for jobs on Dice."""
    return await base_job_search(query, "mohamedgb00714/dicecom-job-scraper")


# Create Dice search tool
tool_dice_search = Tool(
    name="search_dice_jobs",
    description="Search for jobs on Dice. Input format: 'job title, location'",
    func=_dice_search,
    coroutine=_dice_search
)


async def _analyze_resume(resume_text: str) -> Dict[str, Any]:
    """Analyze a resume to extract key information."""
    if not resume_text.strip():
        return {
            "error": "Empty resume text provided",
            "skills": [], "experience": [], "education": [],
            "summary": "No resume to analyze", "years_experience": 0
        }

    try:
        llm = ChatOpenAI(temperature=0)
        output_parser = JsonOutputParser()
        
        prompt = ChatPromptTemplate.from_template(
            """Analyze this resume and extract key information. Return ONLY a JSON object:
            
            Resume: {resume_text}
            
            Format: {format_instructions}
            """
        )
        
        chain = prompt | llm | output_parser
        
        analysis = await chain.ainvoke({
            "resume_text": resume_text,
            "format_instructions": output_parser.get_format_instructions()
        })
        
        return {**analysis, "raw_text": resume_text}
        
    except Exception as e:
        Actor.log.error(f"Resume analysis failed: {str(e)}")
        return {
            "error": str(e),
            "skills": [], "experience": [], "education": [],
            "summary": "Analysis failed", "years_experience": 0,
            "raw_text": resume_text
        }


# Create analyze_resume tool
analyze_resume = Tool(
    name="analyze_resume",
    description="Analyze a resume to extract skills, experience, and other key information.",
    func=_analyze_resume,
    coroutine=_analyze_resume
)
