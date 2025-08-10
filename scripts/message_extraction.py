"""
Message extraction utilities for Instagram automation
"""
from typing import List, Dict, Any, Optional
from playwright.sync_api import Page, ElementHandle
from . import config
from .helpers import convert_date
from .data_utils import convert_segments_to_messages, filter_messages_by_date


def create_text_extraction_script(main_username: str, partner_displayname: str, partner_username: str) -> str:
    """Create the JavaScript text extraction script"""
    return f"""node => {{
        const main_username = `{main_username}`;
        const partner_displayname = `{partner_displayname}`;
        const partner_username = `{partner_username}`;
        const contentSegments = [];
        
        // Precollect parent elements of date_break nodes
        const dateParents = new Set();
        const dateBreaks = node.querySelectorAll('[data-scope="date_break"]');
        dateBreaks.forEach(breakEl => {{
            if (breakEl.parentElement) {{
                dateParents.add(breakEl.parentElement);
            }}
        }});

        // Precollect "Original message" text nodes and their content elements
        const originalMessageTextNodes = new Set();
        const originalMessageContentElements = new Set();
        const textWalker = document.createTreeWalker(
            node,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        while (textWalker.nextNode()) {{
            const textNode = textWalker.currentNode;
            if (textNode.textContent.trim() === "Original message:") {{
                originalMessageTextNodes.add(textNode);
                const container = textNode.parentNode;
                if (container.nextElementSibling) {{
                    originalMessageContentElements.add(container.nextElementSibling);
                }}
            }}
        }}

        // Precollect reaction containers and their emoji content
        const reactionContainers = new Set();
        const reactionEmojis = new Map();
        const reactionNodes = node.querySelectorAll('[aria-label*="see who reacted to this"]');
        reactionNodes.forEach(container => {{
            reactionContainers.add(container);
            const emojis = container.textContent.trim();
            reactionEmojis.set(container, emojis);
        }});

        // Precollect all profile links and their usernames
        const profileLinks = new Map();
        const profileLinkElements = node.querySelectorAll('a[aria-label^="Open the profile page of"]');
        profileLinkElements.forEach(link => {{
            const ariaLabel = link.getAttribute('aria-label');
            const username = ariaLabel.substring(ariaLabel.lastIndexOf(' ') + 1);
            profileLinks.set(link, username);
        }});

        // Keep track of which rows have had sender tags added
        const rowSenderAdded = new Set();
        
        // Helper to find row element (role="gridcell")
        const findRowForNode = (node) => {{
            let parent = node.parentNode;
            while (parent && parent !== node) {{
                if (parent.nodeType === Node.ELEMENT_NODE && 
                    parent.getAttribute('role') === 'gridcell') {{
                    return parent;
                }}
                parent = parent.parentNode;
            }}
            return null;
        }};

        const extractSubtreeContent = (root) => {{
            const segments = [];
            const walker = document.createTreeWalker(
                root,
                NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT,
                {{ 
                    acceptNode: function(node) {{
                        if (node.nodeType === Node.ELEMENT_NODE && 
                            node.getAttribute('data-scope') === 'date_break') {{
                            return NodeFilter.FILTER_REJECT;
                        }}
                        return NodeFilter.FILTER_ACCEPT;
                    }}
                }},
                false
            );

            while (walker.nextNode()) {{
                const node = walker.currentNode;
                if (node.nodeType === Node.TEXT_NODE) {{
                    segments.push(node.textContent);
                }} 
                else if (node.nodeType === Node.ELEMENT_NODE && node.tagName === 'IMG') {{
                    let hasProfileLinkAncestor = false;
                    let parent = node.parentElement;
                    while (parent) {{
                        if (parent.tagName === 'A' && parent.hasAttribute('aria-label')) {{
                            const ariaLabel = parent.getAttribute('aria-label');
                            if (ariaLabel.includes('Open the profile page of')) {{
                                hasProfileLinkAncestor = true;
                                break;
                            }}
                        }}
                        parent = parent.parentElement;
                    }}

                    if (!hasProfileLinkAncestor) {{
                        const altText = node.alt || '';
                        const trimmedAlt = altText.trim();
                        const src = node.getAttribute('src') || '';

                        if (trimmedAlt === "Open photo" && src) {{
                            segments.push(`[IMG] ${{src}}`);
                        }}
                        else if (trimmedAlt === "Open Video" && src) {{
                            segments.push(`[VIDEO] ${{src}}`);
                        }}
                        else if (src.includes("emoji.php") && trimmedAlt) {{
                            segments.push(trimmedAlt);
                        }}
                        else if (trimmedAlt) {{
                            segments.push(`[IMG ALT]: ${{trimmedAlt}}`);
                        }}
                    }}
                }}
            }}
            const combined = segments.join('');
            return combined.replace(/\\s+/g, ' ').trim();
        }};

        const walker = document.createTreeWalker(
            node,
            NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT,
            {{ 
                acceptNode: function(node) {{
                    let parent = node.parentNode;
                    while (parent && parent !== node) {{
                        if (parent.nodeType === Node.ELEMENT_NODE && 
                            parent.classList.contains('html-div') && 
                            parent.getAttribute('dir') === 'auto' &&
                            !dateParents.has(parent) && 
                            !originalMessageContentElements.has(parent)) {{
                            return NodeFilter.FILTER_REJECT;
                        }}
                        parent = parent.parentNode;
                    }}

                    if (node.nodeType === Node.ELEMENT_NODE && 
                        node.getAttribute('data-scope') === 'date_break') {{
                        return NodeFilter.FILTER_REJECT;
                    }}

                    let parentCheck = node.parentNode;
                    while (parentCheck) {{
                        if (originalMessageContentElements.has(parentCheck) || 
                            reactionContainers.has(parentCheck)) {{
                            return NodeFilter.FILTER_REJECT;
                        }}
                        parentCheck = parentCheck.parentNode;
                    }}

                    return NodeFilter.FILTER_ACCEPT;
                }}
            }},
            false
        );

        while (walker.nextNode()) {{
            const currentNode = walker.currentNode;
            let segmentPrefix = "";

            let parent = currentNode.parentElement;
            while (parent) {{
                if (dateParents.has(parent)) {{
                    segmentPrefix = "[DATE] ";
                    break;
                }}
                parent = parent.parentElement;
            }}

            // Find row element for current node
            const row = findRowForNode(currentNode);
            
            // Add sender tag if missing for this row
            if (row && !rowSenderAdded.has(row)) {{
                let senderAdded = false;
                
                // Check for profile links in ancestors
                let profileParent = currentNode.parentElement;
                while (profileParent) {{
                    if (profileParent.tagName === 'A' && profileLinks.has(profileParent)) {{
                        const username = profileLinks.get(profileParent);
                        if (username === main_username) {{
                            contentSegments.push(segmentPrefix + '[SENT BY] ' + main_username);
                        }} else {{
                            contentSegments.push(segmentPrefix + '[SENT BY] ' + partner_displayname);
                        }}
                        rowSenderAdded.add(row);
                        senderAdded = true;
                        break;
                    }}
                    profileParent = profileParent.parentElement;
                }}
            }}

            if (currentNode.nodeType === Node.TEXT_NODE && originalMessageTextNodes.has(currentNode)) {{
                continue;
            }}

            if (currentNode.nodeType === Node.ELEMENT_NODE && 
                originalMessageContentElements.has(currentNode)) {{
                const fullContent = extractSubtreeContent(currentNode);
                if (fullContent) {{
                    contentSegments.push(segmentPrefix + '[QUOTED TEXT] ' + fullContent);
                }}
                continue;
            }}

            // Handle reaction containers
            if (currentNode.nodeType === Node.ELEMENT_NODE && 
                reactionContainers.has(currentNode)) {{
                const emojis = reactionEmojis.get(currentNode);
                if (emojis) {{
                    contentSegments.push(segmentPrefix + '[REACTIONS] ' + emojis);
                }}
                continue;
            }}

            // Handle message content containers
            if (currentNode.nodeType === Node.ELEMENT_NODE && 
                currentNode.classList.contains('html-div') && 
                currentNode.getAttribute('dir') === 'auto' &&
                !dateParents.has(currentNode) && 
                !originalMessageContentElements.has(currentNode)) {{
                
                const fullContent = extractSubtreeContent(currentNode);
                if (fullContent) {{
                    contentSegments.push(segmentPrefix + '[MESSAGE] ' + fullContent);
                }}
                continue;
            }}

            if (currentNode.nodeType === Node.TEXT_NODE) {{
                const text = currentNode.textContent.trim();
                if (text) {{
                    if (text === "Edited" || text === ".") continue;
                    
                    // Handle reply indicators
                    if (text.endsWith("replied to you")) {{
                        contentSegments.push(segmentPrefix + '[REPLY SENT BY] ' + partner_displayname);
                        contentSegments.push(segmentPrefix + '[ORIGINAL MESSAGE BY] ' + main_username);
                        if (row) rowSenderAdded.add(row);
                    }}
                    else if (text.endsWith("replied to themself")) {{
                        contentSegments.push(segmentPrefix + '[REPLY SENT BY] ' + partner_displayname);
                        contentSegments.push(segmentPrefix + '[ORIGINAL MESSAGE BY] ' + partner_displayname);
                        if (row) rowSenderAdded.add(row);
                    }}
                    else if (text.startsWith("You replied to yourself")) {{
                        contentSegments.push(segmentPrefix + '[REPLY SENT BY] ' + main_username);
                        contentSegments.push(segmentPrefix + '[ORIGINAL MESSAGE BY] ' + main_username);
                        if (row) rowSenderAdded.add(row);
                    }}
                    else if (text.startsWith("You replied to")) {{
                        contentSegments.push(segmentPrefix + '[REPLY SENT BY] ' + main_username);
                        contentSegments.push(segmentPrefix + '[ORIGINAL MESSAGE BY] ' + partner_displayname);
                        if (row) rowSenderAdded.add(row);
                    }}
                    else if (text === partner_displayname || text === partner_username) {{
                        contentSegments.push(segmentPrefix + '[SENT BY] ' + text);
                        if (row) rowSenderAdded.add(row);
                    }} 
                    else if (text === 'You sent') {{
                        contentSegments.push(segmentPrefix + '[SENT BY] ' + main_username);
                        if (row) rowSenderAdded.add(row);
                    }}
                    else if (text === 'Enter') {{
                        // Do nothing
                    }}
                    else if (text === 'Shared your story' || text.includes('Shared your story')) {{
                        contentSegments.push(segmentPrefix + '[STORY SHARED] ' + text);
                        // For story shares, the next text element should be the sender
                        // Don't mark row as sender added yet - let the username be processed as sender
                    }}
                    else if (text.includes('Replied to') && text.includes('story')) {{
                        // Handle "Replied to @Username's story" segments
                        contentSegments.push(segmentPrefix + '[STORY REPLY] ' + text);
                    }}
                    else if (text.includes('Reacted to') && text.includes('story')) {{
                        // Handle "Reacted to @Username's story" segments
                        contentSegments.push(segmentPrefix + '[STORY REACTION] ' + text);
                    }}
                    else if (row && rowSenderAdded.has(row)) {{
                        contentSegments.push(segmentPrefix + '[MESSAGE] ' + text);
                    }}
                    else {{
                        contentSegments.push(segmentPrefix + text);
                    }}
                }}
            }} 
            else if (currentNode.nodeType === Node.ELEMENT_NODE && currentNode.tagName === 'IMG') {{
                let hasProfileLinkAncestor = false;
                let parent = currentNode.parentElement;
                while (parent) {{
                    if (parent.tagName === 'A' && parent.hasAttribute('aria-label')) {{
                        const ariaLabel = parent.getAttribute('aria-label');
                        if (ariaLabel.includes('Open the profile page of')) {{
                            hasProfileLinkAncestor = true;
                            break;
                        }}
                    }}
                    parent = parent.parentElement;
                }}

                if (!hasProfileLinkAncestor) {{
                    const altText = currentNode.alt || '';
                    const trimmedAlt = altText.trim();
                    const src = currentNode.getAttribute('src') || '';

                    if (trimmedAlt === "Open photo" && src) {{
                        contentSegments.push(segmentPrefix + `[MEDIA ATTACHED: IMG] ${{src}}`);
                    }}
                    else if (trimmedAlt === "Open Video" && src) {{
                        contentSegments.push(segmentPrefix + `[MEDIA ATTACHED: VIDEO] ${{src}}`);
                    }}
                    else if (src.includes("emoji.php") && trimmedAlt) {{
                        contentSegments.push(segmentPrefix + trimmedAlt);
                    }}
                    else if (trimmedAlt) {{
                        contentSegments.push(segmentPrefix + `[IMG ALT]: ${{trimmedAlt}}`);
                    }}
                }}
            }}
        }}
        
        // POST-PROCESSING: Merge segments and clean up
        const mergedSegments = [];
        let i = 0;
        while (i < contentSegments.length) {{
            if (i < contentSegments.length - 1 && 
                contentSegments[i+1] === "Use the Instagram mobile app to view this message." &&
                (contentSegments[i] === "Unsupported message" || 
                contentSegments[i] === "[MESSAGE] Unsupported message")) {{
                mergedSegments.push("[ONE TIME VIEW MEDIA]");
                i += 2;
            }} else {{
                mergedSegments.push(contentSegments[i]);
                i++;
            }}
        }}

        // Merge content name + "Clip" into special tag
        const mergedSegments2 = [];
        i = 0;
        while (i < mergedSegments.length) {{
            if (i < mergedSegments.length - 1 && 
                mergedSegments[i+1] === "Clip") {{
                
                let contentName = mergedSegments[i];
                
                if (contentName.startsWith('[MESSAGE] ')) {{
                    contentName = contentName.substring('[MESSAGE] '.length);
                }}
                
                mergedSegments2.push("[IG CONTENT SHARED] " + contentName);
                i += 2;
            }} else {{
                mergedSegments2.push(mergedSegments[i]);
                i++;
            }}
        }}
        
        // Handle link previews
        const tagsToSkip = [
            '[DATE]', '[SENT BY]', '[REPLY SENT BY]', 
            '[REACTIONS]', '[QUOTED TEXT]', '[ONE TIME VIEW MEDIA]',
            '[MEDIA ATTACHED: IMG]', '[MEDIA ATTACHED: VIDEO]', 
            '[IMG ALT]:', '[MESSAGE]', '[LINK PREVIEW]',
            '[IG CONTENT SHARED]'
        ];
        
        const finalSegments = [];
        i = 0;
        while (i < mergedSegments2.length) {{
            const current = mergedSegments2[i];
            if (current.startsWith('[MESSAGE]') && 
                (current.includes('http://') || 
                current.includes('https://') || 
                current.includes('www.'))) {{
                
                if (i + 1 < mergedSegments2.length) {{
                    const next = mergedSegments2[i + 1];
                    const isPlainText = !tagsToSkip.some(tag => next.startsWith(tag));
                    
                    if (isPlainText && next.trim() !== '') {{
                        finalSegments.push(current);
                        finalSegments.push('[LINK PREVIEW] ' + next);
                        i += 2;
                        continue;
                    }}
                }}
            }}
            finalSegments.push(current);
            i++;
        }}
        
        // Filter out noise
        const filteredSegments = finalSegments.filter(segment => 
            segment !== "Edited" && 
            segment !== "." &&
            !segment.endsWith(" Edited") &&
            !segment.startsWith("Edited ") &&
            !/^(\[[^\]]+\]\s*)*\.$/.test(segment)
        );
        
        return filteredSegments;
    }}"""


