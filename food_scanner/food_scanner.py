import requests
import base64
import json
import re
import os
from dotenv import load_dotenv
load_dotenv()
invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
stream = False
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")


# 🔹 Analyze food image and return nutrition data
def food_scanner(image_base64: str) -> dict:
    """
    Analyze a food image and return nutrition information
    
    Args:
        image_base64 (str): Base64 encoded image string (without data: prefix)
        
    Returns:
        dict: Food analysis with nutrition data or error information
    """
    
    # 🔹 Validate base64 string
    if not image_base64:
        return {"error": "Image base64 string is empty or None"}
    
    if not isinstance(image_base64, str):
        return {"error": f"Image must be a string, got {type(image_base64).__name__}"}
    
    # Check if it's valid base64
    try:
        # Remove any whitespace
        image_base64_clean = image_base64.strip()
        
        # Validate base64 format
        decoded = base64.b64decode(image_base64_clean, validate=True)
        print(f"✅ Valid base64 string received ({len(decoded)} bytes)")
    except Exception as e:
        print(f"❌ Invalid base64 format: {str(e)}")
        return {"error": f"Invalid base64 format: {str(e)}"}

    # 🔹 Clean and extract JSON safely
    def clean_json_response(text):
        try:
            # remove markdown if present
            text = re.sub(r"```json|```", "", text).strip()

            # extract JSON block
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group())

            raise ValueError("No valid JSON found")

        except Exception as e:
            print("❌ JSON parsing error:", str(e))
            return {"error": "Invalid JSON response", "raw": text}

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Accept": "text/event-stream" if stream else "application/json"
    }

    payload = {
        "model": "google/gemma-3-27b-it",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """You are a nutrition expert specialized in PCOS/PCOD.

Analyze the given food image and return ONLY valid JSON.

STRICT RULES:
- when the items is fully white in color like Mlik it should product Curd or Milk 
- DO NOT use ```json or markdown
- DO NOT add explanations outside JSON
- DO NOT add text before or after JSON
- Output must be directly parsable JSON

STRICT FORMAT:

{
  "food_name": "",
  "calories": "",
  "health_score": "",
  "macros": {
    "protein": "",
    "carbs": "",
    "fats": ""
  },
  "pcos_impact": {
    "positive": "",
    "negative": ""
  },
  "recommendation": "",
  "alternative": ""
}
"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64_clean}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 800,
        "temperature": 0.2,
        "top_p": 1.0,
        "stream": stream
    }

    try:
        # 🔹 Debug: Log headers being sent
        debug_headers = {k: (v[:20] + "..." if len(str(v)) > 20 else v) if k != "Authorization" else "Bearer [REDACTED]" for k, v in headers.items()}
        print(f"\n📋 Request Headers: {debug_headers}")
        print(f"📋 API URL: {invoke_url}")
        print(f"📋 Base64 length: {len(image_base64_clean)} characters")
        
        response = requests.post(invoke_url, headers=headers, json=payload)
        response.raise_for_status()

        result = response.json()

        # 🔹 Extract model output text
        output_text = result["choices"][0]["message"]["content"]

        # 🔹 Clean JSON
        parsed_output = clean_json_response(output_text)

        print("\n✅ FINAL PARSED OUTPUT:\n")
        print(json.dumps(parsed_output, indent=2))
        return parsed_output
        

    except requests.exceptions.RequestException as e:
        print("❌ API Error:", str(e))
        if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
            if e.response.status_code == 401:
                print("\n⚠️  AUTHORIZATION ERROR (401):")
                print("   - Your NVIDIA API key is invalid or expired")
                print("   - Get a valid key from: https://build.nvidia.com/")
                print("   - Update environment: set NVIDIA_API_KEY=your-new-key")
                print(f"   - Response: {e.response.text}")
            elif e.response.status_code == 400:
                print("\n⚠️  BAD REQUEST ERROR (400):")
                print("   - Check your base64 image format")
                print("   - Make sure it's valid base64 encoded data")
                print(f"   - Response: {e.response.text}")
            else:
                print(f"   - Status Code: {e.response.status_code}")
                print(f"   - Response: {e.response.text}")
        return {"error": str(e)}

    except KeyError as e:
        print("❌ Unexpected response format:", response.text)
        return {"error": f"Unexpected response format: {str(e)}"}
    
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return {"error": str(e)}