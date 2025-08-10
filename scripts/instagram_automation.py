"""
Instagram automation main class
"""
import time
import json
import os
import traceback
import datetime
import pytz

from typing import Optional, Dict, Any, List
from playwright.sync_api import sync_playwright, Page, ElementHandle

from . import config
from .browser_utils import (
    setup_browser_context, 
    handle_notification_prompt, 
    handle_direct_message_icon,
    extract_main_username,
    extract_target_text,
    extract_username_from_open_chat
)
from .scroll_utils import scroll_to_end_of_chat_list, scroll_till_start_open_chat, scroll_to_date
from .message_extraction import initial_messages_extraction
from .data_utils import (
    check_userid_json, 
    save_initial_messages, 
    get_our_information,
    get_user_information
)
from .helpers import save_merged_messages, filter_recent_messages
from .deepseek_api_client import create_client_from_env
from .ai_api_functions import ask_ai_provider

class InstagramAutomation:
    """Main Instagram automation class"""
    
    def __init__(self, headless: bool = None):
        """Initialize the Instagram automation"""
        self.headless = headless if headless is not None else config.HEADLESS_MODE
        self.browser = None
        self.page = None
        self.main_username = None
        
        # Ensure required directories exist
        config.ensure_directories_exist()
    
    def __enter__(self):
        """Context manager entry"""
        self.start_browser()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close_browser()
    
    def start_browser(self) -> None:
        """Start the browser and navigate to Instagram"""
        try:
            self.playwright = sync_playwright().start()
            self.browser, self.page = setup_browser_context(self.playwright, self.headless)
            
            print("Navigating to Instagram Direct...")
            self.page.goto(config.INSTAGRAM_DIRECT_INBOX_URL, wait_until="domcontentloaded")
            self.page.wait_for_timeout(2000)
            
            # Set transform scale to 80% for better content visibility
            if not self.headless:
                self.page.evaluate("""
                    document.body.style.transform = 'scale(0.8)';
                    document.body.style.transformOrigin = 'top left';
                    document.body.style.width = '125%';
                    document.body.style.height = '125%';
                """)
                print("Transform scale set to 80%")
            
            self.page.wait_for_timeout(3000)
            print("Browser started successfully")
        except Exception as e:
            print(f"Error starting browser: {str(e)}")
            raise
    
    def set_window_position(self, x: int, y: int, width: int, height: int) -> None:
        """Manually set window position and size (for debugging/testing)"""
        if self.page and not self.headless:
            try:
                # Use JavaScript to set window bounds with error handling
                result = self.page.evaluate(f"""
                    try {{
                        // Log current position
                        console.log('Current position:', window.screenX, window.screenY);
                        console.log('Current size:', window.outerWidth, window.outerHeight);
                        
                        // Move and resize window
                        window.moveTo({x}, {y});
                        window.resizeTo({width}, {height});
                        
                        // Wait a moment and check final position
                        setTimeout(() => {{
                            console.log('Final position:', window.screenX, window.screenY);
                            console.log('Final size:', window.outerWidth, window.outerHeight);
                        }}, 100);
                        
                        return {{
                            success: true,
                            position: {{x: window.screenX, y: window.screenY}},
                            size: {{width: window.outerWidth, height: window.outerHeight}}
                        }};
                    }} catch (error) {{
                        return {{success: false, error: error.message}};
                    }}
                """)
                
                if result.get('success'):
                    print(f"Window positioned at: ({x}, {y}) with size {width}x{height}")
                    print(f"Actual position: {result['position']}, size: {result['size']}")
                else:
                    print(f"Could not set window position: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"Could not set window position: {e}")
    
    def get_window_position(self) -> dict:
        """Get current window position and size"""
        if self.page and not self.headless:
            try:
                result = self.page.evaluate("""
                    ({
                        x: window.screenX,
                        y: window.screenY,
                        width: window.outerWidth,
                        height: window.outerHeight,
                        innerWidth: window.innerWidth,
                        innerHeight: window.innerHeight
                    })
                """)
                return result
            except Exception as e:
                print(f"Could not get window position: {e}")
                return {}
        return {}
    
    def center_window_on_secondary_screen(self) -> None:
        """Center the window on the secondary screen"""
        if self.page and not self.headless:
            try:
                window_config = config.get_screen_configuration()
                
                # Calculate center position
                center_x = window_config['x'] + (window_config['width'] - 960) // 2
                center_y = window_config['y'] + (window_config['height'] - 1080) // 2
                
                self.set_window_position(center_x, center_y, 960, 1080)
                print(f"Window centered on secondary screen at ({center_x}, {center_y})")
                
            except Exception as e:
                print(f"Could not center window: {e}")
    
    def align_window_to_calibrated_position(self) -> None:
        """Align window to the manually calibrated position"""
        if self.page and not self.headless:
            try:
                # Use the calibrated position directly
                pos = config.get_calibrated_position()
                
                self.set_window_position(pos['x'], pos['y'], pos['width'], pos['height'])
                print(f"Window aligned to calibrated position: ({pos['x']}, {pos['y']}) size {pos['width']}x{pos['height']}")
                
                # Verify positioning
                actual_pos = self.get_window_position()
                print(f"Actual window position: {actual_pos}")
                
            except Exception as e:
                print(f"Could not align window to calibrated position: {e}")
    
    def align_window_to_left_half(self) -> None:
        """Align window to left half of secondary screen with perfect positioning"""
        if self.page and not self.headless:
            try:
                window_config = config.get_screen_configuration()
                
                # Calculate exact left half position
                left_x = window_config['x']
                left_y = window_config['y']
                left_width = window_config['width']
                left_height = window_config['height']
                
                self.set_window_position(left_x, left_y, left_width, left_height)
                print(f"Window aligned to position: ({left_x}, {left_y}) size {left_width}x{left_height}")
                
                # Verify positioning
                actual_pos = self.get_window_position()
                print(f"Actual window position: {actual_pos}")
                
            except Exception as e:
                print(f"Could not align window to left half: {e}")
    
    def close_browser(self) -> None:
        """Close the browser"""
        if self.browser:
            self.browser.close()
        if hasattr(self, 'playwright'):
            self.playwright.stop()
    
    def setup_session(self) -> bool:
        """Setup the Instagram session"""
        try:
            # Fine-tune window positioning after page load
            if not self.headless:
                print("Fine-tuning window position...")
                self.page.wait_for_timeout(1000)  # Wait for page to fully load
                self.align_window_to_calibrated_position()
            
            # Handle notification prompt
            if not handle_notification_prompt(self.page):
                print("Warning: Could not handle notification prompt")
            
            # Extract main username
            self.main_username = extract_main_username(self.page)
            if not self.main_username:
                print("Error: Could not extract main username")
                return False
            
            print(f"Main username: {self.main_username}")
            return True
        except Exception as e:
            print(f"Error setting up session: {str(e)}")
            return False
    
    def get_chat_list(self) -> Optional[ElementHandle]:
        """Get the chat list element"""
        try:
            return scroll_to_end_of_chat_list(self.page)
        except Exception as e:
            print(f"Error getting chat list: {str(e)}")
            return None
    
    def process_single_chat(self, chat_index: int, parent_element: ElementHandle) -> None:
        """Process a single chat conversation"""
        try:
            print(f"Processing chat {chat_index}")
            
            # Click on the chat
            div = parent_element.evaluate_handle('''(element, index) => {
                return element.children[index];
            }''', chat_index).as_element()
            
            print(f"      📍 CHAT SELECTION SCROLL: Scrolling chat div into view before clicking")
            pre_chat_scroll = self.page.evaluate("window.scrollY || document.documentElement.scrollTop")
            div.evaluate(config.JS_SNIPPETS['scroll_into_view'])
            post_chat_scroll = self.page.evaluate("window.scrollY || document.documentElement.scrollTop")
            chat_scroll_delta = post_chat_scroll - pre_chat_scroll
            print(f"      📍 CHAT SCROLL DELTA: {chat_scroll_delta} pixels ({'UP' if chat_scroll_delta < 0 else 'DOWN' if chat_scroll_delta > 0 else 'NO CHANGE'})")
            
            div.click(timeout=config.CHAT_LOAD_TIMEOUT)
            time.sleep(2)
            
            # Extract chat information
            partner_name = extract_target_text(self.page)
            partner_user_id, partner_username = extract_username_from_open_chat(self.page)
            
            print(f"Partner: {partner_name}")
            print(f"Partner username: {partner_username}")
            print(f"Partner user ID: {partner_user_id}")
            
            if not partner_username:
                print("Warning: Could not extract partner username, skipping chat")
                return
            
            # Check for existing conversation data
            existing_data = check_userid_json(partner_username)
            all_messages = None
            
            if existing_data is not None:
                all_messages = self._process_existing_conversation(partner_name, partner_username, existing_data)
            else:
                all_messages = self._process_new_conversation(partner_name, partner_username)
            
            # Generate response with the actual messages
            if all_messages and isinstance(all_messages, list):
                print("Last message object:")
                print(json.dumps(all_messages[-1], indent=2, ensure_ascii=False))
                if all_messages[-1]['sent_by'] != 'kaila_mentari_':
                    
                    # Extract the date string
                    date_str = all_messages[-1]['date']

                    # Parse the date string into a datetime object
                    parsed_date = datetime.datetime.strptime(date_str, "%d.%m.%Y %H:%M")

                    # Define Bali timezone
                    bali_tz = pytz.timezone('Asia/Makassar')

                    # Localize the parsed datetime to Bali timezone
                    parsed_date_bali = bali_tz.localize(parsed_date)

                    # Get the current time in Bali timezone
                    current_time_bali = datetime.datetime.now(bali_tz)

                    # Calculate absolute time difference in seconds
                    time_difference = abs((current_time_bali - parsed_date_bali).total_seconds())
                    print("=== NOT RESPONEDED YET ===")
                    # Determine placeholder based on time difference
                    if time_difference < 3600:  # 3600 seconds = 1 hour
                        result = "less_than_1hr_placeholder"
                        print("less_than_1hr_placeholder")
                    else:
                        result = "1hr_or_more_placeholder"
                        print("1hr_or_more_placeholder")
                        
                        # Skip logic - prompt user to skip this chat
                        user_input = input(f"\nProcess chat with {partner_name} (@{partner_username})? (y/n/skip): ").strip().lower()
                        if user_input in ['n', 'skip', 'no']:
                            print(f"Skipping chat with {partner_name}")
                            return
                        
                        response_data = self._generate_response(partner_username, all_messages)
                        
                        print(json.dumps(response_data, indent=2, ensure_ascii=False))
                        print(type(response_data))
                        
                        # Check if ai_response exists in response_data
                        if "ai_response" not in response_data:
                            print("❌ No 'ai_response' key found in response_data")
                            return
                        
                        if "generated_message" not in response_data["ai_response"]:
                            print("❌ No 'generated_message' key found in ai_response")
                            return
                            
                        message = response_data["ai_response"]["generated_message"]
                        print(f"Print Message: {message}")
                        
                        # CRITICAL: Hard-coded hyphen removal as final safety net
                        if message:
                            original_message = message
                            
                            # Replace all types of hyphens and dashes with commas
                            cleaned_message = original_message
                            cleaned_message = cleaned_message.replace(' - ', ', ')  # Hyphen with spaces
                            cleaned_message = cleaned_message.replace(' — ', ', ')  # Em-dash with spaces
                            cleaned_message = cleaned_message.replace('—', ', ')    # Any remaining em-dashes
                            cleaned_message = cleaned_message.replace(' – ', ', ')  # En-dash with spaces
                            cleaned_message = cleaned_message.replace('–', ', ')    # Any remaining en-dashes
                            
                            cleaned_message = cleaned_message.strip()
                            
                            # Update the message if changes were made
                            if cleaned_message != original_message:
                                print(f"🔧 HYPHEN CLEANUP: Replaced hyphens/dashes with commas")
                                print(f"   Original: {original_message}")
                                print(f"   Cleaned:  {cleaned_message}")
                                message = cleaned_message
                            else:
                                print("✅ No hyphens found in message")
                        
                        print(f"Final Message: {message}")
                        
                        # Find the message input element and insert the message
                        try:
                            # Try multiple selectors for Instagram DM input
                            selectors = [
                                'div[aria-describedby="Message"][aria-label="Message"]',
                                'div[contenteditable="true"][aria-label="Message"]',
                                'div[data-testid="message-input"]',
                                'div[role="textbox"][aria-label="Message"]',
                                'div[contenteditable="true"][data-testid="message-input"]',
                                'div[contenteditable="true"]',
                                'textarea[placeholder*="message" i]',
                                'div[aria-label*="message" i][contenteditable="true"]'
                            ]
                            
                            message_input = None
                            used_selector = None
                            
                            for selector in selectors:
                                try:
                                    input_element = self.page.locator(selector)
                                    if input_element.count() > 0:
                                        message_input = input_element
                                        used_selector = selector
                                        print(f"📍 Found message input with selector: {selector}")
                                        break
                                except:
                                    continue
                            
                            if message_input and message_input.count() > 0:
                                # Use optimized reliable method for long messages
                                try:
                                    print("📝 Inserting message with optimized method...")
                                    
                                    # Focus on the input field
                                    message_input.first.click()
                                    self.page.wait_for_timeout(500)
                                    
                                    # Clear existing content more reliably
                                    message_input.first.press("Control+a")
                                    self.page.wait_for_timeout(200)
                                    message_input.first.press("Delete")
                                    self.page.wait_for_timeout(300)
                                    
                                    # Use fill method for longer messages (faster than type)
                                    print("📝 Filling message content...")
                                    message_input.first.fill(message)
                                    self.page.wait_for_timeout(500)
                                    
                                    # Trigger input events to ensure Instagram recognizes the content
                                    print("📝 Triggering input events...")
                                    message_input.first.press("Space")
                                    self.page.wait_for_timeout(200)
                                    message_input.first.press("Backspace")
                                    self.page.wait_for_timeout(300)
                                    
                                    # Wait and verify the message was inserted
                                    print("⏳ Verifying message insertion...")
                                    max_retries = 10
                                    for retry in range(max_retries):
                                        try:
                                            current_content = message_input.first.input_value()
                                            if current_content and len(current_content) > 0:
                                                print(f"✅ Message insertion verified! Content length: {len(current_content)}")
                                                break
                                        except:
                                            # Try alternative method to check content
                                            try:
                                                current_content = message_input.first.text_content()
                                                if current_content and len(current_content) > 0:
                                                    print(f"✅ Message insertion verified via text_content! Length: {len(current_content)}")
                                                    break
                                            except:
                                                pass
                                        
                                        print(f"⏳ Retry {retry + 1}/{max_retries} - waiting for message insertion...")
                                        self.page.wait_for_timeout(500)
                                    else:
                                        print("⚠️ Could not verify message insertion, but proceeding...")
                                    
                                    print("✅ Message insertion process completed")
                                    
                                    # Show message preview
                                    print("\n" + "="*80)
                                    print("📝 MESSAGE READY TO SEND:")
                                    print("="*80)
                                    print(f"💬 {message}")
                                    print("="*80)
                                    
                                    # Wait for user confirmation with clear instructions
                                    print("\n🔴 CONFIRMATION REQUIRED:")
                                    print("   - Press ENTER to send this message")
                                    print("   - Type 'skip' to cancel and skip this message")
                                    print("   - Type 'exit' to stop the automation")
                                    
                                    while True:
                                        try:
                                            user_input = input("\n👉 Your choice: ").strip().lower()
                                            if user_input == "":
                                                # User pressed ENTER - send message
                                                break
                                            elif user_input in ['skip', 's']:
                                                # User wants to skip
                                                print("⏭️ Message sending skipped by user")
                                                return  # Exit the function
                                            elif user_input in ['exit', 'quit', 'stop']:
                                                # User wants to stop automation
                                                print("🛑 Automation stopped by user")
                                                exit()
                                            else:
                                                print("❌ Invalid input. Please press ENTER to send, type 'skip' to skip, or 'exit' to stop.")
                                        except KeyboardInterrupt:
                                            print("\n🛑 Automation interrupted by user")
                                            exit()
                                    
                                    # User pressed ENTER - proceed with sending
                                    print("📤 Sending message...")
                                    
                                    # Ensure the input field is focused
                                    message_input.first.click()
                                    self.page.wait_for_timeout(300)
                                    
                                    # Send the message by pressing Enter
                                    try:
                                        message_input.first.press("Enter")
                                        print("✅ Message sent successfully!")
                                        
                                        # Wait to see the result and ensure message is sent
                                        self.page.wait_for_timeout(2000)
                                        
                                    except Exception as send_error:
                                        print(f"❌ Error sending message with Enter: {send_error}")
                                        
                                        # Fallback: Try using keyboard directly
                                        try:
                                            print("🔄 Trying fallback method with keyboard...")
                                            self.page.keyboard.press("Enter")
                                            print("✅ Message sent with fallback method!")
                                            self.page.wait_for_timeout(2000)
                                        except Exception as keyboard_error:
                                            print(f"❌ Fallback method also failed: {keyboard_error}")
                                            traceback.print_exc()
                                        
                                except Exception as e:
                                    print(f"❌ Message insertion failed: {e}")
                            else:
                                print("❌ Message input element not found with any selector")
                                # Debug: Print available elements
                                try:
                                    elements = self.page.evaluate('''
                                        () => {
                                            const contentEditables = document.querySelectorAll('[contenteditable="true"]');
                                            const textareas = document.querySelectorAll('textarea');
                                            const inputs = document.querySelectorAll('input[type="text"]');
                                            
                                            return {
                                                contentEditables: Array.from(contentEditables).map(el => ({
                                                    tagName: el.tagName,
                                                    className: el.className,
                                                    ariaLabel: el.getAttribute('aria-label'),
                                                    placeholder: el.placeholder
                                                })),
                                                textareas: Array.from(textareas).map(el => ({
                                                    tagName: el.tagName,
                                                    className: el.className,
                                                    placeholder: el.placeholder
                                                })),
                                                inputs: Array.from(inputs).map(el => ({
                                                    tagName: el.tagName,
                                                    className: el.className,
                                                    placeholder: el.placeholder
                                                }))
                                            };
                                        }
                                    ''')
                                    print("📋 Available input elements:")
                                    print(json.dumps(elements, indent=2))
                                except:
                                    pass
                                    
                        except Exception as e:
                            print(f"❌ Error inserting message: {str(e)}")
                            traceback.print_exc()
                        # Print the generated response
                        if response_data and 'ai_response' in response_data:
                            ai_response = response_data['ai_response']
                            print("\n" + "="*50)
                            print("🤖 GENERATED RESPONSE:")
                            print("="*50)
                            
                            if ai_response.get('generated_message'):
                                print(f"💬 Message: {ai_response['generated_message']}")
                            else:
                                print("❌ No message generated")
                            
                            if ai_response.get('reasoning'):
                                print(f"\n🧠 Reasoning: {ai_response['reasoning']}")
                            
                            if ai_response.get('usage'):
                                print(f"\n📊 Usage: {ai_response['usage']}")
                            
                            if ai_response.get('error'):
                                print(f"\n❌ Error: {ai_response['error']}")
                            
                            print("="*50)
                        else:
                            print("\n❌ No AI response generated")
                else:
                    print("=== NOTHING TO RESPONDE TO ===")
            
        except Exception as e:
            print(f"Error processing chat {chat_index}: {str(e)}")
            traceback.print_exc()
        finally:
            self.page.wait_for_timeout(1000)
    
    def _process_existing_conversation(self, partner_name: str, partner_username: str, existing_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process an existing conversation with incremental updates"""
        try:
            if isinstance(existing_data, list) and existing_data:
                last_message = existing_data[-1]
                print("Last message in existing data:")
                print(json.dumps(last_message, indent=2, ensure_ascii=False))
                
                # Scroll to the date of the last message
                print(f"      📍 DATE SCROLL: About to scroll to date {last_message['date']}")
                from .browser_utils import get_scroll_container
                scroll_container = get_scroll_container(self.page)
                if scroll_container:
                    pre_date_scroll = scroll_container.evaluate("el => el.scrollTop")
                    scroll_to_date(self.page, last_message['date'])
                    post_date_scroll = scroll_container.evaluate("el => el.scrollTop")
                    print(f"      📍 DATE SCROLL DELTA (container): {post_date_scroll - pre_date_scroll} pixels")
                else:
                    pre_date_scroll = self.page.evaluate("window.scrollY || document.documentElement.scrollTop")
                    scroll_to_date(self.page, last_message['date'])
                    post_date_scroll = self.page.evaluate("window.scrollY || document.documentElement.scrollTop")
                    print(f"      📍 DATE SCROLL DELTA (window fallback): {post_date_scroll - pre_date_scroll} pixels")
                date_scroll_delta = post_date_scroll - pre_date_scroll
                print(f"      📍 DATE SCROLL DELTA: {date_scroll_delta} pixels ({'UP' if date_scroll_delta < 0 else 'DOWN' if date_scroll_delta > 0 else 'NO CHANGE'})")
                
                # Scroll down slightly to ensure we're positioned after the date marker
                # This helps ensure we capture the actual message area, not just the date break
                print("      📍 POSITION ADJUSTMENT: Scrolling down to position after date marker")
                from .browser_utils import get_scroll_container
                scroll_container = get_scroll_container(self.page)
                if scroll_container:
                    scroll_container.evaluate("el => el.scrollTop += 300")  # Scroll down 300px in container
                    print("      📍 POSITION ADJUSTMENT: Used container scrolling")
                else:
                    self.page.evaluate("window.scrollBy(0, 300)")  # Fallback to window scrolling
                    print("      📍 POSITION ADJUSTMENT: Used window scrolling (fallback)")
                self.page.wait_for_timeout(1000)  # Wait for positioning
                
                # Extract new messages (skip progressive scroll since we're positioned at target date)
                new_messages = initial_messages_extraction(
                    self.page, self.main_username, partner_name, partner_username, last_message, 
                    skip_progressive_scroll=True
                )
                
                if new_messages:
                    print(f"Extracted {len(new_messages)} new messages")
                    print(json.dumps(new_messages, indent=2, ensure_ascii=False))
                    
                    # Save merged messages and return the updated list
                    updated_messages = save_merged_messages(partner_username, new_messages)
                    return updated_messages if updated_messages else existing_data
                else:
                    print("No new messages found")
                    return existing_data
            else:
                print("Existing data found but empty")
                return []
                
        except Exception as e:
            print(f"Error during incremental extraction: {e}")
            traceback.print_exc()
            return existing_data if existing_data else []
    
    def _process_new_conversation(self, partner_name: str, partner_username: str) -> List[Dict[str, Any]]:
        """Process a new conversation from the beginning"""
        try:
            print("No existing data found - performing initial extraction")
            
            # Scroll to the beginning of the chat
            print(f"      📍 START SCROLL: About to scroll to start of chat")
            pre_start_scroll = self.page.evaluate("window.scrollY || document.documentElement.scrollTop")
            scroll_till_start_open_chat(self.page)
            post_start_scroll = self.page.evaluate("window.scrollY || document.documentElement.scrollTop")
            start_scroll_delta = post_start_scroll - pre_start_scroll
            print(f"      📍 START SCROLL DELTA: {start_scroll_delta} pixels ({'UP' if start_scroll_delta < 0 else 'DOWN' if start_scroll_delta > 0 else 'NO CHANGE'})")
            
            # Extract all messages (use progressive scroll for complete extraction)
            messages = initial_messages_extraction(
                self.page, self.main_username, partner_name, partner_username, 
                skip_progressive_scroll=False
            )
            
            if messages:
                print(f"Extracted {len(messages)} initial messages")
                save_initial_messages(partner_username, messages)
                return messages
            else:
                print("No messages extracted from new conversation")
                return []
                
        except Exception as e:
            print(f"Error during initial extraction: {e}")
            traceback.print_exc()
            return []
    
    def _generate_response(self, partner_username: str, all_messages: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Generate a response using multi-step conversation analysis"""
        try:
            print(f"\n[MULTI-STEP RESPONSE] Generating response for {partner_username}")
            
            # Ensure we have messages to work with
            if not all_messages:
                print("[WARNING] No messages available for response generation")
                return {}
            
            print(f"[PROCESSING] {len(all_messages)} total messages available")
            
            # Get our information
            our_data = get_our_information()
            user_data = get_user_information(partner_username)
            
            # STEP 1: Comprehensive Conversation Analysis
            print("\n[STEP 1] Analyzing conversation state...")
            conversation_analysis = self._analyze_conversation_state(
                all_messages, our_data, user_data
            )
            
            print(f"[ANALYSIS RESULT] {conversation_analysis}")
            
            # STEP 2: Context Optimization 
            print("\n[STEP 2] Optimizing context...")
            optimized_context = self._optimize_conversation_context(
                all_messages, conversation_analysis
            )
            
            print(f"[CONTEXT] Using {len(optimized_context['messages'])} messages, strategy: {optimized_context['strategy']}")
            
            # STEP 3: Generate Response with Specialized Prompt
            print(f"\n[STEP 3] Generating {conversation_analysis['response_type']} response...")
            response_data = self._generate_specialized_response(
                conversation_analysis, optimized_context, our_data, user_data, partner_username
            )
            
            print("[SUCCESS] Multi-step response generated")
            
            # Save analysis and response data
            self._save_analysis_data(partner_username, conversation_analysis, optimized_context, response_data)
            
            return response_data
            
        except Exception as e:
            print(f"[ERROR] Error in multi-step response generation: {e}")
            traceback.print_exc()
            return {}
    
    def _call_deepseek_with_prompt(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call DeepSeek API with the generated JSON prompt"""
        try:
            print("[DEEPSEEK] Calling DeepSeek API with optimized prompt...")
            
            # Create DeepSeek client
            client = create_client_from_env()
            
            # Build a more focused prompt instead of sending the entire JSON
            # conversation_history = response_data.get('conversation_history', [])
            # partner_context = response_data.get('partner_context', {})
            # your_context = response_data.get('your_context', {})
            
            # Create a concise prompt
            # prompt = self._build_optimized_prompt(conversation_history, partner_context, your_context)
            
            # Generate response using AI provider
            result = ask_ai_provider(json.dumps(response_data).replace(' - ', ', '))
            
            print(f"[DEEPSEEK] API call result: {result}")
            
            if result['success']:
                # Extract message from the content
                content = result['content']
                message = content
                
                # Try to parse JSON from the content if it looks like JSON
                try:
                    if content.strip().startswith('{') and content.strip().endswith('}'):
                        parsed_json = json.loads(content)
                        if 'message' in parsed_json:
                            message = parsed_json['message']
                        elif 'response_message' in parsed_json:
                            message = parsed_json['response_message']
                    else:
                        # Try to extract JSON from markdown code block
                        import re
                        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                        if json_match:
                            parsed_json = json.loads(json_match.group(1))
                            if 'message' in parsed_json:
                                message = parsed_json['message']
                            elif 'response_message' in parsed_json:
                                message = parsed_json['response_message']
                except json.JSONDecodeError:
                    # If parsing fails, use the content as-is
                    message = content
                
                return {
                    'generated_message': message,
                    'reasoning': None,
                    'usage': result.get('usage', {}),
                    'success': True
                }
            else:
                return {
                    'generated_message': None,
                    'reasoning': None,
                    'usage': None,
                    'error': result.get('error', 'Unknown error'),
                    'success': False
                }
            
        except Exception as e:
            print(f"[ERROR] Error calling DeepSeek API: {e}")
            traceback.print_exc()
            return {
                'generated_message': None,
                'reasoning': None,
                'usage': None,
                'error': str(e),
                'success': False
            }
    
    def _build_optimized_prompt(self, conversation_history: List[Dict[str, Any]], partner_context: Dict[str, Any], your_context: Dict[str, Any]) -> str:
        """Build an optimized prompt for DeepSeek API"""
        
        # Handle None values with proper defaults
        partner_context = partner_context or {}
        your_context = your_context or {}
        conversation_history = conversation_history or []
        
        # Extract key information
        partner_name = partner_context.get('name', 'Unknown')
        partner_interests = partner_context.get('interests', [])
        partner_location = partner_context.get('living_locations', 'Unknown')
        
        # Get recent conversation (last 10 messages)
        recent_messages = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
        
        # Build conversation context
        conversation_text = ""
        for msg in recent_messages:
            sender = "You" if msg.get('sent_by') == 'kaila_mentari_' else partner_name
            content = msg.get('content', '')
            conversation_text += f"{sender}: {content}\n"
        
        # Build the optimized prompt
        prompt = f"""You are kaila_mentari_, responding to {partner_name} on Instagram DM.

PERSONA: Warm, casual companion building trust through natural conversation. Instagram DM style: personal but not intrusive, casual with contractions, max 3 sentences, one emoji max when organic, NO hyphens/em-dashes, mirror user's communication rhythm.

PARTNER INFO:
- Name: {partner_name}
- Location: {partner_location}
- Interests: {', '.join(partner_interests) if partner_interests else 'None provided'}

RECENT CONVERSATION:
{conversation_text}

RULES:
1. Respond naturally as kaila_mentari_
2. Keep it casual and warm like texting a friend
3. 1-3 sentences max
4. Address any questions in the last message
5. Never agree to send pictures/videos
6. Don't mention being AI or non-human
7. No concrete meeting plans or dates
8. Output ONLY the message text, no JSON or formatting

Generate your response:"""

        return prompt
    
    def _save_response_json(self, partner_username: str, response_data: Dict[str, Any]) -> None:
        """Save the response JSON to a file for external processing"""
        try:
            # Create responses directory
            responses_dir = os.path.join(config.DATA_DIR, "responses")
            os.makedirs(responses_dir, exist_ok=True)
            
            # Create filename with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{partner_username}_{timestamp}_response.json"
            filepath = os.path.join(responses_dir, filename)
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            
            print(f"[SAVED] Response JSON saved to: {filepath}")
            
        except Exception as e:
            print(f"[ERROR] Could not save response JSON: {e}")
    
    def _build_response_json(self, conversation_history: List[Dict[str, Any]], our_data: Optional[Dict[str, Any]], user_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build the response JSON object with enhanced prompting for natural, quality responses"""
        
        # Import timezone handling
        from datetime import datetime
        import pytz
        
        # Get current Bali time
        bali_tz = pytz.timezone('Asia/Makassar')  # Bali timezone (UTC+8)
        bali_now = datetime.now(bali_tz)
        bali_time_info = {
            "day": bali_now.strftime("%A"),
            "time": bali_now.strftime("%H:%M"),
            "date": bali_now.strftime("%Y-%m-%d")
        }
        
        # Calculate partner's time if timezone difference is available
        partner_time_info = None
        if user_data and "living_locations_time_difference_to_bali_time" in user_data:
            try:
                time_diff = user_data["living_locations_time_difference_to_bali_time"]
                if isinstance(time_diff, (int, float)):
                    from datetime import timedelta
                    partner_time = bali_now + timedelta(hours=time_diff)
                    partner_time_info = {
                        "day": partner_time.strftime("%A"),
                        "time": partner_time.strftime("%H:%M"),
                        "date": partner_time.strftime("%Y-%m-%d"),
                        "timezone_difference": f"{'+' if time_diff >= 0 else ''}{time_diff} hours from Bali"
                    }
            except Exception as e:
                print(f"Warning: Could not calculate partner time: {e}")
                partner_time_info = None
        
        # Calculate time since last message
        hours_since_last_message = None
        if conversation_history and len(conversation_history) > 0:
            try:
                last_message = conversation_history[-1]
                if 'date' in last_message:
                    last_message_date_str = last_message['date']
                    last_message_date = datetime.strptime(last_message_date_str, "%d.%m.%Y %H:%M")
                    last_message_date_bali = bali_tz.localize(last_message_date)
                    time_difference_seconds = (bali_now - last_message_date_bali).total_seconds()
                    hours_since_last_message = time_difference_seconds / 3600
                    print(f"[TIME CALC] Last message: {last_message_date_str}, Hours since: {hours_since_last_message:.2f}")
            except Exception as e:
                print(f"Warning: Could not calculate time since last message: {e}")
                hours_since_last_message = None
        
        # Calculate delay category
        if hours_since_last_message is None:
            calculated_delay_category = "unknown"
        elif 0 <= hours_since_last_message < 24:
            calculated_delay_category = "short"
        elif 24 <= hours_since_last_message <= 48:
            calculated_delay_category = "medium"
        elif hours_since_last_message > 48:
            calculated_delay_category = "long"
        else:
            calculated_delay_category = "unknown"
        
        # Build enhanced response JSON structure
        response_json = {
            "system_identity": "You are kaila_mentari_, a warm, authentic person having natural conversations on Instagram DM. You communicate like a genuine friend - engaging, thoughtful, and naturally expressive.",
            
            "core_mission": "Generate responses that feel completely natural and fit seamlessly into the conversation flow. Focus on quality, authenticity, and genuine connection over artificial constraints.",
            
            "conversation_context": {
                "partner_info": user_data,
                "your_info": our_data,
                "message_history": conversation_history,
                "current_time_bali": bali_time_info,
                "partner_time": partner_time_info,
                "hours_since_last_message": hours_since_last_message,
                "delay_category": calculated_delay_category
            },
            
            "response_guidelines": {
                "primary_focus": [
                    "CRITICAL: The LAST message in conversation_history is what you MUST respond to - ignore all previous messages unless they provide necessary context",
                    "If the last message is a goodbye ('cya', 'talk soon', 'bye'), respond appropriately to that goodbye",
                    "If the last message asks a question, answer that specific question",
                    "If the last message makes a statement, acknowledge and respond to that statement",
                    "DO NOT bring up topics from earlier in the conversation unless the last message specifically references them",
                    "Read and understand the full conversation context, but respond ONLY to the most recent message",
                    "Generate responses that feel natural and unforced",
                    "Match the emotional tone and energy of the LAST message",
                    "Be genuinely interested in the person you're talking to"
                ],
                
                "authenticity_principles": [
                    "Write as if you're texting a friend you care about",
                    "Use natural speech patterns and conversational flow",
                    "Show genuine interest and curiosity",
                    "Be warm and engaging without being overwhelming",
                    "Let your personality shine through naturally"
                ],
                
                "conversation_flow": [
                    "Acknowledge what they've shared before adding your own thoughts",
                    "Ask follow-up questions that show you're truly listening",
                    "Share relevant experiences or thoughts when appropriate",
                    "Keep the conversation moving forward naturally",
                    "Respond to their emotional state and energy level"
                ],
                
                "style_notes": [
                    "Use contractions and casual language (I'm, you're, can't, etc.)",
                    "Vary your sentence structure naturally", 
                    "Include appropriate emojis when they add to the message (not required)",
                    "Write in a way that sounds like spoken conversation",
                    "Don't be afraid to use sentence fragments or casual punctuation",
                    "CRITICAL: NEVER use hyphens (-) or em-dashes (—) in your response - use commas or periods instead"
                ],
                
                "timing_awareness": {
                    "short_delay": "0-24 hours: Respond naturally without mentioning time",
                    "medium_delay": "24-48 hours: Brief casual acknowledgment if appropriate", 
                    "long_delay": "48+ hours: Consider if conversation needs restarting",
                    "very_long_delay": "7+ days: Definitely needs conversation restart",
                    "current_delay": f"{calculated_delay_category} ({hours_since_last_message:.1f} hours)" if hours_since_last_message else "unknown"
                },
                
                "conversation_flow_analysis": {
                    "break_indicators": [
                        "Last exchange was goodbyes ('bye', 'cya', 'talk soon', etc.)",
                        "Long time gap (48+ hours) since last message", 
                        "Conversation ended naturally with closing statements",
                        "Short responses that didn't continue the topic",
                        "One-word responses or just emojis as last messages"
                    ],
                    "continuation_indicators": [
                        "Recent active conversation (under 24 hours)",
                        "Last message was a question waiting for answer",
                        "Ongoing topic discussion that wasn't concluded",
                        "Last message showed engagement and interest"
                    ]
                }
            },
            
            "quality_standards": {
                "engagement_level": "HIGH - Show genuine interest and investment in the conversation",
                "naturalness": "MAXIMUM - Sound like a real person, not an AI or template",
                "context_awareness": "COMPLETE - Reference and build upon previous messages appropriately",
                "emotional_intelligence": "STRONG - Pick up on and respond to emotional cues",
                "conversation_advancement": "ALWAYS - Move the conversation forward in meaningful ways"
            },
            
            "conversation_restart_logic": {
                "CRITICAL_DECISION": "Determine if this needs a CONVERSATION RESTART or a DIRECT RESPONSE",
                "restart_triggers": [
                    f"Time gap over 48 hours ({hours_since_last_message:.1f} hours)" if hours_since_last_message and hours_since_last_message > 48 else None,
                    "Last message was a goodbye that ended the conversation",
                    "Conversation flow was clearly interrupted or concluded",
                    "Multiple short/cold responses in a row"
                ],
                "restart_needed": hours_since_last_message is not None and hours_since_last_message > 48,
                "opening_message_guidelines": {
                    "acknowledge_gap": "Briefly acknowledge time passed if appropriate",
                    "fresh_energy": "Bring new positive energy to restart conversation",
                    "reference_connection": "Reference something from your history together",
                    "provide_hook": "Give them something interesting to respond to",
                    "examples": [
                        "Hey Mark! Hope you're having a good week 😊 Just saw something that reminded me of those beautiful photos you take",
                        "Hi there! Been thinking about our chat the other day, how's everything going?",
                        "Good morning Mark! ✨ Hope your photography adventures are going well"
                    ]
                }
            },
            
            "last_message_analysis": {
                "MANDATORY_STEP": "Before writing ANY response, identify what the LAST message says and its type",
                "message_types": {
                    "goodbye": "Messages like 'cya', 'bye', 'talk soon', 'see you later' - usually indicates conversation break",
                    "question": "Direct questions that need specific answers", 
                    "statement": "Comments or observations that need acknowledgment",
                    "share": "Sharing photos, music, experiences - respond to what was shared",
                    "compliment": "Praise or nice comments - acknowledge gracefully"
                },
                "response_rule": "Your response must directly address the TYPE and CONTENT of the last message OR restart conversation if appropriate"
            },
            
            "content_generation_process": [
                "1. CHECK TIME: How long since the last message? Is restart_needed = true?",
                "2. ANALYZE FLOW: Was the last message a goodbye or conversation ender?",
                "3. DECIDE: Does this need a CONVERSATION RESTART or DIRECT RESPONSE?",
                "4a. IF RESTART NEEDED: Generate fresh opening message with new energy",
                "4b. IF DIRECT RESPONSE: Address the last message directly", 
                "5. REFINE: Ensure it sounds natural and appropriate for the situation"
            ],
            
            "punctuation_rules": {
                "ABSOLUTELY_FORBIDDEN": [
                    "- (hyphen)",
                    "— (em-dash)", 
                    "– (en-dash)"
                ],
                "ALLOWED_PUNCTUATION": [
                    ". (period)",
                    ", (comma)",
                    "? (question mark)",
                    "! (exclamation mark)",
                    "' (apostrophe for contractions)"
                ],
                "ENFORCEMENT": "If your response contains ANY hyphens or dashes, it will be rejected. Use commas or periods to separate thoughts instead."
            },
            
            "safety_boundaries": {
                "authenticity": "Never reveal AI nature or break character as kaila_mentari_",
                "media_sharing": "Politely decline requests to send photos/videos",
                "personal_safety": "Don't share specific location details or contact information", 
                "meeting_plans": "Keep future meeting discussions theoretical and non-specific",
                "relationship_pace": "Let connections develop naturally without rushing"
            },
            
            "output_format": "Return only a JSON object with a 'message' field containing your response. No additional formatting or explanation needed.",
            
            "FINAL_CRITICAL_INSTRUCTION": {
                "decision_point": f"TIME GAP: {hours_since_last_message:.1f} hours - RESTART NEEDED: {hours_since_last_message is not None and hours_since_last_message > 48}" if hours_since_last_message else "TIME GAP: unknown",
                "primary_logic": [
                    "IF restart_needed = true OR last message was goodbye: Generate opening message to restart conversation",
                    "IF restart_needed = false AND recent conversation: Respond directly to last message"
                ],
                "restart_scenario": {
                    "when": "Long gaps (48+ hours) or after goodbyes",
                    "approach": "Fresh greeting + connection reference + conversation hook",
                    "example": "Hey! Hope you're doing well ✨ Been thinking about those amazing photos you shared, any new adventures lately?"
                },
                "direct_response_scenario": {
                    "when": "Recent active conversation",
                    "approach": "Direct reply to their last message content"
                },
                "enforcement": "Choose the right approach based on timing and conversation flow",
                "style_reminder": "No hyphens (-) or dashes (—, –) allowed - use commas or periods instead"
            },
            
            "final_instruction": "Generate a response that directly addresses the LAST message only. Be natural, engaging, and contextually appropriate. Focus on quality and authenticity while responding specifically to what they just said."
        }
        
        return response_json
    
    def _analyze_conversation_state(self, all_messages: List[Dict[str, Any]], our_data: Optional[Dict[str, Any]], user_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """STEP 1: Comprehensive conversation state analysis"""
        from datetime import datetime
        import pytz
        
        # Get Bali time for calculations
        bali_tz = pytz.timezone('Asia/Makassar')
        bali_now = datetime.now(bali_tz)
        
        # Get last message and timing
        last_message = all_messages[-1] if all_messages else None
        if not last_message:
            return {"error": "No messages to analyze"}
            
        # Calculate time gap
        hours_since_last = None
        if 'date' in last_message:
            try:
                last_date = datetime.strptime(last_message['date'], "%d.%m.%Y %H:%M")
                last_date_bali = bali_tz.localize(last_date)
                time_diff_seconds = (bali_now - last_date_bali).total_seconds()
                hours_since_last = time_diff_seconds / 3600
            except Exception as e:
                print(f"[WARNING] Could not calculate time gap: {e}")
        
        # Analyze timing category
        timing_category = self._categorize_timing(hours_since_last)
        
        # Analyze last message type
        last_message_type = self._categorize_message_type(last_message)
        
        # Analyze conversation flow
        conversation_flow = self._analyze_conversation_flow(all_messages, hours_since_last)
        
        # Determine response strategy
        response_type = self._determine_response_type(timing_category, last_message_type, conversation_flow)
        
        # Calculate partner timezone if available
        partner_timezone_info = self._calculate_partner_timezone(user_data, bali_now)
        
        # Analyze conversation patterns
        conversation_patterns = self._analyze_conversation_patterns(all_messages)
        
        return {
            "last_message": last_message,
            "hours_since_last": hours_since_last,
            "timing_category": timing_category,
            "last_message_type": last_message_type,
            "conversation_flow": conversation_flow,
            "response_type": response_type,
            "partner_timezone": partner_timezone_info,
            "conversation_patterns": conversation_patterns,
            "total_messages": len(all_messages),
            "analysis_timestamp": bali_now.isoformat()
        }
    
    def _categorize_timing(self, hours_since_last: Optional[float]) -> str:
        """Categorize timing for response strategy"""
        if hours_since_last is None:
            return "unknown"
        elif hours_since_last < 1:
            return "immediate"  # 0-1 hours
        elif hours_since_last < 24:
            return "recent"     # 1-24 hours  
        elif hours_since_last < 72:
            return "medium"     # 1-3 days
        elif hours_since_last < 168:
            return "long"       # 3-7 days
        elif hours_since_last < 720:
            return "very_long"  # 7-30 days
        else:
            return "extended"   # 30+ days
    
    def _categorize_message_type(self, message: Dict[str, Any]) -> str:
        """Analyze the type of the last message"""
        msg_content = message.get('message', '')
        # Handle case where message might be a list
        if isinstance(msg_content, list):
            content = ' '.join(str(item) for item in msg_content).lower().strip()
        else:
            content = str(msg_content).lower().strip()
        
        # Check for goodbyes
        goodbye_words = ['bye', 'cya', 'see ya', 'see you', 'talk soon', 'later', 'ttyl', 'goodbye', 'good bye', 'alright -', 'okay -']
        if any(word in content for word in goodbye_words):
            return "goodbye"
        
        # Check for questions
        if '?' in content or content.startswith(('what', 'how', 'why', 'when', 'where', 'who', 'which', 'do you', 'did you', 'have you', 'are you', 'can you', 'would you', 'will you')):
            return "question"
        
        # Check for greetings
        greeting_words = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'morning', 'afternoon', 'evening']
        if any(word in content for word in greeting_words):
            return "greeting"
        
        # Check for media shares
        if message.get('media_attached_img') or 'clip' in content.lower():
            return "media_share"
        
        # Check for compliments
        compliment_words = ['beautiful', 'amazing', 'gorgeous', 'lovely', 'wonderful', 'perfect', 'great', 'awesome', 'incredible', 'stunning']
        if any(word in content for word in compliment_words):
            return "compliment"
        
        # Check for brief responses
        brief_responses = ['ok', 'okay', 'lol', 'haha', 'yeah', 'yes', 'no', 'sure', 'cool', 'nice', 'wow', 'oh']
        if content in brief_responses or len(content) < 10:
            return "brief"
        
        # Check for emotional expressions
        emotional_words = ['love', 'hate', 'excited', 'happy', 'sad', 'angry', 'worried', 'nervous', 'thrilled', 'disappointed']
        if any(word in content for word in emotional_words):
            return "emotional"
        
        # Check for activity sharing
        activity_words = ['just', 'currently', 'right now', 'today i', 'yesterday i', 'going to', 'about to']
        if any(word in content for word in activity_words):
            return "activity_share"
        
        # Check for invitations
        invitation_words = ['want to', 'would you like', 'let\'s', 'we should', 'how about', 'interested in']
        if any(word in content for word in invitation_words):
            return "invitation"
        
        # Default to statement
        return "statement"
    
    def _analyze_conversation_flow(self, all_messages: List[Dict[str, Any]], hours_since_last: Optional[float]) -> str:
        """Analyze the overall conversation flow state"""
        if len(all_messages) < 2:
            return "new"
        
        last_message = all_messages[-1]
        
        # Check if conversation was concluded
        if self._categorize_message_type(last_message) == "goodbye":
            return "concluded"
        
        # Check for very long gaps
        if hours_since_last and hours_since_last > 168:  # 7 days
            return "dormant"
        
        # Analyze recent message patterns
        recent_messages = all_messages[-5:] if len(all_messages) >= 5 else all_messages
        
        # Count brief responses in recent messages
        brief_count = sum(1 for msg in recent_messages if len(msg.get('message', '')) < 15)
        if brief_count >= 3:
            return "fading"
        
        # Check for active conversation (multiple exchanges recently)
        kaila_recent = sum(1 for msg in recent_messages if msg.get('sent_by') == 'kaila_mentari_')
        partner_recent = len(recent_messages) - kaila_recent
        
        if kaila_recent >= 2 and partner_recent >= 2:
            return "active"
        
        # Check for interrupted conversation (sudden stop)
        if hours_since_last and hours_since_last > 48 and len(all_messages[-1].get('message', '')) > 20:
            return "interrupted"
        
        # Default to active for recent messages
        if hours_since_last and hours_since_last < 24:
            return "active"
        
        return "interrupted"
    
    def _determine_response_type(self, timing_category: str, message_type: str, conversation_flow: str) -> str:
        """Determine the type of response needed"""
        
        # Handle dormant conversations
        if conversation_flow == "dormant" or timing_category == "extended":
            return "revival_opener"
        
        # Handle concluded conversations
        if conversation_flow == "concluded" and timing_category in ["medium", "long", "very_long"]:
            return "new_opener" 
        
        # Handle immediate goodbyes (just said goodbye)
        if message_type == "goodbye" and timing_category == "immediate":
            return "farewell"
        
        # Handle conversation restarts after gaps
        if timing_category in ["long", "very_long"] or conversation_flow in ["interrupted", "fading"]:
            return "restart_opener"
        
        # Handle direct responses for active conversations
        if conversation_flow == "active" and timing_category in ["immediate", "recent"]:
            if message_type == "question":
                return "direct_answer"
            elif message_type == "compliment":
                return "gracious_acknowledgment"
            elif message_type == "media_share":
                return "media_response"
            elif message_type == "greeting":
                return "greeting_response"
            elif message_type == "invitation":
                return "invitation_response"
            else:
                return "conversational_response"
        
        # Handle medium delays
        if timing_category == "medium":
            return "casual_reconnect"
        
        # Default to conversational response
        return "conversational_response"
    
    def _calculate_partner_timezone(self, user_data: Optional[Dict[str, Any]], bali_now: datetime) -> Optional[Dict[str, Any]]:
        """Calculate partner's current time and timezone info"""
        if not user_data or "living_locations_time_difference_to_bali_time" not in user_data:
            return None
            
        try:
            time_diff = user_data["living_locations_time_difference_to_bali_time"]
            if isinstance(time_diff, (int, float)):
                from datetime import timedelta
                partner_time = bali_now + timedelta(hours=time_diff)
                
                return {
                    "current_time": partner_time.strftime("%H:%M"),
                    "current_day": partner_time.strftime("%A"),
                    "current_date": partner_time.strftime("%Y-%m-%d"),
                    "time_difference": f"{'+' if time_diff >= 0 else ''}{time_diff} hours from Bali",
                    "is_morning": 6 <= partner_time.hour <= 11,
                    "is_afternoon": 12 <= partner_time.hour <= 17,
                    "is_evening": 18 <= partner_time.hour <= 22,
                    "is_night": partner_time.hour >= 23 or partner_time.hour <= 5
                }
        except Exception as e:
            print(f"[WARNING] Could not calculate partner timezone: {e}")
        
        return None
    
    def _analyze_conversation_patterns(self, all_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in the conversation for better context"""
        if not all_messages:
            return {}
        
        # Count message distribution
        kaila_messages = [msg for msg in all_messages if msg.get('sent_by') == 'kaila_mentari_']
        partner_messages = [msg for msg in all_messages if msg.get('sent_by') != 'kaila_mentari_']
        
        # Find common topics/keywords
        all_content = ' '.join([msg.get('message', '') for msg in all_messages if isinstance(msg.get('message'), str)])
        
        # Analyze recent interaction style
        recent_messages = all_messages[-10:] if len(all_messages) >= 10 else all_messages
        avg_message_length = sum(len(msg.get('message', '')) for msg in recent_messages) / len(recent_messages)
        
        # Check for media sharing
        media_messages = [msg for msg in all_messages if msg.get('media_attached_img')]
        
        return {
            "total_exchanges": len(all_messages),
            "kaila_message_count": len(kaila_messages),
            "partner_message_count": len(partner_messages),
            "avg_message_length": avg_message_length,
            "media_shared_count": len(media_messages),
            "conversation_length_days": self._calculate_conversation_span(all_messages),
            "interaction_style": "verbose" if avg_message_length > 50 else "concise"
        }
    
    def _calculate_conversation_span(self, all_messages: List[Dict[str, Any]]) -> Optional[int]:
        """Calculate how many days the conversation has been going"""
        if len(all_messages) < 2:
            return 0
            
        try:
            first_date = datetime.strptime(all_messages[0]['date'], "%d.%m.%Y %H:%M")
            last_date = datetime.strptime(all_messages[-1]['date'], "%d.%m.%Y %H:%M")
            return (last_date - first_date).days
        except:
            return None
    
    def _optimize_conversation_context(self, all_messages: List[Dict[str, Any]], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """STEP 2: Optimize context based on response type and conversation state"""
        
        response_type = analysis.get('response_type', 'conversational_response')
        timing_category = analysis.get('timing_category', 'recent')
        conversation_patterns = analysis.get('conversation_patterns', {})
        
        # Define context strategies based on response type
        if response_type in ['revival_opener', 'new_opener']:
            # For conversation restarts, need broader context to reference shared history
            context_messages = self._get_historical_context(all_messages, 15)
            strategy = "historical_context"
            
        elif response_type == 'restart_opener':
            # For restarting after interruption, focus on last active exchange
            context_messages = self._get_recent_active_context(all_messages, 8)
            strategy = "recent_active"
            
        elif response_type in ['direct_answer', 'media_response', 'gracious_acknowledgment']:
            # For direct responses, focus on immediate context
            context_messages = self._get_immediate_context(all_messages, 5)
            strategy = "immediate_focus"
            
        elif response_type == 'farewell':
            # For farewells, minimal context needed
            context_messages = all_messages[-2:] if len(all_messages) >= 2 else all_messages
            strategy = "minimal_context"
            
        elif response_type == 'casual_reconnect':
            # For medium delays, balanced context
            context_messages = self._get_balanced_context(all_messages, 10)
            strategy = "balanced_context"
            
        else:
            # Default conversational response
            context_messages = self._get_conversational_context(all_messages, 7, analysis)
            strategy = "conversational_flow"
        
        # Ensure we always include the last message
        if context_messages and all_messages:
            last_message = all_messages[-1]
            if last_message not in context_messages:
                context_messages.append(last_message)
        
        return {
            "messages": context_messages,
            "strategy": strategy,
            "context_length": len(context_messages),
            "optimization_reasoning": self._explain_context_choice(response_type, strategy, len(context_messages))
        }
    
    def _get_historical_context(self, all_messages: List[Dict[str, Any]], max_messages: int) -> List[Dict[str, Any]]:
        """Get diverse historical context for conversation revival"""
        if len(all_messages) <= max_messages:
            return all_messages
            
        # Strategy: Get early messages + some middle + recent
        early_messages = all_messages[:3]
        middle_start = len(all_messages) // 2
        middle_messages = all_messages[middle_start:middle_start + 3]
        recent_messages = all_messages[-(max_messages-6):] if max_messages > 6 else all_messages[-2:]
        
        # Combine and remove duplicates while preserving order
        combined = early_messages + middle_messages + recent_messages
        seen = set()
        result = []
        for msg in combined:
            msg_id = f"{msg.get('date', '')}{msg.get('message', '')}"
            if msg_id not in seen:
                seen.add(msg_id)
                result.append(msg)
                
        return result[:max_messages]
    
    def _get_recent_active_context(self, all_messages: List[Dict[str, Any]], max_messages: int) -> List[Dict[str, Any]]:
        """Get context from the most recent active conversation period"""
        if len(all_messages) <= max_messages:
            return all_messages
            
        # Find the last active conversation period by looking for message clusters
        return all_messages[-max_messages:]
    
    def _get_immediate_context(self, all_messages: List[Dict[str, Any]], max_messages: int) -> List[Dict[str, Any]]:
        """Get immediate context for direct responses"""
        return all_messages[-max_messages:] if all_messages else []
    
    def _get_balanced_context(self, all_messages: List[Dict[str, Any]], max_messages: int) -> List[Dict[str, Any]]:
        """Get balanced context for medium-delay responses"""
        if len(all_messages) <= max_messages:
            return all_messages
            
        # Take more from recent messages, but include some earlier context
        recent_count = int(max_messages * 0.7)  # 70% recent
        earlier_count = max_messages - recent_count
        
        recent_messages = all_messages[-recent_count:] if recent_count > 0 else []
        earlier_messages = all_messages[-max_messages:-recent_count] if earlier_count > 0 and len(all_messages) > recent_count else []
        
        return earlier_messages + recent_messages
    
    def _get_conversational_context(self, all_messages: List[Dict[str, Any]], max_messages: int, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get optimized context for conversational flow"""
        if len(all_messages) <= max_messages:
            return all_messages
            
        # Adjust based on conversation patterns
        patterns = analysis.get('conversation_patterns', {})
        interaction_style = patterns.get('interaction_style', 'concise')
        
        if interaction_style == 'verbose':
            # For verbose conversations, we might need more context
            return all_messages[-max_messages:]
        else:
            # For concise conversations, focus on recent exchanges
            return all_messages[-min(max_messages, 5):]
    
    def _explain_context_choice(self, response_type: str, strategy: str, context_length: int) -> str:
        """Explain why this context strategy was chosen"""
        explanations = {
            "historical_context": f"Using {context_length} messages with historical span for conversation revival",
            "recent_active": f"Focusing on {context_length} recent messages from last active period", 
            "immediate_focus": f"Using {context_length} immediate messages for direct response",
            "minimal_context": f"Minimal {context_length} messages for farewell",
            "balanced_context": f"Balanced {context_length} messages for medium-delay reconnection",
            "conversational_flow": f"Conversational {context_length} messages for natural flow"
        }
        return explanations.get(strategy, f"Using {context_length} messages with {strategy} strategy")
    
    def _generate_specialized_response(self, analysis: Dict[str, Any], context: Dict[str, Any], our_data: Optional[Dict[str, Any]], user_data: Optional[Dict[str, Any]], partner_username: str) -> Dict[str, Any]:
        """STEP 3: Generate response using specialized prompt based on analysis"""
        
        response_type = analysis.get('response_type', 'conversational_response')
        
        # Build specialized prompt based on response type
        if response_type == 'revival_opener':
            prompt_data = self._build_revival_opener_prompt(analysis, context, our_data, user_data)
        elif response_type == 'new_opener':
            prompt_data = self._build_new_opener_prompt(analysis, context, our_data, user_data)
        elif response_type == 'restart_opener':
            prompt_data = self._build_restart_opener_prompt(analysis, context, our_data, user_data)
        elif response_type == 'farewell':
            prompt_data = self._build_farewell_prompt(analysis, context, our_data, user_data)
        elif response_type == 'direct_answer':
            prompt_data = self._build_direct_answer_prompt(analysis, context, our_data, user_data)
        elif response_type == 'gracious_acknowledgment':
            prompt_data = self._build_gracious_acknowledgment_prompt(analysis, context, our_data, user_data)
        elif response_type == 'media_response':
            prompt_data = self._build_media_response_prompt(analysis, context, our_data, user_data)
        elif response_type == 'greeting_response':
            prompt_data = self._build_greeting_response_prompt(analysis, context, our_data, user_data)
        elif response_type == 'invitation_response':
            prompt_data = self._build_invitation_response_prompt(analysis, context, our_data, user_data)
        elif response_type == 'casual_reconnect':
            prompt_data = self._build_casual_reconnect_prompt(analysis, context, our_data, user_data)
        else:
            # Default conversational response
            prompt_data = self._build_conversational_response_prompt(analysis, context, our_data, user_data)
        
        # Save prompt data for debugging
        self._save_prompt_data(partner_username, prompt_data)
        
        # Generate AI response
        ai_response = self._call_deepseek_with_prompt(prompt_data)
        
        # CRITICAL: Hard-coded hyphen removal as final safety net
        if ai_response and 'generated_message' in ai_response and ai_response['generated_message']:
            original_message = ai_response['generated_message']
            
            # Replace all types of hyphens and dashes with commas
            cleaned_message = original_message
            cleaned_message = cleaned_message.replace(' - ', ', ')  # Hyphen with spaces
            cleaned_message = cleaned_message.replace('-', ', ')    # Any remaining hyphens
            cleaned_message = cleaned_message.replace(' — ', ', ')  # Em-dash with spaces
            cleaned_message = cleaned_message.replace('—', ', ')    # Any remaining em-dashes
            cleaned_message = cleaned_message.replace(' – ', ', ')  # En-dash with spaces
            cleaned_message = cleaned_message.replace('–', ', ')    # Any remaining en-dashes
            
            # Clean up any double commas or awkward spacing
            cleaned_message = cleaned_message.replace(', ,', ',')
            cleaned_message = cleaned_message.replace(',,', ',')
            cleaned_message = cleaned_message.replace(' ,', ',')
            
            # Update the response if changes were made
            if cleaned_message != original_message:
                print(f"🔧 HYPHEN CLEANUP: Replaced hyphens/dashes with commas")
                print(f"   Original: {original_message}")
                print(f"   Cleaned:  {cleaned_message}")
                ai_response['generated_message'] = cleaned_message
                ai_response['hyphen_cleanup_applied'] = True
            else:
                ai_response['hyphen_cleanup_applied'] = False
        
        from datetime import datetime
        return {
            "analysis": analysis,
            "context": context,
            "prompt_type": response_type,
            "ai_response": ai_response,
            "generation_timestamp": datetime.now().isoformat()
        }
    
    def _build_revival_opener_prompt(self, analysis: Dict[str, Any], context: Dict[str, Any], our_data: Optional[Dict[str, Any]], user_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build prompt for reviving dormant conversations (7+ days or 30+ days)"""
        
        partner_timezone = analysis.get('partner_timezone', {})
        conversation_patterns = analysis.get('conversation_patterns', {})
        
        return {
            "prompt_type": "revival_opener",
            "mission": "Generate a warm, engaging message to revive a dormant conversation. This should feel natural and reference your shared history.",
            
            "situation": {
                "conversation_state": "Dormant - needs revival",
                "time_gap": f"{analysis.get('hours_since_last', 0):.1f} hours since last message",
                "last_interaction": analysis.get('last_message', {}),
                "shared_history_context": context.get('messages', []),
                "partner_timezone": partner_timezone
            },
            
            "your_identity": {
                "name": "kaila_mentari_",
                "personality": "Warm, authentic, naturally curious friend",
                "communication_style": "Casual, caring, genuine interest in people",
                "your_info": our_data
            },
            
            "partner_info": user_data,
            
            "revival_strategy": {
                "approach": "Friendly reconnection with personal touch",
                "elements_to_include": [
                    "Warm greeting appropriate for time gap",
                    "Brief positive acknowledgment of time passed", 
                    "Reference to something from your shared conversation history",
                    "New conversation hook that invites engagement",
                    "Show genuine interest in how they've been"
                ],
                "tone": "Warm but not overwhelming, natural and unforced"
            },
            
            "contextual_awareness": {
                "time_considerations": self._get_time_appropriate_greeting(partner_timezone),
                "conversation_history_highlights": self._extract_conversation_highlights(context.get('messages', [])),
                "shared_interests": self._identify_shared_interests(context.get('messages', []))
            },
            
            "examples": [
                "Hey! Hope you've been doing well ✨ I was just thinking about those amazing sunset photos you shared, have you been on any new photography adventures?",
                "Hi there! It's been a while, hope everything's going great with you 😊 Your travel stories always inspire me, any exciting plans coming up?",
                "Good morning! Was just reminiscing about our chat about that coffee place you love, made me want to try a new spot today. How have you been?"
            ],
            
            "critical_requirements": [
                "Must feel natural and genuine, not forced or scripted",
                "Reference specific shared history without being overwhelming",
                "Provide clear conversation hook for them to respond to",
                "Match appropriate energy level for the time gap",
                "CRITICAL: NEVER use hyphens (-) or dashes (—, –) - use commas or periods instead",
                "Keep it engaging but give them space to respond naturally"
            ],
            
            "HYPHEN_BAN": {
                "ABSOLUTELY_FORBIDDEN": ["- (hyphen)", "— (em-dash)", "– (en-dash)"],
                "USE_INSTEAD": [", (comma)", ". (period)", "and", "or", "but"],
                "ENFORCEMENT": "If your response contains ANY hyphens or dashes, it will be automatically rejected"
            },
            
            "output_format": "Return JSON: {\"message\": \"your_response_here\"}"
        }
    
    def _build_farewell_prompt(self, analysis: Dict[str, Any], context: Dict[str, Any], our_data: Optional[Dict[str, Any]], user_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build prompt for responding to goodbyes"""
        
        last_message = analysis.get('last_message', {})
        
        return {
            "prompt_type": "farewell",
            "mission": "Respond appropriately to their goodbye message with warmth and natural closure.",
            
            "situation": {
                "their_goodbye": last_message.get('message', ''),
                "conversation_context": context.get('messages', [])[-3:],  # Just recent context
                "timing": f"{analysis.get('hours_since_last', 0):.1f} hours ago"
            },
            
            "your_identity": {
                "name": "kaila_mentari_",
                "response_style": "Warm, appreciative, natural"
            },
            
            "farewell_guidelines": [
                "Match their energy level and tone",
                "Keep it brief but warm",
                "Express appreciation for the conversation if appropriate",
                "Use casual, friendly language",
                "Optional: light suggestion of future conversation"
            ],
            
            "examples": [
                "Bye! 😊",
                "Take care Mark! ✨",
                "See you later! Thanks for the lovely chat",
                "Have a great day! 🌸",
                "Catch you soon!"
            ],
            
            "critical_requirements": [
                "Keep it brief and natural",
                "Match their goodbye style", 
                "No overly emotional or clingy responses",
                "CRITICAL: NEVER use hyphens (-) or dashes (—, –) - use commas or periods instead",
                "Sound genuine and warm"
            ],
            
            "HYPHEN_BAN": {
                "ABSOLUTELY_FORBIDDEN": ["- (hyphen)", "— (em-dash)", "– (en-dash)"],
                "USE_INSTEAD": [", (comma)", ". (period)", "and", "or", "but"],
                "ENFORCEMENT": "If your response contains ANY hyphens or dashes, it will be automatically rejected"
            },
            
            "output_format": "Return JSON: {\"message\": \"your_response_here\"}"
        }
    
    def _build_direct_answer_prompt(self, analysis: Dict[str, Any], context: Dict[str, Any], our_data: Optional[Dict[str, Any]], user_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build prompt for answering direct questions"""
        
        last_message = analysis.get('last_message', {})
        partner_timezone = analysis.get('partner_timezone', {})
        
        return {
            "prompt_type": "direct_answer", 
            "mission": "Answer their question directly while keeping conversation flowing naturally.",
            
            "situation": {
                "their_question": last_message.get('message', ''),
                "conversation_context": context.get('messages', []),
                "timing_category": analysis.get('timing_category', 'recent')
            },
            
            "your_identity": {
                "name": "kaila_mentari_",
                "personality": "Helpful, genuine, engaging",
                "your_background": our_data
            },
            
            "partner_info": user_data,
            "partner_timezone": partner_timezone,
            
            "response_strategy": [
                "Answer their question directly and thoroughly", 
                "Add personal touch or related experience if relevant",
                "Keep conversation going with follow-up question or comment",
                "Be authentic and show genuine interest",
                "Match their communication style and energy"
            ],
            
            "critical_requirements": [
                "MUST answer the specific question they asked",
                "Don't be vague or avoid their question",
                "Keep response natural and conversational",
                "CRITICAL: NEVER use hyphens (-) or dashes (—, –) - use commas or periods instead",
                "Show genuine interest in continuing conversation"
            ],
            
            "HYPHEN_BAN": {
                "ABSOLUTELY_FORBIDDEN": ["- (hyphen)", "— (em-dash)", "– (en-dash)"],
                "USE_INSTEAD": [", (comma)", ". (period)", "and", "or", "but"],
                "ENFORCEMENT": "If your response contains ANY hyphens or dashes, it will be automatically rejected"
            },
            
            "output_format": "Return JSON: {\"message\": \"your_response_here\"}"
        }
    
    # Helper functions for prompt building
    def _get_time_appropriate_greeting(self, partner_timezone: Optional[Dict[str, Any]]) -> str:
        """Get time-appropriate greeting based on partner's timezone"""
        if not partner_timezone:
            return "Hello"
            
        if partner_timezone.get('is_morning'):
            return "Good morning"
        elif partner_timezone.get('is_afternoon'): 
            return "Good afternoon"
        elif partner_timezone.get('is_evening'):
            return "Good evening"
        else:
            return "Hey"
    
    def _extract_conversation_highlights(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract interesting topics from conversation history"""
        highlights = []
        
        for msg in messages:
            content = msg.get('message', '')
            if isinstance(content, str) and len(content) > 30:
                # Look for topics like photography, travel, food, hobbies
                topic_keywords = ['photo', 'picture', 'travel', 'trip', 'food', 'coffee', 'music', 'work', 'hobby', 'adventure', 'beautiful', 'amazing']
                if any(keyword in content.lower() for keyword in topic_keywords):
                    highlights.append(content[:100] + "..." if len(content) > 100 else content)
                    
        return highlights[:3]  # Return top 3 highlights
    
    def _identify_shared_interests(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Identify shared interests from conversation"""
        interests = []
        interest_keywords = {
            'photography': ['photo', 'picture', 'camera', 'shot', 'capture'],
            'travel': ['travel', 'trip', 'vacation', 'adventure', 'explore'],
            'music': ['music', 'song', 'band', 'concert', 'listen'],
            'food': ['food', 'restaurant', 'coffee', 'eat', 'delicious'],
            'art': ['art', 'creative', 'draw', 'paint', 'design'],
            'sports': ['sport', 'game', 'play', 'team', 'match'],
            'nature': ['nature', 'outdoor', 'hiking', 'beach', 'mountain']
        }
        
        all_content = ' '.join([msg.get('message', '').lower() for msg in messages if isinstance(msg.get('message'), str)])
        
        for interest, keywords in interest_keywords.items():
            if any(keyword in all_content for keyword in keywords):
                interests.append(interest)
                
        return interests
    
    # Additional prompt builders for missing response types
    def _build_new_opener_prompt(self, analysis: Dict[str, Any], context: Dict[str, Any], our_data: Optional[Dict[str, Any]], user_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build prompt for new conversation openers after concluded conversations"""
        return self._build_revival_opener_prompt(analysis, context, our_data, user_data)  # Similar logic
    
    def _build_restart_opener_prompt(self, analysis: Dict[str, Any], context: Dict[str, Any], our_data: Optional[Dict[str, Any]], user_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build prompt for restarting interrupted conversations"""
        last_message = analysis.get('last_message', {})
        
        return {
            "prompt_type": "restart_opener",
            "mission": "Restart conversation after interruption with natural reconnection",
            "situation": {
                "interruption_context": context.get('messages', [])[-5:],
                "time_gap": f"{analysis.get('hours_since_last', 0):.1f} hours",
                "flow_state": analysis.get('conversation_flow', 'interrupted')
            },
            "restart_strategy": [
                "Acknowledge time gap casually if significant",
                "Reference last conversation topic naturally", 
                "Bring fresh energy to restart dialogue",
                "Provide easy engagement hook"
            ],
            "critical_requirements": [
                "Feel natural, not forced",
                "CRITICAL: NEVER use hyphens (-) or dashes (—, –) - use commas or periods instead",
                "Match appropriate energy for gap",
                "Give them easy way to respond"
            ],
            
            "HYPHEN_BAN": {
                "ABSOLUTELY_FORBIDDEN": ["- (hyphen)", "— (em-dash)", "– (en-dash)"],
                "USE_INSTEAD": [", (comma)", ". (period)", "and", "or", "but"],
                "ENFORCEMENT": "If your response contains ANY hyphens or dashes, it will be automatically rejected"
            },
            "output_format": "Return JSON: {\"message\": \"your_response_here\"}"
        }
    
    def _build_gracious_acknowledgment_prompt(self, analysis: Dict[str, Any], context: Dict[str, Any], our_data: Optional[Dict[str, Any]], user_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build prompt for acknowledging compliments graciously"""
        last_message = analysis.get('last_message', {})
        
        return {
            "prompt_type": "gracious_acknowledgment",
            "mission": "Acknowledge their compliment graciously while keeping conversation natural",
            "situation": {
                "their_compliment": last_message.get('message', ''),
                "conversation_context": context.get('messages', [])
            },
            "response_strategy": [
                "Thank them genuinely without being over the top",
                "Deflect graciously if needed",
                "Turn focus back to them or continue conversation",
                "Keep it natural and warm"
            ],
            "critical_requirements": [
                "Sound genuinely appreciative",
                "Don't be overly modest or boastful",
                "Keep conversation flowing",
                "CRITICAL: NEVER use hyphens (-) or dashes (—, –) - use commas or periods instead"
            ],
            
            "HYPHEN_BAN": {
                "ABSOLUTELY_FORBIDDEN": ["- (hyphen)", "— (em-dash)", "– (en-dash)"],
                "USE_INSTEAD": [", (comma)", ". (period)", "and", "or", "but"],
                "ENFORCEMENT": "If your response contains ANY hyphens or dashes, it will be automatically rejected"
            },
            "output_format": "Return JSON: {\"message\": \"your_response_here\"}"
        }
    
    def _build_media_response_prompt(self, analysis: Dict[str, Any], context: Dict[str, Any], our_data: Optional[Dict[str, Any]], user_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build prompt for responding to shared media"""
        last_message = analysis.get('last_message', {})
        
        return {
            "prompt_type": "media_response", 
            "mission": "Respond appropriately to their shared media (photos, videos, music, etc.)",
            "situation": {
                "media_context": last_message,
                "conversation_history": context.get('messages', [])
            },
            "response_approach": [
                "Comment on what they shared specifically",
                "Show genuine interest and appreciation",
                "Ask relevant follow-up questions",
                "Connect to conversation naturally"
            ],
            "critical_requirements": [
                "Be specific about what they shared",
                "Show genuine interest",
                "CRITICAL: NEVER use hyphens (-) or dashes (—, –) - use commas or periods instead",
                "Keep it engaging and conversational"
            ],
            
            "HYPHEN_BAN": {
                "ABSOLUTELY_FORBIDDEN": ["- (hyphen)", "— (em-dash)", "– (en-dash)"],
                "USE_INSTEAD": [", (comma)", ". (period)", "and", "or", "but"],
                "ENFORCEMENT": "If your response contains ANY hyphens or dashes, it will be automatically rejected"
            },
            "output_format": "Return JSON: {\"message\": \"your_response_here\"}"
        }
    
    def _build_greeting_response_prompt(self, analysis: Dict[str, Any], context: Dict[str, Any], our_data: Optional[Dict[str, Any]], user_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build prompt for responding to greetings"""
        last_message = analysis.get('last_message', {})
        partner_timezone = analysis.get('partner_timezone', {})
        
        return {
            "prompt_type": "greeting_response",
            "mission": "Respond to their greeting warmly and naturally",
            "situation": {
                "their_greeting": last_message.get('message', ''),
                "time_context": partner_timezone,
                "relationship_context": context.get('messages', [])
            },
            "response_approach": [
                "Return appropriate greeting",
                "Add personal touch or question",
                "Match their energy level",
                "Keep conversation going"
            ],
            "critical_requirements": [
                "Match greeting appropriately",
                "Sound natural and warm",
                "CRITICAL: NEVER use hyphens (-) or dashes (—, –) - use commas or periods instead",
                "Encourage further conversation"
            ],
            
            "HYPHEN_BAN": {
                "ABSOLUTELY_FORBIDDEN": ["- (hyphen)", "— (em-dash)", "– (en-dash)"],
                "USE_INSTEAD": [", (comma)", ". (period)", "and", "or", "but"],
                "ENFORCEMENT": "If your response contains ANY hyphens or dashes, it will be automatically rejected"
            },
            "output_format": "Return JSON: {\"message\": \"your_response_here\"}"
        }
    
    def _build_invitation_response_prompt(self, analysis: Dict[str, Any], context: Dict[str, Any], our_data: Optional[Dict[str, Any]], user_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build prompt for responding to invitations"""
        last_message = analysis.get('last_message', {})
        
        return {
            "prompt_type": "invitation_response",
            "mission": "Respond to their invitation appropriately while maintaining safety boundaries",
            "situation": {
                "their_invitation": last_message.get('message', ''),
                "conversation_context": context.get('messages', [])
            },
            "response_strategy": [
                "Acknowledge invitation positively",
                "Keep responses theoretical/general rather than specific plans",
                "Show interest but maintain appropriate boundaries",
                "Redirect to continued conversation"
            ],
            "safety_requirements": [
                "No specific meeting plans or dates",
                "Keep things theoretical and general",
                "Maintain friendly but safe boundaries"
            ],
            "critical_requirements": [
                "Sound appreciative of invitation",
                "Keep it general and safe",
                "CRITICAL: NEVER use hyphens (-) or dashes (—, –) - use commas or periods instead",
                "Continue engaging conversation"
            ],
            
            "HYPHEN_BAN": {
                "ABSOLUTELY_FORBIDDEN": ["- (hyphen)", "— (em-dash)", "– (en-dash)"],
                "USE_INSTEAD": [", (comma)", ". (period)", "and", "or", "but"],
                "ENFORCEMENT": "If your response contains ANY hyphens or dashes, it will be automatically rejected"
            },
            "output_format": "Return JSON: {\"message\": \"your_response_here\"}"
        }
    
    def _build_casual_reconnect_prompt(self, analysis: Dict[str, Any], context: Dict[str, Any], our_data: Optional[Dict[str, Any]], user_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build prompt for casual reconnection after medium delays"""
        last_message = analysis.get('last_message', {})
        
        return {
            "prompt_type": "casual_reconnect",
            "mission": "Reconnect casually after medium delay (1-3 days) with natural flow",
            "situation": {
                "delay_context": f"{analysis.get('hours_since_last', 0):.1f} hours gap",
                "last_interaction": last_message,
                "conversation_history": context.get('messages', [])
            },
            "reconnect_approach": [
                "Light acknowledgment of delay if appropriate",
                "Respond to their last message", 
                "Add something new to move conversation forward",
                "Keep energy positive and engaging"
            ],
            "critical_requirements": [
                "Feel natural and unforced",
                "Address their last message",
                "Positive, engaging tone",
                "CRITICAL: NEVER use hyphens (-) or dashes (—, –) - use commas or periods instead"
            ],
            
            "HYPHEN_BAN": {
                "ABSOLUTELY_FORBIDDEN": ["- (hyphen)", "— (em-dash)", "– (en-dash)"],
                "USE_INSTEAD": [", (comma)", ". (period)", "and", "or", "but"],
                "ENFORCEMENT": "If your response contains ANY hyphens or dashes, it will be automatically rejected"
            },
            "output_format": "Return JSON: {\"message\": \"your_response_here\"}"
        }
    
    def _build_conversational_response_prompt(self, analysis: Dict[str, Any], context: Dict[str, Any], our_data: Optional[Dict[str, Any]], user_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build prompt for general conversational responses"""
        
        last_message = analysis.get('last_message', {})
        partner_timezone = analysis.get('partner_timezone', {})
        
        return {
            "prompt_type": "conversational_response",
            "mission": "Generate a natural, engaging conversational response that continues the dialogue meaningfully.",
            
            "situation": {
                "their_message": last_message.get('message', ''),
                "message_type": analysis.get('last_message_type', 'statement'),
                "conversation_context": context.get('messages', []),
                "timing": f"{analysis.get('timing_category', 'recent')} ({analysis.get('hours_since_last', 0):.1f} hours)",
                "conversation_flow": analysis.get('conversation_flow', 'active')
            },
            
            "your_identity": {
                "name": "kaila_mentari_",
                "personality": "Warm, genuine, naturally curious and engaging",
                "communication_style": "Casual, friendly, shows real interest in people",
                "your_background": our_data
            },
            
            "partner_info": user_data,
            "partner_timezone": partner_timezone,
            
            "response_guidelines": [
                "Respond naturally to what they just said",
                "Show genuine interest and engagement",
                "Keep conversation flowing with questions or comments",
                "Be authentically yourself while staying in character",
                "Match their energy level and communication style",
                "Reference conversation context when relevant"
            ],
            
            "critical_requirements": [
                "Must respond to their actual message content",
                "Sound natural and unscripted",
                "CRITICAL: NEVER use hyphens (-) or dashes (—, –) - use commas or periods instead",
                "Keep it conversational and engaging",
                "Don't be repetitive or template-like"
            ],
            
            "HYPHEN_BAN": {
                "ABSOLUTELY_FORBIDDEN": ["- (hyphen)", "— (em-dash)", "– (en-dash)"],
                "USE_INSTEAD": [", (comma)", ". (period)", "and", "or", "but"],
                "ENFORCEMENT": "If your response contains ANY hyphens or dashes, it will be automatically rejected"
            },
            
            "output_format": "Return JSON: {\"message\": \"your_response_here\"}"
        }
    
    def _save_prompt_data(self, partner_username: str, prompt_data: Dict[str, Any]) -> None:
        """Save prompt data for debugging"""
        try:
            prompts_dir = os.path.join(config.DATA_DIR, "prompts") 
            os.makedirs(prompts_dir, exist_ok=True)
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{partner_username}_{timestamp}_prompt.json"
            filepath = os.path.join(prompts_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(prompt_data, f, indent=2, ensure_ascii=False)
                
            print(f"[DEBUG] Prompt saved to: {filepath}")
        except Exception as e:
            print(f"[WARNING] Could not save prompt data: {e}")
    
    def _save_analysis_data(self, partner_username: str, analysis: Dict[str, Any], context: Dict[str, Any], response_data: Dict[str, Any]) -> None:
        """Save complete analysis data for debugging"""
        try:
            analysis_dir = os.path.join(config.DATA_DIR, "analysis")
            os.makedirs(analysis_dir, exist_ok=True)
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{partner_username}_{timestamp}_analysis.json"
            filepath = os.path.join(analysis_dir, filename)
            
            complete_data = {
                "analysis": analysis,
                "context_optimization": context,
                "response_data": response_data,
                "timestamp": timestamp
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(complete_data, f, indent=2, ensure_ascii=False)
                
            print(f"[DEBUG] Analysis saved to: {filepath}")
        except Exception as e:
            print(f"[WARNING] Could not save analysis data: {e}")

    def process_all_chats(self) -> None:
        """Process all chats in the chat list"""
        try:
            parent_element = self.get_chat_list()
            if not parent_element:
                print("Error: Could not get chat list")
                return
            
            # Count total chats
            chat_count = parent_element.evaluate('''(element) => {
                let count = 0;
                for (const child of element.children) {
                    if (child.tagName === 'DIV' && !child.hasAttribute('class')) {
                        count++;
                    }
                }
                return count;
            }''')
            
            print(f"Found {chat_count} chats to process")
            
            # Process each chat
            for i in range(chat_count):
                print(f"\n--- Processing chat {i+1}/{chat_count} ---")
                self.process_single_chat(i, parent_element)
                
        except Exception as e:
            print(f"Error processing all chats: {str(e)}")
            traceback.print_exc()
    
    def wait_for_user_input(self) -> None:
        """Wait for user input before closing"""
        input("Press Enter to close browser...")
    
    def run(self) -> None:
        """Main execution method"""
        try:
            print("Starting Instagram automation...")
            
            # Start browser if not already started
            if not self.page:
                self.start_browser()
            
            # Setup session
            if not self.setup_session():
                print("Error: Could not setup session")
                return
            
            # Process all chats
            self.process_all_chats()
            
            # Wait for user input
            self.wait_for_user_input()
            
        except Exception as e:
            print(f"Error in main execution: {str(e)}")
            traceback.print_exc()
        finally:
            self.close_browser()


def main():
    """Main entry point"""
    try:
        with InstagramAutomation(headless=False) as automation:
            automation.run()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    main()