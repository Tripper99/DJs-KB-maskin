# -*- coding: utf-8 -*-
"""
Gmail attachment processing functionality
"""

import base64
import logging
from typing import Dict, List, Optional

try:
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False

logger = logging.getLogger(__name__)

class AttachmentProcessor:
    def __init__(self, gmail_service):
        self.service = gmail_service
    
    def get_email_details(self, message_id: str, cancel_check=None) -> Optional[Dict]:
        try:
            # Check cancellation before API call
            if cancel_check and cancel_check():
                logger.info("Email details retrieval cancelled")
                return None
                
            message = self.service.users().messages().get(userId='me', id=message_id).execute()
            
            # Check cancellation after API call
            if cancel_check and cancel_check():
                logger.info("Email details processing cancelled")
                return None
                
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Inget ämne')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Okänd avsändare')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Okänt datum')
            return {
                'id': message_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'payload': message['payload']
            }
        except HttpError as error:
            logger.warning(f"Failed to get email details for {message_id}: {error}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error getting email details: {e}")
            return None
    
    def _process_email_part(self, part: Dict, attachments: List[Dict]) -> None:
        if part.get('filename'):
            filename = part['filename']
            if filename.lower().endswith(('.jpg', '.jpeg')):
                attachment_id = part['body'].get('attachmentId')
                if attachment_id:
                    attachments.append({
                        'filename': filename,
                        'attachment_id': attachment_id,
                        'size': part['body'].get('size', 0)
                    })
        if 'parts' in part:
            for subpart in part['parts']:
                self._process_email_part(subpart, attachments)
    
    def extract_attachments(self, payload: Dict) -> List[Dict]:
        attachments = []
        self._process_email_part(payload, attachments)
        return attachments
    
    def download_attachment(self, message_id: str, attachment_id: str, cancel_check=None) -> Optional[bytes]:
        try:
            # Check cancellation before API call
            if cancel_check and cancel_check():
                logger.info("Attachment download cancelled")
                return None
                
            attachment = self.service.users().messages().attachments().get(userId='me', messageId=message_id, id=attachment_id).execute()
            
            # Check cancellation after API call but before data processing
            if cancel_check and cancel_check():
                logger.info("Attachment download cancelled after API call")
                return None
                
            data = attachment['data']
            file_data = base64.urlsafe_b64decode(data)
            return file_data
        except HttpError as error:
            logger.warning(f"Failed to download attachment {attachment_id}: {error}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error downloading attachment: {e}")
            return None