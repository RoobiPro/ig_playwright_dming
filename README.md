# Instagram Playwright Automation

This project provides Instagram automation tools using Playwright and includes a DeepSeek API client for AI-powered response generation.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Playwright browsers:**
   ```bash
   playwright install
   ```

3. **Configure environment variables:**
   - Copy `.env` file and edit it
   - Replace `your_deepseek_api_key_here` with your actual DeepSeek API key
   - Other API keys can be added as needed

4. **Run the application:**
   ```bash
   python main.py
   ```

## DeepSeek API Client

The `scripts/deepseek_api_client.py` provides a complete interface for DeepSeek's R1 model with reasoning capabilities.

### Quick Start

```python
from scripts.deepseek_api_client import create_client_from_env

# Create client (automatically loads from .env)
client = create_client_from_env()

# Simple prompt with reasoning
response = client.simple_prompt(
    "Explain quantum computing in simple terms",
    enable_reasoning=True
)

print("Response:", response.content)
if response.reasoning:
    print("Reasoning:", response.reasoning)
```

### Features

- **Reasoning Support**: Full R1 reasoning capabilities
- **Error Handling**: Automatic retries with exponential backoff
- **Response Management**: Save responses to JSON files
- **Environment Configuration**: Easy setup with .env files
- **Multiple Usage Patterns**: Simple prompts, conversations, reasoning-focused

## Project Structure

```
├── main.py                    # Main entry point
├── scripts/                   # All Python modules
│   ├── deepseek_api_client.py # DeepSeek API client
│   ├── instagram_automation.py # Instagram automation
│   ├── config.py              # Configuration
│   └── ...                    # Other modules
├── data/                      # Data storage
├── .env                       # Environment variables
└── requirements.txt           # Dependencies
```

## Security

- Never commit `.env` files to version control
- API keys are automatically loaded from `.env`
- The `.gitignore` file is configured to exclude sensitive files

## Examples

Run the DeepSeek client examples:

```bash
cd scripts
python deepseek_api_client.py
```

This will demonstrate:
- Basic usage
- Reasoning-focused prompts
- Multi-turn conversations# ig_playwright_dming
