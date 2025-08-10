"""
Browser utilities for Instagram automation
"""
from typing import Dict, Any, List, Optional, Tuple
from playwright.sync_api import sync_playwright, Page, ElementHandle
import time
from . import config


def convert_cookie(cookie: Dict[str, Any]) -> Dict[str, Any]:
    """Convert cookie format for Playwright"""
    new_cookie = {
        'name': cookie['name'],
        'value': cookie['value'],
        'domain': cookie['domain'],
        'path': cookie['path'],
        'secure': cookie['secure'],
        'httpOnly': cookie['httpOnly']
    }
    
    # Handle sameSite conversion
    same_site = cookie.get('sameSite')
    if same_site == "no_restriction":
        new_cookie['sameSite'] = "None"
    elif same_site == "lax":
        new_cookie['sameSite'] = "Lax"
    else:
        new_cookie['sameSite'] = "Lax"
    
    # Add expiration if available
    if not cookie.get('session', False) and 'expirationDate' in cookie:
        new_cookie['expires'] = cookie['expirationDate']
    
    return new_cookie


def setup_browser_context(playwright, headless: bool = None) -> Tuple[Any, Page]:
    """Initialize browser context with cookies and window positioning"""
    if headless is None:
        headless = config.HEADLESS_MODE
    
    # Get screen configuration for window positioning
    if not headless:
        window_config = config.get_screen_configuration()
        print(f"Positioning browser window at: {window_config}")
        
        # Use exact calibrated positioning (no adjustment needed since it's manually calibrated)
        adjusted_x = window_config['x']
        adjusted_y = window_config['y']
        adjusted_width = window_config['width']
        adjusted_height = window_config['height']
        
        print(f"Adjusted position: x={adjusted_x}, y={adjusted_y}, width={adjusted_width}, height={adjusted_height}")
        
        browser = playwright.chromium.launch(
            headless=headless,
            args=[
                f"--window-position={adjusted_x},{adjusted_y}",
                f"--window-size={adjusted_width},{adjusted_height}",
                "--start-maximized=false",  # Prevent auto-maximize
                "--disable-extensions",     # Disable extensions that might affect positioning
                "--disable-default-apps",   # Disable default apps
                "--no-first-run",          # Skip first run experience
                "--disable-infobars",      # Disable info bars
                "--disable-web-security",  # Disable web security (for automation)
                "--disable-features=TranslateUI",  # Disable translate UI
                "--disable-background-timer-throttling",  # Disable background throttling
                "--disable-backgrounding-occluded-windows",  # Disable backgrounding
                "--disable-renderer-backgrounding"  # Disable renderer backgrounding
            ]
        )
    else:
        browser = playwright.chromium.launch(headless=headless)
    
    # Create context with dynamic viewport (no fixed dimensions)
    context = browser.new_context(
        user_agent=config.USER_AGENT,
        no_viewport=True  # Let viewport adjust dynamically to window size
    )
    
    cookies_data = config.load_cookies_from_file()
    if cookies_data:
        playwright_cookies = [convert_cookie(c) for c in cookies_data]
        context.add_cookies(playwright_cookies)
    
    page = context.new_page()
    
    # Additional positioning adjustment after page creation
    if not headless:
        try:
            # Wait a moment for the window to fully load
            page.wait_for_timeout(1000)
            
            # Use JavaScript to fine-tune window positioning and set zoom
            page.evaluate(f"""
                // Move window to exact position
                window.moveTo({adjusted_x}, {adjusted_y});
                
                // Resize to exact dimensions
                window.resizeTo({adjusted_width}, {adjusted_height});
                
                // Set transform scale to 80% to see more content while filling viewport
                document.body.style.transform = 'scale(0.8)';
                document.body.style.transformOrigin = 'top left';
                document.body.style.width = '125%';  // 100% / 0.8 = 125%
                document.body.style.height = '125%';
                
                // Ensure window is focused and on top
                window.focus();
                
                console.log('Window positioned at:', window.screenX, window.screenY);
                console.log('Window size:', window.outerWidth, window.outerHeight);
                console.log('Transform scale set to: 80%');
            """)
            
            print(f"Final window positioning completed")
            
        except Exception as e:
            print(f"Warning: Could not fine-tune window positioning: {e}")
    
    return browser, page


