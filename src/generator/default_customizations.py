"""Default system prompts and RAG documents for different industries"""

DEFAULT_PROMPTS = {
    "tech_senior": {
        "name": "Tech - Senior/Staff Engineer",
        "industry": "tech",
        "prompt_text": """You are an expert technical resume writer specializing in senior engineering positions. 
Your expertise includes:
- Highlighting technical leadership and architecture decisions
- Quantifying impact with metrics (performance improvements, scale, cost savings)
- Balancing technical depth with business impact
- Using modern tech terminology while remaining ATS-friendly
- Emphasizing both IC and leadership contributions

Focus on:
1. System design and architecture achievements
2. Team leadership and mentorship
3. Technical innovations and optimizations
4. Cross-functional collaboration
5. Open source contributions if relevant""",
        "description": "Optimized for senior and staff-level engineering positions"
    },
    
    "tech_junior": {
        "name": "Tech - Entry/Junior Developer",
        "industry": "tech",
        "prompt_text": """You are an expert resume writer for early-career software developers.
Focus on:
- Educational projects and internships
- Technical skills and eagerness to learn
- Collaborative abilities and team contributions
- Problem-solving approach
- Any relevant coursework or certifications

Emphasize potential and foundational skills over years of experience.""",
        "description": "Perfect for new grads and junior developers"
    },
    
    "finance": {
        "name": "Finance - General",
        "industry": "finance",
        "prompt_text": """You are an expert finance resume writer who understands:
- Quantitative achievements (ROI, cost savings, revenue growth)
- Regulatory compliance and risk management
- Financial modeling and analysis
- Industry-specific software and certifications
- Deal flow and transaction experience

Use precise financial terminology and emphasize analytical skills.""",
        "description": "For finance, banking, and accounting roles"
    },
    
    "marketing": {
        "name": "Marketing - Digital/Growth",
        "industry": "marketing",
        "prompt_text": """You are an expert marketing resume writer specializing in:
- Campaign performance metrics (CTR, conversion rates, ROAS)
- Channel expertise (SEO, SEM, social, email)
- Marketing automation and CRM tools
- Data-driven decision making
- Creative and analytical balance

Focus on measurable growth and brand impact.""",
        "description": "For digital marketing and growth roles"
    }
}

DEFAULT_RAG_DOCUMENTS = {
    "ats_optimization": {
        "name": "ATS Optimization Guide",
        "content": """Key ATS Optimization Rules:
1. Use standard section headers: Summary, Experience, Education, Skills
2. Avoid tables, columns, headers, footers, or text boxes
3. Use standard fonts (Arial, Calibri, Times New Roman)
4. Include keywords from job description naturally
5. Use both acronyms and full terms (e.g., "SEO (Search Engine Optimization)")
6. Avoid special characters in bullet points
7. Save as .docx or .pdf (text-based, not image)
8. Use consistent date formats (Month Year)""",
        "document_type": "guide",
        "industry": "general"
    },
    
    "tech_metrics": {
        "name": "Technical Achievement Metrics",
        "content": """Examples of strong technical metrics:
- Improved API response time by 60% (from 800ms to 320ms)
- Reduced infrastructure costs by $200K annually through optimization
- Scaled system to handle 10M+ daily active users
- Decreased deployment time from 2 hours to 15 minutes
- Increased test coverage from 45% to 90%
- Reduced bug rate by 40% through improved code review process
- Mentored 5 junior engineers, 3 promoted within 18 months""",
        "document_type": "example",
        "industry": "tech"
    },
    
    "action_verbs": {
        "name": "Strong Action Verbs by Category",
        "content": """Technical: Architected, Optimized, Refactored, Implemented, Debugged, Automated
Leadership: Spearheaded, Orchestrated, Championed, Mentored, Directed
Analysis: Analyzed, Evaluated, Assessed, Investigated, Diagnosed
Achievement: Delivered, Achieved, Exceeded, Surpassed, Accomplished
Innovation: Pioneered, Innovated, Designed, Created, Developed""",
        "document_type": "guide",
        "industry": "general"
    }
}
