from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import json
import random
import os

# --- GLOBAL DATA STORES ---
CAT_DB = []
MAT_DB = []
XAT_DB = []
CMAT_DB = [] # New: CMAT Store

@asynccontextmanager
async def lifespan(app: FastAPI):
    """ Modern way to handle startup and shutdown events """
    global CAT_DB, MAT_DB, XAT_DB, CMAT_DB
    
    # Load CAT
    if os.path.exists("data/master_db.json"):
        with open("data/master_db.json", "r", encoding="utf-8") as f:
            CAT_DB = json.load(f)
            
    # Load MAT
    if os.path.exists("data/mat_db.json"):
        with open("data/mat_db.json", "r", encoding="utf-8") as f:
            MAT_DB = json.load(f)

    # Load XAT
    if os.path.exists("data/xat_db.json"):
        with open("data/xat_db.json", "r", encoding="utf-8") as f:
            XAT_DB = json.load(f)

    # New: Load CMAT
    if os.path.exists("data/cmat_db.json"):
        with open("data/cmat_db.json", "r", encoding="utf-8") as f:
            CMAT_DB = json.load(f)
    
    print(f"✅ Databases Loaded: CAT({len(CAT_DB)}), MAT({len(MAT_DB)}), XAT({len(XAT_DB)}), CMAT({len(CMAT_DB)})")
    yield
    print("👋 Shutting down...")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- HELPER: SELECT DB ---
def get_db(exam_type):
    if exam_type == "MAT": return MAT_DB
    if exam_type == "XAT": return XAT_DB
    if exam_type == "CMAT": return CMAT_DB # New: CMAT selection
    return CAT_DB

@app.get("/")
def read_root():
    return {
        "status": "active", 
        "service": "Multi-Exam Engine Backend",
        "stats": {
            "cat_loaded": len(CAT_DB) > 0,
            "mat_loaded": len(MAT_DB) > 0,
            "xat_loaded": len(XAT_DB) > 0,
            "cmat_loaded": len(CMAT_DB) > 0
        }
    }

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
        raise HTTPException(status_code=500, detail=f"Database for {exam_type} is empty.")

    # Filter by Year
    filtered_pool = []
    for item in db:
        if not item.get('questions'): continue
        q_year = int(item['questions'][0].get('exam_year', 0))
        if year_start <= q_year <= year_end:
            filtered_pool.append(item)

    if not filtered_pool:
        raise HTTPException(status_code=404, detail="No questions found in this range.")

    # --- CMAT PATTERN LOGIC ---
    if exam_type == "CMAT":
        # CMAT: 5 Sections, 20 Qs each
        cmat_pattern = [
            ("Quantitative Techniques and Data Interpretation", 20),
            ("Logical Reasoning", 20),
            ("Language Comprehension", 20),
            ("General Awareness", 20),
            ("Innovation and Entrepreneurship", 20)
        ]
        test_structure = {}
        for sec_name, count in cmat_pattern:
            # Filter pool for exact section name
            sec_pool = [i for i in filtered_pool if i['section'] == sec_name]
            if sec_pool:
                # CMAT often has RC sets. We sample 'items' and then flatten.
                # To get exactly 20, we may need to trim after flattening.
                selected_items = random.sample(sec_pool, min(len(sec_pool), count))
                flat = []
                for s in selected_items:
                    # Inject passage into question if it's a set
                    for q in s['questions']:
                        q['context_passage'] = s.get('passage_text')
                    flat.extend(s['questions'])
                test_structure[sec_name] = flat[:count] # Strict 20 count
        return {"id": f"CMAT_MOCK_{random.randint(100,999)}", "sections": test_structure}

    elif exam_type == "XAT":
        sections = [("VALR", 26), ("BDM", 21), ("QADI", 26)]
        test_structure = {}
        for sec_name, count in sections:
            sec_pool = [i for i in filtered_pool if sec_name in i['section']]
            if sec_pool:
                selected = random.sample(sec_pool, min(len(sec_pool), count))
                flat = []
                for s in selected: 
                    for q in s['questions']: q['context_passage'] = s.get('passage_text')
                    flat.extend(s['questions'])
                test_structure[sec_name] = flat[:count]
        return {"id": f"XAT_MOCK_{random.randint(100,999)}", "sections": test_structure}

    elif exam_type == "MAT":
        sections = ["Language Comprehension", "Mathematical Skills", "Data Analysis & Sufficiency", "Intelligence & Critical Reasoning", "Indian & Global Environment"]
        test_structure = {}
        for sec in sections:
            sec_pool = [i for i in filtered_pool if i['section'] == sec]
            if sec_pool:
                selected = random.sample(sec_pool, min(len(sec_pool), 30))
                flat = []
                for s in selected: 
                    for q in s['questions']: q['context_passage'] = s.get('passage_text')
                    flat.extend(s['questions'])
                test_structure[sec] = flat[:40] # MAT is usually 40, adjust based on your needs
        return {"id": f"MAT_MOCK_{random.randint(100,999)}", "sections": test_structure}

    else:
        # Default: CAT Pattern
        rc_sets = [q for q in filtered_pool if q['section'] == 'VARC' and q.get('is_set') is True]
        va_standalone = [q for q in filtered_pool if q['section'] == 'VARC' and q.get('is_set') is False]
        dilr_sets = [q for q in filtered_pool if q['section'] == 'DILR' and q.get('is_set') is True]
        qa_standalone = [q for q in filtered_pool if q['section'] == 'QA']

        varc = []
        for s in random.sample(rc_sets, min(4, len(rc_sets))):
            for q in s['questions']: q['context_passage'] = s.get('passage_text')
            varc.extend(s['questions'])
        for q in random.sample(va_standalone, min(8, len(va_standalone))): varc.extend(q['questions'])
        
        dilr = []
        for s in random.sample(dilr_sets, min(4, len(dilr_sets))):
            for q in s['questions']: q['context_passage'] = s.get('passage_text')
            dilr.extend(s['questions'])
        
        qa = []
        for q in random.sample(qa_standalone, min(22, len(qa_standalone))): qa.extend(q['questions'])

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
    db = get_db(exam_type)
    if not db: raise HTTPException(status_code=500, detail="Database empty.")
    
    pool = []
    for item in db:
        if not item.get('questions'): continue
        q_year = int(item['questions'][0].get('exam_year', 0))
        if not (year_start <= q_year <= year_end): continue
        if section != "ALL" and section not in item['section']: continue
        
        if topic and topic != "ALL":
            if not any(q.get('topic') == topic for q in item['questions']): continue
        pool.append(item)

    if not pool: raise HTTPException(status_code=404, detail="No questions found.")

    random.shuffle(pool)
    practice_questions = []
    for item in pool:
        for q in item['questions']:
            if len(practice_questions) >= count: break
            # Inject passage for display
            q['context_passage'] = item.get('passage_text')
            if topic and topic != "ALL":
                if q.get('topic') == topic: practice_questions.append(q)
            else:
                practice_questions.append(q)

    return {
        "id": f"PRAC_{exam_type}_{random.randint(1000,9999)}",
        "questions": practice_questions[:count]
    }