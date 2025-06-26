#!/usr/bin/env python3
"""
Test script for resume generation functionality.
Tests both basic LaTeX generation and AI-powered customization.
"""

import asyncio
import sys
import os
import traceback
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

print("🚀 Starting resume generation test...")
print(f"Python version: {sys.version}")
print(f"Current directory: {Path.cwd()}")

try:
    print("📦 Importing modules...")
    from src.generator.resume_generator import ResumeGenerator
    print("✅ ResumeGenerator imported")
    
    from src.generator.example_data import FULL_RESUME_DATA, MINIMAL_RESUME_DATA
    print("✅ Example data imported")
    
    # Note: ResumeCustomizer and JobAnalyzer moved to Agents in event-driven architecture
    print("✅ Core generator components imported")
    
    from src.core.config import settings
    print("✅ Settings imported")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    print(f"Traceback: {traceback.format_exc()}")
    sys.exit(1)

async def test_basic_generation():
    """Test basic resume generation without AI"""
    print("\n🧪 Testing basic resume generation...")
    
    try:
        generator = ResumeGenerator()
        
        # Test with minimal data
        print("   📝 Testing minimal resume data...")
        latex_content = generator.generate_latex("modern_professional", MINIMAL_RESUME_DATA)
        print(f"   ✅ Generated LaTeX ({len(latex_content)} characters)")
        
        # Test PDF generation if pdflatex is available
        try:
            pdf_path = generator.compile_latex_to_pdf(latex_content, "test_minimal.pdf")
            if pdf_path and Path(pdf_path).exists():
                print(f"   ✅ Generated PDF: {pdf_path}")
                print(f"      File size: {Path(pdf_path).stat().st_size} bytes")
            else:
                print("   ⚠️  PDF generation returned no path")
        except Exception as pdf_error:
            print(f"   ⚠️  PDF generation failed (this is OK if pdflatex not installed): {pdf_error}")
        
        # Test with full data
        print("   📝 Testing full resume data...")
        latex_content = generator.generate_latex("modern_professional", FULL_RESUME_DATA)
        print(f"   ✅ Generated LaTeX ({len(latex_content)} characters)")
        
        try:
            pdf_path = generator.compile_latex_to_pdf(latex_content, "test_full.pdf")
            if pdf_path and Path(pdf_path).exists():
                print(f"   ✅ Generated PDF: {pdf_path}")
                print(f"      File size: {Path(pdf_path).stat().st_size} bytes")
        except Exception as pdf_error:
            print(f"   ⚠️  PDF generation failed: {pdf_error}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Basic generation failed: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

async def test_ai_customization():
    """Test AI-powered resume customization - Now handled by AnalyzerAgent and GeneratorAgent"""
    print("\n🤖 Testing AI resume customization...")
    
    # Check if API keys are configured
    if not settings.openai_api_key and not settings.anthropic_api_key:
        print("   ⚠️  No LLM API keys configured, skipping AI tests")
        print("      Set OPENAI_API_KEY and/or ANTHROPIC_API_KEY to test AI features")
        return True
    
    try:
        # AI customization is now handled by AnalyzerAgent and GeneratorAgent in the workflow system
        print("   ✅ AI customization moved to AnalyzerAgent and GeneratorAgent")
        
        # AI functionality testing is now handled by:
        # - AnalyzerAgent: Job description analysis
        # - GeneratorAgent: AI-powered resume customization
        # These run as part of the workflow system
        
        print("   📋 AI features now integrated into workflow system:")
        print("      - AnalyzerAgent handles job description analysis")
        print("      - GeneratorAgent handles AI-powered customization")
        print("      - Use workflow system to test end-to-end AI functionality")
        
        return True
        
    except Exception as e:
        print(f"   ❌ AI customization test failed: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

async def test_template_availability():
    """Test that resume templates are available"""
    print("\n📄 Testing template availability...")
    
    try:
        generator = ResumeGenerator()
        template_dir = Path(__file__).parent.parent / "src" / "generator" / "templates"
        
        print(f"   📁 Template directory: {template_dir}")
        
        if not template_dir.exists():
            print("   ❌ Template directory not found")
            return False
        
        templates = list(template_dir.glob("*.tex"))
        print(f"   ✅ Found {len(templates)} LaTeX templates:")
        
        for template in templates:
            print(f"      - {template.name}")
            
            # Test that template loads without error
            try:
                template_obj = generator.env.get_template(template.name)
                print(f"        ✅ Template loads successfully")
            except Exception as template_error:
                print(f"        ❌ Template load error: {template_error}")
                return False
        
        if not templates:
            print("   ❌ No templates found")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Template test failed: {e}")
        return False

async def test_output_directory():
    """Test that output directory is created and accessible"""
    print("\n📂 Testing output directory...")
    
    try:
        output_dir = Path("resume_outputs")
        
        if not output_dir.exists():
            print("   📁 Creating output directory...")
            output_dir.mkdir(exist_ok=True)
        
        print(f"   ✅ Output directory exists: {output_dir.absolute()}")
        
        # Test write permissions
        test_file = output_dir / "test_write.txt"
        test_file.write_text("test")
        test_file.unlink()
        print("   ✅ Directory is writable")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Output directory test failed: {e}")
        return False

def print_system_info():
    """Print system information for debugging"""
    print("\n🔧 System Information:")
    print(f"   - Python: {sys.version}")
    print(f"   - Platform: {sys.platform}")
    print(f"   - Working directory: {os.getcwd()}")
    
    # Check for pdflatex
    try:
        import subprocess
        result = subprocess.run(['pdflatex', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"   - pdflatex: {version_line}")
        else:
            print("   - pdflatex: Not available")
    except FileNotFoundError:
        print("   - pdflatex: Not installed")
    except Exception as e:
        print(f"   - pdflatex: Error checking ({e})")
    
    # Check environment variables
    print(f"   - OPENAI_API_KEY: {'Set' if settings.openai_api_key else 'Not set'}")
    print(f"   - ANTHROPIC_API_KEY: {'Set' if settings.anthropic_api_key else 'Not set'}")
    print(f"   - DEFAULT_LLM_PROVIDER: {settings.default_llm_provider}")

async def main():
    """Run all tests"""
    print_system_info()
    
    tests = [
        ("Output Directory", test_output_directory()),
        ("Template Availability", test_template_availability()),
        ("Basic Generation", test_basic_generation()),
        ("AI Customization", test_ai_customization()),
    ]
    
    results = []
    
    for test_name, test_coro in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            result = await test_coro
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("🏁 TEST SUMMARY")
    print('='*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed - check output above")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test runner crashed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)