def handle_notification_prompt(page: Page) -> bool:
    """Handle notification prompt if it appears"""
    try:
        page.wait_for_timeout(config.NOTIFICATION_TIMEOUT)
        if page.get_by_text(config.SELECTORS['notification_turn_on'], exact=True).is_visible():
            print("Notification prompt detected")
            not_now_button = page.get_by_role("button", name=config.SELECTORS['notification_not_now'], exact=True)
            if not_now_button.is_visible():
                not_now_button.click(delay=100)
                page.wait_for_timeout(1000)
                print("Clicked 'Not Now' button")
            else:
                print("'Not Now' button not found")
        else:
            print("No notification prompt found")
        return True
    except Exception as e:
        print(f"Error handling notification prompt: {str(e)}")
        return False


def handle_direct_message_icon(page: Page) -> bool:
    """Find and click the direct message icon"""
    try:
        dm_icons = page.locator(config.SELECTORS['direct_message_icon'])
        dm_icons.first.wait_for(state="attached", timeout=config.DEFAULT_TIMEOUT)
        print(f"Found {dm_icons.count()} Direct messaging icons")

        for i in range(dm_icons.count()):
            if dm_icons.nth(i).is_visible():
                dm_icons.nth(i).scroll_into_view_if_needed()
                dm_icons.nth(i).click(delay=200)
                print("Clicked on Direct messaging icon")
                page.wait_for_selector(config.SELECTORS['chats_container'], timeout=config.DEFAULT_TIMEOUT)
                page.screenshot(path=config.SCREENSHOT_PATHS['direct_icon_click'])
                print("Messages page loaded successfully")
                return True
        raise Exception("No visible Direct messaging icon found")
    except Exception as e:
        print(f"Error clicking Direct messaging icon: {str(e)}")
        page.screenshot(path=config.SCREENSHOT_PATHS['error'])
        return False


def get_scroll_container(page: Page) -> Optional[ElementHandle]:
    """Get the scrollable container for chat messages"""
    try:
        chat_container = page.locator(config.SELECTORS['messages_container']).first
        if not chat_container.is_visible():
            chat_container.wait_for(state='visible', timeout=config.DEFAULT_TIMEOUT)
        
        scrollable_element = chat_container.evaluate_handle('''element => {
            if (!element.children.length) return null;
            const level1 = element.firstElementChild;
            if (!level1 || !level1.children.length) return null;
            const level2 = level1.firstElementChild;
            if (!level2 || !level2.children.length) return null;
            const level3 = level2.firstElementChild;
            if (!level3 || !level3.children.length) return null;
            return level3.firstElementChild;
        }''').as_element()
        
        if scrollable_element:
            return scrollable_element
        
        return chat_container.element_handle()
    except Exception as e:
        print(f"⚠️ Error getting scroll container: {str(e)}")
        return None


def extract_username_from_open_chat(page: Page) -> Tuple[Optional[str], Optional[str]]:
    """Extract username and user ID from open chat"""
    profile_link = page.locator(config.SELECTORS['profile_link']).first
    if not profile_link.is_visible():
        return None, None

    # Extract username from href
    href = profile_link.get_attribute("href")
    username = href.strip('/') if href else None

    # Extract user ID from image within the profile link
    user_id = None
    img = profile_link.locator('img').first
    if img.is_visible():
        src = img.get_attribute("src")
        if src:
            # Extract from URL pattern: ..._USERID_...
            import re
            match = re.search(r'_(\d{15,20})_', src)
            if match:
                user_id = match.group(1)

    return user_id, username


def extract_main_username(page: Page) -> Optional[str]:
    """Extract the main username from the thread list"""
    thread_list = page.locator(config.SELECTORS['thread_list'])
    
    if thread_list.count() == 0:
        print("Thread list container not found")
        return None
    
    # Navigate through 6 levels of first children
    current = thread_list
    for level in range(6):
        current = current.locator('xpath=./*[1]')
        
        if current.count() == 0:
            print(f"Element at level {level+1} not found")
            return None
    
    # Verify element is visible and extract text
    if current.is_visible():
        text_content = current.text_content().strip()
        print(f"Extracted text: {text_content}")
        return text_content
    else:
        print("Target element is not visible")
        return None


def extract_target_text(page: Page) -> str:
    """Extract target text from conversation"""
    conv_div = page.locator(config.SELECTORS['conversation_div']).first
    
    return conv_div.evaluate('''(div) => {
        try {
            const img = div.querySelector('img');
            if (!img) return '';
            
            let node = img;
            for (let i = 0; i < 4; i++) {
                node = node.parentNode;
                if (!node) return '';
            }
            
            if (node.children.length < 2) return '';
            node = node.children[1];
            
            if (node.children.length < 1) return '';
            node = node.children[0];
            
            if (node.children.length < 1) return '';
            node = node.children[0];
            
            if (node.children.length < 1) return '';
            node = node.children[0];
            
            return node.textContent || '';
        } catch {
            return '';
        }
    }''')