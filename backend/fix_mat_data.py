
import json
import re
from collections import Counter

def clean_text(text):
    """
    Cleans text by fixing encoding errors, removing HTML tags, and normalizing specific symbols.
    """
    if not isinstance(text, str):
        return text
    
    # Fix common encoding errors (smart quotes/dashes)
    text = text.replace('â€™', "'")
    text = text.replace('â€œ', '"')
    text = text.replace('â€', '"')
    text = text.replace('â€“', '-')
    text = text.replace('â€¢', '-') # bullet point
    text = text.replace('`', "'") # Backticks sometimes used for quotes

    # Remove HTML tags and entities
    text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
    text = text.replace('&nbsp;', ' ')   # Replace non-breaking space
    text = text.replace('&amp;', '&')    # Replace ampersand entity
    text = text.replace('&lt;', '<')     # Replace less than
    text = text.replace('&gt;', '>')     # Replace greater than

    # Fix LaTeX-like escapes for common text elements (e.g., ordinal suffixes)
    text = text.replace('\\textsuperscript{th}', 'th')
    text = text.replace('\\textsuperscript{st}', 'st')
    text = text.replace('\\textsuperscript{nd}', 'nd')
    text = text.replace('\\textsuperscript{rd}', 'rd')

    # Handle Rupee symbol (unicode `\u20b9` and some text like `\u20b9`)
    text = text.replace('\u20b9', 'Rs.')
    text = text.replace('\\u20b9', 'Rs.') # in case it's double escaped

    # Handle mathematical italics for units if they are just text
    text = text.replace('\ud835\udc58\ud835\udc54', 'kg') # italic 'kg'
    text = text.replace('\ud835\udc5a', 'm') # italic 'm'

    # Remove any extra spaces introduced by replacements
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def classify_single_question(question_text, options_list):
    """
    Classifies a single question into one of the 5 MAT sections and infers a short topic.
    Prioritizes specific categories to handle overlaps.
    """
    text_lower = question_text.lower()
    combined_text = (question_text + " ".join(options_list)).lower()

    # SECTION: LANGUAGE COMPREHENSION
    lang_keywords = [
        "passage", "infer", "primary concern", "true as per the passage", "strengthen the claim that",
        "grammatically incorrect", "fill in the blanks", "idiom/phrase", "meaning of the idiom/phrase",
        "opposite in meaning", "best expresses the meaning", "rearrange these sentences",
        "proper order to form a meaningful paragraph", "one word substitute", "given phrase",
        "sentence is divided into four parts", "grammatically incorrect sentence",
        "most logical order of sentences", "underlined part", "correct alternative",
        "incorrect sentence", "best way of writing the sentence", "identify the error",
        "most appropriate form of writing", "vocabulary", "grammar", "reading comprehension",
        "text portion followed by four alternative summaries", "essence of the text", "analogy that is most similar",
        "word in capital letters", "choose the part that is/are grammatically incorrect",
        "choose an option, which can be substituted", "choose an option for the blank",
        "choose the most logical order", "choose the grammatically incorrect sentence",
        "identify the best way of writing", "rearrange the jumbled alphabets", "rearrange the jumbled word",
        "jumbled word and select the word which is opposite"
    ]
    if any(k in combined_text for k in lang_keywords):
        topic = "English" # Default language topic
        if "grammatically incorrect" in text_lower or "error" in text_lower or "underlined part" in text_lower or "most appropriate form of writing" in text_lower or "incorrect sentence" in text_lower or "best way of writing the sentence" in text_lower:
            topic = "Grammar"
        elif "idiom/phrase" in text_lower or "meaning of the idiom/phrase" in text_lower or "opposite in meaning" in text_lower or "best expresses the meaning" in text_lower or "one word substitute" in text_lower or "given phrase" in text_lower or "word in capital letters" in text_lower or "jumbled word and select the word which is opposite" in text_lower:
            topic = "Vocabulary"
        elif "passage" in text_lower or "infer" in text_lower or "primary concern" in text_lower or "true as per the passage" in text_lower or "strengthen the claim that" in text_lower or "text portion followed by four alternative summaries" in text_lower or "essence of the text" in text_lower or "author holds that the" in text_lower or "according to the passage":
            topic = "Reading Comprehension"
        elif "rearrange these sentences" in text_lower or "proper order to form a meaningful paragraph" in text_lower or "most logical order of sentences" in text_lower:
            topic = "Sentence Rearrangement"
        elif "fill in the blanks" in text_lower:
            topic = "Fill in the Blanks"
        elif "analogy" in text_lower or "similar to the one" in text_lower:
            topic = "Analogies"
        return "Language Comprehension", topic

    # SECTION: DATA ANALYSIS & SUFFICIENCY
    das_keywords = [
        "table shows", "graph", "chart", "data", "average", "marks", "percentage", "annual", "population", "sales",
        "revenue", "statements i", "statements ii", "sufficient to answer", "data interpretation", "sufficiency",
        "average number of", "excise duty collected", "percentage of export", "number of workers", "hectares of fsi",
        "number of girls in school", "percentage of candidates from institute", "readership per magazine",
        "average annual growth rate", "highest selling colour", "qualifying percentage", "females working in night shifts",
        "monthly expenses for water", "total dividend paid by ntpc", "average age of boys and girls",
        "average daily wages", "shares of profits", "compound interest on a sum after 3 years", "height of a right-angled triangle",
        "area of a square is equal to the area of a circle", "cost of laying the carpet", "how much did the salesman earn",
        "which number is greatest", "total surface area of a cube", "profit percentage earned by selling",
        "average height in the class", "price of movie ticket", "average number of stamps", "average of 11 observations",
        "average age of an adult class", "average age of 8 persons", "ratio of processing cost for water",
        "average annual growth rate of pal car production", "average number of females working in night shifts",
        "average monthly salary of employees", "average marks of the students", "average marks of students in four sections",
        "sex ratio we mean", "individual prices of three cameras", "numerical value of the ratio n/m",
        "area of a regular hexagon", "highest power of 5 that can completely divide n!",
        "mr. dhingra earns rs.", "positive number is exactly divisible", "radio is normally sold at a profit",
        "room 20 m x 10 m is to be painted", "train leaves from delhi", "average of \\(\\\\sqrt{0.49}\\)",
        "compare a and b", "column a column b"
    ]
    if any(k in combined_text for k in das_keywords):
        topic = "Data Interpretation"
        if "sufficien" in combined_text and ("statement" in combined_text or "statements" in combined_text) and "answer the question" in combined_text:
            topic = "Data Sufficiency"
        return "Data Analysis & Sufficiency", topic

    # SECTION: INTELLIGENCE & CRITICAL REASONING
    cr_keywords = [
        "series", "missing term", "code", "coding-decoding", "relationships", "family tree", "blood relations",
        "directions", "sitting arrangement", "statements", "conclusions", "assumptions", "arguments",
        "logical sequence", "logic", "cause and effect", "assertion (a)", "reason (r)", "premise",
        "justify the conclusion", "logically follow", "strengthen", "weaken", "underlie the argument",
        "explain the discrepancies", "hypothesised", "assumed", "person x, y, z, q live in", "clock is place",
        "ram starts from his house", "mahender walked", "aditya faces north", "queue of children",
        "number of such even numbers", "members of a family", "five senior citizens", "ages are to be computed",
        "cube has six sides", "person goes 20 m", "man was walking with his face", "musical instruments",
        "village a is 20 km to the north", "50 students admitted", "who left the earliest",
        "poets a, b, c, d, e, f, g and h", "one -rupee coin is placed", "after a get-together every person present shakes the hand",
        "queue i am the last person", "office has as many four-legged chairs", "game of cards", "girls and boys are to sit",
        "30 plants of chiku", "equilateral triangle below, rakesh", "choose the best option for the blank",
        "incomplete arguments is followed by four sentences", "ordered pair of statements where the first statement implies the second",
        "jumbled alphabets", "odd word among them", "what will be the middle letter of the word", "rearrange the jumbled alphabets"
    ]
    if any(k in combined_text for k in cr_keywords):
        topic = "Logic" # Default CR topic
        if "series" in text_lower or "missing term" in text_lower or "complete the series" in text_lower:
            topic = "Sequences & Series"
        elif "code" in text_lower or "coding" in text_lower or "written as" in text_lower or "rearranged as" in text_lower:
            topic = "Coding-Decoding"
        elif "family" in text_lower or "related to" in text_lower or "father" in text_lower or "mother" in text_lower or "brother" in text_lower or "sister" in text_lower or "son" in text_lower or "daughter" in text_lower or "grandfather" in text_lower or "grandmother" in text_lower or "uncle" in text_lower or "aunt" in text_lower or "nephew" in text_lower or "niece" in text_lower or "mother-in-law" in text_lower or "husband" in text_lower or "wife" in text_lower or "marri" in text_lower:
            topic = "Blood Relations"
        elif "sitting" in text_lower or "arrangement" in text_lower or "circular table" in text_lower or "queue" in text_lower or "plants in a row" in text_lower or "books a b c d e" in text_lower or "poets a, b, c, d, e, f, g and h" in text_lower or "five senior citizens" in text_lower or "30 plants of chiku" in text_lower:
            topic = "Seating Arrangement"
        elif "direction" in text_lower or "north" in text_lower or "south" in text_lower or "east" in text_lower or "west" in text_lower or "turned" in text_lower or "walking towards" in text_lower or "faces" in text_lower or "clock is place" in text_lower:
            topic = "Directions"
        elif "statements" in text_lower and ("conclusions" in text_lower or "assumptions" in text_lower or "arguments" in text_lower or "assertion" in text_lower or "reason (r)" in text_lower or "logically" in text_lower or "implicit" in text_lower):
            if "conclusions" in text_lower: topic = "Statement & Conclusion"
            elif "assumptions" in text_lower: topic = "Statement & Assumption"
            elif "arguments" in text_lower: topic = "Statement & Argument"
            elif "assertion (a)" in text_lower or "reason (r)" in text_lower: topic = "Assertion & Reason"
            else: topic = "Logic" # Catch all for general logic statements
        elif "jumbled alphabets" in text_lower or "odd word among them" in text_lower or "rearrange the jumbled word" in text_lower:
            topic = "Verbal Reasoning"
        elif "puzzle" in text_lower or "who is good in" in text_lower or "which book is between" in text_lower or "what is the profession of" in text_lower or "which two volumes are old engineering books" in text_lower or "name the boy who is good at all the subjects":
            topic = "Puzzles"
        elif "critical reasoning" in text_lower or "strengthen" in text_lower or "weaken" in text_lower or "undermine" in text_lower or "explain the discrepancies" in text_lower or "hypothesised" in text_lower or "assumed" in text_lower:
            topic = "Critical Reasoning"
        return "Intelligence & Critical Reasoning", topic

    # SECTION: MATHEMATICAL SKILLS
    math_op_keywords = re.compile(r'\d[\+\-\*\/%]|sum of|product of|difference of|average of|calculate|value of|equation|total amount|money|cost|profit|loss|ratio|percentage|area|volume|speed|distance|interest|time.*work|time.*speed|probability|permutation|combination|circumference|perimeter|hcf|lcm|digits|remainder|divisible by|arithmetic|algebra|geometry|mensuration|mixtures|alligation|number theory|finance|inequalities|logarithms|functions|\( \\\w+\\ \)|\\\(\w+\\)')
    if math_op_keywords.search(combined_text): # Check for math specific ops or latex/dollar signs
        topic = "Arithmetic" # Default math topic
        if "time" in text_lower and ("work" in text_lower or "fill a tank" in text_lower or "pipes" in text_lower or "taps" in text_lower or "journey" in text_lower or "hours" in text_lower or "days" in text_lower):
            topic = "Time & Work"
        elif "speed" in text_lower or "distance" in text_lower or "km/hr" in text_lower or "cyclist" in text_lower or "train" in text_lower or "boat" in text_lower or "stream" in text_lower or "aeroplane" in text_lower:
            topic = "Time, Speed & Distance"
        elif "profit" in text_lower or "loss" in text_lower or "discount" in text_lower or "cost price" in text_lower or "selling price" in text_lower or "remuneration" in text_lower or "dealer offered" in text_lower or "trader owes":
            topic = "Profit & Loss"
        elif "interest" in text_lower or "amount earns" in text_lower or "invested" in text_lower or "loan" in text_lower or "salary" in text_lower or "finance company" in text_lower or "puja bonus":
            topic = "Interest & Finance"
        elif "area" in text_lower or "volume" in text_lower or "perimeter" in text_lower or "radius" in text_lower or "height" in text_lower or "square" in text_lower or "triangle" in text_lower or "circle" in text_lower or "cylinder" in text_lower or "cone" in text_lower or "sphere" in text_lower or "cuboid" in text_lower or "angles" in text_lower or "trapezium" in text_lower or "diameter" in text_lower or "metal sheet" in text_lower or "rectangular plot" in text_lower or "qutab minar" in text_lower or "vikas minar" in text_lower or "cistern":
            topic = "Geometry & Mensuration"
        elif "mixture" in text_lower or "alligation" in text_lower or "alcohol" in text_lower or "water" in text_lower or "milk" in text_lower or "syrup" in text_lower or "tea" in text_lower or "sugar" in text_lower or "glycerin content" in text_lower or "pure salt" in text_lower:
            topic = "Mixtures & Alligation"
        elif "number" in text_lower and ("divisible by" in text_lower or "hcf" in text_lower or "lcm" in text_lower or "remainder" in text_lower or "prime" in text_lower or "whole number" in text_lower or "digits" in text_lower):
            topic = "Number Theory / Divisibility"
        elif "formed using digits" in text_lower or "permutations" in text_lower or "combinations" in text_lower or "arrangements are possible" in text_lower or "ways can" in text_lower or "number of ways" in text_lower or "price of gold increases by" in text_lower or "tax on a commodity is diminished" in text_lower or "population of a town increases geometrically" in text_lower or "pairs of black socks" in text_lower or "average sale of a car dealership" in text_lower or "trees planted on new year's day" in text_lower or "avg age of 40 boys" in text_lower:
            topic = "Permutations & Combinations"
        elif "probability" in text_lower or "dice" in text_lower or "beads" in text_lower or "socks" in text_lower or "balls" in text_lower or "target" in text_lower:
            topic = "Probability"
        elif "inequalities" in text_lower or "greater than" in text_lower or "less than" in text_lower or "equal to" in text_lower or "comparison" in text_lower or "range":
            topic = "Inequalities / Ranges"
        elif "logarithms" in text_lower or "log" in text_lower:
            topic = "Logarithms"
        elif "set of students" in text_lower or "students are below" in text_lower or "number of boys and girls in a college" in text_lower or "out of 80 students" in text_lower or "class consists of 100 students" in text_lower:
            topic = "Set Theory / Counting"
        elif "ages of" in text_lower or "age of c" in text_lower:
            topic = "Ages" # Often falls under arithmetic.
        return "Mathematical Skills", topic

    # SECTION: INDIAN & GLOBAL ENVIRONMENT (GK, Current Affairs, History, Science)
    # This is often the catch-all if not clearly math/DA/CR/Lang.
    gk_indicator_keywords = [
        "national sports day", "har ghar jal", "quad", "human development index", "pulitzer prize", "itu",
        "commonwealth games", "vayu sena medal", "liberty medal", "pm jan dhan yojana", "nabfid", "vigil aunty",
        "natgrid", "smile-75 initiative", "chief justice of india", "rupee co-operative bank", "serena williams",
        "mandla district", "border road organization", "electric double-decker bus", "paytm has partnered",
        "goodfellows", "secretary to president", "chandigarh international airport", "bibi: my story",
        "world water week", "bwf world championships", "temple of vedic planetarium", "aspirational district",
        "msme start-up expo", "women’s equality day", "unesco peace prize", "ramon magsaysay award",
        "smart solutions challenge", "aicte", "e-samadhan", "mahila nidhi", "atal tinkering labs",
        "world radio day", "oscar", "car battery acid", "maze tower", "brics new development bank",
        "minor planet is named after", "biometric seafarer identity document", "cites",
        "economic capital framework", "indian national calendar", "largest rail network", "saina nehwal",
        "kathakali", "periodic table", "lysosomes", "pocket digital bank", "indian institute of space science",
        "ashgabat", "paisa portal", "world mosquito day", "first space shuttle", "durand cup", "madhubani",
        "swachh bharat abhiyan", "parliament", "president", "lok sabha", "rajya sabha", "economic growth",
        "human rights day", "indirect tax", "largest read daily", "mini constitution", "post and telegraph",
        "indian railways", "ltte delegation", "un secretary general", "union government revenue", "earth day",
        "perejil island", "world bank", "pm of australia", "world post day", "president venezuela",
        "britain scotland referendum", "malala", "monisha kaltenborn", "west indies cricket team", "wayne rooney",
        "2016 olympic games", "quanto suv", "diesel loco modernization", "sez in mundra", "it company acquired",
        "indian origin banking firm", "posco", "steve ballmer", "nissan car brand", "timothy geithner",
        "apple patent case", "world bank chief economist", "starbucks india", "largest urban population",
        "hamid ansari", "dreamyuga", "jiyo befikar", "iit and iim city", "first woman speaker lok sabha",
        "kargil vijay divas", "cbdt", "chess piece", "thomas cup", "sugarcane research", "nokia",
        "god's own country", "cocaine narcotics gdp", "infrastructure", "oldest financial institution",
        "prima", "dudhwa national park", "jaffna", "novartis", "mahindra satyam", "steven spielberg",
        "agmark", "uttarakhand high court", "slumdog millionaire", "jyoti basu", "kyoto protocol", "gdp",
        "forest cover", "usaid", "nuclear power", "global financial integrity", "dta", "hong kong university",
        "sal borer", "percolation theory", "cricket coach", "falcon-i", "south asian football", "indian credit rating",
        "gnp", "census", "gatt", "wto", "world intellectual property", "reserve bank of india", "planning commission",
        "world population", "orhan pamuk", "national development council", "commonwealth games movement",
        "internet was developed upon", "who - washington", "fao - rome", "itu - geneva", "unicef - new york",
        "secretary general of the united nations", "geography", "history", "science", "politics", "economy",
        "current affairs", "awards", "books and authors", "sports", "days", "dates", "places", "state becomes", "state / uts",
        "ministry", "governing body", "scheme called", "president droupadi murmu", "revolutionary", "autobiography",
        "championships", "religious monument", "aspirational district", "expo & summit", "equality day",
        "peace prize", "magsaysay award", "smart solutions challenge", "digital creativity skills", "grievance redressal",
        "mahila nidhi", "atal tinkering labs", "car battery", "maze tower", "biometric seafarer",
        "economic capital framework", "national calendar", "rail network", "fencing", "wrestling", "shooting", "athletics",
        "badminton final", "freight train", "vayu sena medal", "liberty medal", "pm jan dhan yojana", "nabfid",
        "vigil aunty", "natgrid", "smile-75", "cji", "rupee co-operative bank", "tennis legend", "functionally literate",
        "steel slag", "double-decker bus", "point-of-sale", "goodfellows", "president's secretary", "chandigarh airport",
        "bibi my story", "world water week", "bwf world", "temple of vedic", "aspirational district", "msme expo",
        "women's equality", "unesco peace", "ramon magsaysay", "smart solutions", "aicte", "e-samadhan", "mahila nidhi",
        "atal tinkering", "world radio", "oscar best", "car battery", "maze tower", "brics new", "minor planet",
        "bsid", "cites", "economic capital", "indian national", "largest rail", "saina nehwal", "kathakali",
        "periodic table", "lysosomes", "pocket", "space science", "ashgabat", "paisa", "mosquito day",
        "space shuttle", "durand cup", "golden boot", "madhubani", "swachh bharat", "final approves",
        "largest private sector bank", "unctad report", "11th plan investment", "central government declared 2007",
        "'aero india 2001'", "'friendship year' between india and", "rbi holds ..... equity", "national stock exchange functions",
        "india brand equity fund", "external debt", "planning commission of india is", "percentage of india's population",
        "novel which is not the work of orhan pamuk", "chairman of the national development council", "commonwealth games movement",
        "internet was developed upon", "which among the following matches is incorrect", "secretary general of the united nations",
        "myanmar gas pipeline", "un body on climate change", "woman speaker of lok sabha", "chess piece", "thomas cup",
        "sugarcane research", "nokia comes from", "god's own country", "income cocaine and narcotics", "infrastructure sectors",
        "oldest development financial institution", "dudhwa national park", "jaffna is situated", "novartis is a/an..... company",
        "mahindra satyam", "steven spielberg", "agmark", "high court of uttarakhand", "slumdog millionaire",
        "jyoti basu", "kyoto protocol", "real gdp growth", "indian-american was recently appointed", "children below the age of",
        "infants born who do not drop out", "world's illiteracy lives", "infants born in south asia do not survive",
        "adult literacy rate in sub-saharan africa", "nuclear-risk reduction treaty", "mascot of the 33rd national games",
        "theme for the 21 st national science day", "best picture award at the 97th oscar awards", "'empowering people' is linked with",
        "chief minister of uttarakhand is", "satellites was successfully launched", "xix commonwealth games", "cricket coach death",
        "'falcon-i'", "japan has signed its first security pact", "devaluation means", "lerms-rupee convertibility",
        "tax which is not shared", "south asian football championship", "economic growth per cent has the indian credit rating agency",
        "gnp (gross national product) is the money value of", "census 200 i, which one of the fol lowing was taken as being literate",
        "gatt was succeeded by the world trade organization", "rbi not decided by", "speed swimming gear company",
        "steel industry in india has grown by", "national rural employment guarantee scheme", "sensation and memory",
        "percolation theory of unmixing", "forest diseases", "ai capabilities", "demonetization drive", "e-pharmacies",
        "pakistan", "ukraine", "india", "denmark", "japan", "usa", "russia", "china", "germany", "france", "netherlands",
        "singapore", "bangladesh", "thimphu", "maldives", "myanmar", "korea", "indonesia", "srilanka", "bhutan", "nepal",
        "brazil", "italy", "poland", "australia", "switzerland", "washington", "new york", "beijing", "london", "sofia",
        "berlin", "paris", "tokyo", "mumbai", "jodhpur", "jaipur", "pune", "guwahati", "gandhinagar", "bengaluru",
        "chennai", "hyderabad", "thiruvananthapuram", "patna", "bhopal", "raipur", "dehradun", "nainital", "haridwar",
        "kozhikode", "kolkata", "lucknow", "meerut", "nasik", "pauri", "indore", "patiala", "ludhiana"
    ]
    if any(k in combined_text for k in gk_indicator_keywords):
        topic = "Miscellaneous GK"
        if "award" in text_lower or "prize" in text_lower or "medal" in text_lower or "samman" in text_lower: topic = "Awards"
        elif "sport" in text_lower or "game" in text_lower or "cup" in text_lower or "cricket" in text_lower or "badminton" in text_lower or "tennis" in text_lower or "football" in text_lower or "hockey" in text_lower or "golf" in text_lower: topic = "Sports"
        elif "capital" in text_lower or "location" in text_lower or "city" in text_lower or "park" in text_lower or "state" in text_lower or "country" in text_lower or "headquarters" in text_lower: topic = "Geography"
        elif "pm" in text_lower or "president" in text_lower or "minister" in text_lower or "government" in text_lower or "rbi" in text_lower or "constitution" in text_lower or "parliament" in text_lower or "judiciary" in text_lower or "election" in text_lower or "act" in text_lower or "scheme": topic = "Politics"
        elif "index" in text_lower or "gdp" in text_lower or "economy" in text_lower or "bank" in text_lower or "finance" in text_lower or "investment" in text_lower or "disinvestment" in text_lower or "money" in text_lower or "budgetary support" in text_lower or "tax" in text_lower or "salary" in text_lower or "income" in text_lower: topic = "Economy"
        elif "history" in text_lower or "era" in text_lower or "launched on which date" in text_lower or "was created" in text_lower or "commitee was formed" in text_lower or "historical documentation": topic = "History"
        elif "science" in text_lower or "dna" in text_lower or "physics" in text_lower or "biology" in text_lower or "acid" in text_lower or "lysosomes" in text_lower or "periodic table" in text_lower or "space science" in text_lower or "satellite" in text_lower: topic = "Science"
        elif "ceo" in text_lower or "company" in text_lower or "brand" in text_lower or "partner" in text_lower or "corporate" in text_lower or "automoble": topic = "Companies/Branding"
        elif "book" in text_lower or "author" in text_lower or "autobiography" in text_lower: topic = "Books & Authors"
        elif "day" in text_lower or "month" in text_lower or "year" in text_lower or "date" in text_lower or "week" in text_lower: topic = "Days & Dates"
        elif "railways" in text_lower or "bus" in text_lower or "train": topic = "Transportation"
        elif "ai capabilities" in text_lower or "digital creativity skills" in text_lower or "internet service provider" in text_lower or "software company" in text_lower or "telecom giant" in text_lower: topic = "Technology"
        elif "quad" in text_lower or "itu" in text_lower or "brics" in text_lower or "un" in text_lower or "opec" in text_lower or "saarc" in text_lower or "asean" in text_lower or "commonwealth" in text_lower or "international" in text_lower or "global": topic = "International Org."
        elif "pollution" in text_lower or "environment" in text_lower or "water crisis" in text_lower or "climate change": topic = "Environment"
        return "Indian & Global Environment", topic

    # Default if nothing matches clearly (should not happen with good keywords)
    return "Indian & Global Environment", "Miscellaneous GK" # Final fallback for unclassified

