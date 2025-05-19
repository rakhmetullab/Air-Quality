# email_service.py - Service for sending email alerts

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

def send_email_alert(recipient: str, subject: str, message: str) -> bool:
    """
    Sends an email alert using SMTP.
    
    Args:
        recipient: Email address to send the alert to
        subject: Subject line of the email
        message: Content of the email message
        
    Returns:
        Boolean indicating if the email was sent successfully
    """
    # Get email credentials from Streamlit secrets
    sender_email = st.secrets.get("EMAIL_ADDRESS", "")
    sender_password = st.secrets.get("EMAIL_PASSWORD", "")
    smtp_server = st.secrets.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = st.secrets.get("SMTP_PORT", 587)
    
    # Return early if credentials are missing
    if not sender_email or not sender_password:
        st.error("Email credentials are missing. Please add EMAIL_ADDRESS and EMAIL_PASSWORD to .streamlit/secrets.toml")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(message, 'plain'))
        
        # Connect to SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Secure the connection
        
        # Login to email account
        server.login(sender_email, sender_password)
        
        # Send email
        server.send_message(msg)
        
        # Close connection
        server.quit()
        
        return True
    
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False