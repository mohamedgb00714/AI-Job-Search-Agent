"""This module defines the main entry point for the Apify Actor.

Feel free to modify this file to suit your specific needs.

To build Apify Actors, utilize the Apify SDK toolkit, read more at the official documentation:
https://docs.apify.com/sdk/python
"""

from __future__ import annotations

import logging
import os
from typing import Dict, Any, List
import json
import re

from apify import Actor
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent as create_base_agent, initialize_agent
from langchain.prompts import PromptTemplate
from langchain.agents import AgentType
from pydantic import BaseModel

from src.models import AgentStructuredOutput
from src.ppe_utils import charge_for_actor_start, charge_for_model_tokens, get_all_messages_total_tokens
from src.tools import  tool_linkedin_search, tool_indeed_search, tool_dice_search, analyze_resume
from src.utils import log_state

os.environ["OPENAI_API_KEY"] = "yourapi key here"

# fallback input is provided only for testing, you need to delete this line
fallback_input = {
    'query': 'This is fallback test query, do not nothing and ignore it.',
    'modelName': 'gpt-4o-mini',
}

def setup_react_agent(llm: ChatOpenAI, tools: list, response_format: Any) -> AgentExecutor:
    """Create a ReAct agent with the given LLM and tools."""
    
    prompt = PromptTemplate.from_template("""Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of {tool_names}
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin! Remember to ALWAYS follow the format above - start with Thought, then Action, then Action Input.

Question: {input}

{agent_scratchpad}""")
    
    # Create the agent using LangChain's create_react_agent
    agent = create_base_agent(llm, tools, prompt)
    
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5  # Limit the number of iterations to prevent infinite loops
    )

def format_job_results(jobs: List[Dict[str, Any]]) -> str:
    """Format job results into a readable report"""
    if not jobs:
        return "No jobs found matching your criteria."
        
    report = "# Available Job Opportunities\n\n"
    
    for i, job in enumerate(jobs, 1):
        report += f"## {i}. {job['title']}\n"
        report += f"**Company:** {job['company']}\n"
        report += f"**Location:** {job['location']}\n"
        report += f"**Type:** {job['employment_type']}\n"
        report += f"**Salary:** {job['salary']}\n"
        report += f"**Posted:** {job['posting_date']}\n"
        report += f"**Description:** {job['description']}\n"
        report += f"**Apply here:** {job['url']}\n\n"
        report += "---\n\n"
    
    return report

# Update the agent's system message to enforce strict JSON output
system_message = """You are a job search assistant. When searching for jobs, you MUST ONLY return a JSON response wrapped in code block markers, with NO OTHER TEXT before or after. Format exactly like this:

```json
{
    "summary": {
        "total_jobs_found": <number>,
        "skills_matched": ["skill1", "skill2", ...],
        "experience_years": <number>,
        "previous_position": "position title"
    },
    "jobs": [
        {
            "title": "Job Title",
            "company": "Company Name",
            "location": "Location",
            "posting_date": "YYYY-MM-DD",
            "employment_type": "Full-time/Contract/etc",
            "salary": "Salary Range",
            "description": "Brief job description",
            "url": "Application URL",
            "is_remote": true/false,
            "skills_match": ["matched_skill1", "matched_skill2", ...],
            "match_percentage": 85
        }
    ]
}
```

CRITICAL RULES:
1. Return ONLY the JSON code block above - no other text
2. Always start with ```json and end with ```
3. Ensure the JSON is valid and properly formatted
4. Do not include any explanations or thoughts in the output
5. Fill in all fields, using "Not specified" for missing values
"""

async def charge_for_actor_start() -> None:
    # Implement charging logic here
    pass

async def main() -> None:
    """Main entry point for the Apify Actor."""
    async with Actor:
        # Get input
        actor_input = await Actor.get_input() or fallback_input
        resume = actor_input.get('resume', '')
        location = actor_input.get('location', 'Remote')
        job_type = actor_input.get('jobType', 'full-time')
        keywords = actor_input.get('keywords', '')

        # Initialize the LLM
        llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.7,
            max_tokens=2000
        )

        # Create the tools list
        tools = [tool_linkedin_search, tool_indeed_search, tool_dice_search, analyze_resume]

        # Get tool names for the prompt
        tool_names = [tool.name for tool in tools]

        # Create the agent
        agent = setup_react_agent(llm, tools, None)

        # Process the query
        result = await agent.ainvoke(
            {
                "input": f"""Find relevant job opportunities based on this resume and preferences:
Resume:
{resume}

Job Preferences:
- Location: {location}
- Job Type: {job_type}
- Keywords: {keywords}

Analyze the resume and search for matching jobs. Return a JSON response with:
1. A brief summary of the search results
2. An array of relevant jobs found (limit to top 5 most relevant)
3. Recommended next steps for the job seeker

Format the response as a JSON object with these exact fields:
{{
    "summary": "Brief overview of search results",
    "jobs": [
        {{
            "title": "Job title",
            "company": "Company name",
            "location": "Job location",
            "salary": "Salary if available",
            "match_score": "Relevance score 0-1",
            "url": "Job posting URL"
        }}
    ],
    "recommendations": ["List of recommended next steps"]
}}""",
                "tools": tools,
                "tool_names": tool_names
            }
        )

        # Process and push final results only once
        try:
            if isinstance(result, dict) and 'output' in result:
                output = result['output']
                
                # Try to extract JSON from various formats
                json_data = None
                
                # Try direct JSON parsing first
                if isinstance(output, str):
                    try:
                        json_data = json.loads(output)
                    except json.JSONDecodeError:
                        # Try extracting from markdown block
                        json_match = re.search(r'```(?:json)?\s*({\s*".*?})\s*```', output, re.DOTALL)
                        if json_match:
                            try:
                                json_data = json.loads(json_match.group(1).strip())
                            except json.JSONDecodeError:
                                pass

                if json_data:
                    # Validate and clean the data
                    cleaned_data = {
                        "summary": json_data.get("summary", "No summary provided"),
                        "jobs": json_data.get("jobs", [])[:5],  # Limit to top 5 jobs
                        "recommendations": json_data.get("recommendations", [])
                    }
                    await Actor.push_data(cleaned_data)
                else:
                    await Actor.push_data({
                        "error": "Could not parse JSON output",
                        "raw_output": output
                    })
            else:
                await Actor.push_data({
                    "error": "Unexpected output format",
                    "raw_output": str(result)
                })
                
        except Exception as e:
            Actor.log.error(f"Failed to process results: {str(e)}")
            await Actor.push_data({
                "error": f"Failed to process results: {str(e)}",
                "raw_output": str(result)
            })

if __name__ == "__main__":
    Actor.main(main)