# Load the raw data
# Make sure this path matches where you put the file!
# It is likely in data/raw/mat_final_final.json
with open('data/raw/mat_final_final.json', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

cleaned_data = []

for group in raw_data:
    temp_questions_classified = [] # Store classified questions temporarily
    
    # Process each question to get its individual classification and cleaned data
    for question in group['questions']:
        cleaned_q_text = clean_text(question["question_text"])
        
        # Robustly handle options: ensure it's a list of strings, splitting if necessary
        cleaned_options = []
        if isinstance(question['options'], list):
            cleaned_options = [clean_text(opt) for opt in question['options']]
        elif isinstance(question['options'], str):
            # Attempt to split by common delimiters, default to single item if no split found
            if '\n' in question['options']:
                cleaned_options = [clean_text(opt.strip()) for opt in question['options'].split('\n') if opt.strip()]
            elif ',' in question['options'] and len(question['options'].split(',')) > 1:
                cleaned_options = [clean_text(opt.strip()) for opt in question['options'].split(',') if opt.strip()]
            else:
                cleaned_options = [clean_text(question['options'])]
        
        cleaned_correct_option = clean_text(question["correct_option"]) if isinstance(question["correct_option"], str) else question["correct_option"]

        # Classify and infer topic for the current question
        assigned_section, inferred_topic = classify_single_question(
            cleaned_q_text,
            cleaned_options
        )
        
        temp_questions_classified.append({
            "id": question["id"],
            "exam_type": question["exam_type"],
            "exam_year": question["exam_year"],
            "temp_assigned_section": assigned_section, # Store temporarily
            "topic": inferred_topic, # This is the question's specific topic
            "question_text": cleaned_q_text,
            "options": cleaned_options,
            "correct_option": cleaned_correct_option,
            "image_url": question.get("image_url")
        })

    # Determine the *group's* final section. As per "Same as parent" rule, use the first question's section.
    group_final_section = "Indian & Global Environment" # Default for safety
    if temp_questions_classified:
        group_final_section = temp_questions_classified[0]['temp_assigned_section']

    new_group = {
        "group_id": group["group_id"],
        "is_set": group["is_set"],
        "section": group_final_section, # Set the group's section
        "questions": []
    }

    # Now, populate the questions for the new group, setting their 'section' to the determined group_final_section
    for q_data in temp_questions_classified:
        final_question = {
            "id": q_data["id"],
            "exam_type": q_data["exam_type"],
            "exam_year": q_data["exam_year"],
            "section": new_group["section"], # All questions in this group get the parent's section
            "topic": q_data["topic"], # Use the specific inferred topic
            "question_text": q_data["question_text"],
            "options": q_data["options"],
            "correct_option": q_data["correct_option"],
            "image_url": q_data["image_url"]
        }
        new_group['questions'].append(final_question)

    cleaned_data.append(new_group)

# Output the cleaned JSON data
json_output = json.dumps(cleaned_data, indent=2, ensure_ascii=False)

# ... (rest of the code above) ...

# Output the cleaned JSON data to a FILE
output_path = "data/mat_db.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

print(f"✅ Successfully cleaned and saved {len(cleaned_data)} groups to {output_path}")