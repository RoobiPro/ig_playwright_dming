import os
import json
import datetime
import time
import traceback

import re
from datetime import timedelta

import pytz  # Import pytz for timezone handling

def filter_recent_messages(messages):
    # Handle empty input immediately
    if not messages:
        return []

    # Setup Bali timezone
    bali_tz = pytz.timezone('Asia/Makassar')
    
    # Get current time in Bali
    now_aware = datetime.datetime.now(bali_tz)
    
    # Calculate cutoff (3 days ago in Bali time)
    cutoff_aware = now_aware - datetime.timedelta(days=2)
    
    result = []
    
    # Process messages to find recent ones
    for msg in messages:
        date_str = msg['date']
        try:
            # Parse string into naive datetime
            naive_dt = datetime.datetime.strptime(date_str, "%d.%m.%Y %H:%M")
            # Convert to Bali timezone
            dt = bali_tz.localize(naive_dt)
            
            # Check if within time window
            if cutoff_aware <= dt <= now_aware:
                result.append(msg)
        except ValueError:
            # Skip messages with invalid date formats
            continue
    
    # Fallback to last 5 messages if no recent messages found
    if not result:
        return messages[-5:]
    
    return result

def convert_date(date_str):
    """Convert date strings to dd.mm.yyyy hh:mm format"""
    base_date = datetime.datetime.now()
    date_str = date_str.replace('[DATE] ', '').strip()
    
    # Handle "Today" and "Yesterday"
    if date_str.startswith('Today at '):
        date_part = base_date.date()
        time_str = date_str.replace('Today at ', '')
    elif date_str.startswith('Yesterday at '):
        date_part = (base_date - timedelta(days=1)).date()
        time_str = date_str.replace('Yesterday at ', '')
    else:
        # Handle new format: "Jul 2, 2025, 3:26 PM"
        new_format_match = re.match(r'(\w{3})\s+(\d{1,2}),\s+(\d{4}),\s+(\d{1,2}:\d{2}\s*[AP]M)', date_str, re.IGNORECASE)
        if new_format_match:
            month_abbr, day, year, time_str = new_format_match.groups()
            try:
                # Convert abbreviated month to number
                month_num = datetime.datetime.strptime(month_abbr, '%b').month
                # Create date object directly
                date_part = datetime.datetime(int(year), month_num, int(day)).date()
            except Exception as e:
                print(f"⚠️ Error parsing new format: {date_str} - {e}")
                return date_str
        else:
            # Handle standalone time format
            cleaned_time_str = date_str.replace(u'\u202f', ' ').replace(' ', '')
            if re.match(r'^\d{1,2}:\d{2}[AP]M$', cleaned_time_str, re.IGNORECASE):
                try:
                    time_obj = datetime.datetime.strptime(cleaned_time_str, '%I:%M%p').time()
                except ValueError:
                    cleaned_time_str = re.sub(r'^(\d):', r'0\1:', cleaned_time_str)
                    time_obj = datetime.datetime.strptime(cleaned_time_str, '%I:%M%p').time()
                full_datetime = datetime.datetime.combine(base_date.date(), time_obj)
                return full_datetime.strftime('%d.%m.%Y %H:%M')
            
            # Handle day-of-week format
            match_dow = re.match(r'^(\w{3})\s+(\d{1,2}:\d{2}\s*[AP]M)$', date_str, re.IGNORECASE)
            if match_dow:
                dow_abbrev, time_str = match_dow.groups()
                dow_map = {
                    'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3,
                    'Fri': 4, 'Sat': 5, 'Sun': 6
                }
                dow_abbrev = dow_abbrev.capitalize()
                if dow_abbrev not in dow_map:
                    return date_str
                
                target_weekday = dow_map[dow_abbrev]
                current_weekday = base_date.weekday()
                days_diff = (current_weekday - target_weekday + 7) % 7
                candidate_date = base_date.date() - timedelta(days=days_diff)
                
                time_str = time_str.replace(u'\u202f', ' ').replace(' ', '')
                try:
                    time_obj = datetime.datetime.strptime(time_str, '%I:%M%p').time()
                except ValueError:
                    time_str = re.sub(r'^(\d):', r'0\1:', time_str)
                    time_obj = datetime.datetime.strptime(time_str, '%I:%M%p').time()
                
                candidate_datetime = datetime.datetime.combine(candidate_date, time_obj)
                if candidate_datetime > base_date:
                    candidate_datetime -= timedelta(days=7)
                return candidate_datetime.strftime('%d.%m.%Y %H:%M')
            
            # Handle month-day format (with or without time)
            match_with_time = re.match(r'(\w+)\s+(\d+)\s+at\s+(.+)', date_str)
            match_without_time = re.match(r'^(\w+)\s+(\d+)$', date_str)
            if match_with_time or match_without_time:
                if match_with_time:
                    month_name, day, time_str_part = match_with_time.groups()
                else:  # match_without_time
                    month_name, day = match_without_time.groups()
                    time_str_part = None  # Mark no time part
                
                try:
                    month_num = datetime.datetime.strptime(month_name, '%B').month
                except ValueError:
                    return date_str
                
                current_year = base_date.year
                candidate = datetime.datetime(current_year, month_num, int(day))
                if candidate > base_date:
                    candidate = candidate.replace(year=current_year - 1)
                
                if time_str_part is None:
                    # Without time: set to midnight
                    full_datetime = candidate
                else:
                    # Process the time string
                    time_str_clean = time_str_part.replace(u'\u202f', ' ').replace(' ', '')
                    try:
                        time_obj = datetime.datetime.strptime(time_str_clean, '%I:%M%p').time()
                    except ValueError:
                        time_str_clean = re.sub(r'^(\d):', r'0\1:', time_str_clean)
                        time_obj = datetime.datetime.strptime(time_str_clean, '%I:%M%p').time()
                    full_datetime = datetime.datetime.combine(candidate.date(), time_obj)
                
                return full_datetime.strftime('%d.%m.%Y %H:%M')
            else:
                return date_str  # Unrecognized format
    
    # Common time processing for "Today" and "Yesterday"
    time_str = time_str.replace(u'\u202f', ' ').replace(' ', '')
    try:
        time_obj = datetime.datetime.strptime(time_str, '%I:%M%p').time()
    except ValueError:
        time_str = re.sub(r'^(\d):', r'0\1:', time_str)
        time_obj = datetime.datetime.strptime(time_str, '%I:%M%p').time()
    
    full_datetime = datetime.datetime.combine(date_part, time_obj)
    return full_datetime.strftime('%d.%m.%Y %H:%M')

