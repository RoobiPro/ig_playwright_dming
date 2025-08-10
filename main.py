"""
Refactored Instagram automation main entry point
"""
from scripts.instagram_automation import InstagramAutomation
from scripts.logger import setup_logger, log_error
import traceback

def main():
    """Main entry point using refactored Instagram automation"""
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

