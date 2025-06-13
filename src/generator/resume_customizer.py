from typing import Dict, Any, List
from pydantic import BaseModel
import json
from src.generator.llm_interface import LLMService


class ResumeCustomizer:
    def __init__(self):
        self.llm = LLMService()
        self.system_prompt = """You are an expert resume writer who creates ATS-optimized resumes. 
Your goal is to customize resumes to match specific job requirements while maintaining truthfulness 
and highlighting relevant experience."""
    
    async def customize_resume_for_job(
        self,
        master_resume_data: Dict[str, Any],
        job_description: str,
        job_title: str,
        company: str,
        provider: str = None
    ) -> Dict[str, Any]:
        """Customize resume content based on job description using specified LLM provider"""
        
        prompt = self._create_customization_prompt(
            master_resume_data,
            job_description,
            job_title,
            company
        )
        
        # Generate with specified provider
        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            provider=provider,
            max_tokens=2000
        )
        
        # Parse and validate response
        customized_data = self._parse_response(response)
        
        # Merge with original data
        return self._merge_resume_data(master_resume_data, customized_data)
    
    def _create_customization_prompt(
        self,
        resume_data: Dict[str, Any],
        job_description: str,
        job_title: str,
        company: str
    ) -> str:
        return f"""Customize this resume for a {job_title} position at {company}.

MASTER RESUME DATA:
{json.dumps(resume_data, indent=2)}

JOB DESCRIPTION:
{job_description}

INSTRUCTIONS:
1. Write a compelling summary (2-3 sentences) that directly addresses this job's requirements
2. Select and group the most relevant skills for this position
3. For each experience, select the most relevant bullets and rewrite them to:
   - Emphasize achievements that match job requirements
   - Include metrics and quantifiable results
   - Use keywords from the job description naturally
   - Start with strong action verbs
4. Order experiences by relevance (most relevant first)
5. Keep the same job titles, companies, and dates
6. Limit to 3-5 bullets per job, focusing on quality over quantity

Return a JSON object with this exact structure:
{{
    "summary": "Customized professional summary",
    "skills": {{
        "Primary Skills": ["skill1", "skill2", "skill3"],
        "Secondary Skills": ["skill1", "skill2", "skill3"],
        "Tools & Technologies": ["tool1", "tool2", "tool3"]
    }},
    "experience": [
        {{
            "title": "Original Job Title",
            "company": "Original Company",
            "location": "Original Location",
            "start_date": "Original Start Date",
            "end_date": "Original End Date",
            "bullets": [
                "Rewritten bullet emphasizing relevant achievement",
                "Another bullet with metrics matching job needs"
            ]
        }}
    ]
}}

Return ONLY valid JSON, no additional text."""
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate LLM response"""
        try:
            # Try to extract JSON from response
            import re
            
            # First try to parse as-is
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                pass
            
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            raise ValueError("No valid JSON found in response")
            
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {str(e)}")
    
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
            merged["experience"] = customized["experience"]
        
        return merged


class JobAnalyzer:
    """Analyze job descriptions using multiple LLM providers"""
    
    def __init__(self):
        self.llm = LLMService()
        self.system_prompt = "You are an expert at analyzing job descriptions and extracting key requirements."
    
    async def analyze_job(self, job_description: str, provider: str = None) -> Dict[str, Any]:
        """Extract key information from job description"""
        
        prompt = f"""Analyze this job description and extract key information:

{job_description}

Return a JSON object with:
{{
    "required_skills": ["skill1", "skill2", "skill3"],
    "preferred_skills": ["skill1", "skill2"],
    "key_responsibilities": ["responsibility1", "responsibility2"],
    "experience_level": "junior/mid/senior/lead/principal",
    "job_type": "technical/management/hybrid",
    "important_keywords": ["keyword1", "keyword2", "keyword3"],
    "company_culture_hints": ["remote-friendly", "fast-paced", etc],
    "estimated_salary_range": "e.g., $120k-$150k or null if not mentioned"
}}

Focus on technical requirements and actionable information.
Return ONLY valid JSON."""
        
        try:
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=self.system_prompt,
                provider=provider,
                max_tokens=1000
            )
            
            # Parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(response)
            
        except Exception as e:
            # Return empty analysis on error
            return {
                "required_skills": [],
                "preferred_skills": [],
                "key_responsibilities": [],
                "experience_level": "unknown",
                "job_type": "technical",
                "important_keywords": [],
                "company_culture_hints": [],
                "estimated_salary_range": None
            }