def get_conversations_dir():
    """Get the correct path to conversations directory (one level up from scripts)"""
    # Get directory of current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go one directory back (parent of scripts directory)
    parent_dir = os.path.dirname(script_dir)
    # Create and return the conversations directory path
    conversations_dir = os.path.join(parent_dir, "data", "conversations")
    os.makedirs(conversations_dir, exist_ok=True)
    return conversations_dir

def save_merged_messages(partner_user_id, new_messages):
    """Load existing messages, merge with new ones (removing duplicates), and save back to file"""
    import os
    import json
    from urllib.parse import urlparse
    from datetime import datetime

    print(f"\n[DEBUG] save_merged_messages called for partner: {partner_user_id}")
    print(f"[DEBUG] Number of new messages to process: {len(new_messages)}")
    
    conversations_dir = get_conversations_dir()
    
    # Ensure conversations directory exists
    if not os.path.exists(conversations_dir):
        os.makedirs(conversations_dir)
    
    file_path = os.path.join(conversations_dir, f"{partner_user_id}.json")
    print(f"[DEBUG] File path: {file_path}")
    
    # Load existing messages if available
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_messages = json.load(f)
            # print(f"[DEBUG] Loaded {len(existing_messages)} existing messages")
        except Exception as e:
            # print(f"[DEBUG] Error loading existing messages: {e}")
            existing_messages = []
    else:
        print(f"[DEBUG] No existing file found, starting fresh")
        existing_messages = []
    
    # Helper function to normalize a message for comparison
    def normalize_message(msg):
        if not isinstance(msg, dict):
            return msg
        normalized = msg.copy()
        
        # Normalize date to YYYY-MM-DD format if possible
        if 'date' in normalized:
            original_date = normalized['date']
            try:
                # Parse and reformat to date-only string
                dt = datetime.fromisoformat(normalized['date'])
                normalized['date'] = dt.date().isoformat()
                print(f"[DEBUG] Date normalized: '{original_date}' -> '{normalized['date']}'")
            except (TypeError, ValueError) as e:
                # Fallback to original value if parsing fails
                print(f"[DEBUG] Date normalization failed for '{original_date}': {e}")
                pass
        
        # Normalize media URL to path only
        if 'media_attached_img' in normalized:
            img_url = normalized['media_attached_img']
            if isinstance(img_url, str) and img_url.strip() != '':
                try:
                    parsed = urlparse(img_url)
                    normalized['media_attached_img'] = parsed.path
                    print(f"[DEBUG] Media URL normalized: '{img_url}' -> '{normalized['media_attached_img']}'")
                except Exception as e:
                    # Keep original URL if parsing fails
                    print(f"[DEBUG] Media URL normalization failed: {e}")
                    pass
        return normalized
    
    # Create a set of canonical JSON strings for normalized existing messages
    print(f"[DEBUG] Creating normalized set for {len(existing_messages)} existing messages")
    existing_set = set()
    for i, msg in enumerate(existing_messages):
        norm_msg = normalize_message(msg)
        canonical = json.dumps(norm_msg, sort_keys=True, ensure_ascii=False)
        existing_set.add(canonical)
        print(f"[DEBUG] Existing message {i}: {json.dumps(msg, ensure_ascii=False)}")
        print(f"[DEBUG] Normalized: {canonical}")
    
    # Filter new_messages to exclude duplicates
    print(f"[DEBUG] Processing {len(new_messages)} new messages for duplicates")
    unique_new_messages = []
    for i, msg in enumerate(new_messages):
        print(f"[DEBUG] Processing new message {i}: {json.dumps(msg, ensure_ascii=False)}")
        norm_msg = normalize_message(msg)
        canonical = json.dumps(norm_msg, sort_keys=True, ensure_ascii=False)
        print(f"[DEBUG] New message {i} normalized: {canonical}")
        
        if canonical not in existing_set:
            print(f"[DEBUG] New message {i} is UNIQUE - adding to unique_new_messages")
            unique_new_messages.append(msg)
            existing_set.add(canonical)  # Prevent duplicates within new_messages
        else:
            print(f"[DEBUG] New message {i} is DUPLICATE - skipping")
    
    print(f"[DEBUG] Found {len(unique_new_messages)} unique new messages out of {len(new_messages)} total")
    
    # Merge messages
    merged_messages = existing_messages + unique_new_messages
    print(f"[DEBUG] Final merged messages count: {len(merged_messages)}")
    
    # Save merged messages back to file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(merged_messages, f, ensure_ascii=False, indent=2)
        print(f"[DEBUG] Successfully saved {len(merged_messages)} messages to file")
        return merged_messages        
    except Exception as e:
        print(f"[DEBUG] Error saving merged messages: {e}")
        return None