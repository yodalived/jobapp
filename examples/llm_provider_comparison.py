"""
Example showing how to use different LLM providers for resume customization
"""

import asyncio
import httpx

async def compare_providers():
    async with httpx.AsyncClient() as client:
        # Login first
        login_response = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            data={"username": "test@example.com", "password": "password123"}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Check available providers
        providers_response = await client.get(
            "http://localhost:8000/api/v1/generator/llm-providers",
            headers=headers
        )
        print("Available Providers:", providers_response.json())
        
        # Example job description
        job_description = """
        Senior Python Developer needed for AI startup.
        Must have experience with FastAPI, LangChain, and vector databases.
        Knowledge of transformer models and prompt engineering is a plus.
        """
        
        # Analyze with OpenAI
        openai_analysis = await client.post(
            "http://localhost:8000/api/v1/generator/analyze-job",
            headers=headers,
            params={
                "job_description": job_description,
                "llm_provider": "openai"
            }
        )
        print("\nOpenAI Analysis:", openai_analysis.json())
        
        # Analyze with Claude
        claude_analysis = await client.post(
            "http://localhost:8000/api/v1/generator/analyze-job",
            headers=headers,
            params={
                "job_description": job_description,
                "llm_provider": "anthropic"
            }
        )
        print("\nClaude Analysis:", claude_analysis.json())
        
        # Compare both providers
        comparison = await client.post(
            "http://localhost:8000/api/v1/generator/compare-providers",
            headers=headers,
            params={"job_description": job_description}
        )
        print("\nProvider Comparison:", comparison.json())

if __name__ == "__main__":
    asyncio.run(compare_providers())
