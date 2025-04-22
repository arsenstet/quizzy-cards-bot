from sklearn.feature_extraction.text import TfidfVectorizer
import requests
from bs4 import BeautifulSoup
import spacy

# Завантажуємо модель spaCy
nlp = spacy.load("en_core_web_sm")


def extract_text_from_url(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            paragraphs = soup.find_all('p')
            return " ".join([para.get_text() for para in paragraphs])
        return None
    except Exception as e:
        return None


def extract_important_words(text):
    # Аналізуємо текст за допомогою spaCy для виявлення іменованих сутностей
    doc = nlp(text)
    named_entities = {ent.text.lower() for ent in doc.ents}  # Множина всіх сутностей

    # Використовуємо TF-IDF для вибору ключових слів
    vectorizer = TfidfVectorizer(
        stop_words='english',
        max_features=15,  # Беремо більше слів для фільтрації
        ngram_range=(1, 2)  # Включаємо біграми
    )
    tfidf_matrix = vectorizer.fit_transform([text])
    keywords = vectorizer.get_feature_names_out().tolist()

    # Фільтруємо слова: виключаємо іменовані сутності та короткі слова
    filtered_keywords = [
        word for word in keywords
        if word.lower() not in named_entities and len(word) > 3
    ]

    # Якщо слів замало, додаємо з оригінального списку, але без сутностей
    if len(filtered_keywords) < 10 and keywords:
        extra_words = [word for word in keywords if word not in filtered_keywords and word.lower() not in named_entities]
        filtered_keywords.extend(extra_words[:10 - len(filtered_keywords)])

    # Повертаємо до 10 слів, розвертаємо для різноманітності
    return filtered_keywords[:10][::-1]