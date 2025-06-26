#!/usr/bin/env python3
"""
Test LaTeX escaping functionality with various special characters.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.generator.resume_generator import ResumeGenerator

def test_latex_escaping():
    """Test LaTeX escaping with various special characters"""
    print("🧪 Testing LaTeX character escaping...")
    
    generator = ResumeGenerator()
    
    # Test cases with special characters
    test_cases = [
        ("Simple text", "Simple text"),
        ("Tools & Technologies", r"Tools \& Technologies"),
        ("50% improvement", r"50\% improvement"),
        ("Cost: $100,000", r"Cost: \$100,000"),
        ("Issue #123", r"Issue \#123"),
        ("Temperature: 20°C", r"Temperature: 20°C"),  # Degree symbol should pass through
        ("File path: C:\\Users\\Name", r"File path: C:\textbackslash Users\textbackslash Name"),
        ("Underscore_variable", r"Underscore\_variable"),
        ("Math: x^2 + y^2", r"Math: x\textasciicircum 2 + y\textasciicircum 2"),
        ("Tilde: ~user", r"Tilde: \textasciitilde user"),
        ("Braces: {important}", r"Braces: \{important\}"),
        ("Comparison: x < y > z", r"Comparison: x \textless  y \textgreater  z"),
        ("Pipe: command | grep", r"Pipe: command \textbar  grep"),
        ('Quote: "Hello World"', r"Quote: ''Hello World''"),
        ("Arrays: data[0] and data[1]", r"Arrays: data{[}0{]} and data{[}1{]}"),
        ("Complex: R&D at 50% cost with {data[x]} & ~temp", 
         r"Complex: R\&D at 50\% cost with \{data{[}x{]}\} \& \textasciitilde temp"),
    ]
    
    passed = 0
    failed = 0
    
    for i, (input_text, expected) in enumerate(test_cases, 1):
        result = generator._latex_escape(input_text)
        
        if result == expected:
            print(f"   ✅ Test {i:2d}: '{input_text}' → '{result}'")
            passed += 1
        else:
            print(f"   ❌ Test {i:2d}: '{input_text}'")
            print(f"        Expected: '{expected}'")
            print(f"        Got:      '{result}'")
            failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All LaTeX escaping tests passed!")
        return True
    else:
        print("⚠️  Some escaping tests failed")
        return False

def test_resume_with_special_chars():
    """Test full resume generation with special characters"""
    print("\n🧪 Testing resume generation with special characters...")
    
    generator = ResumeGenerator()
    
    # Create test data with lots of special characters
    test_data = {
        "name": "John O'Reilly & Associates",
        "email": "john@company.com",
        "phone": "(555) 123-4567",
        "location": "Austin, TX",
        "summary": "Senior Developer with 90% success rate in C++ & Python projects. Experienced with $1M+ budgets and ~50 team members.",
        "skills": {
            "Languages & Frameworks": ["C++", "Python", "C#/.NET", "Node.js"],
            "Databases & Storage": ["PostgreSQL", "MongoDB", "Redis"],
            "Tools & Technologies": ["Docker", "AWS/GCP", "Git/SVN", "Jenkins/CI"]
        },
        "experience": [
            {
                "title": "Senior Software Engineer (Team Lead)",
                "company": "Tech Corp & Partners LLC",
                "location": "Remote/Austin, TX",
                "start_date": "Jan 2020",
                "end_date": "Present",
                "bullets": [
                    "Led team of 8+ engineers on $2M project with <24hr response time",
                    "Improved performance by 75% using advanced algorithms & caching",
                    "Managed databases with ~1TB data using PostgreSQL & Redis",
                    "Built CI/CD pipeline reducing deployment time from 2hrs to <15min"
                ]
            }
        ],
        "education": [
            {
                "school": "University of Texas @ Austin",
                "degree": "BS in Computer Science & Mathematics",
                "date": "May 2019"
            }
        ]
    }
    
    try:
        # Generate LaTeX
        latex_content = generator.generate_latex("modern_professional", test_data)
        print("   ✅ LaTeX generation successful")
        
        # Check for unescaped characters (these should NOT appear in output)
        dangerous_chars = ['&', '%', '$', '#', '^', '_', '{', '}', '~', '<', '>', '|']
        unescaped_found = []
        
        for char in dangerous_chars:
            # Look for unescaped characters (not preceded by backslash)
            import re
            if char in ['\\', '^', '$', '|', '{', '}']:
                # These need special regex escaping
                pattern = f'(?<!\\\\)\\{char}'
            else:
                pattern = f'(?<!\\\\){re.escape(char)}'
            
            matches = re.findall(pattern, latex_content)
            if matches:
                unescaped_found.append((char, len(matches)))
        
        if unescaped_found:
            print(f"   ⚠️  Found unescaped characters: {unescaped_found}")
        else:
            print("   ✅ All special characters properly escaped")
        
        # Try to compile PDF
        try:
            pdf_path = generator.compile_latex_to_pdf(latex_content, "test_special_chars.pdf")
            print(f"   ✅ PDF compilation successful: {pdf_path}")
            return True
        except Exception as pdf_error:
            print(f"   ❌ PDF compilation failed: {pdf_error}")
            return False
            
    except Exception as e:
        print(f"   ❌ LaTeX generation failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing LaTeX Escaping System\n")
    
    test1_passed = test_latex_escaping()
    test2_passed = test_resume_with_special_chars()
    
    print(f"\n{'='*50}")
    print("🏁 FINAL RESULTS")
    print('='*50)
    
    if test1_passed and test2_passed:
        print("🎉 All tests passed! LaTeX escaping is comprehensive.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Check output above.")
        sys.exit(1)