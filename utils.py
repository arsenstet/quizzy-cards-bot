import requests


GOOGLE_TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single"


def translate_word(word, target_lang="uk"):
    params = {
        "client": "gtx",
        "sl": "auto",
        "tl": target_lang,
        "dt": "t",
        "q": word
    }
    try:
        response = requests.get(GOOGLE_TRANSLATE_URL, params=params)
        if response.status_code == 200:
            return response.json()[0][0][0].lower()
        return None
    except Exception:
        return None