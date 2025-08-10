# Instagram Playwright Automation - Project Context

## Overview
This is an Instagram Direct Message automation project that uses Playwright for web automation, DeepSeek API for AI-powered responses, and includes comprehensive message extraction and response generation capabilities.

**Project Type**: Instagram automation bot with AI-powered responses  
**Main Language**: Python  
**Key Technology**: Playwright, DeepSeek API  
**Purpose**: Automate Instagram DM conversations with intelligent responses  

## Key Features
- 🤖 **AI-Powered Responses**: Uses DeepSeek R1 model with reasoning capabilities
- 📱 **Instagram DM Automation**: Full Direct Message workflow automation
- 💬 **Message Extraction**: Advanced message parsing and conversation history
- 🎯 **Precise Window Positioning**: Calibrated window positioning for multi-monitor setups
- 📊 **Data Management**: Comprehensive conversation and user data tracking
- 🔄 **Scroll & Navigation**: Advanced scrolling and chat navigation utilities

## Project Structure
```
C:\python\IG_playwright\
├── main.py                           # Main entry point
├── requirements.txt                  # Python dependencies  
├── README.md                         # Project documentation
├── CALIBRATED_POSITION_README.md     # Window positioning guide
├── MESSAGE_FLOW_UPDATE.md            # Message processing flow documentation
├── scripts\                          # Core Python modules
│   ├── __init__.py
│   ├── instagram_automation.py       # Main automation class
│   ├── deepseek_api_client.py        # DeepSeek API client
│   ├── config.py                     # Configuration constants
│   ├── browser_utils.py              # Browser setup and utilities
│   ├── scroll_utils.py               # Scrolling and navigation
│   ├── message_extraction.py         # Message parsing logic
│   ├── data_utils.py                 # Data storage/retrieval
│   ├── ai_api_functions.py           # AI response generation
│   ├── helpers.py                    # Utility functions
│   ├── logger.py                     # Logging configuration
│   └── [testing/calibration scripts]
├── data\                             # Data storage
│   ├── conversations\                # User conversation histories
│   ├── facts\                        # User fact databases
│   ├── responses\                    # Generated AI responses
│   ├── logs\                         # Application logs
│   ├── cookies.json                  # Browser session cookies
│   └── our_data.json                 # Bot's own data
└── venv\                             # Python virtual environment
```

## Core Components

### 1. Main Automation (`main.py` → `InstagramAutomation`)
- **Entry Point**: `main()` function in main.py:31
- **Main Class**: `InstagramAutomation` in scripts/instagram_automation.py:35
- **Execution Flow**: Creates automation instance and calls `run()` method
- **Error Handling**: Comprehensive error logging and graceful shutdown

### 2. Browser Automation (`browser_utils.py`)
- **Browser Setup**: Chrome browser with calibrated window positioning
- **Session Management**: Cookie handling and Instagram login state
- **Element Interaction**: Direct message navigation and chat selection
- **Positioning**: Precise window placement for multi-monitor setups

### 3. Message Processing (`message_extraction.py`)
- **Message Parsing**: Extracts messages from Instagram DOM structure
- **Conversation Threading**: Handles replies, reactions, and media attachments
- **Data Formatting**: Converts raw DOM data to structured JSON
- **Content Types**: Text, images, videos, story replies, reactions

### 4. AI Response Generation (`deepseek_api_client.py`)
- **DeepSeek Integration**: R1 model with reasoning capabilities
- **Response Generation**: Context-aware message responses
- **API Management**: Error handling, retries, rate limiting
- **Response Saving**: Timestamped response storage

### 5. Data Management (`data_utils.py`)
- **Conversation Storage**: JSON files for each user conversation
- **User Facts**: Persistent user information database
- **Message Merging**: Combines new and existing message data
- **Response Archive**: Timestamped AI response history

### 6. Window Positioning System
- **Calibrated Position**: Manually calibrated coordinates (2312, 113)
- **Multi-Monitor Support**: Secondary screen positioning
- **Fallback Detection**: Windows API-based screen detection
- **Position Methods**: Multiple alignment options available

