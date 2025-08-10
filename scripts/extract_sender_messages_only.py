import os
import json

def process_conversations():
    # Define the target directory
    directory = 'data/conversations'
    
    # Iterate through all files in the directory
    for filename in os.listdir(directory):
        print("========================================================")
        print(filename)
        print("========================================================")
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)
            
            try:
                # Read and parse JSON file
                with open(filepath, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
                
                # Process each message
                for message in messages:
                    if message.get('sent_by') != 'kaila_mentari_':
                        msg_content = message.get('message', '')
                        
                        # Handle list-type messages
                        if isinstance(msg_content, list):
                            # Join list elements into a single string
                            msg_content = " ".join(str(item) for item in msg_content)
                        
                        print(f'"{msg_content}",')
            
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

if __name__ == '__main__':
    process_conversations()