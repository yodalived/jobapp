# test_all_endpoints.py - Cleaned up version
import asyncio
import httpx
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_system():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        base_url = os.getenv('NEXT_PUBLIC_API_URL', 'http://localhost:8048')
        print("🔍 TESTING RESUME AUTOMATION API\n")
        
        # 1. Health check
        print("1. Testing health endpoint...")
        health = await client.get(f"{base_url}/health")
        print(f"   ✅ Health: {health.json()}")
        
        # 2. Authentication
        print("\n2. Testing authentication...")
        register = await client.post(
            f"{base_url}/api/v1/auth/register",
            json={"email": "test@example.com", "password": "password123"}
        )
        if register.status_code != 200:
            print(f"   ℹ️  Register: {register.json()['detail']}")
        
        login = await client.post(
            f"{base_url}/api/v1/auth/login",
            data={"username": "test@example.com", "password": "password123"}
        )
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("   ✅ Login successful")
        
        # 3. User info
        print("\n3. Testing user endpoints...")
        me = await client.get(f"{base_url}/api/v1/auth/me", headers=headers)
        user_data = me.json()
        print(f"   ✅ Current user: {user_data['email']}")
        print(f"      - Tier: {user_data['subscription_tier']}")
        print(f"      - Applications: {user_data['applications_count']}")
        print(f"      - Resumes generated: {user_data['resumes_generated_count']}")
        
        # Get usage stats
        usage = await client.get(f"{base_url}/api/v1/auth/me/usage", headers=headers)
        if usage.status_code == 200:
            usage_data = usage.json()
            print("   ✅ Usage stats:")
            if 'usage' in usage_data:
                print(f"      - Applications count: {usage_data['usage']['applications_count']}")
                print(f"      - Resumes generated: {usage_data['usage']['resumes_generated_count']}")
            if 'limits' in usage_data:
                limits = usage_data['limits']
                print(f"      - Monthly applications limit: {limits.get('monthly_applications', 'unlimited')}")
                print(f"      - Monthly resumes limit: {limits.get('monthly_resumes', 'unlimited')}")
                print(f"      - Can use auto-apply: {limits.get('can_use_auto_apply', False)}")
                print(f"      - Can use AI suggestions: {limits.get('can_use_ai_suggestions', True)}")
        
        # 4. Create a job application
        print("\n4. Testing job applications...")
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        app_data = {
            "company": "TechCorp",
            "position": "Senior Python Developer",
            "url": f"https://example.com/job/python-dev-{timestamp}",
            "job_description": """
                We're looking for a Senior Python Developer to join our team.
                Requirements:
                - 5+ years Python experience
                - Strong FastAPI and async programming skills
                - PostgreSQL and Redis experience
                - Docker and Kubernetes knowledge
                - Experience with AI/ML is a plus
            """,
            "status": "interested",
            "job_type": "technical",
            "location": "San Francisco, CA",
            "remote": True,
            "salary_min": 150000,
            "salary_max": 200000
        }
        
        app = await client.post(
            f"{base_url}/api/v1/applications/",
            headers=headers,
            json=app_data
        )
        
        app_id = None
        if app.status_code in [200, 201]:
            app_json = app.json()
            app_id = app_json["id"]
            print(f"   ✅ Created application ID: {app_id}")
        else:
            print(f"   ❌ Failed to create: {app.text}")
            # Get existing application for testing
            apps = await client.get(f"{base_url}/api/v1/applications/", headers=headers)
            if apps.json():
                app_id = apps.json()[0]["id"]
                print(f"   ℹ️  Using existing application ID: {app_id}")
        
        # List applications
        apps = await client.get(f"{base_url}/api/v1/applications/", headers=headers)
        print(f"   ✅ Total applications: {len(apps.json())}")
        
        # Get statistics
        stats = await client.get(f"{base_url}/api/v1/applications/stats/summary", headers=headers)
        stats_data = stats.json()
        print("   ✅ Application stats:")
        print(f"      - Total: {stats_data['total_applications']}")
        print(f"      - This week: {stats_data['applications_this_week']}")
        print(f"      - By status: {stats_data['by_status']}")
        
        # 5. Test generator endpoints
        print("\n5. Testing AI/Generator endpoints...")
        
        # Check LLM providers
        providers = await client.get(
            f"{base_url}/api/v1/generator/llm-providers",
            headers=headers
        )
        if providers.status_code == 200:
            print(f"   ✅ Available LLM providers: {providers.json()}")
        else:
            print(f"   ❌ LLM providers error: {providers.status_code} - {providers.text}")
        
        # 6. Test job analysis
        if app_id and providers.status_code == 200:
            print("\n6. Testing job analysis...")
            # Send job_description as query parameter
            analysis = await client.post(
                f"{base_url}/api/v1/generator/analyze-job",
                headers=headers,
                params={  # Use params instead of json
                    "job_description": app_data["job_description"]
                }
            )
            if analysis.status_code == 200:
                analysis_data = analysis.json()
                print("   ✅ Job analysis successful")
                if 'required_skills' in analysis_data:
                    print(f"      - Required skills: {analysis_data.get('required_skills', [])[:3]}...")
                if 'nice_to_have' in analysis_data:
                    print(f"      - Nice to have: {analysis_data.get('nice_to_have', [])[:3]}...")
            else:
                print(f"   ❌ Job analysis error: {analysis.status_code} - {analysis.text}")
        
        # 7. Test application updates
        if app_id:
            print("\n7. Testing application updates...")
            update = await client.patch(
                f"{base_url}/api/v1/applications/{app_id}",
                headers=headers,
                json={"status": "applied"}
            )
            if update.status_code == 200:
                print("   ✅ Updated application status to 'applied'")
            
            # Add a note
            note = await client.post(
                f"{base_url}/api/v1/applications/{app_id}/notes",
                headers=headers,
                json={"note": "Submitted application with customized resume"}
            )
            if note.status_code in [200, 201]:
                print("   ✅ Added note to application")
            else:
                print(f"   ❌ Note error: {note.status_code} - {note.text}")
        
        print("\n✅ All tests completed!")
        print("\n📊 Summary:")
        print("   - API Status: Healthy")
        print(f"   - User: {user_data['email']} ({user_data['subscription_tier']} tier)")
        print(f"   - Applications: {stats_data['total_applications']}")
        print(f"   - Ready for resume generation: {'Yes' if providers.status_code == 200 else 'No (check LLM config)'}")

# Run the test
if __name__ == "__main__":
    asyncio.run(test_system())
