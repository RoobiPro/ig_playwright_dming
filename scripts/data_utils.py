"""
Data utilities for Instagram automation
"""
import json
import os
from typing import Dict, Any, List, Optional
from . import config


def get_our_information() -> Optional[Dict[str, Any]]:
    """Load our data from JSON file"""
    filepath = config.OUR_DATA_FILE

    if os.path.isfile(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error: File exists but contains invalid JSON: {filepath}")
            return None
        except UnicodeDecodeError:
            print(f"Encoding error in file: {filepath}")
            return None
    
    return None


def get_user_information(userid: str) -> Optional[Dict[str, Any]]:
    """
    Load user information from JSON file
    
    Args:
        userid: The base userid or partial filename
        
    Returns:
        If exists: returns the loaded JSON content
        If not exists: returns None
    """
    directory = config.FACTS_DIR
    
    try:
        filenames = []
        if userid.endswith(".json"):
            filenames.append(userid)
        else:
            filenames.append(f"{userid}.json")
            filenames.append(userid)
        
        for filename in filenames:
            filepath = os.path.join(directory, filename)
            
            if os.path.isfile(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except json.JSONDecodeError:
                    print(f"Error: File exists but contains invalid JSON: {filepath}")
                    return None
                except UnicodeDecodeError:
                    print(f"Encoding error in file: {filepath}")
                    return None
        
        return None
    except Exception:
        return None


def check_userid_json(userid: str) -> Optional[Dict[str, Any]]:
    """
    Check if user conversation data exists and load it
    
    Args:
        userid: The base userid or partial filename
        
    Returns:
        If exists: returns the loaded JSON content
        If not exists: returns None
    """
    directory = config.CONVERSATIONS_DIR
    
    filenames = []
    if userid.endswith(".json"):
        filenames.append(userid)
    else:
        filenames.append(f"{userid}.json")
        filenames.append(userid)
    
    for filename in filenames:
        filepath = os.path.join(directory, filename)
        
        if os.path.isfile(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Error: File exists but contains invalid JSON: {filepath}")
                return None
            except UnicodeDecodeError:
                print(f"Encoding error in file: {filepath}")
                return None
    
    return None


def save_initial_messages(partner_username: str, messages: List[Dict[str, Any]]) -> None:
    """Save initial messages to conversation file"""
    save_dir = config.CONVERSATIONS_DIR
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, f"{partner_username}.json")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved initial messages to {file_path}")


def message_equals(msg_a: Dict[str, Any], msg_b: Dict[str, Any]) -> bool:
    """Compare two message objects for equality"""
    if set(msg_a.keys()) != set(msg_b.keys()):
        return False
    
    for key in msg_a:
        val_a = msg_a[key]
        val_b = msg_b[key]
        if isinstance(val_a, list):
            if not isinstance(val_b, list) or len(val_a) != len(val_b):
                return False
            for i in range(len(val_a)):
                if val_a[i] != val_b[i]:
                    return False
        else:
            if val_a != val_b:
                return False
    
    return True


def convert_segments_to_messages(valid_texts: List[List[str]]) -> List[Dict[str, Any]]:
    """Convert text segments to message objects"""
    tag_mapping = config.MESSAGE_TAG_MAPPING
    tags_sorted = sorted(tag_mapping.keys(), key=len, reverse=True)
    messages = []

    for segments in valid_texts:
        if not segments:
            continue
        
        # Reorder segments to ensure date and sent_by come first
        reordered_segments = []
        other_segments = []
        
        # First pass: find date and sent_by segments
        for segment in segments:
            if segment.startswith('[DATE]'):
                reordered_segments.append(segment)
            elif segment.startswith('[SENT BY]') or segment.startswith('[REPLY SENT BY]'):
                reordered_segments.append(segment)
            else:
                other_segments.append(segment)
        
        # Combine: date and sent_by first, then everything else
        reordered_segments.extend(other_segments)
            
        msg_obj = {}
        valid_message = True
        
        for segment in reordered_segments:
            found_tag = False
            for tag in tags_sorted:
                if segment.startswith(tag):
                    key = tag_mapping[tag]
                    value = segment[len(tag):].strip()
                    
                    if key == 'one_time_view_media':
                        value = "Media content (viewed once)"
                    elif key == 'story_shared':
                        # For story shares, the value contains the username
                        value = "Shared your story"
                    
                    if key in msg_obj:
                        if not isinstance(msg_obj[key], list):
                            msg_obj[key] = [msg_obj[key]]
                        msg_obj[key].append(value)
                    else:
                        msg_obj[key] = value
                        
                    found_tag = True
                    break
            
            if not found_tag:
                # Skip unrecognized segments instead of invalidating entire message
                print(f"⚠️ Skipping unrecognized segment: '{segment}'")
                continue
        
        if valid_message and 'date' in msg_obj and 'sent_by' in msg_obj:
            # Message is valid if it has content OR story interactions
            has_content = len(msg_obj.keys()) > 2
            has_story_share = 'story_shared' in msg_obj
            has_story_reply = 'story_reply' in msg_obj
            has_story_reaction = 'story_reaction' in msg_obj
            
            if has_content or has_story_share or has_story_reply or has_story_reaction:
                # For story interactions without other message content, add the interaction as the message
                if has_story_share and 'message' not in msg_obj:
                    msg_obj['message'] = msg_obj['story_shared']
                elif has_story_reply and 'message' not in msg_obj:
                    msg_obj['message'] = msg_obj['story_reply']
                elif has_story_reaction and 'message' not in msg_obj:
                    msg_obj['message'] = msg_obj['story_reaction']
                messages.append(msg_obj)
            else:
                print(f"⚠️ Skipping message with only date and sender: {msg_obj}")

    return messages


def filter_messages_by_date(messages: List[Dict[str, Any]], cutoff_message: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Filter messages to only include those newer than the cutoff message"""
    try:
        from datetime import datetime
        cutoff_date_str = cutoff_message['date']
        
        # Parse cutoff date properly
        cutoff_date = datetime.strptime(cutoff_date_str, "%d.%m.%Y %H:%M")
        
        # Remove messages older than cutoff date using proper date comparison
        filtered = []
        for msg in messages:
            try:
                msg_date = datetime.strptime(msg['date'], "%d.%m.%Y %H:%M")
                if msg_date >= cutoff_date:
                    filtered.append(msg)
            except ValueError:
                # If date parsing fails, skip the message
                print(f"⚠️ Invalid date format in message: {msg.get('date', 'No date')}")
                continue
        
        # Remove the cutoff message itself and return newer messages
        new_messages = []
        found = False
        for msg in filtered:
            if not found and message_equals(msg, cutoff_message):
                found = True
                print(f"🔍 Found cutoff message: {msg['date']} - {msg.get('message', 'No message')[:50]}...")
                continue
            if found:  # Only add messages after we've found the cutoff message
                new_messages.append(msg)
        
        # If we couldn't find an exact match, fall back to date-based filtering
        if not found and len(filtered) > 0:
            print(f"⚠️ Could not find exact cutoff message match, using date-based filtering fallback")
            # Find the last message in filtered that has the same date as cutoff_message
            cutoff_date = cutoff_message['date']
            cutoff_idx = -1
            for i, msg in enumerate(filtered):
                if msg['date'] == cutoff_date:
                    cutoff_idx = i
            
            if cutoff_idx >= 0:
                # Return all messages after the last message with the cutoff date
                new_messages = filtered[cutoff_idx + 1:]
                print(f"🔄 Fallback filtering: found {len(new_messages)} messages after cutoff date {cutoff_date}")
            else:
                # If no messages with cutoff date found, return all filtered messages
                new_messages = filtered
                print(f"🔄 Fallback filtering: cutoff date not found, returning all {len(filtered)} filtered messages")
        
        print(f"🔄 Filtering summary: {len(messages)} total -> {len(filtered)} after date filter -> {len(new_messages)} after cutoff removal")
        return new_messages
        
    except Exception as e:
        print(f"⚠️ Error during message filtering: {str(e)}")
        return messages