def traverse_dom_to_target(page: Page) -> Optional[ElementHandle]:
    """Traverse DOM to find the target element for message extraction"""
    try:
        print("Locating chat container...")
        chat_container = page.locator(config.SELECTORS['messages_container']).first
        chat_container.wait_for(state='visible', timeout=config.DEFAULT_TIMEOUT)
        print("✅ Found chat container")
        
        print("Traversing DOM path...")
        target_element = chat_container.evaluate_handle('''element => {
            const getChild = (parent, index) => {
                if (!parent || !parent.children || parent.children.length <= index) return null;
                return parent.children[index];
            };
            
            const level1 = getChild(element, 0);
            if (!level1) return null;
            
            const level2 = getChild(level1, 0);
            if (!level2) return null;
            
            const level3 = getChild(level2, 0);
            if (!level3) return null;
            
            const level4 = getChild(level3, 0);
            if (!level4) return null;
            
            const level5 = getChild(level4, 2);
            if (!level5) return null;
            
            const level6 = getChild(level5, 0);
            if (!level6) return null;
            
            const level7 = getChild(level6, 0);
            return level7;
        }''').as_element()
        
        if not target_element:
            print("❌ Could not traverse full DOM path")
            return None
            
        print("✅ Found target element")
        return target_element
    except Exception as e:
        print(f"❌ Error traversing DOM: {str(e)}")
        return None


