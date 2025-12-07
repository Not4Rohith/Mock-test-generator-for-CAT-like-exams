import json
import glob
import os
import hashlib

# CONFIG
RAW_DATA_DIR = "data/raw"
OUTPUT_FILE = "data/master_db.json"

def clean_text(text):
    """Normalize text to ensure grouping works even if there are small spacing errors."""
    if not text:
        return ""
    return text.strip().lower()

def process_data():
    print("🚀 Starting Data Pipeline...")
    
    # 1. Load all Raw JSONs
    json_files = glob.glob(os.path.join(RAW_DATA_DIR, "*.json"))
    print(f"📂 Found {len(json_files)} raw files.")

    final_sets = []
    total_questions = 0

    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            questions = data.get("question_bank", [])
            answers = data.get("answer_keys", [])
            
            # Map Answers for O(1) Lookup
            answer_map = {item['question_id']: item['correct_option'] for item in answers}

            # Temp bucket to hold groups for THIS file
            # Key = Passage Hash, Value = List of Questions
            file_groups = {}

            for q in questions:
                # A. Merge Answer
                q['correct_option'] = answer_map.get(q['id'], None)
                
                # B. Determine Grouping Key
                passage = q.get('context_passage')
                
                if passage and len(passage) > 50:
                    # It's a Set (DILR or RC) -> Group by Passage
                    # We use a hash of the clean text to avoid storing huge keys
                    key = hashlib.md5(clean_text(passage).encode()).hexdigest()
                    is_set = True
                else:
                    # It's Standalone (QA or Parajumble) -> Group by Question ID
                    key = q['id']
                    is_set = False

                if key not in file_groups:
                    file_groups[key] = {
                        "group_id": key,
                        "is_set": is_set,
                        "section": q.get('section', 'UNKNOWN'),
                        "passage_text": passage if is_set else None,
                        "questions": []
                    }
                
                file_groups[key]["questions"].append(q)
                total_questions += 1

            # Add these groups to our master list
            final_sets.extend(file_groups.values())

        except Exception as e:
            print(f"❌ Error processing {filepath}: {e}")

    # 2. Save the Structured Database
    print(f"🧩 Grouped into {len(final_sets)} unique items (Sets + Standalones).")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_sets, f, indent=2)
    
    print(f"✅ Success! Master DB saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    process_data()