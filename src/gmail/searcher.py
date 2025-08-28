# -*- coding: utf-8 -*-
"""
Gmail email searching functionality
"""

import datetime
import logging
from typing import List

try:
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False

logger = logging.getLogger(__name__)

class GmailSearcher:
    def __init__(self, gmail_service):
        self.service = gmail_service
    
    def build_search_query(self, sender_email: str, start_date: str, end_date: str, has_attachment: bool = True) -> str:
        query_parts = []
        if sender_email:
            query_parts.append(f"from:{sender_email}")
        if start_date:
            query_parts.append(f"after:{start_date}")
            logger.info(f"Start date: Including from {start_date} using after:{start_date}")
        
        # Only add end date if it's different from start date
        if end_date and end_date != start_date:
            try:
                end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
                next_day = end_dt + datetime.timedelta(days=1)
                next_day_str = next_day.strftime("%Y-%m-%d")
                query_parts.append(f"before:{next_day_str}")
                logger.info(f"End date: Including {end_date} by using before:{next_day_str}")
            except ValueError:
                logger.error(f"Invalid end date format: {end_date}")
                raise ValueError(f"Invalid end date format: {end_date}")
        elif start_date and not end_date:
            try:
                start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
                next_day = start_dt + datetime.timedelta(days=1)
                next_day_str = next_day.strftime("%Y-%m-%d")
                query_parts.append(f"before:{next_day_str}")
                logger.info(f"Single day: Searching {start_date} using before:{next_day_str}")
            except ValueError:
                logger.error(f"Invalid date format: {start_date}")
                raise ValueError(f"Invalid date format: {start_date}")
        
        if has_attachment:
            query_parts.append("has:attachment")
        query = " ".join(query_parts)
        logger.info(f"🔍 Built search query: '{query}'")
        return query
    
    def search_emails(self, query: str, progress_callback=None, gui_update_callback=None, cancel_check=None) -> List[str]:
        try:
            if progress_callback:
                progress_callback("Söker efter emails...", 0)
            if gui_update_callback:
                gui_update_callback()
            logger.info(f"🔍 Starting email search with query: '{query}'")
            
            all_messages = []
            page_token = None
            page_count = 0
            
            while True:
                if cancel_check and cancel_check():
                    logger.info("Email search cancelled by user")
                    return []
                try:
                    search_params = {'userId': 'me', 'q': query}
                    if page_token:
                        search_params['pageToken'] = page_token
                    results = self.service.users().messages().list(**search_params).execute()
                except HttpError as e:
                    logger.error(f"Gmail API error during search: {e}")
                    raise Exception(f"Gmail API fel vid sökning: {e}")
                
                messages = results.get('messages', [])
                all_messages.extend(messages)
                page_count += 1
                logger.info(f"📄 Page {page_count}: Found {len(messages)} messages (Total: {len(all_messages)})")
                
                if progress_callback:
                    progress_callback(f"Hämtat {len(all_messages)} emails från {page_count} sidor...", 0)
                if gui_update_callback:
                    gui_update_callback()
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            
            logger.info(f"FINAL RESULT: Found {len(all_messages)} emails matching query '{query}'")
            return [msg['id'] for msg in all_messages]
            
        except HttpError as error:
            logger.error(f"HTTP error during email search: {error}")
            raise Exception(f"Ett fel uppstod vid sökning: {error}")
        except Exception as e:
            logger.error(f"Unexpected error during email search: {e}")
            raise