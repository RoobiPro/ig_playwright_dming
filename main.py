"""
Refactored Instagram automation main entry point
"""
from scripts.instagram_automation import InstagramAutomation
from scripts.logger import setup_logger, log_error
import traceback
import os
from dotenv import load_dotenv

def main():
    """Main entry point using refactored Instagram automation"""
    # Load environment variables
    load_dotenv()
    
    # Print .env variables for testing
    print("=== Environment Variables Test ===")
    print(f"DEEPSEEK_API_KEY: {os.getenv('DEEPSEEK_API_KEY')}")
    print(f"DEEPSEEK_BASE_URL: {os.getenv('DEEPSEEK_BASE_URL')}")
    print(f"DEEPSEEK_MODEL: {os.getenv('DEEPSEEK_MODEL')}")
    print(f"DEEPSEEK_TIMEOUT: {os.getenv('DEEPSEEK_TIMEOUT')}")
    print(f"DEEPSEEK_MAX_RETRIES: {os.getenv('DEEPSEEK_MAX_RETRIES')}")
    print(f"AI_PROVIDER: {os.getenv('AI_PROVIDER')}")
    print(f"DEEPINFRA_API_KEY: {os.getenv('DEEPINFRA_API_KEY')}")
    print("=== End Environment Variables ===")
    
    logger = setup_logger()
    
    try:
        logger.info("Starting Instagram automation (refactored version)")
        
        # Create and run automation
        automation = InstagramAutomation(headless=False)
        automation.run()
        
        logger.info("Instagram automation completed successfully")
        
    except Exception as e:
        log_error(logger, e, "main execution")
        print(f"Fatal error: {str(e)}")
        traceback.print_exc()
        
    finally:
        logger.info("Instagram automation session ended")


if __name__ == "__main__":
    main()