def extract_and_process_elements(page: Page, target_element: ElementHandle, text_extraction_script: str) -> List[List[str]]:
    """Extract and process message elements"""
    try:
        target_class = target_element.get_attribute("class") or ""
        print(f"🎯 Target element class: '{target_class}'")
        
        parent_element = target_element.evaluate_handle('el => el.parentElement').as_element()
        if not parent_element:
            print("❌ Parent element not found")
            return []
        
        # Debug: Show all children and their classes
        print(f"🔍 Analyzing parent element children...")
        all_children_info = parent_element.evaluate('''(parent, targetClass) => {
            return Array.from(parent.children).map((child, index) => ({
                index: index,
                className: child.className,
                tagName: child.tagName,
                hasTargetClass: child.className.includes(targetClass)
            }));
        }''', target_class)
        
        print(f"  Parent has {len(all_children_info)} total children:")
        for child_info in all_children_info:
            print(f"    [{child_info['index']}] {child_info['tagName']} class='{child_info['className'][:50]}...' matches_target={child_info['hasTargetClass']}")
        
        # More flexible class matching - look for core message container classes
        js_handle = parent_element.evaluate_handle('''(parent, className) => {
            // Extract base classes (first two) for more flexible matching
            const baseClasses = className.split(' ').slice(0, 2); // x78zum5 xdt5ytf
            
            return Array.from(parent.children).filter(child => {
                // Must have both base classes but third class is optional
                // Removed data-virtualized filter to include all matching elements
                return baseClasses.every(cls => child.className.includes(cls)) &&
                       child.tagName === 'DIV';
            });
        }''', target_class)
        
        count = js_handle.evaluate('arr => arr.length')
        print(f"🔢 Found {count} elements with flexible class matching")
        
        # Debug: Show which elements matched with flexible matching
        matched_elements_info = js_handle.evaluate('''(elements, targetClass) => {
            const baseClasses = targetClass.split(' ').slice(0, 2);
            return elements.map((el, index) => ({
                index: index,
                className: el.className,
                hasBaseClasses: baseClasses.every(cls => el.className.includes(cls)),
                dataVirtualized: el.getAttribute('data-virtualized')
            }));
        }''', target_class)
        
        print(f"🎯 Flexible matching results:")
        for i, info in enumerate(matched_elements_info):
            print(f"  Match {i+1}: hasBaseClasses={info['hasBaseClasses']}, data-virtualized={info['dataVirtualized']} (now included)")
            print(f"    class='{info['className'][:60]}...')")
        
        original_elements = []
        print(f"\n🔍 Element identification and viewport analysis:")
        try:
            viewport_size = page.viewport_size()
            if viewport_size is None:
                # Fallback for dynamic viewport
                viewport_size = page.evaluate("({width: window.innerWidth, height: window.innerHeight})")
            print(f"  Viewport size: {viewport_size['width']}x{viewport_size['height']}")
        except Exception as e:
            print(f"  ⚠️ Could not get viewport size: {e}")
            viewport_size = {"width": 1280, "height": 720}  # Default fallback
        
        for i in range(count):
            element_handle = js_handle.evaluate_handle('(arr, idx) => arr[idx]', i).as_element()
            if element_handle:
                original_elements.append(element_handle)
                
                # Get element position info
                try:
                    rect = element_handle.bounding_box()
                    if rect:
                        in_viewport = (rect['y'] >= 0 and rect['y'] < viewport_size['height'])
                        print(f"  Element {i+1}: position y={rect['y']:.1f}, height={rect['height']:.1f}, in_viewport={in_viewport}")
                    else:
                        print(f"  Element {i+1}: No bounding box available")
                except Exception as e:
                    print(f"  Element {i+1}: Error getting position - {str(e)}")
            else:
                print(f"  Element {i+1}: Failed to get element handle")
        
        def count_children(element):
            try:
                if element is None:
                    print(f"⚠️ Cannot count children: element is None")
                    return 0
                result = element.evaluate(config.JS_SNIPPETS['recursive_count'])
                if result is None:
                    print(f"⚠️ JS snippet returned None for child count")
                    return 0
                return result
            except Exception as e:
                print(f"⚠️ Error counting children: {str(e)}")
                return 0
        
        print(f"\n📊 Counting children for {len(original_elements)} elements...")
        element_counts = []
        for i, el in enumerate(original_elements):
            print(f"  Counting element {i+1}...")
            count_val = count_children(el)
            element_counts.append(count_val)
            print(f"  Element {i+1}: {count_val} children")
        
        print(f"\n📊 Initial child counts summary:")
        for i, count_val in enumerate(element_counts, 1):
            print(f"  Element {i}: {count_val} children")
        
        # Process elements
        min_threshold = config.MIN_CHILD_THRESHOLD
        max_retries = config.MAX_RETRY_ATTEMPTS
        retry_count = 0
        
        print(f"\n⚙️ Processing configuration:")
        print(f"  MIN_CHILD_THRESHOLD: {min_threshold}")
        print(f"  MAX_RETRY_ATTEMPTS: {max_retries}")
        
        needs_processing = [count < min_threshold for count in element_counts]
        extracted_texts = [None] * len(original_elements)
        
        print(f"\n📋 Element processing status:")
        for i, (count_val, needs_proc) in enumerate(zip(element_counts, needs_processing), 1):
            status = "NEEDS SCROLL" if needs_proc else "READY"
            print(f"  Element {i}: {count_val} children -> {status}")
        
        # Extract text for initially loaded elements
        print("\n🔍 Extracting text for initially loaded elements")
        for i, (element, count_val) in enumerate(zip(original_elements, element_counts)):
            if count_val >= min_threshold:
                try:
                    print(f"  Extracting text for element {i+1} (count: {count_val})...")
                    if element is None:
                        print(f"  ⚠️ Element {i+1} is None!")
                        extracted_texts[i] = []
                        continue
                    text_segments = element.evaluate(text_extraction_script)
                    if text_segments is None:
                        print(f"  ⚠️ Text extraction returned None for element {i+1}")
                        extracted_texts[i] = []
                    else:
                        extracted_texts[i] = text_segments
                        print(f"  Element {i+1}: Extracted {len(text_segments)} text segments")
                except Exception as e:
                    print(f"⚠️ Text extraction failed for element {i+1}: {str(e)}")
                    import traceback
                    print(f"⚠️ Full traceback: {traceback.format_exc()}")
                    extracted_texts[i] = []
        
        # Process elements below threshold
        while retry_count < max_retries and any(needs_processing):
            retry_count += 1
            print(f"\n🔄 Retry {retry_count}: Processing {sum(needs_processing)} elements")
            
            for i, (element, needs_load) in enumerate(zip(original_elements, needs_processing)):
                if needs_load:
                    try:
                        print(f"    ↳ SCROLL DEBUG: About to scroll element {i+1} into view")
                        print(f"      SCROLL REASON: Element {i+1} has {element_counts[i]} children (below threshold {min_threshold})")
                        
                        # Get scroll position before scrolling
                        scroll_before = page.evaluate("window.scrollY || document.documentElement.scrollTop")
                        element_rect_before = element.bounding_box()
                        print(f"      PRE-SCROLL: Page scrollY={scroll_before}")
                        if element_rect_before:
                            print(f"      PRE-SCROLL: Element position y={element_rect_before['y']}")
                        
                        # Perform the scroll
                        element.scroll_into_view_if_needed()
                        
                        # Get scroll position after scrolling
                        scroll_after = page.evaluate("window.scrollY || document.documentElement.scrollTop")
                        element_rect_after = element.bounding_box()
                        scroll_delta = scroll_after - scroll_before
                        
                        print(f"      POST-SCROLL: Page scrollY={scroll_after}")
                        if element_rect_after:
                            print(f"      POST-SCROLL: Element position y={element_rect_after['y']}")
                        print(f"      SCROLL DELTA: {scroll_delta} pixels ({'UP' if scroll_delta < 0 else 'DOWN' if scroll_delta > 0 else 'NO CHANGE'})")
                        
                        if scroll_delta < 0:
                            print(f"      ⚠️ UPWARD SCROLL DETECTED: {abs(scroll_delta)} pixels")
                        
                        page.wait_for_timeout(config.SCROLL_INTO_VIEW_WAIT_MS)
                        
                        new_count = count_children(element)
                        element_counts[i] = new_count
                        print(f"      Updated count: {new_count} children")
                        
                        try:
                            if element is None:
                                print(f"      ⚠️ Element {i+1} is None during retry!")
                                extracted_texts[i] = []
                                continue
                            text_segments = element.evaluate(text_extraction_script)
                            if text_segments is None:
                                print(f"      ⚠️ Text extraction returned None for element {i+1} during retry")
                                extracted_texts[i] = []
                            else:
                                extracted_texts[i] = text_segments
                                print(f"      Extracted {len(text_segments)} text segments")
                        except Exception as e:
                            print(f"⚠️ Text extraction failed for element {i+1} during retry: {str(e)}")
                            import traceback
                            print(f"⚠️ Full traceback: {traceback.format_exc()}")
                            extracted_texts[i] = []
                        
                        needs_processing[i] = new_count < min_threshold
                    except Exception as e:
                        print(f"⚠️ Scroll failed for element {i+1}: {str(e)}")
                        needs_processing[i] = False
        
        # Collect valid texts with detailed debugging
        valid_texts = []
        print(f"\n🔍 Final threshold check (min_threshold = {min_threshold}):")
        for i, (element, count_val) in enumerate(zip(original_elements, element_counts)):
            meets_threshold = count_val >= min_threshold
            has_text = extracted_texts[i] is not None and len(extracted_texts[i]) > 0
            
            print(f"  Element {i+1}: count={count_val}, meets_threshold={meets_threshold}, has_text={has_text}")
            
            if meets_threshold:
                text_to_add = extracted_texts[i] if extracted_texts[i] is not None else []
                valid_texts.append(text_to_add)
                print(f"    ✅ INCLUDED: {len(text_to_add)} text segments")
            else:
                excluded_text = extracted_texts[i] if extracted_texts[i] is not None else []
                print(f"    ❌ EXCLUDED: Below threshold ({count_val} < {min_threshold})")
                if excluded_text:
                    print(f"    📝 EXCLUDED TEXT ({len(excluded_text)} segments):")
                    for j, segment in enumerate(excluded_text[:3], 1):  # Show first 3 segments
                        print(f"        {j}. {segment}")
                    if len(excluded_text) > 3:
                        print(f"        ... and {len(excluded_text) - 3} more segments")
                else:
                    print(f"    📝 EXCLUDED TEXT: No text extracted")
        
        print(f"\n📊 Summary: {len(valid_texts)} elements out of {len(original_elements)} passed threshold check")
        
        # Show suggestion if elements were excluded
        excluded_count = len(original_elements) - len(valid_texts)
        if excluded_count > 0:
            print(f"\n💡 SUGGESTION: {excluded_count} element(s) excluded due to low child count.")
            print(f"   Consider lowering MIN_CHILD_THRESHOLD (currently {min_threshold}) if these contain valid messages.")
        
        return valid_texts
    
    except Exception as e:
        print(f"❌ Error processing elements: {str(e)}")
        return []


