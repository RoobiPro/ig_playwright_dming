"""
Configuration file for Instagram Playwright automation
"""
import json
import os
from typing import Dict, List, Any

# Application constants
APP_NAME = "Instagram Playwright Bot"
VERSION = "1.0.0"

# Directory paths
DATA_DIR = "data"
CONVERSATIONS_DIR = os.path.join(DATA_DIR, "conversations")
FACTS_DIR = os.path.join(DATA_DIR, "facts")
OUR_DATA_FILE = os.path.join(DATA_DIR, "our_data.json")

# Browser configuration
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
HEADLESS_MODE = False

# Window positioning for secondary screen (manually calibrated)
CALIBRATED_WINDOW_POSITION = {
    'x': 2312,
    'y': 113,
    'width': 883,
    'height': 937
}

# Fallback window positioning for secondary screen (dynamic detection)
FALLBACK_WINDOW_POSITION = {
    'x': 1920,  # X position for secondary screen (assuming 1920px primary screen width)
    'y': 0,     # Y position at top of screen
    'width': 960,   # Half width of secondary screen (assuming 1920px width)
    'height': 1080  # Full height (assuming 1080px height)
}

# Instagram URLs
INSTAGRAM_BASE_URL = "https://www.instagram.com"
INSTAGRAM_DIRECT_INBOX_URL = f"{INSTAGRAM_BASE_URL}/direct/inbox/"

# Timeout settings (in milliseconds)
DEFAULT_TIMEOUT = 10000
SCROLL_TIMEOUT = 2000
NOTIFICATION_TIMEOUT = 2000
CHAT_LOAD_TIMEOUT = 5000

# Scroll configuration
MAX_SCROLL_ATTEMPTS = 30
SCROLL_PAUSE_SECONDS = 2
MAX_SCROLL_TO_TOP_ATTEMPTS = 500
SCROLL_TO_TOP_WAIT_MS = 2000
SCROLL_TO_TOP_EXTENDED_WAIT_MS = 3000

# Message processing
MIN_CHILD_THRESHOLD = 10  # Reduced from 25 to include more elements
MAX_RETRY_ATTEMPTS = 5    # Increased from 3 for more thorough loading
SCROLL_INTO_VIEW_WAIT_MS = 2000  # Increased from 1500 for slower loading

# Date scrolling
MAX_DATE_SCROLL_ATTEMPTS = 50
DATE_SCROLL_WAIT_MS = 3000
SCROLL_UP_PERCENTAGE = 0.8
SCROLL_TOP_THRESHOLD = 100

# DOM selectors
SELECTORS = {
    'direct_message_icon': 'svg[aria-label="Direct"]',
    'chats_container': 'div[aria-label="Chats"]',
    'chat_list': 'div[aria-label="Chats"][role="list"]',
    'conversation_div': 'div[aria-label^="Conversation with "]',
    'messages_container': 'div[aria-label*="Messages in conversation with"]',
    'thread_list': 'div[aria-label="Thread list"]',
    'profile_link': 'a[aria-label*="Open the profile page"]',
    'date_break': 'div[data-scope="date_break"]',
    'notification_turn_on': 'Turn on Notifications',
    'notification_not_now': 'Not Now',
    'list_item': '[role="listitem"]',
    'grid_cell': 'role="gridcell"',
    'message_content': '.html-div[dir="auto"]',
    'reaction_container': '[aria-label*="see who reacted to this"]',
}

# Screenshot paths
SCREENSHOT_PATHS = {
    'direct_icon_click': 'instagram_direct_icon_click.png',
    'error': 'instagram_error.png',
    'chat_list_full': 'instagram_chat_list_full.png',
    'scroll_error': 'instagram_scroll_error.png',
    'scroll_debug_final': 'scroll_debug_final.png',
    'chat_scroll_error': 'chat_scroll_error.png',
}

# Message tags mapping
MESSAGE_TAG_MAPPING = {
    '[DATE]': 'date',
    '[SENT BY]': 'sent_by',
    '[REPLY SENT BY]': 'sent_by',
    '[ORIGINAL MESSAGE BY]': 'original_message_by',
    '[REACTIONS]': 'reactions',
    '[QUOTED TEXT]': 'quoted_text',
    '[ONE TIME VIEW MEDIA]': 'one_time_view_media',
    '[MEDIA ATTACHED: IMG]': 'media_attached_img',
    '[MEDIA ATTACHED: VIDEO]': 'media_attached_video',
    '[IMG ALT]:': 'img_alt',
    '[MESSAGE]': 'message',
    '[LINK PREVIEW]': 'link_preview',
    '[IG CONTENT SHARED]': 'ig_content_shared',
    '[STORY SHARED]': 'story_shared',
    '[STORY REPLY]': 'story_reply',
    '[STORY REACTION]': 'story_reaction'
}

# JavaScript code snippets
JS_SNIPPETS = {
    'recursive_count': """node => {
        function countAllChildren(element) {
            let count = element.childElementCount;
            for (let child of element.children) {
                count += countAllChildren(child);
            }
            return count;
        }
        return countAllChildren(node);
    }""",
    
    'scroll_to_height': """el => {
        const scrollDistance = el.clientHeight * 0.8;
        console.log('Scrolling up by', scrollDistance, 'px');
        el.scrollTop -= scrollDistance;
    }""",
    
    'scroll_into_view': """div => {
        div.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
            inline: 'center'
        });
    }""",
}

def load_cookies_from_file(file_path: str = None) -> List[Dict[str, Any]]:
    """Load cookies from a JSON file"""
    if file_path is None:
        file_path = os.path.join(DATA_DIR, "cookies.json")
    
    if not os.path.exists(file_path):
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading cookies from {file_path}: {e}")
        return []