## Key Configuration (`config.py`)

### Instagram Settings
- **Base URL**: https://www.instagram.com
- **Direct Inbox**: /direct/inbox/
- **Timeouts**: Various timeout settings for different operations
- **DOM Selectors**: Instagram-specific element selectors

### Window Positioning
```python
CALIBRATED_WINDOW_POSITION = {
    'x': 2312, 'y': 113, 'width': 883, 'height': 937
}
```

### Scroll Configuration
- **Max Attempts**: 30 scroll attempts for chat list
- **Scroll Timing**: 2-second pauses between scrolls
- **Date Navigation**: Up to 50 attempts for historical messages

### Message Processing
- **DOM Thresholds**: Minimum 10 child elements for processing
- **Retry Logic**: Up to 5 attempts for message extraction
- **Content Types**: Support for text, media, reactions, stories

## Dependencies (`requirements.txt`)
- **playwright==1.40.0**: Web automation framework
- **requests==2.31.0**: HTTP client for API calls
- **python-dotenv==1.0.0**: Environment variable management
- **pytz==2023.3**: Timezone handling

## Data Flow

### 1. New Conversation Processing
1. Extract messages from Instagram DOM
2. Save initial messages to JSON file
3. Generate AI response using message context
4. Store response with timestamp

### 2. Existing Conversation Processing  
1. Load existing conversation data
2. Extract new messages from Instagram
3. Merge with existing message history
4. Generate contextual AI response
5. Update conversation file

### 3. Message Structure
```json
{
  "date": "2025-07-21",
  "sent_by": "username", 
  "message": "text content",
  "media_attached_img": "image_alt_text",
  "reactions": "reaction_data"
}
```

## Current Implementation Status

### ✅ Completed Features
- Instagram login and navigation automation
- Message extraction from DOM structure  
- DeepSeek API integration with reasoning
- Conversation data persistence
- Multi-monitor window positioning
- Comprehensive error handling and logging
- Message flow optimization (per MESSAGE_FLOW_UPDATE.md)

### 🎯 Key Strengths
- **Robust Message Parsing**: Handles complex Instagram DOM structures
- **AI Integration**: Full DeepSeek R1 reasoning capabilities
- **Precise Positioning**: Calibrated multi-monitor window placement
- **Data Persistence**: Comprehensive conversation and user data tracking
- **Error Recovery**: Extensive error handling and recovery mechanisms

## Usage Patterns

### Basic Usage
```bash
python main.py  # Starts automation with default settings
```

### Development/Testing
```python
from scripts.instagram_automation import InstagramAutomation
automation = InstagramAutomation(headless=False)
automation.run()
```

### Position Calibration
```bash
python scripts/get_window_position.py     # Capture new position
python scripts/test_calibrated_position.py  # Test current position  
```

## File Locations for Common Tasks

### Core Logic
- **Main automation logic**: scripts/instagram_automation.py:35
- **Message extraction**: scripts/message_extraction.py
- **AI response generation**: scripts/ai_api_functions.py
- **Browser setup**: scripts/browser_utils.py

### Configuration
- **Main config**: scripts/config.py
- **Window positioning**: config.py:23 (CALIBRATED_WINDOW_POSITION)
- **DOM selectors**: config.py:67 (SELECTORS)
- **Timeout settings**: config.py:42-53

### Data Management  
- **User conversations**: data/conversations/[username].json
- **User facts**: data/facts/[username].json
- **AI responses**: data/responses/[username]_[timestamp]_response.json
- **Application logs**: data/logs/instagram_automation_[date].log

## Development Notes
- **Python Version**: Compatible with Python 3.7+
- **Environment**: Uses virtual environment (venv/)
- **Logging**: Comprehensive logging to data/logs/
- **Error Handling**: Graceful error recovery with detailed logging
- **Browser State**: Maintains session cookies for Instagram login
- **Multi-threaded**: Handles concurrent message processing

This project represents a sophisticated Instagram automation solution with AI-powered responses, precise browser control, and comprehensive data management capabilities.