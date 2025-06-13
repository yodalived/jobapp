from typing import Dict, Any, List
import openai
from pydantic import BaseModel
from src.core.config import settings
import json


class ResumeCustomizer:
    def __init__(self):
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
        else:
            raise ValueError("OpenAI API key not configured")
    
    async def customize_resume_for_job(
        self,
        master_resume_data: Dict[str, Any],
        job_description: str,
        job_title: str,
        company: str
    ) -> Dict[str, Any]:
        """Customize resume content based on job description"""
        
        # Prepare the prompt
        prompt = self._create_customization_prompt(
            master_resume_data,
            job_description,
            job_title,
            company
        )
        
        # Call OpenAI
        response = await self._call_openai(prompt)
        
        # Parse and validate response
        customized_data = self._parse_response(response)
        
        # Merge with original data (keep contact info, education unchanged)
        return self._merge_resume_data(master_resume_data, customized_data)
    
    def _create_customization_prompt(
        self,
        resume_data: Dict[str, Any],
        job_description: str,
        job_title: str,
        company: str
    ) -> str:
        return f"""You are an expert resume writer. Customize this resume for a {job_title} position at {company}.

MASTER RESUME DATA:
{json.dumps(resume_data, indent=2)}

JOB DESCRIPTION:
{job_description}

INSTRUCTIONS:
1. Rewrite the summary to directly address this job's requirements
2. Select and reorder the most relevant skills for this position
3. Rewrite experience bullets to emphasize relevant achievements
4. Use keywords from the job description naturally
5. Quantify achievements with metrics where possible
6. Keep bullets concise and impactful
7. Prioritize recent and relevant experience

Return a JSON object with these fields:
{{
    "summary": "Customized summary targeting this specific role",
    "skills": {{
        "Group1": ["skill1", "skill2"],
        "Group2": ["skill1", "skill2"]
    }},
    "experience": [
        {{
            "title": "Job Title",
            "company": "Company Name",
            "location": "Location",
            "start_date": "Month Year",
            "end_date": "Month Year or Present",
            "bullets": [
                "Achievement focused on job requirements",
                "Quantified result matching job needs"
            ],
            "relevance_score": 9  // 1-10 score for this job
        }}
    ]
}}

Focus on achievements that match the job requirements. Return ONLY valid JSON."""
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API with retry logic"""
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4-turbo-preview",  # or gpt-3.5-turbo for cost savings
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert resume writer who creates ATS-optimized resumes."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            # Fallback or retry logic
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate OpenAI response"""
        try:
            # Extract JSON from response (in case there's extra text)
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return json.loads(response)
        except json.JSONDecodeError:
            raise ValueError("Failed to parse LLM response as JSON")
    
    def _merge_resume_data(
        self,
        original: Dict[str, Any],
        customized: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge customized content with original resume data"""
        merged = original.copy()
        
        # Update with customized content
        if "summary" in customized:
            merged["summary"] = customized["summary"]
        
        if "skills" in customized:
            merged["skills"] = customized["skills"]
        
        if "experience" in customized:
            # Sort experience by relevance score if provided
            experiences = customized["experience"]
            for exp in experiences:
                exp.pop("relevance_score", None)  # Remove internal score
            merged["experience"] = experiences
        
        return merged


class JobAnalyzer:
    """Analyze job descriptions to extract key requirements"""
    
    def __init__(self):
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
    
    async def analyze_job(self, job_description: str) -> Dict[str, Any]:
        """Extract key information from job description"""
        prompt = f"""Analyze this job description and extract key information:

{job_description}

Return a JSON object with:
{{
    "required_skills": ["skill1", "skill2"],
    "preferred_skills": ["skill1", "skill2"],
    "key_responsibilities": ["resp1", "resp2"],
    "experience_level": "junior/mid/senior/lead",
    "job_type": "technical/management/hybrid",
    "important_keywords": ["keyword1", "keyword2"],
    "company_culture_hints": ["hint1", "hint2"]
}}

Return ONLY valid JSON."""
        
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a job description analyzer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            return json.loads(response.choices[0].message.content)
        except:
            # Return empty analysis on error
            return {
                "required_skills": [],
                "preferred_skills": [],
                "key_responsibilities": [],
                "experience_level": "unknown",
                "job_type": "technical",
                "important_keywords": [],
                "company_culture_hints": []
            }
