"""
Email service for sending verification emails and notifications.
"""
import smtplib
import ssl
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from src.core.config import settings


class EmailService:
    """Service for sending emails via SMTP"""
    
    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email
        self.from_name = settings.smtp_from_name
    
    def _is_configured(self) -> bool:
        """Check if SMTP settings are configured"""
        return all([
            self.smtp_host,
            self.smtp_username, 
            self.smtp_password,
            self.from_email
        ])
    
    def _send_email_sync(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """
        Send an email via SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML content of the email
            text_body: Plain text fallback (optional)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self._is_configured():
            print(f"📧 Email not configured. Would send to {to_email}: {subject}")
            return False
            
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            
            # Add text part if provided
            if text_body:
                text_part = MIMEText(text_body, "plain")
                message.attach(text_part)
            
            # Add HTML part
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)
            
            # Create secure connection and send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(
                    self.from_email,
                    to_email,
                    message.as_string()
                )
            
            print(f"✅ Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {str(e)}")
            return False
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """Async wrapper for sending email"""
        # Run sync email function in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._send_email_sync, 
            to_email, 
            subject, 
            html_body, 
            text_body
        )
    
    async def send_verification_email(self, to_email: str, verification_token: str) -> bool:
        """
        Send email verification email
        
        Args:
            to_email: User's email address
            verification_token: Verification token
            
        Returns:
            bool: True if email sent successfully
        """
        verification_url = f"http://localhost:3080/verify-email?token={verification_token}"
        
        subject = "Verify your ResumeAI account"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your Email</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background-color: #f8fafc; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
                .header {{ background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); padding: 40px 20px; text-align: center; }}
                .header h1 {{ color: white; margin: 0; font-size: 28px; font-weight: bold; }}
                .content {{ padding: 40px 20px; }}
                .button {{ display: inline-block; background-color: #3b82f6; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; }}
                .footer {{ background-color: #f1f5f9; padding: 20px; text-align: center; font-size: 14px; color: #64748b; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 ResumeAI</h1>
                </div>
                <div class="content">
                    <h2>Welcome to ResumeAI!</h2>
                    <p>Thanks for signing up! To get started with creating professional resumes and tracking your job applications, please verify your email address.</p>
                    
                    <p style="text-align: center;">
                        <a href="{verification_url}" class="button">Verify Email Address</a>
                    </p>
                    
                    <p>If the button doesn't work, you can also copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #3b82f6;">{verification_url}</p>
                    
                    <p><strong>This link will expire in 24 hours for security reasons.</strong></p>
                    
                    <p>If you didn't create an account with ResumeAI, you can safely ignore this email.</p>
                    
                    <p>Best regards,<br>The ResumeAI Team</p>
                </div>
                <div class="footer">
                    <p>© 2025 ResumeAI Platform. All rights reserved.</p>
                    <p>This email was sent to {to_email}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Welcome to ResumeAI!
        
        Thanks for signing up! To get started, please verify your email address by clicking the link below:
        
        {verification_url}
        
        If you didn't create an account with ResumeAI, you can safely ignore this email.
        
        Best regards,
        The ResumeAI Team
        """
        
        return await self.send_email(to_email, subject, html_body, text_body)


# Global email service instance
email_service = EmailService()