def process_and_convert_dates(valid_texts: List[List[str]]) -> List[List[str]]:
    """Process dates in extracted text segments"""
    # Propagate dates forward
    last_date = None
    adjusted_texts = []
    for segments in valid_texts:
        if segments:
            if segments[0].startswith('[DATE]'):
                last_date = segments[0]
                adjusted_texts.append(segments)
            elif last_date is not None:
                adjusted_texts.append([last_date] + segments)
            else:
                adjusted_texts.append(segments)
        else:
            adjusted_texts.append(segments)

    # Backward propagation: find first date and propagate backward to fill missing dates
    first_date = None
    for segments in adjusted_texts:
        if segments and segments[0].startswith('[DATE]'):
            first_date = segments[0]
            break
    
    if first_date is not None:
        # Propagate the first found date backward to messages without dates
        for i in range(len(adjusted_texts)):
            if adjusted_texts[i] and not adjusted_texts[i][0].startswith('[DATE]'):
                adjusted_texts[i] = [first_date] + adjusted_texts[i]
            else:
                # Once we hit a message with a date, stop backward propagation
                break

    # Convert dates
    converted_texts = []
    for segments in adjusted_texts:
        new_segments = []
        for segment in segments:
            if segment.startswith('[DATE]'):
                new_segments.append('[DATE] ' + convert_date(segment))
            else:
                new_segments.append(segment)
        converted_texts.append(new_segments)
    
    return converted_texts


