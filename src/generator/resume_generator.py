import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape
import hashlib
from datetime import datetime

from src.api.models.schema import ResumeVersion, JobApplication
from src.api.models.auth import User
from sqlalchemy.ext.asyncio import AsyncSession


class ResumeGenerator:
    def __init__(self):
        # Set up Jinja2 environment
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add LaTeX escaping filter
        self.env.filters['latex_escape'] = self._latex_escape
        
        # Create output directory
        self.output_dir = Path("resume_outputs")
        self.output_dir.mkdir(exist_ok=True)
    
    def _latex_escape(self, text):
        """Escape special LaTeX characters"""
        if not isinstance(text, str):
            return text
        
        # LaTeX special characters that need escaping
        # Order matters: backslash must be first to avoid double-escaping
        replacements = [
            ('\\', r'\textbackslash '),  # Must be first, use space instead of {}
            ('&', r'\&'),
            ('%', r'\%'),
            ('$', r'\$'),
            ('#', r'\#'),
            ('^', r'\textasciicircum '),
            ('_', r'\_'),
            ('~', r'\textasciitilde '),
            ('{', r'\{'),
            ('}', r'\}'),
            ('<', r'\textless '),
            ('>', r'\textgreater '),
            ('|', r'\textbar '),
            ('"', r"''"),  # Convert quotes to LaTeX style
            ('[', r'{[}'),  # Protect square brackets
            (']', r'{]}'),
        ]
        
        for char, escaped in replacements:
            text = text.replace(char, escaped)
        
        return text
    
    def generate_latex(self, template_name: str, data: Dict[str, Any]) -> str:
        """Generate LaTeX content from template and data"""
        template = self.env.get_template(f"{template_name}.tex")
        return template.render(**data)
    
    def compile_latex_to_pdf(self, latex_content: str, output_filename: str) -> str:
        """Compile LaTeX content to PDF"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Write LaTeX content to file
            tex_file = temp_path / "resume.tex"
            tex_file.write_text(latex_content, encoding='utf-8')
            
            # Compile LaTeX to PDF (run twice for proper rendering)
            for i in range(2):
                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-output-directory", temp_dir, str(tex_file)],
                    capture_output=True,
                    text=True
                )
                
                # Check if PDF was created successfully (more important than return code)
                pdf_path = temp_path / "resume.pdf"
                if not pdf_path.exists():
                    error_msg = f"LaTeX compilation failed - no PDF generated (run {i+1}/2):\n"
                    error_msg += f"Return code: {result.returncode}\n"
                    error_msg += f"STDOUT: {result.stdout}\n"
                    error_msg += f"STDERR: {result.stderr}\n"
                    error_msg += f"Command: pdflatex -interaction=nonstopmode -output-directory {temp_dir} {tex_file}"
                    raise Exception(error_msg)
            
            # Move PDF to output directory
            pdf_path = temp_path / "resume.pdf"
            output_path = self.output_dir / output_filename
            
            # Use shutil.move() to handle cross-device moves
            shutil.move(str(pdf_path), str(output_path))
            
            return str(output_path)
    
    def generate_content_hash(self, content: str) -> str:
        """Generate hash of resume content for deduplication"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def generate_resume(
        self,
        user: User,
        job_application: JobApplication,
        resume_data: Dict[str, Any],
        template_name: str = "modern_professional",
        db: AsyncSession = None
    ) -> ResumeVersion:
        """Generate a resume and save it to database"""
        
        # Generate LaTeX content
        latex_content = self.generate_latex(template_name, resume_data)
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"resume_{user.id}_{job_application.id}_{timestamp}.pdf"
        
        # Compile to PDF
        pdf_path = self.compile_latex_to_pdf(latex_content, filename)
        
        # Create database record
        resume_version = ResumeVersion(
            user_id=user.id,
            version_name=f"Resume for {job_application.company} - {job_application.position}",
            template_name=template_name,
            file_url=pdf_path,
            content_hash=self.generate_content_hash(latex_content),
            job_type=job_application.job_type,
            extra_data={
                "job_application_id": job_application.id,
                "company": job_application.company,
                "position": job_application.position,
                "generated_at": datetime.utcnow().isoformat()
            }
        )
        
        if db:
            db.add(resume_version)
            await db.commit()
            await db.refresh(resume_version)
            
            # Update job application with resume
            job_application.resume_version = resume_version.version_name
            job_application.resume_url = pdf_path
            await db.commit()
        
        return resume_version
