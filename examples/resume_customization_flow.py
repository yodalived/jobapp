"""
Example flow for using the resume customization system

1. User uploads their master resume data (or enters it manually)
2. User finds a job and creates an application
3. System analyzes the job description
4. System customizes the resume for that specific job
5. System generates a PDF
"""

import asyncio
import httpx

# Example master resume data
MASTER_RESUME = {
    "name": "Jane Developer",
    "email": "jane@example.com",
    "phone": "(555) 123-4567",
    "github": "https://github.com/janedev",
    "github_display": "github.com/janedev",
    "linkedin": "https://linkedin.com/in/janedev",
    
    # Generic summary - will be customized per job
    "summary": "Experienced software engineer with expertise in full-stack development, cloud architecture, and team leadership. Passionate about building scalable solutions and mentoring developers.",
    
    # All skills - AI will select most relevant
    "skills": {
        "Languages": ["Python", "JavaScript", "TypeScript", "Go", "Java", "SQL"],
        "Backend": ["FastAPI", "Django", "Node.js", "Express", "GraphQL"],
        "Frontend": ["React", "Vue.js", "Next.js", "Redux", "Tailwind CSS"],
        "Databases": ["PostgreSQL", "MongoDB", "Redis", "Elasticsearch"],
        "Cloud/DevOps": ["AWS", "Docker", "Kubernetes", "Terraform", "CI/CD"],
        "Tools": ["Git", "Jira", "Datadog", "Sentry", "Linux"]
    },
    
    # Full experience - AI will emphasize relevant bullets
    "experience": [
        {
            "title": "Senior Software Engineer",
            "company": "TechCorp",
            "location": "San Francisco, CA",
            "start_date": "Jan 2022",
            "end_date": "Present",
            "bullets": [
                "Led development of microservices architecture serving 5M+ daily users",
                "Reduced API response time by 60% through optimization and caching",
                "Mentored team of 5 junior developers, improving team velocity by 30%",
                "Implemented CI/CD pipeline reducing deployment time from 2 hours to 15 minutes",
                "Designed and built real-time analytics dashboard using React and WebSockets",
                "Managed AWS infrastructure with Terraform, reducing costs by 40%",
                "Built Python-based ETL pipelines processing 100GB+ of data daily"
            ]
        },
        {
            "title": "Software Engineer II",
            "company": "StartupXYZ",
            "location": "Remote",
            "start_date": "Jun 2020",
            "end_date": "Dec 2021",
            "bullets": [
                "Developed REST APIs and GraphQL endpoints for mobile and web clients",
                "Built responsive React components used across 10+ products",
                "Implemented automated testing increasing coverage from 40% to 85%",
                "Collaborated with PM and design team in agile environment",
                "Optimized database queries reducing load time by 70%",
                "Created Docker-based development environment for team of 20",
                "Participated in on-call rotation ensuring 99.9% uptime"
            ]
        }
    ],
    
    "education": [
        {
            "school": "University of California, Berkeley",
            "degree": "BS in Computer Science",
            "graduation_date": "May 2020"
        }
    ]
}

# Example job description
EXAMPLE_JOB = {
    "company": "AI Startup Inc",
    "position": "Senior Python Engineer",
    "job_description": """
    We're looking for a Senior Python Engineer to join our ML Platform team.
    
    Requirements:
    - 3+ years of Python development experience
    - Strong experience with FastAPI or similar frameworks
    - Experience with Docker and Kubernetes
    - Knowledge of machine learning concepts
    - Experience with PostgreSQL and Redis
    - Strong communication skills
    
    Nice to have:
    - Experience with LangChain or similar LLM frameworks
    - AWS experience
    - Background in data engineering
    
    You'll be:
    - Building scalable APIs for our ML models
    - Designing data pipelines
    - Mentoring junior engineers
    - Working closely with our data science team
    """
}


async def demonstrate_flow():
    """Show the complete resume customization flow"""
    
    async with httpx.AsyncClient() as client:
        # 1. Login
        login_response = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            data={"username": "test@example.com", "password": "password123"}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Create job application
        app_response = await client.post(
            "http://localhost:8000/api/v1/applications/",
            headers=headers,
            json={
                "company": EXAMPLE_JOB["company"],
                "position": EXAMPLE_JOB["position"],
                "job_description": EXAMPLE_JOB["job_description"],
                "url": "https://example.com/job/123",
                "source": "company_website"
            }
        )
        application_id = app_response.json()["id"]
        
        # 3. Analyze the job
        analysis_response = await client.post(
            "http://localhost:8000/api/v1/generator/analyze-job",
            headers=headers,
            json={"job_description": EXAMPLE_JOB["job_description"]}
        )
        print("Job Analysis:", analysis_response.json())
        
        # 4. Preview customization
        preview_response = await client.post(
            "http://localhost:8000/api/v1/generator/preview-customization",
            headers=headers,
            json={
                "application_id": application_id,
                "master_resume_data": MASTER_RESUME,
                "customize_with_ai": True
            }
        )
        print("Customization Preview:", preview_response.json()["customized"]["summary"][:200] + "...")
        
        # 5. Generate customized resume
        generate_response = await client.post(
            "http://localhost:8000/api/v1/generator/generate-customized",
            headers=headers,
            json={
                "application_id": application_id,
                "master_resume_data": MASTER_RESUME,
                "customize_with_ai": True,
                "template_name": "modern_professional"
            }
        )
        print("Generated Resume:", generate_response.json())


if __name__ == "__main__":
    asyncio.run(demonstrate_flow())
