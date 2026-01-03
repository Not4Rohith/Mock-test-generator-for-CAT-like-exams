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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """ Modern way to handle startup and shutdown events """
    global CAT_DB, MAT_DB, XAT_DB
    
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
    
    print(f"✅ Databases Loaded: CAT({len(CAT_DB)}), MAT({len(MAT_DB)}), XAT({len(XAT_DB)})")
    yield
    print("👋 Shutting down...")

# Initialize FastAPI with the lifespan handler
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "status": "active", 
        "service": "Multi-Exam Engine Backend",
        "stats": {
            "cat_loaded": len(CAT_DB) > 0,
            "mat_loaded": len(MAT_DB) > 0,
            "xat_loaded": len(XAT_DB) > 0
        },
        "docs_url": "/docs"
    }

# --- HELPER: SELECT DB ---
def get_db(exam_type):
    if exam_type == "MAT": return MAT_DB
    if exam_type == "XAT": return XAT_DB
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
        raise HTTPException(status_code=500, detail=f"Database for {exam_type} is empty.")

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
    if exam_type == "XAT":
        # XAT Pattern: VALR (~26), BDM (~21), QADI (~26)
        sections = [
            ("VALR", 26), 
            ("BDM", 21), 
            ("QADI", 26)
        ]
        test_structure = {}
        for sec_name, count in sections:
            sec_pool = [i for i in filtered_pool if sec_name in i['section']]
            if sec_pool:
                selected = random.sample(sec_pool, min(len(sec_pool), count))
                flat = []
                for s in selected: flat.extend(s['questions'])
                test_structure[sec_name] = flat
        return {"id": f"XAT_MOCK_{random.randint(100,999)}", "sections": test_structure}

    elif exam_type == "MAT":
        sections = [
            "Language Comprehension", "Mathematical Skills", 
            "Data Analysis & Sufficiency", "Intelligence & Critical Reasoning", 
            "Indian & Global Environment"
        ]
        test_structure = {}
        for sec in sections:
            sec_pool = [i for i in filtered_pool if i['section'] == sec]
            count = min(len(sec_pool), 30) 
            if count > 0:
                selected = random.sample(sec_pool, count)
                flat_questions = []
                for s in selected: flat_questions.extend(s['questions'])
                test_structure[sec] = flat_questions
        return {"id": f"MAT_MOCK_{random.randint(100,999)}", "sections": test_structure}

    else:
        # Default: CAT Pattern
        rc_sets = [q for q in filtered_pool if q['section'] == 'VARC' and q.get('is_set') is True]
        va_standalone = [q for q in filtered_pool if q['section'] == 'VARC' and q.get('is_set') is False]
        dilr_sets = [q for q in filtered_pool if q['section'] == 'DILR' and q.get('is_set') is True]
        qa_standalone = [q for q in filtered_pool if q['section'] == 'QA']

        varc = []
        for s in random.sample(rc_sets, min(4, len(rc_sets))): varc.extend(s['questions'])
        for q in random.sample(va_standalone, min(8, len(va_standalone))): varc.extend(q['questions'])
        
        dilr = []
        for s in random.sample(dilr_sets, min(4, len(dilr_sets))): dilr.extend(s['questions'])
        
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

    if not pool: raise HTTPException(status_code=404, detail="No questions found matching criteria.")

    random.shuffle(pool)
    practice_questions = []
    for item in pool:
        for q in item['questions']:
            if len(practice_questions) >= count: break
            if topic and topic != "ALL":
                if q.get('topic') == topic: practice_questions.append(q)
            else:
                practice_questions.append(q)

    return {
        "id": f"PRAC_{exam_type}_{random.randint(1000,9999)}",
        "mode": "practice",
        "questions": practice_questions[:count]
    }