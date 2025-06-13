#!/usr/bin/env python3
import asyncio
from src.generator.resume_generator import ResumeGenerator, EXAMPLE_RESUME_DATA

async def test_generation():
    generator = ResumeGenerator()
    
    # Generate LaTeX
    latex_content = generator.generate_latex("modern_professional", EXAMPLE_RESUME_DATA)
    print("LaTeX generated successfully!")
    
    # Compile to PDF
    pdf_path = generator.compile_latex_to_pdf(latex_content, "test_resume.pdf")
    print(f"PDF generated at: {pdf_path}")

if __name__ == "__main__":
    asyncio.run(test_generation())
