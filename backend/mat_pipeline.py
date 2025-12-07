import json
import uuid
import re

# CONFIG
INPUT_FILE = "data/raw/mat_final_final.json"
OUTPUT_FILE = "data/mat_db.json"

def clean_text(text):
    if not text: return ""
    
    # 1. Convert to string and strip
    text = str(text).strip()
    
    # 2. Fix common Encoding Glitches (Mojibake)
    replacements = {
        "â€™": "'", "â€œ": '"', "â€": '"', "â€“": "-", "â€”": "-",
        "&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">",
        "Â": "", "â€¦": "..."
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
        
    # 3. Strip HTML Tags (e.g., <p>, <br>)
    text = re.sub(r'<[^>]+>', '', text)
    
    # 4. Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def guess_section(topic, question_text):
    """
    Decides the section based on Topic AND Question Content.
    """
    # Combine them for searching (lower case)
    content = (str(topic) + " " + str(question_text)).lower()
    
    # --- 1. DATA ANALYSIS (High Priority) ---
    # Look for data interpretation keywords
    if any(x in content for x in ["bar chart", "pie chart", "data interpretation", "sufficiency", "caselet", "table below", "graph shows"]):
        return "Data Analysis & Sufficiency"

    # --- 2. LANGUAGE (High Priority) ---
    # Look for grammar/reading keywords
    if any(x in content for x in ["synonym", "antonym", "passage", "comprehension", "grammatical", "idiom", "phrase", "spelt", "adjective", "verb", "jumbled sentence"]):
        return "Language Comprehension"

    # --- 3. GK (Strict Check) ---
    # GK usually talks about countries, history, science, but NEVER contains equations or "solve"
    if any(x in content for x in ["capital of", "currency", "minister", "author of", "headquarter", "invented", "award", "trophy", "located in", "which year"]):
        # SAFETY: Ensure it's not a math word problem about years
        if not any(math_word in content for math_word in ["calculate", "ratio", "average", "solve", "x", "percentage"]):
            return "Indian & Global Environment"

    # --- 4. REASONING ---
    if any(x in content for x in ["coding", "decoding", "series", "blood relation", "direction", "syllogism", "assertion", "reasoning", "argument", "conclusion", "arrangement"]):
        return "Intelligence & Critical Reasoning"

    # --- 5. MATH (The "Catch-All") ---
    # Most leftovers are math, but let's confirm with keywords
    return "Mathematical Skills" 

def process_mat():
    print("🚀 Starting Advanced MAT Pipeline...")
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            
        print(f"📂 Found {len(raw_data)} raw MAT questions.")
        
        cleaned_data = []
        valid_count = 0
        
        for item in raw_data:
            q_text = clean_text(item.get('question_text'))
            options = item.get('options', [])
            
            # Skip empty questions
            if not q_text or len(q_text) < 5: 
                continue

            # Standardize Options: Ensure it's a list of strings
            final_options = []
            if isinstance(options, list):
                final_options = [clean_text(opt) for opt in options if opt]
            elif isinstance(options, str):
                # Try to split by comma or newlines if it's a dirty string
                final_options = [clean_text(o) for o in options.split(',')]
            
            # Determine Section
            topic = item.get('topic', '')
            section = guess_section(topic, q_text)
            
            # Generate ID
            q_id = f"MAT_{uuid.uuid4().hex[:8].upper()}"
            
            new_q = {
                "id": q_id,
                "exam_type": "MAT",
                "exam_year": 0, 
                "section": section,
                "topic": topic if topic else "General",
                "question_text": q_text,
                "options": final_options,
                "correct_option": clean_text(item.get('answer')),
                "image_url": item.get('image_url'), 
                "context_passage": None,
                "is_set": False
            }
            
            wrapper = {
                "group_id": q_id + "_GRP",
                "is_set": False,
                "section": section,
                "questions": [new_q]
            }
            
            cleaned_data.append(wrapper)
            valid_count += 1
            
        print(f"🧩 Processed {valid_count} clean items.")
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=2)
            
        print(f"✅ Success! MAT DB saved to {OUTPUT_FILE}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    process_mat()