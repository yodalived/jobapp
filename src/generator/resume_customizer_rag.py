from typing import Dict, Any, List, Optional
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import numpy as np
from src.generator.llm_interface import LLMService
from src.api.models.resume_customization import SystemPrompt, RAGDocument, IndustryTemplate, IndustryType


class ResumeCustomizerWithRAG:
    def __init__(self):
        self.llm = LLMService()
        self._default_system_prompt = """You are an expert resume writer who creates ATS-optimized resumes."""
    
    async def get_system_prompt(
        self,
        db: AsyncSession,
        prompt_id: Optional[int] = None,
        industry: Optional[IndustryType] = None,
        user_id: Optional[int] = None
    ) -> SystemPrompt:
        """Get appropriate system prompt based on criteria"""
        
        if prompt_id:
            # Get specific prompt
            result = await db.execute(
                select(SystemPrompt).where(
                    SystemPrompt.id == prompt_id,
                    SystemPrompt.is_active == True
                )
            )
            prompt = result.scalar_one_or_none()
            if prompt:
                return prompt
        
        # Try to find industry-specific prompt
        if industry:
            result = await db.execute(
                select(SystemPrompt).where(
                    SystemPrompt.industry == industry,
                    SystemPrompt.is_default == True,
                    SystemPrompt.is_active == True
                )
            )
            prompt = result.scalar_one_or_none()
            if prompt:
                return prompt
        
        # Fall back to general default
        result = await db.execute(
            select(SystemPrompt).where(
                SystemPrompt.industry == IndustryType.GENERAL,
                SystemPrompt.is_default == True,
                SystemPrompt.is_active == True
            )
        )
        return result.scalar_one_or_none()
    
    async def get_relevant_rag_documents(
        self,
        db: AsyncSession,
        job_description: str,
        industry: Optional[IndustryType] = None,
        system_prompt_id: Optional[int] = None,
        limit: int = 5
    ) -> List[RAGDocument]:
        """Get relevant RAG documents for the job"""
        
        # Build query
        query = select(RAGDocument)
        
        if system_prompt_id:
            query = query.where(RAGDocument.system_prompt_id == system_prompt_id)
        elif industry:
            query = query.where(RAGDocument.industry.in_([industry, IndustryType.GENERAL]))
        
        result = await db.execute(query)
        documents = result.scalars().all()
        
        # TODO: Implement vector similarity search when embeddings are available
        # For now, return all matching documents up to limit
        return documents[:limit]
    
    async def customize_resume_for_job(
        self,
        db: AsyncSession,
        master_resume_data: Dict[str, Any],
        job_description: str,
        job_title: str,
        company: str,
        industry: Optional[IndustryType] = None,
        system_prompt_id: Optional[int] = None,
        user_id: Optional[int] = None,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Customize resume with industry-specific prompts and RAG"""
        
        # Get appropriate system prompt
        system_prompt_obj = await self.get_system_prompt(
            db, system_prompt_id, industry, user_id
        )
        
        # Get relevant RAG documents
        rag_docs = await self.get_relevant_rag_documents(
            db, job_description, industry, system_prompt_obj.id if system_prompt_obj else None
        )
        
        # Build the enhanced prompt
        prompt = await self._build_rag_enhanced_prompt(
            master_resume_data,
            job_description,
            job_title,
            company,
            system_prompt_obj,
            rag_docs
        )
        
        # Get system prompt text
        system_prompt_text = system_prompt_obj.prompt_text if system_prompt_obj else self._default_system_prompt
        
        # Generate with LLM
        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt_text,
            provider=provider,
            max_tokens=2500
        )
        
        # Update usage count
        if system_prompt_obj:
            system_prompt_obj.usage_count += 1
            await db.commit()
        
        # Parse and return
        customized_data = self._parse_response(response)
        return self._merge_resume_data(master_resume_data, customized_data)
    
    async def _build_rag_enhanced_prompt(
        self,
        resume_data: Dict[str, Any],
        job_description: str,
        job_title: str,
        company: str,
        system_prompt: Optional[SystemPrompt],
        rag_documents: List[RAGDocument]
    ) -> str:
        """Build prompt enhanced with RAG context"""
        
        # Add RAG context
        rag_context = ""
        if rag_documents:
            rag_context = "\n\nRELEVANT GUIDELINES AND EXAMPLES:\n"
            for i, doc in enumerate(rag_documents, 1):
                rag_context += f"\n{i}. {doc.name}:\n{doc.content}\n"
        
        # Get industry-specific tips if available
        industry_tips = ""
        if system_prompt and system_prompt.config:
            tips = system_prompt.config.get("tips", [])
            if tips:
                industry_tips = "\n\nINDUSTRY-SPECIFIC TIPS:\n" + "\n".join(f"- {tip}" for tip in tips)
        
        return f"""Customize this resume for a {job_title} position at {company}.

MASTER RESUME DATA:
{json.dumps(resume_data, indent=2)}

JOB DESCRIPTION:
{job_description}
{rag_context}
{industry_tips}

INSTRUCTIONS:
1. Follow all guidelines from the provided documents
2. Write a compelling summary (2-3 sentences) targeting this specific role
3. Select and organize skills based on job requirements and industry standards
4. Customize experience bullets to:
   - Match the job requirements
   - Follow industry-specific best practices
   - Include relevant metrics and achievements
   - Use appropriate industry terminology
5. Ensure ATS optimization with relevant keywords

Return a JSON object with customized resume content following this structure:
{{
    "summary": "...",
    "skills": {{"Category": ["skill1", "skill2"]}},
    "experience": [
        {{
            "title": "...",
            "company": "...",
            "location": "...",
            "start_date": "...",
            "end_date": "...",
            "bullets": ["..."]
        }}
    ]
}}

Return ONLY valid JSON."""
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response: {str(e)}")
    
    def _merge_resume_data(
        self,
        original: Dict[str, Any],
        customized: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge customized content with original data"""
        merged = original.copy()
        for key in ["summary", "skills", "experience"]:
            if key in customized:
                merged[key] = customized[key]
        return merged
