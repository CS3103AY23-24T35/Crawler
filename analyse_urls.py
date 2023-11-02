from urllib.parse import urlparse
from collections import Counter
import re
import matplotlib.pyplot as plt

# Function to read URLs from a text file
def read_urls_from_file(file_path):
    with open(file_path, 'r') as file:
        urls = [line.strip() for line in file]
    return urls

# List of URLs to analyze, read from a text file
urls = read_urls_from_file('urls.txt')

# Define keywords for OWASP Top 10 categories (case-insensitive)
owasp_keywords = {
    "Injection": ["sql", "injection", "xss", "command", "code", "query"],
    "Broken Authentication": ["authentication", "login", "session", "password"],
    "Sensitive Data Exposure": ["sensitive", "data", "exposure", "privacy"],
    "XML External Entity (XXE)": ["xxe", "xml", "entity", "external"],
    "Broken Access Control": ["access", "control", "authorization"],
    "Security Misconfiguration": ["misconfiguration", "security", "configure", "setting"],
    "Cross-Site Scripting (XSS)": ["xss", "cross-site scripting", "script", "javascript"],
    "Insecure Deserialization": ["insecure deserialization", "deserialize"],
    "Using Components with Known Vulnerabilities": ["known vulnerabilities", "components", "dependency"],
    "Insufficient Logging & Monitoring": ["insufficient logging", "monitoring", "audit", "logging"]
    # Add keywords for other OWASP categories here
}

# Function to extract words from a URL
def extract_words_from_url(url):
    parsed_url = urlparse(url)
    path = parsed_url.path.lower()
    
    # Use regular expressions to extract words
    words = re.findall(r'\b\w+\b', path)
    
    # Exclude "http" and "https" from the words
    words = [word for word in words if word not in ["http", "https"]]
    
    return words

# Function to count OWASP keywords in URLs (case-insensitive)
def count_owasp_keywords(urls, owasp_keywords):
    keyword_counts = {category: 0 for category in owasp_keywords.keys()}
    
    for url in urls:
        words = extract_words_from_url(url)
        
        for category, keywords in owasp_keywords.items():
            for keyword in keywords:
                keyword = keyword.lower()  # Convert the keyword to lowercase
                for word in words:
                    if keyword in word.lower():  # Convert the word to lowercase for comparison
                        keyword_counts[category] += 1
    
    return keyword_counts

# Count OWASP keywords in URLs (case-insensitive)
owasp_keyword_counts = count_owasp_keywords(urls, owasp_keywords)

# Plot the counts of OWASP keywords
categories = list(owasp_keywords.keys())
counts = list(owasp_keyword_counts.values())

plt.figure(figsize=(10, 6))
plt.bar(categories, counts)
plt.xlabel("OWASP Categories")
plt.ylabel("Keyword Counts")
plt.title("OWASP Top 10 Keyword Counts in URLs")
plt.xticks(rotation=45)
plt.show()
