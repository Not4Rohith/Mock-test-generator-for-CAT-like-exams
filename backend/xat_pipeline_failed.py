import requests
from bs4 import BeautifulSoup
import json
import uuid
import re
import time
import os
import hashlib

# --- CONFIG ---
BASE_URL = "https://cdquestions.com/exams/xat-questions"
DOMAIN = "https://cdquestions.com"
OUTPUT_FILE = "data/xat_db_final_v4.json"

def get_q_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def clean_text(text):
    if not text: return ""
    text = str(text).strip()
    replacements = {"â€™": "'", "â€œ": '"', "â€": '"', "â€“": "-", "â€”": "-", "&nbsp;": " ", "&amp;": "&", "Â": "", "\\(": "$", "\\)": "$"}
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Strip most HTML tags but keep structure for math
    text = re.sub(r'<(?!/?sub|/?sup|/?b|/?i)[^>]+>', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def get_soup(url):
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Arch Linux; rv:120.0) Gecko/20100101 Firefox/120.0'}
    try:
        response = requests.get(url, headers=headers, timeout=25)
        if response.status_code == 200: return BeautifulSoup(response.text, 'html.parser')
    except: pass
    return None

def extract_content_image(block):
    """Specifically looks for images INSIDE the question/passage content, not the logo."""
    # Find the content div first
    content_div = block.find('div', class_=re.compile(r'ck-content|Question_questionText|Question_description'))
    if not content_div:
        return None
    
    img = content_div.find('img')
    if not img: return None
    
    # Ignore common UI icons/logos
    src = img.get('data-src') or img.get('src')
    if not src or "base64" in src or "logo" in src.lower() or "icon" in src.lower():
        return None
        
    return src if src.startswith('http') else DOMAIN + src

def extract_page_data(soup, year, topic, section):
    passage_el = soup.find('div', class_=re.compile(r'comprehension|passage|Question_description'))
    passage_text = clean_text(passage_el.get_text()) if passage_el else None
    
    # Check for image in passage area specifically
    passage_image = extract_content_image(soup) if passage_el else None
    
    q_blocks = soup.find_all('div', class_=re.compile(r'Question_questionWrapper|Question_container'))
    if not q_blocks:
        main = soup.find('div', id='__next')
        q_blocks = [main] if main else []

    extracted_questions = []
    for block in q_blocks:
        if not block: continue
        q_text_el = block.find(['div', 'h1', 'h2', 'h3'], class_=re.compile(r'questionText|text-title|ck-content'))
        if not q_text_el: continue
        q_text = clean_text(q_text_el.get_text())
        if len(q_text) < 10: continue

        # --- IMAGE FIX ---
        # Checks question block first, falls back to passage image if it exists
        img_url = extract_content_image(block) or passage_image

        # --- OPTIONS ---
        options = []
        opt_items = block.find_all(['li', 'button'], attrs={"data-csm-title": True})
        for li in opt_items:
            opt_content = li.find('div', class_=re.compile(r'ck-content|content-section'))
            val = clean_text(opt_content.get_text()) if opt_content else clean_text(li.get_text())
            val = re.sub(r'^[A-E1-5][\.\):]\s*', '', val)
            if val: options.append(val)

        # --- CORRECT OPTION FIX ---
        correct_option = ""
        # 1. Search literal text (reliable if solution is rendered)
        full_text = block.get_text(separator=' ')
        match = re.search(r'The Correct Option is\s*([A-E])', full_text, re.I)
        if match:
            correct_option = match.group(1).upper()
        
        # 2. Fallback: Check if an option has a 'correct' class applied
        if not correct_option:
            for li in opt_items:
                if 'correct' in str(li.get('class', [])).lower() or li.find(class_=re.compile(r'correct|active|success')):
                    correct_option = li.get('data-csm-title', '').upper()

        if q_text and len(options) >= 2:
            extracted_questions.append({
                "id": f"{year}_{section}_{uuid.uuid4().hex[:6]}",
                "question_text": q_text,
                "has_image": True if img_url else False,
                "image_url": img_url,
                "options": options,
                "correct_option": correct_option,
                "topic": topic
            })

    if not extracted_questions: return None
    return {
        "group_id": uuid.uuid4().hex,
        "exam_year": year,
        "section": section,
        "is_set": len(extracted_questions) > 1,
        "passage_text": passage_text if len(extracted_questions) > 1 else None,
        "questions": extracted_questions
    }

def main():
    print("🚀 Starting XAT Scraper V4 (Fixed Image Scoping & Answers)...")
    all_data = []
    seen_hashes = set()
    
    for page_num in range(1, 41): 
        current_url = BASE_URL if page_num == 1 else f"{BASE_URL}/page-{page_num}"
        print(f"--- Processing Page {page_num} ---")
        soup = get_soup(current_url)
        if not soup: break
        
        links = soup.find_all('a', href=re.compile(r'/exams/questions/'))
        for link_el in links:
            detail_soup = get_soup(DOMAIN + link_el['href'])
            if not detail_soup: continue
            
            meta = detail_soup.get_text()
            year_match = re.search(r'20(1[89]|2[0-5])', meta)
            year = int(year_match.group(0)) if year_match else 2025
            
            breadcrumb = detail_soup.find('div', class_=re.compile(r'breadcrumb'))
            topic = clean_text(breadcrumb.find_all('a')[-1].get_text()) if breadcrumb else "General"
            
            # Auto-detect section
            section = "QA"
            if "Verbal" in meta or "VARC" in meta: section = "VARC"
            elif "Decision" in meta: section = "DM"

            group_data = extract_page_data(detail_soup, year, topic, section)
            if group_data:
                q_sig = get_q_hash(group_data['questions'][0]['question_text'])
                if q_sig not in seen_hashes:
                    seen_hashes.add(q_sig)
                    all_data.append(group_data)
                    # Instant Save
                    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                        json.dump(all_data, f, indent=2, ensure_ascii=False)
            time.sleep(0.5)

if __name__ == "__main__":
    main()