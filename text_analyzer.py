import spacy
import requests
from bs4 import BeautifulSoup

def extract_text_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        text = ' '.join(p.get_text() for p in soup.find_all('p'))
        return text
    except requests.RequestException:
        return None

def extract_important_words(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    words = [token.text.lower() for token in doc if token.pos_ in ["NOUN", "ADJ", "VERB"] and not token.is_stop and token.is_alpha]
    return list(dict.fromkeys(words))[:10]