from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import json
import random
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GLOBAL DATA STORES ---
CAT_DB = []
MAT_DB = []

@app.on_event("startup")
def load_data():
    global CAT_DB, MAT_DB
    
    # Load CAT
    if os.path.exists("data/master_db.json"):
        try:
            with open("data/master_db.json", "r", encoding="utf-8") as f:
                CAT_DB = json.load(f)
            print(f"✅ Loaded CAT DB: {len(CAT_DB)} items.")
        except Exception as e:
            print(f"❌ Error loading CAT DB: {e}")
    else:
        print("⚠️ Warning: data/master_db.json not found.")
    
    # Load MAT
    if os.path.exists("data/mat_db.json"):
        try:
            with open("data/mat_db.json", "r", encoding="utf-8") as f:
                MAT_DB = json.load(f)
            print(f"✅ Loaded MAT DB: {len(MAT_DB)} items.")
        except Exception as e:
            print(f"❌ Error loading MAT DB: {e}")
    else:
        print("⚠️ Warning: data/mat_db.json not found.")

# --- HELPER: SELECT DB ---
def get_db(exam_type):
    if exam_type == "MAT": return MAT_DB
    return CAT_DB

@app.get("/get-topics")
def get_topics(section: str = Query("ALL"), exam_type: str = Query("CAT")):
    db = get_db(exam_type)
    unique_topics = set()
    
    for item in db:
        if section != "ALL" and item['section'] != section: continue
        for q in item['questions']:
            if q.get('topic'): unique_topics.add(q['topic'])
                
    return {"topics": sorted(list(unique_topics))}

@app.get("/generate-mock")
def generate_mock(
    exam_type: str = Query("CAT"), 
    year_start: int = Query(0),
    year_end: int = Query(9999)
):
    print(f"--- GENERATING {exam_type} MOCK ---")
    db = get_db(exam_type)
    
    if not db:
        raise HTTPException(status_code=500, detail=f"Database for {exam_type} is empty or not loaded.")

    # 1. Filter by Year
    filtered_pool = []
    for item in db:
        if not item.get('questions'): continue
        q_year = int(item['questions'][0].get('exam_year', 0))
        if year_start <= q_year <= year_end:
            filtered_pool.append(item)

    if not filtered_pool:
        raise HTTPException(status_code=404, detail="No questions found in this year range.")

    # 2. Exam Pattern Logic
    if exam_type == "MAT":
        # MAT PATTERN: 5 Sections
        sections = [
            "Language Comprehension", "Mathematical Skills", 
            "Data Analysis & Sufficiency", "Intelligence & Critical Reasoning", 
            "Indian & Global Environment"
        ]
        test_structure = {}
        
        for sec in sections:
            sec_pool = [i for i in filtered_pool if i['section'] == sec]
            
            # --- UPDATED: 30 Questions per Section ---
            count = min(len(sec_pool), 30) 
            
            if count > 0:
                selected = random.sample(sec_pool, count)
                flat_questions = []
                for s in selected: flat_questions.extend(s['questions'])
                test_structure[sec] = flat_questions
            else:
                print(f"⚠️ Warning: Skipping section '{sec}' (No questions found).")
        
        if not test_structure:
             raise HTTPException(status_code=404, detail="MAT Mock Failed: No questions found.")

        return {"id": f"MAT_MOCK_{random.randint(100,999)}", "sections": test_structure}

    else:
        # CAT PATTERN (Unchanged)
        rc_sets = [q for q in filtered_pool if q['section'] == 'VARC' and q['is_set'] is True]
        va_standalone = [q for q in filtered_pool if q['section'] == 'VARC' and q['is_set'] is False]
        dilr_sets = [q for q in filtered_pool if q['section'] == 'DILR' and q['is_set'] is True]
        qa_standalone = [q for q in filtered_pool if q['section'] == 'QA']

        selected_rc = random.sample(rc_sets, min(4, len(rc_sets)))
        selected_va = random.sample(va_standalone, min(8, len(va_standalone)))
        selected_dilr = random.sample(dilr_sets, min(4, len(dilr_sets)))
        selected_qa = random.sample(qa_standalone, min(22, len(qa_standalone)))

        varc = []
        for s in selected_rc: varc.extend(s['questions'])
        for q in selected_va: varc.extend(q['questions'])
        
        dilr = []
        for s in selected_dilr: dilr.extend(s['questions'])
        
        qa = []
        for q in selected_qa: qa.extend(q['questions'])

        return {
            "id": f"CAT_MOCK_{random.randint(100,999)}",
            "sections": { "VARC": varc, "DILR": dilr, "QA": qa }
        }

@app.get("/generate-practice")
def generate_practice(
    exam_type: str = Query("CAT"),
    section: str = Query("ALL"),
    count: int = Query(10),
    topic: str = Query(None),
    year_start: int = Query(0),
    year_end: int = Query(9999)
):
    # (Same practice logic as before)
    db = get_db(exam_type)
    if not db: raise HTTPException(status_code=500, detail="Database empty.")
    pool = []
    for item in db:
        if not item.get('questions'): continue
        q_year = int(item['questions'][0].get('exam_year', 0))
        if not (year_start <= q_year <= year_end): continue
        if section != "ALL" and item['section'] != section: continue
        if topic and topic != "ALL":
            has_topic = any(q.get('topic') == topic for q in item['questions'])
            if not has_topic: continue
        pool.append(item)

    if not pool: raise HTTPException(status_code=404, detail="No questions found.")

    random.shuffle(pool)
    selected_items = pool[:count]
    practice_questions = []
    for item in selected_items:
        for q in item['questions']:
            if topic and topic != "ALL":
                if q.get('topic') == topic: practice_questions.append(q)
            else:
                practice_questions.append(q)

    return {
        "id": f"PRAC_{exam_type}_{random.randint(1000,9999)}",
        "mode": "practice",
        "questions": practice_questions[:count]
    }