def initial_messages_extraction(page: Page, main_username: str, partner_displayname: str, 
                              partner_username: str, message_obj: Optional[Dict[str, Any]] = None, 
                              skip_progressive_scroll: bool = False) -> List[Dict[str, Any]]:
    """
    Extract messages from the chat interface
    
    Args:
        page: Playwright page object
        main_username: Username of the main user
        partner_displayname: Display name of the chat partner
        partner_username: Username of the chat partner
        message_obj: Optional message object to filter from (returns only newer messages)
        skip_progressive_scroll: If True, extract only current viewport without progressive scrolling
    
    Returns:
        List of message dictionaries
    """
    try:
        print(f"\n🚀 STARTING initial_messages_extraction")
        
        # Get the correct scroll container (same as used by scroll_to_date)
        from .browser_utils import get_scroll_container
        scroll_container = get_scroll_container(page)
        if scroll_container:
            initial_scroll_pos = scroll_container.evaluate("el => el.scrollTop")
            print(f"   INITIAL SCROLL POSITION (container): {initial_scroll_pos}")
        else:
            initial_scroll_pos = page.evaluate("window.scrollY || document.documentElement.scrollTop")
            print(f"   INITIAL SCROLL POSITION (window fallback): {initial_scroll_pos}")
        
        target_element = traverse_dom_to_target(page)
        if not target_element:
            return []
        
        text_extraction_script = create_text_extraction_script(main_username, partner_displayname, partner_username)
        
        if skip_progressive_scroll:
            print(f"\n🔄 Skipping progressive scrolling - extracting from current position only")
            # Extract messages from current viewport only
            all_valid_texts = extract_and_process_elements(page, target_element, text_extraction_script)
        else:
            # Progressive scrolling to load all messages
            all_valid_texts = []
            max_progressive_scrolls = 15  # Increased to handle more content
            scroll_count = 0
            consecutive_no_new_messages = 0
            max_consecutive_no_new = 3  # Allow 3 consecutive attempts with no new messages
            
            print(f"\n🔄 Starting progressive message extraction...")
            
            while scroll_count < max_progressive_scrolls:
                scroll_count += 1
                print(f"\n📜 Progressive scroll {scroll_count}/{max_progressive_scrolls}")
                
                # Extract messages from current viewport
                valid_texts = extract_and_process_elements(page, target_element, text_extraction_script)
                
                if not valid_texts:
                    print(f"   No messages found in current viewport")
                    consecutive_no_new_messages += 1
                    if consecutive_no_new_messages >= max_consecutive_no_new:
                        print(f"   Breaking after {consecutive_no_new_messages} consecutive attempts with no messages")
                        break
                else:
                    current_message_count = len(valid_texts)
                    print(f"   Found {current_message_count} messages in current viewport")
                    
                    # Check if we got significantly more messages (at least 2 more to account for variations)
                    if len(all_valid_texts) > 0 and current_message_count <= len(all_valid_texts) + 1:
                        consecutive_no_new_messages += 1
                        print(f"   Minimal new messages found (current: {current_message_count}, previous: {len(all_valid_texts)})")
                        print(f"   Consecutive no-new count: {consecutive_no_new_messages}/{max_consecutive_no_new}")
                        
                        if consecutive_no_new_messages >= max_consecutive_no_new:
                            print(f"   Breaking after {consecutive_no_new_messages} consecutive attempts with minimal new messages")
                            break
                    else:
                        consecutive_no_new_messages = 0  # Reset counter when we find new messages
                        print(f"   Good progress: {current_message_count} messages (previous: {len(all_valid_texts)})")
                    
                    # Update our collection with new messages
                    all_valid_texts = valid_texts  # Keep the latest extraction
                
                # Scroll down to load more messages
                print(f"   Scrolling down to load more messages...")
                if scroll_container:
                    scroll_container.evaluate("el => el.scrollTop += 600")  # Scroll down 600px in container
                    print("   Using container scrolling for progressive loading")
                else:
                    page.evaluate("window.scrollBy(0, 600)")  # Fallback to window scrolling
                    print("   Using window scrolling for progressive loading (fallback)")
                page.wait_for_timeout(2500)  # Increased wait time for content to load
                
                # Re-traverse to target element after scrolling
                target_element = traverse_dom_to_target(page)
                if not target_element:
                    print(f"   Lost target element after scrolling, stopping extraction")
                    break
        
        valid_texts = all_valid_texts
        print(f"\n✅ Progressive extraction complete: {len(valid_texts)} total messages found")
        
        if not valid_texts:
            return []
        
        # Process dates
        valid_texts = process_and_convert_dates(valid_texts)
        
        # Print extraction results
        print(f"\n📊 Final results:")
        print(f"  Valid elements: {len(valid_texts)}")
        
        print("\n📝 Element text content:")
        for idx, text_segments in enumerate(valid_texts, 1):
            if not text_segments:
                print(f"Element {idx} - No text extracted")
                continue
                
            print(f"Element {idx} - Total text segments: {len(text_segments)}")
            for i, segment in enumerate(text_segments, 1):
                print(f"  {i}. {segment}")
        
        # Convert to message objects
        messages = convert_segments_to_messages(valid_texts)
        print(f"\n📦 Message objects created: {len(messages)}")
        
        # Filter messages if message_obj is provided
        if message_obj is not None:
            print("🔄 Filtering messages: removing provided message_obj and all older messages")
            messages = filter_messages_by_date(messages, message_obj)
            print(f"🔄 Filtering result: {len(messages)} messages after filtering")
        
        # Final scroll position check (use same container as initial measurement)
        if scroll_container:
            final_scroll_pos = scroll_container.evaluate("el => el.scrollTop")
            print(f"\n🏁 ENDING initial_messages_extraction")
            print(f"   FINAL SCROLL POSITION (container): {final_scroll_pos}")
        else:
            final_scroll_pos = page.evaluate("window.scrollY || document.documentElement.scrollTop")
            print(f"\n🏁 ENDING initial_messages_extraction")
            print(f"   FINAL SCROLL POSITION (window fallback): {final_scroll_pos}")
        
        total_scroll_delta = final_scroll_pos - initial_scroll_pos
        print(f"   TOTAL SCROLL DELTA: {total_scroll_delta} pixels ({'UP' if total_scroll_delta < 0 else 'DOWN' if total_scroll_delta > 0 else 'NO CHANGE'})")
        
        if total_scroll_delta < 0:
            print(f"   ⚠️ OVERALL UPWARD SCROLL: {abs(total_scroll_delta)} pixels")
        
        return messages
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return []