def save_cookies_to_file(cookies: List[Dict[str, Any]], file_path: str = None) -> bool:
    """Save cookies to a JSON file"""
    if file_path is None:
        file_path = os.path.join(DATA_DIR, "cookies.json")
    
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"Error saving cookies to {file_path}: {e}")
        return False

def get_screen_configuration(use_calibrated=True):
    """Get screen configuration with option to use calibrated values"""
    
    if use_calibrated:
        print("Using manually calibrated window position")
        print(f"Position: ({CALIBRATED_WINDOW_POSITION['x']}, {CALIBRATED_WINDOW_POSITION['y']})")
        print(f"Size: {CALIBRATED_WINDOW_POSITION['width']}x{CALIBRATED_WINDOW_POSITION['height']}")
        return CALIBRATED_WINDOW_POSITION.copy()
    
    # Dynamic detection as fallback
    print("Using dynamic screen detection...")
    
    try:
        import ctypes
        import ctypes.wintypes
        
        # Windows API constants
        SM_CMONITORS = 80
        SM_CXSCREEN = 0
        SM_CYSCREEN = 1
        
        # Get number of monitors
        num_monitors = ctypes.windll.user32.GetSystemMetrics(SM_CMONITORS)
        print(f"Number of monitors detected: {num_monitors}")
        
        if num_monitors < 2:
            # Single monitor - use left half
            primary_width = ctypes.windll.user32.GetSystemMetrics(SM_CXSCREEN)
            primary_height = ctypes.windll.user32.GetSystemMetrics(SM_CYSCREEN)
            
            window_config = {
                'x': 0,
                'y': 0,
                'width': primary_width // 2,
                'height': primary_height
            }
            print(f"Single monitor: Using left half of primary screen")
            return window_config
        
        # Multiple monitors - get monitor info
        monitors = []
        
        def enum_display_monitors_proc(hMonitor, hdcMonitor, lprcMonitor, dwData):
            monitors.append({
                'handle': hMonitor,
                'left': lprcMonitor.contents.left,
                'top': lprcMonitor.contents.top,
                'right': lprcMonitor.contents.right,
                'bottom': lprcMonitor.contents.bottom,
                'width': lprcMonitor.contents.right - lprcMonitor.contents.left,
                'height': lprcMonitor.contents.bottom - lprcMonitor.contents.top
            })
            return True
        
        # Define the callback function type
        MonitorEnumProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.wintypes.HMONITOR,
            ctypes.wintypes.HDC,
            ctypes.POINTER(ctypes.wintypes.RECT),
            ctypes.wintypes.LPARAM
        )
        
        # Enumerate all monitors
        ctypes.windll.user32.EnumDisplayMonitors(
            None, None, MonitorEnumProc(enum_display_monitors_proc), 0
        )
        
        # Sort monitors by left position to identify primary and secondary
        monitors.sort(key=lambda m: m['left'])
        
        print(f"Monitor details:")
        for i, monitor in enumerate(monitors):
            print(f"  Monitor {i+1}: {monitor['width']}x{monitor['height']} at ({monitor['left']}, {monitor['top']})")
        
        # Find secondary monitor (usually the one that's not at position 0,0)
        secondary_monitor = None
        for monitor in monitors:
            if monitor['left'] != 0 or monitor['top'] != 0:
                secondary_monitor = monitor
                break
        
        # If no secondary monitor found, use the second monitor in the list
        if secondary_monitor is None and len(monitors) > 1:
            secondary_monitor = monitors[1]
        
        # If still no secondary monitor, use primary monitor
        if secondary_monitor is None:
            secondary_monitor = monitors[0]
        
        # Try to match your calibrated position to understand the layout
        if secondary_monitor and CALIBRATED_WINDOW_POSITION['x'] >= secondary_monitor['left']:
            # Your calibrated position seems to be on the detected secondary monitor
            # Calculate relative position within the secondary monitor
            relative_x = CALIBRATED_WINDOW_POSITION['x'] - secondary_monitor['left']
            relative_y = CALIBRATED_WINDOW_POSITION['y'] - secondary_monitor['top']
            
            print(f"Calibrated position appears to be {relative_x}px from left edge of secondary monitor")
            
            # Use calibrated values but verify they fit within the detected monitor
            window_config = {
                'x': CALIBRATED_WINDOW_POSITION['x'],
                'y': CALIBRATED_WINDOW_POSITION['y'],
                'width': CALIBRATED_WINDOW_POSITION['width'],
                'height': CALIBRATED_WINDOW_POSITION['height']
            }
            
            print(f"Using calibrated position: ({window_config['x']}, {window_config['y']}) size {window_config['width']}x{window_config['height']}")
            return window_config
        
        # Fallback to calculated left half
        window_config = {
            'x': secondary_monitor['left'],
            'y': secondary_monitor['top'],
            'width': secondary_monitor['width'] // 2,
            'height': secondary_monitor['height']
        }
        
        print(f"Using calculated left half: ({window_config['x']}, {window_config['y']}) size {window_config['width']}x{window_config['height']}")
        return window_config
        
    except Exception as e:
        print(f"Error detecting screen configuration with Windows API: {e}")
        print("Falling back to calibrated values...")
        
        # Fallback to calibrated values
        return CALIBRATED_WINDOW_POSITION.copy()


def get_calibrated_position():
    """Get the manually calibrated window position"""
    return CALIBRATED_WINDOW_POSITION.copy()


def get_dynamic_screen_configuration():
    """Get dynamic screen configuration (bypass calibrated values)"""
    return get_screen_configuration(use_calibrated=False)


def ensure_directories_exist():
    """Ensure all required directories exist"""
    directories = [DATA_DIR, CONVERSATIONS_DIR, FACTS_DIR]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)