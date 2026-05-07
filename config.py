# config.py

SECRET_KEY = "safenet_secret_key"
LOG_FILE = "query_log.csv"
MODEL_PATH = "waf_model.pkl"
VECTORIZER_PATH = "vectorizer.pkl"
ALLOWED_ATTACKS = {
    0: "Benign",
    1: "SQL Injection",
    2: "Cross-Site Scripting (XSS)",
    3: "Command Injection",
    4: "Path Traversal",
    5: "Log Forging",
    6: "LDAP Injection",
    7: "XPath Injection",
    8: "SSTI",
    9: "Open Redirect",
    10: "Insecure File Upload"
}

ATTACK_INFO = {
    "SQL Injection": {
        "what": "An attack where malicious SQL queries are injected into input fields.",
        "why": "Can lead to database leakage, data deletion, and admin takeover."
    },
    "Cross-Site Scripting (XSS)": {
        "what": "Injection of malicious scripts into web pages viewed by users.",
        "why": "Allows session hijacking, credential theft, and defacement."
    },
    "Command Injection": {
        "what": "Execution of system commands through vulnerable inputs.",
        "why": "Can give attackers full server control."
    },
    "Path Traversal": {
        "what": "Accessing restricted files by manipulating file paths.",
        "why": "Leads to leakage of sensitive system files."
    }
}

