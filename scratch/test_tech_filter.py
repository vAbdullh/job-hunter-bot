import re

def is_technical_job(title: str) -> bool:
    if not title:
        return False
    title_lower = title.lower()
    
    # 1. Direct tech keywords/roles (case-insensitive, substring is fine)
    direct_tech_keywords = [
        "developer", "programmer", "webmaster", "frontend", "front-end", 
        "backend", "back-end", "fullstack", "full-stack", "devops", "sysadmin", 
        "cybersecurity", "cyber security", "cloud", "ui/ux", "ux/ui", "helpdesk", "help desk",
        "data scientist", "data analyst", "data science", "data engineer",
        "database", "network administrator", "network specialist", "systems administrator",
        "information technology", "computer science", "software",
        "python", "javascript", "typescript", "react", "flutter", "laravel", "django", 
        "kubernetes", "docker", "aws", "azure", "gcp", "golang", "swift", "kotlin",
        # Arabic technical terms
        "مبرمج", "مطور", "برمجيات", "شبكات", "بيانات", "سحابية", 
        "أمن سيبراني", "أمن المعلومات", "دعم فني", "قواعد بيانات"
    ]
    
    for kw in direct_tech_keywords:
        if kw in title_lower:
            return True
            
    # 2. Whole-word only keywords (to avoid false positives in substrings)
    whole_words = ["it", "ict", "dev", "tech", "web", "برمجة", "حاسب", "نظم"]
    for word in whole_words:
        pattern = r'\b' + re.escape(word) + r'\b'
        # For Arabic words, word boundaries can be tricky in python's re module, but usually \b or custom checks work.
        if re.search(pattern, title_lower):
            return True
            
    # 3. Engineer check (only count if it's a tech/IT/software engineer)
    if "engineer" in title_lower or "مهندس" in title_lower:
        tech_prefixes = [
            "software", "system", "network", "cloud", "devops", "data", "security", 
            "computer", "qa", "test", "web", "it", "infrastructure", "platform", "sre", 
            "fullstack", "full-stack", "frontend", "backend", "application", "support",
            # Arabic
            "برمجيات", "شبكات", "حاسب", "معلومات", "اتصالات", "نظم"
        ]
        for pref in tech_prefixes:
            if pref in title_lower:
                return True

    return False

# Test cases
test_jobs = [
    ("Software Engineer", True),
    ("Mechanical Engineer", False),
    ("Civil Engineer", False),
    ("IT Support Specialist", True),
    ("Marketing Manager", False),
    ("Python Developer", True),
    ("Sales Representative", False),
    ("مطور واجهات", True),
    ("مهندس برمجيات", True),
    ("مهندس مدني", False),
    ("محلل بيانات", True),
    ("Web Designer", True),
    ("Digital Marketing SpecialIT", False), # Test substring of 'IT'
    ("HR Generalist", False),
]

for title, expected in test_jobs:
    result = is_technical_job(title)
    print(f"Title: {title:30} | Expected: {expected:5} | Result: {result:5} | {'PASS' if result == expected else 'FAIL'}")
