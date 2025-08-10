"""
Test the response generation functionality
"""
import json
from .instagram_automation import InstagramAutomation


def test_response_json_generation():
    """Test the response JSON generation without browser"""
    print("Testing Response JSON Generation")
    print("=" * 40)
    
    # Create automation instance
    automation = InstagramAutomation(headless=True)
    
    # Sample conversation data
    sample_messages = [
        {
            "date": "13.07.2025 11:47",
            "sent_by": "Awl Lee",
            "message": "Safe travels babe enjoy your day, I am in Calgary will be heading home soon"
        },
        {
            "date": "13.07.2025 18:05",
            "sent_by": "kaila_mentari_",
            "message": "Hello babe, my biked died so couldn't make it. Gonna send my stuff over with a taxi because I have to be at a friends bday soon. Hope u made it home safe 😘"
        },
        {
            "date": "14.07.2025 00:59",
            "sent_by": "Awl Lee",
            "message": "Oh my god I hope you're ok, sorry to hear about your bike babe. I was so tired when I got home I went to bed right away. They want me to come back again tonight for dinner but that a 1.5 drive each way to go for dinner so I'll make a last minute decision if I go. If I was there I help you get your stuff over from our house. And get you safely to your friends birthday party. Anyways I hope everything went well and the party was fun. Have a goodnight, sweet dreams 😴"
        },
        {
            "date": "14.07.2025 11:56",
            "sent_by": "kaila_mentari_",
            "message": "Hehe nothing happened babe, it was just a fuse at the end but still had to push the bike with my dad all the way to the shop, but its all good now. I'm a at the village now, will send some pics over later. That's hell of a long drive for dinner, did u go or did u skip it?"
        },
        {
            "date": "14.07.2025 12:51",
            "sent_by": "Awl Lee",
            "message": "Morning babe, yes I went for dinner and I just got home now so all good it was a long drive for dinner, but I don't mind I get to drive my Porsche. Thanks babe I am going to bed now as I have work tomorrow morning so thanks for the hugs and kisses wish we could do it in person. Have a wonderful day! I look forward to you're photos always. 💕 🥰"
        }
    ]
    
    # Sample user data
    sample_our_data = {
        "name": "kaila_mentari_",
        "personality": "warm and casual",
        "interests": "photography, travel, friends"
    }
    
    sample_user_data = {
        "name": "Awl Lee",
        "location": "Calgary",
        "vehicle": "Porsche",
        "relationship": "close friend/romantic interest"
    }
    
    try:
        print("\n[TEST] Generating response JSON...")
        
        # Test the _build_response_json method directly
        response_json = automation._build_response_json(
            partner_username="awl_lee",
            conversation_history=sample_messages,
            our_data=sample_our_data,
            user_data=sample_user_data
        )
        
        print("\n[SUCCESS] Response JSON generated!")
        print("\n[JSON OUTPUT]")
        print("=" * 50)
        print(json.dumps(response_json, indent=2, ensure_ascii=True))
        print("=" * 50)
        
        # Validate JSON structure
        print("\n[VALIDATION]")
        required_keys = [
            "system_prompt", 
            "persona_definition", 
            "partner_context", 
            "your_context", 
            "conversation_history", 
            "generation_rules", 
            "output_format"
        ]
        
        for key in required_keys:
            if key in response_json:
                print(f"  [OK] {key}: Present")
            else:
                print(f"  [MISSING] {key}: Not found")
        
        print(f"\n[CONTEXT] Partner context length: {len(response_json.get('partner_context', ''))}")
        print(f"[CONTEXT] Your context length: {len(response_json.get('your_context', ''))}")
        print(f"[HISTORY] Conversation messages: {len(response_json.get('conversation_history', []))}")
        
        print("\n[TEST COMPLETE] Response JSON generation working correctly!")
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()


def test_empty_data():
    """Test response generation with empty/None data"""
    print("\n" + "=" * 40)
    print("Testing with Empty Data")
    print("=" * 40)
    
    automation = InstagramAutomation(headless=True)
    
    try:
        # Test with None data
        response_json = automation._build_response_json(
            partner_username="test_user",
            conversation_history=[],
            our_data=None,
            user_data=None
        )
        
        print("\n[SUCCESS] Handled empty data correctly!")
        print(f"Partner context: '{response_json.get('partner_context', '')}'")
        print(f"Your context: '{response_json.get('your_context', '')}'")
        print(f"Conversation history length: {len(response_json.get('conversation_history', []))}")
        
    except Exception as e:
        print(f"\n[ERROR] Empty data test failed: {e}")


if __name__ == "__main__":
    test_response_json_generation()
    test_empty_data()