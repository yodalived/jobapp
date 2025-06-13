# Example resume data structures showing required and optional fields

MINIMAL_RESUME_DATA = {
    "name": "Jane Smith",
    "email": "jane.smith@example.com",
    "experience": [
        {
            "title": "Software Engineer",
            "company": "Tech Company",
            "location": "Remote",
            "start_date": "Jan 2022",
            "end_date": "Present",
            "bullets": [
                "Developed and maintained web applications",
                "Collaborated with cross-functional teams"
            ]
        }
    ],
    "education": [
        {
            "school": "State University",
            "degree": "BS in Computer Science"
        }
    ]
}

FULL_RESUME_DATA = {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "(555) 123-4567",
    "location": "San Francisco, CA",
    "portfolio": "https://johndoe.com",
    "portfolio_display": "johndoe.com",
    "github": "https://github.com/johndoe",
    "github_display": "github.com/johndoe",
    "linkedin": "https://linkedin.com/in/johndoe",
    "linkedin_display": "LinkedIn",
    "summary": "Experienced software engineer with 5+ years building scalable web applications. Passionate about clean code, system design, and mentoring junior developers.",
    "skills": {
        "Languages": ["Python", "JavaScript", "Go", "SQL"],
        "Technologies": ["FastAPI", "React", "PostgreSQL", "Docker", "Kubernetes"],
        "Tools": ["Git", "CI/CD", "AWS", "Terraform", "Linux"]
    },
    "experience": [
        {
            "title": "Senior Software Engineer",
            "company": "Tech Corp",
            "location": "San Francisco, CA",
            "start_date": "June 2022",
            "end_date": "Present",
            "bullets": [
                "Built microservices handling 10M+ requests/day using FastAPI and PostgreSQL",
                "Led team of 4 engineers in redesigning core API, improving response time by 40%",
                "Implemented CI/CD pipeline reducing deployment time from 2 hours to 15 minutes",
                "Mentored 2 junior engineers, helping them grow into mid-level positions"
            ]
        },
        {
            "title": "Software Engineer II",
            "company": "Startup Inc",
            "location": "Remote",
            "start_date": "Jan 2021",
            "end_date": "May 2022",
            "bullets": [
                "Developed React dashboard used by 1000+ customers daily",
                "Designed and implemented RESTful APIs serving mobile and web clients",
                "Reduced infrastructure costs by 30% through optimization and caching"
            ]
        },
        {
            "title": "Junior Software Engineer",
            "company": "First Company",
            "location": "Austin, TX",
            "start_date": "Jul 2019",
            "end_date": "Dec 2020",
            "bullets": [
                "Built features for e-commerce platform serving 50K users",
                "Fixed critical bugs and improved test coverage from 45% to 80%"
            ]
        }
    ],
    "education": [
        {
            "school": "University of California, Berkeley",
            "degree": "BS in Computer Science",
            "graduation_date": "May 2019"
        }
    ]
}
