import time as tm
from openai import OpenAI
import threading
import traceback
import requests
from dotenv import load_dotenv
import os
import re
import json
from .deepseek_api_client import create_client_from_env

load_dotenv(override=True)



requested_ai_provider = os.getenv("AI_PROVIDER")

def ask_ai_provider(prompt, mute=False):
    print("AI PROVIDER")
    print(requested_ai_provider)
    if requested_ai_provider == 'DEEPINFRA':
        print("USING DEEPINFRA")
        response = ask_deepinfra(prompt, model='deepseek-ai/DeepSeek-V3-0324')
        return response
    elif requested_ai_provider == 'DEEPSEEK':
        print("USING DEEPSEEK")
        response = ask_R1(prompt, model='deepseek-reasoner', mute=mute)
        return response
    elif requested_ai_provider == 'GEMINI':
        print("USING GEMINI")
        response = ask_gemini(prompt, mute=mute)
        return response

def ask_deepinfra(prompt, system_message="You are a highly intelligent AI assistant. Your primary goal is to provide responses that demonstrate deep reasoning, accuracy, and strict adherence to the user's instructions.", model='deepseek-ai/DeepSeek-V3-0324'):
    try:
        # Ensure .env file is loaded with override
        load_dotenv(override=True)
        
        client = OpenAI(
            api_key=os.getenv("DEEPINFRA_API_KEY"),
            base_url="https://api.deepinfra.com/v1/openai"
        )
        print(f"Sending request to DeepInfra API.")
        chat_completion = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3-0324",
        messages=[
            {"role": "system", "content": "You will be generating messages for Instagram direct messaging"},
            {"role": "user", "content": prompt}
        ],
        # --- Settings meticulously optimized for High Reasoning & Precision ---
        
        # 1. Maximize Reasoning Effort:
        reasoning_effort='high',  # Explicitly instructs the model to prioritize reasoning capabilities.
        
        # 2. Enhance Precision and Determinism:
        temperature=0.2,          # Low temperature reduces randomness, making output focused and predictable, aiding precision and adherence.
        
        # 3. Ensure Comprehensive Consideration (while maintaining focus via temperature):
        top_p=1.0,                # Allows the model to consider all tokens, preventing premature cutoff of potentially valid reasoning paths. Used in conjunction with low temperature.
        
        # 4. Provide Sufficient Output Length for Detailed Reasoning:
        max_tokens=4096,          # Generous limit to prevent truncation of complex reasoning or detailed explanations.
        
        # --- Other parameters kept at default as they don't enhance reasoning/precision further in this configuration ---
        # min_p=0,                # Default, disabled. Not needed with temp/top_p combo.
        # top_k=0,                # Default, disabled. Not needed with temp/top_p combo.
        # stream=False            # Default, affects delivery not quality.
        # stop=None               # Default, unless specific stop sequences are required by the prompt structure.
        )
        
        response_content = chat_completion.choices[0].message.content
        
        # print(f"--- Usage Stats ---")
        # print(f"Prompt tokens: {chat_completion.usage.prompt_tokens}")
        # print(f"Completion tokens: {chat_completion.usage.completion_tokens}")
        # print(f"Total tokens: {chat_completion.usage.total_tokens}")
        # print(f"-------------------")
        
        print("=================== R E S P O N S E ===================")
        print(response_content)
        print("===================================================")
        
        return {
            "content": response_content,
            "usage": {
                "prompt_tokens": chat_completion.usage.prompt_tokens,
                "completion_tokens": chat_completion.usage.completion_tokens,
                "total_tokens": chat_completion.usage.total_tokens
            },
            "success": True
        }

    except Exception as e:
        print(f"An error occurred during API call: {e}")
        return {
            "content": None,
            "error": str(e),
            "success": False
        }
    
def ask_gemini(prompt, model='gemini-2.0-flash', mute=False):
    # Ensure .env file is loaded with override
    load_dotenv(override=True)
    
    print(f"Model being used: {model}")
    if not mute:
        print("=================== P R O M P T ===================")
        print(prompt)
        print("===================================================")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY environment variable not found")
        return False

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    wait_time = 400
    for attempt in range(3):
        print(f"Attempt {attempt + 1}")
        
        start_time = tm.time()
        current_timeout = 15 + wait_time
        
        def worker():
            try:
                payload = json.dumps({
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }]
                })
                headers = {'Content-Type': 'application/json'}
                
                resp = requests.post(url, headers=headers, data=payload, timeout=current_timeout)
                elapsed = tm.time() - start_time
                if elapsed > current_timeout:
                    print(f"Response received after timeout, discarding.")
                    return
                
                if resp.status_code != 200:
                    worker.error = Exception(f"API error {resp.status_code}: {resp.text}")
                    return
                
                response_data = resp.json()
                if not response_data.get('candidates'):
                    worker.error = Exception("No candidates in response")
                    return
                
                text = response_data['candidates'][0]['content']['parts'][0]['text']
                
                # Try to extract JSON from response
                json_str = None
                try:
                    # First try direct parse
                    json_data = json.loads(text)
                    worker.resp = json_data
                except json.JSONDecodeError:
                    # Try extracting from code block
                    json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1).strip()
                        json_data = json.loads(json_str)
                        worker.resp = json_data
                    else:
                        # Fallback to search for any JSON
                        json_match = re.search(r'{.*}', text, re.DOTALL)
                        if json_match:
                            json_data = json.loads(json_match.group())
                            worker.resp = json_data
                        else:
                            worker.error = Exception("No valid JSON found in response")
                
            except Exception as e:
                elapsed = tm.time() - start_time
                if elapsed <= current_timeout:
                    worker.error = e
                    print(f"Exception during API call: {e}")
                else:
                    print(f"Exception after timeout: {e} (not logged)")
        
        worker.resp = None
        worker.error = None
        
        t = threading.Thread(target=worker)
        t.start()
        t.join(timeout=current_timeout)
        
        if worker.resp is not None:
            print(f"Attempt {attempt + 1} succeeded.")
            print("=================== R E S P O N S E ===================")
            print(worker.resp)
            print("=======================================================")
            
            # Return in standardized format
            if isinstance(worker.resp, dict) and 'message' in worker.resp:
                return {
                    "content": worker.resp['message'],
                    "success": True
                }
            else:
                # If it's a different format, try to extract message or use as-is
                content = worker.resp.get('message') if isinstance(worker.resp, dict) else str(worker.resp)
                return {
                    "content": content,
                    "success": True
                }
        elif worker.error is not None:
            print(f"Attempt {attempt + 1} failed with error:")
            print(traceback.print_exc())
        else:
            print(f"Attempt {attempt + 1} timed out. Increasing wait time...")
            wait_time += 45
            tm.sleep(wait_time)
    
    print("All 3 attempts failed.")
    return {
        "content": None,
        "error": "All 3 attempts failed",
        "success": False
    }

def ask_R1(prompt, model='deepseek-reasoner', mute=False):
    """Ask DeepSeek R1 model using the DeepSeek client"""
    try:
        if not mute:
            print("=================== P R O M P T ===================")
            print(prompt)
            print("===================================================")
        
        # Create DeepSeek client
        client = create_client_from_env()
        
        # Generate response
        result = client.generate_response(prompt)
        
        if not mute:
            print("=================== R E S P O N S E ===================")
            print(result)
            print("=======================================================")
        
        return result
        
    except Exception as e:
        print(f"An error occurred during DeepSeek API call: {e}")
        return {
            "content": None,
            "error": str(e),
            "success": False
        }