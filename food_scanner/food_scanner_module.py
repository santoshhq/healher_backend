from fastapi import APIRouter
from food_scanner import food_scanner as analyze_food
from pydantic import BaseModel

scanner = APIRouter()

class FoodImageInput(BaseModel):
    """Schema for food image analysis"""
    image_data: str  # Base64 encoded image string

@scanner.post('/food-analyse')
async def food_analyser(request: FoodImageInput):
    """
    Analyze food image and return nutrition information
    
    Args:
        request: Contains image_data (base64 string, may include data URI prefix)
        
    Returns:
        dict: Nutrition analysis or error
    """
    try:
        image_base64 = request.image_data
        
        # Strip data URI prefix if present (e.g., "data:image/jpeg;base64,")
        if "," in image_base64:
            image_base64 = image_base64.split(",", 1)[1]
        
        # Call food scanner with cleaned base64 string
        result = analyze_food(image_base64)
        return result
        
    except Exception as e:
        return {"error": f"Processing failed: {str(e)}"}