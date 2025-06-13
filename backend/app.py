from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
import google.generativeai as genai
import os
import time
from gtts import gTTS
import re
from fuzzywuzzy import fuzz, process  

app = Flask(__name__)
CORS(app)

# MongoDB Connection
MONGO_URI = "mongodb+srv://niranjanmali960:Nir%40nj%40nM0507@chintu.ie01j.mongodb.net/?retryWrites=true&w=majority&appName=Chintu"
client = MongoClient(MONGO_URI)
db = client["recipe_db"]
recipes = db["recipes"]

# Google Gemini API Key (Ensure it's valid)
GENAI_API_KEY = "AIzaSyCQxidrFVCMJhhHTDzVez9KSb1Z79xsOvg"
genai.configure(api_key=GENAI_API_KEY)

STATIC_FOLDER = "static"
os.makedirs(STATIC_FOLDER, exist_ok=True)

def extract_dish_name(user_input):
    common_phrases = ["give me a recipe for", "Hey Chef", "Can you tell me", "I want to cook", "recipe for"]
    clean_text = user_input.lower()
    for phrase in common_phrases:
        clean_text = clean_text.replace(phrase.lower(), "").strip()
    return clean_text.title()

def find_closest_match(dish_name):
    all_dishes = [recipe["title"] for recipe in recipes.find()]
    match, score = process.extractOne(dish_name, all_dishes) if all_dishes else (None, 0)
    return match if score > 70 else None

@app.route('/get-recipe', methods=['GET'])
def get_recipe():
    user_query = request.args.get('name', '').strip()
    if not user_query:
        return jsonify({"error": "Recipe name is required"}), 400

    dish_name = extract_dish_name(user_query)
    print(f"🔍 Extracted Dish Name: '{dish_name}'")

    recipe = recipes.find_one({"title": {"$regex": f"^{re.escape(dish_name)}$", "$options": "i"}})

    if not recipe:
        closest_match = find_closest_match(dish_name)
        if closest_match:
            print(f"⚠ Suggesting closest match: {closest_match}")
            recipe = recipes.find_one({"title": {"$regex": f"^{re.escape(closest_match)}$", "$options": "i"}})
            if recipe:
                dish_name = closest_match

    if recipe:
        print(f"✅ Returning Recipe for: {recipe['title']}")
        recipe["_id"] = str(recipe["_id"])
        response_text = f"Here is the recipe for {recipe['title']}: Ingredients - {', '.join(recipe.get('ingredients', []))}. Steps: " + " ".join(recipe.get('steps', []))

        voice_filename = f"response_{int(time.time())}.mp3"
        voice_path = os.path.join(STATIC_FOLDER, voice_filename)
        tts = gTTS(text=response_text, lang="en")
        tts.save(voice_path)

        return jsonify({
            "msg": "success",
            "recipe": recipe,
            "response": response_text,
            "voice": f"/static/{voice_filename}"
        })

    print("🤖 Forwarding request to Google Gemini AI...")
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(user_query)
        print(f"🔍 Gemini API Raw Response: {response}")
        gk_response = getattr(response, "text", "Sorry, I couldn't generate a response at the moment.").strip()

        voice_filename = f"response_{int(time.time())}.mp3"
        voice_path = os.path.join(STATIC_FOLDER, voice_filename)
        tts = gTTS(text=gk_response, lang="en")
        tts.save(voice_path)

        return jsonify({
            "msg": "success",
            "response": gk_response,
            "voice": f"/static/{voice_filename}"
        })
    except Exception as e:
        print(f"⚠ Google Gemini API Error: {e}")
        return jsonify({"error": "Sorry, there was an issue fetching a response."})





@app.route('/search-by-ingredients', methods=['GET'])
def search_by_ingredients():
    user_input = request.args.get('ingredients', '').strip().lower()
    if not user_input:
        return jsonify({"error": "Ingredients are required"}), 400

    # Clean input to extract likely ingredients (e.g., remove quantities and verbs)
    cleaned_input = re.sub(r'\b(have|i|a|an|some|cup|cups|of|and|with|spoon|tablespoon|teaspoon|ml|gm|grams|kg|litre|liter)\b', '', user_input)
    input_ingredients = [word.strip() for word in cleaned_input.split() if word.strip()]

    matched_recipes = []

    for recipe in recipes.find():
        recipe_ings = [ing.lower() for ing in recipe.get("ingredients", [])]
        match_score = 0

        for user_ing in input_ingredients:
            for recipe_ing in recipe_ings:
                score = fuzz.partial_ratio(user_ing, recipe_ing)
                if score > 60:
                    match_score += 1
                    break  # Only count first match per user ingredient

        if match_score > 0:
            matched_recipes.append((recipe["title"], match_score))

    matched_recipes.sort(key=lambda x: x[1], reverse=True)
    suggestions = [title for title, score in matched_recipes[:5]]

    if suggestions:
        return jsonify({"msg": "success", "suggestions": suggestions})
    else:
        return jsonify({"msg": "no_match", "suggestions": []})


@app.route('/static/<filename>')
def serve_static(filename):
    return send_from_directory(STATIC_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)
