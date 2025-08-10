"""
Scrolling utilities for Instagram automation
"""
from typing import Optional
from playwright.sync_api import Page, ElementHandle
from datetime import datetime
from . import config
from .browser_utils import get_scroll_container
from .helpers import convert_date


def scroll_to_end_of_chat_list(page: Page) -> Optional[ElementHandle]:
    """Scroll to the end of the chat list and return parent element"""
    try:
        chat_list = page.locator(config.SELECTORS['chat_list']).first
        chat_list.wait_for(state="visible", timeout=config.DEFAULT_TIMEOUT)
        print("Chat list container found")

        scrollable_handle = page.evaluate_handle('''() => {
            const container = document.querySelector('div[aria-label="Chats"][role="list"]');
            const walker = document.createTreeWalker(container, NodeFilter.SHOW_ELEMENT);
            const candidates = [];
            
            while (walker.nextNode()) {
                const node = walker.currentNode;
                const style = getComputedStyle(node);
                if (node.scrollHeight > node.clientHeight && 
                    (style.overflowY === 'auto' || style.overflowY === 'scroll')) {
                    candidates.push(node);
                }
            }
            
            return candidates.sort((a, b) => 
                b.getElementsByTagName('*').length - a.getElementsByTagName('*').length
            )[0] || container;
        }''')
        
        scrollable_container = scrollable_handle.as_element()
        print("Scrolling to end of chat list...")
        
        last_scroll_height = scrollable_container.evaluate("el => el.scrollHeight")
        
        for i in range(config.MAX_SCROLL_ATTEMPTS):
            scrollable_container.evaluate('el => el.scrollTop = el.scrollHeight')
            page.wait_for_timeout(int(config.SCROLL_PAUSE_SECONDS * 1000))
            new_scroll_height = scrollable_container.evaluate("el => el.scrollHeight")
            current_count = scrollable_container.evaluate("el => el.querySelectorAll('[role=\"listitem\"]').length")
            print(f"Scroll attempt {i+1}: Height={new_scroll_height}, Chats={current_count}")
            
            if new_scroll_height == last_scroll_height:
                print("Reached end of chat list")
                break
            last_scroll_height = new_scroll_height
        
        scrollable_container.screenshot(path=config.SCREENSHOT_PATHS['chat_list_full'])
        return scrollable_container.evaluate_handle('''(element) => {
            return element.children[1].firstElementChild;
        }''').as_element()
    except Exception as e:
        print(f"Chat list error: {str(e)}")
        page.screenshot(path=config.SCREENSHOT_PATHS['scroll_error'])
        return None


def scroll_till_start_open_chat(page: Page) -> None:
    """Scroll to the top of an open chat until no more scrolling is possible"""
    try:
        chat_container = page.locator(config.SELECTORS['messages_container']).first
        chat_container.wait_for(state='visible', timeout=config.DEFAULT_TIMEOUT)
        print("Found chat container")
        
        scrollable_element = chat_container.evaluate_handle('''element => {
            if (element.children.length === 0) return null;
            const level1 = element.firstElementChild;
            if (level1.children.length === 0) return null;
            const level2 = level1.firstElementChild;
            if (level2.children.length === 0) return null;
            const level3 = level2.firstElementChild;
            if (level3.children.length === 0) return null;
            return level3.firstElementChild;
        }''').as_element()
        
        if not scrollable_element:
            print("Could not find scrollable element through DOM traversal")
            return
        
        print("Found scrollable element. Scrolling to top...")
        
        previous_scroll_top = -1
        scroll_attempts = 0
        
        while scroll_attempts < config.MAX_SCROLL_TO_TOP_ATTEMPTS:
            scrollable_element.evaluate('el => el.scrollTop = 0')
            page.wait_for_timeout(config.SCROLL_TO_TOP_WAIT_MS)
            
            current_scroll_top = scrollable_element.evaluate('el => el.scrollTop')
            
            if current_scroll_top == 0:
                page.wait_for_timeout(config.SCROLL_TO_TOP_EXTENDED_WAIT_MS)
                current_scroll_top = scrollable_element.evaluate('el => el.scrollTop')
                if current_scroll_top == 0:
                    print("Reached the top of the chat (confirmed after extended wait)")
                    break
            
            if current_scroll_top == previous_scroll_top:
                print("No movement after scroll - reached maximum scroll position")
                break
                
            print(f"Scroll attempt {scroll_attempts + 1}: Current position: {current_scroll_top}")

            previous_scroll_top = current_scroll_top
            scroll_attempts += 1
        else:
            print("Reached maximum scroll attempts without reaching the top")
            
    except Exception as e:
        print(f"Error scrolling chat to top: {str(e)}")
        page.screenshot(path=config.SCREENSHOT_PATHS['chat_scroll_error'])


