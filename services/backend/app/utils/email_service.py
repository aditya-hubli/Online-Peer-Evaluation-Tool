"""
OPETSE-11: Email Notification Service
Handles sending deadline reminder emails to students.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from datetime import datetime
import os


class EmailService:
    """Service for sending email notifications."""

    def __init__(self):
        """Initialize email service with SMTP configuration."""
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)
        self.enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False
    ) -> bool:
        """
        Send an email to a recipient.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            body: Email body content
            is_html: Whether body is HTML (True) or plain text (False)

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            print(f"[EMAIL DISABLED] Would send to {to_email}: {subject}")
            return True

        if not self.smtp_username or not self.smtp_password:
            print("[EMAIL ERROR] SMTP credentials not configured")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject

            # Attach body
            mime_type = 'html' if is_html else 'plain'
            msg.attach(MIMEText(body, mime_type))

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            print(f"[EMAIL SENT] To: {to_email}, Subject: {subject}")
            return True

        except Exception as e:
            print(f"[EMAIL ERROR] Failed to send to {to_email}: {str(e)}")
            return False

    def send_deadline_reminder(
        self,
        to_email: str,
        student_name: str,
        form_title: str,
        deadline: str,
        time_remaining: str,
        project_title: Optional[str] = None
    ) -> bool:
        """
        Send a deadline reminder email to a student.

        Args:
            to_email: Student email address
            student_name: Student's name
            form_title: Evaluation form title
            deadline: Formatted deadline string
            time_remaining: Human-readable time remaining
            project_title: Optional project title

        Returns:
            True if email sent successfully
        """
        subject = f"Reminder: Evaluation Deadline Approaching - {form_title}"

        # Create HTML email body
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4f46e5; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }}
                .deadline-box {{ background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; }}
                .button {{ display: inline-block; background-color: #4f46e5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📅 Evaluation Deadline Reminder</h1>
                </div>
                <div class="content">
                    <p>Hi {student_name},</p>

                    <p>This is a friendly reminder that you have an upcoming evaluation deadline:</p>

                    <div class="deadline-box">
                        <strong>📝 Form:</strong> {form_title}<br>
                        {f'<strong>📁 Project:</strong> {project_title}<br>' if project_title else ''}
                        <strong>⏰ Deadline:</strong> {deadline}<br>
                        <strong>⌛ Time Remaining:</strong> {time_remaining}
                    </div>

                    <p>Please complete your evaluation before the deadline to ensure your feedback is recorded.</p>

                    <a href="#" class="button">Complete Evaluation</a>

                    <p style="margin-top: 30px; color: #6b7280; font-size: 14px;">
                        This is an automated reminder. If you have already submitted your evaluation, please disregard this message.
                    </p>
                </div>
                <div class="footer">
                    <p>© 2025 Peer Evaluation System | OPETSE-11</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(to_email, subject, html_body, is_html=True)

    def send_bulk_reminders(
        self,
        recipients: List[dict]
    ) -> dict:
        """
        Send deadline reminders to multiple recipients.

        Args:
            recipients: List of dicts with keys: to_email, student_name, form_title,
                       deadline, time_remaining, project_title (optional)

        Returns:
            Dict with success count, failure count, and failed emails
        """
        results = {
            "success_count": 0,
            "failure_count": 0,
            "failed_emails": []
        }

        for recipient in recipients:
            success = self.send_deadline_reminder(
                to_email=recipient.get("to_email"),
                student_name=recipient.get("student_name"),
                form_title=recipient.get("form_title"),
                deadline=recipient.get("deadline"),
                time_remaining=recipient.get("time_remaining"),
                project_title=recipient.get("project_title")
            )

            if success:
                results["success_count"] += 1
            else:
                results["failure_count"] += 1
                results["failed_emails"].append(recipient.get("to_email"))

        return results


# Singleton instance
email_service = EmailService()