def scroll_to_date(page: Page, input_date_str: str) -> None:
    """Scroll to a specific date in the chat history"""
    try:
        target_dt = datetime.strptime(input_date_str, '%d.%m.%Y %H:%M')
    except ValueError:
        print(f"❌ Invalid target date format: {input_date_str}")
        return

    scrollable = get_scroll_container(page)
    if not scrollable:
        print("❌ Scroll container not found!")
        return

    found = False
    initial_scroll_height = scrollable.evaluate('el => el.scrollHeight')
    print(f"🎯 Initial scroll height: {initial_scroll_height}")
    
    for attempt in range(config.MAX_DATE_SCROLL_ATTEMPTS):
        print(f"🔍 Search attempt {attempt+1}/{config.MAX_DATE_SCROLL_ATTEMPTS}")
        print("⏳ Waiting for potential content changes...")
        page.wait_for_timeout(config.DATE_SCROLL_WAIT_MS)
        
        date_divs = page.query_selector_all(config.SELECTORS['date_break'])
        print(f"🔢 Found {len(date_divs)} date markers in view")
        
        if not date_divs:
            print("⚠️ No date_break divs found in current view")
        else:
            date_divs.reverse()
            older_date_found = False
            
            for i, div in enumerate(date_divs):
                try:
                    span = div.query_selector('span:last-child')
                    if not span:
                        print(f"  [{i}] ❌ Missing span in date marker")
                        continue
                        
                    extracted_date = span.inner_text().strip()
                    converted_date = convert_date(extracted_date)
                    
                    try:
                        current_dt = datetime.strptime(converted_date, '%d.%m.%Y %H:%M')
                    except ValueError:
                        if converted_date == input_date_str:
                            print(f"✅ Found target date: {input_date_str} (original: {extracted_date})")
                            div.scroll_into_view_if_needed()
                            found = True
                            return
                        print(f"  [{i}] ❌ Failed to parse: {converted_date} (original: {extracted_date})")
                        continue
                    
                    print(f"  [{i}] Comparing: {converted_date} vs target {input_date_str}")
                    
                    if current_dt == target_dt:
                        print(f"✅ Found target date: {input_date_str} (original: {extracted_date})")
                        div.scroll_into_view_if_needed()
                        found = True
                        return
                    
                    if current_dt < target_dt:
                        print(f"⏩ Found older date: {converted_date} (original: {extracted_date})")
                        older_date_found = True
                        break
                    
                    print(f"  - Newer date: {converted_date} vs target: {input_date_str}")
                    
                except Exception as e:
                    print(f"❌ Error processing div: {e}")
                    continue
            
            if older_date_found:
                print("⏹ Stopping search - older date encountered")
                break
        
        print("🔼 Scrolling up to load older messages")
        prev_scroll_height = scrollable.evaluate('el => el.scrollHeight')
        
        scrollable.evaluate(config.JS_SNIPPETS['scroll_to_height'])
        
        try:
            print("⏳ Waiting for new content...")
            page.wait_for_function('''(prevHeight) => {
                return document.querySelector('div[aria-label*="Messages in conversation with"]')
                    ?.firstElementChild?.firstElementChild?.firstElementChild
                    ?.scrollHeight > prevHeight;
            }''', arg=prev_scroll_height, timeout=15000)
            
            new_scroll_height = scrollable.evaluate('el => el.scrollHeight')
            print(f"🆕 New content loaded! Scroll height changed: {prev_scroll_height} → {new_scroll_height}")
        except Exception as e:
            print(f"⛔ No new content detected: {str(e)}")
            current_scroll_top = scrollable.evaluate('el => el.scrollTop')
            if current_scroll_top <= config.SCROLL_TOP_THRESHOLD:
                print("🚩 Reached top of chat history")
                break
            else:
                print("⚠️ Continuing despite timeout - might be slow network")

    if not found:
        print(f"❌ Date not found after {config.MAX_DATE_SCROLL_ATTEMPTS} attempts: {input_date_str}")
        final_scroll_height = scrollable.evaluate('el => el.scrollHeight')
        final_scroll_top = scrollable.evaluate('el => el.scrollTop')
        print(f"📏 Final scroll state: Height={final_scroll_height}, Position={final_scroll_top}")
        print("🖼 Taking screenshot for debugging...")
        page.screenshot(path=config.SCREENSHOT_PATHS['scroll_debug_final'])