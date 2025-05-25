import re
import random
from datetime import datetime
import spacy
from textblob import TextBlob
from googletrans import Translator
import webbrowser
import requests
from spacy.tokens import Doc
from spacy.vocab import Vocab

# Инициализация переводчика
translator = Translator()

# Загрузка модели русского языка
nlp = spacy.load("ru_core_news_lg")

# Настройки бота
BOT_NAME = "Ассистент"
LOG_FILE = "chat_log.txt"
WEATHER_API_KEY = '7a4443cf1174bbbd8262b389c0e57fda'  # Замените на ваш API-ключ OpenWeatherMap

# Словари шаблонов и ответов
patterns = {
    "greeting": r"\b(привет|здравствуйте|хей|добрый день|доброе утро|добрый вечер)\b",
    "time": r"\b(время|который час|сколько времени|дата|какой сегодня день)\b",
    "weather": r"\b(погода|температура|прогноз|погода в [а-яё\s]+|погода на улице)\b",
    "name": r"\b(как тебя зовут|твоё имя|кто ты)\b",
    "function": r"\b(что ты умеешь|твои функции|чем помочь|помощь)\b",
    "math": r"(\d+)\s*([-+*/])\s*(\d+)",
    "search": r"\b(найди|поиск|ищи|найти|гугли)\s+(.+)",
    "how_are_you": r"\b(как дела|как жизнь|как ты|как настроение)\b",
    "joke": r"\b(анекдот|шутка|рассмеши|пошути)\b"
}

responses = {
    "greeting": ["Привет!", "Здравствуйте!", f"Привет! Я {BOT_NAME}. Как я могу вам помочь?"],
    "time": ["Сейчас {time}, сегодня {date}.", "Время: {time}, дата: {date}."],
    "weather": [
        "В городе {city} сейчас {temp}°C, {description}.",
        "Погода в {city}: температура {temp}°C, {description}."
    ],
    "weather_error": [
        "Не удалось получить данные о погоде для города '{city}'.",
        "Город '{city}' не найден. Попробуйте: 'погода в Москве'."
    ],
    "name": [f"Меня зовут {BOT_NAME}.", "Я — ваш виртуальный помощник."],
    "function": [
        "Я могу: сообщать время и дату, рассказывать о погоде, искать в интернете, выполнять вычисления.",
        "Мои функции: поиск информации, прогноз погоды, простые расчеты, поддержка в плохом настроении."
    ],
    "math": ["Результат: {result}.", "Ответ: {result}.", "Получается {result}."],
    "search": ["Ищу информацию по запросу: '{query}'.", "Открываю результаты поиска для: '{query}'."],
    "how_are_you": [
        "У меня все отлично, спасибо что спросили!",
        "Прекрасно! Готов вам помочь."
    ],
    "joke": [
        "Почему программист всегда холодный? Потому что у него windows открыты!",
        "Как назвать медленный интернет? Черепашья сеть!",
        "Зачем программисту зеркало? Чтобы делать отладку кода!"
    ],
    "default": [
        "Извините, я не совсем понимаю. Можете уточнить?",
        "Интересный вопрос. Попробуйте задать его по-другому."
    ],
    "sentiment": {
        "positive": ["Отличные новости! 😊", "Рад, что у вас хорошее настроение!"],
        "negative": ["Мне жаль это слышать...", "Похоже, вам нужна поддержка..."],
        "conflict": ["Ваше сообщение сложно интерпретировать...", "Чувствую противоречия..."]
    }
}


def translate_ru_en(text):
    try:
        return translator.translate(text, src='ru', dest='en', timeout=5).text
    except Exception as e:
        print(f"Ошибка перевода: {e}")
        return ""


def analyze_sentiment_spacy(text):
    doc = nlp(text)

    if not doc.vector_norm:
        return "neutral"

    pos_keywords = nlp("радость восторг счастье удовольствие")
    neg_keywords = nlp("грусть печаль боль разочарование")

    pos_sim = doc.similarity(pos_keywords) if pos_keywords.vector_norm else 0
    neg_sim = doc.similarity(neg_keywords) if neg_keywords.vector_norm else 0

    if pos_sim - neg_sim > 0.2:
        return "positive"
    elif neg_sim - pos_sim > 0.2:
        return "negative"
    return "neutral"


def analyze_sentiment_textblob(text):
    """Анализ настроения с TextBlob через перевод"""
    translated = translate_ru_en(text)
    blob = TextBlob(translated)
    polarity = blob.sentiment.polarity

    if polarity > 0.2:
        return "positive"
    elif polarity < -0.2:
        return "negative"
    return "neutral"


def get_combined_sentiment(text):
    """Комбинированный анализ настроения"""
    spacy_sentiment = analyze_sentiment_spacy(text)
    blob_sentiment = analyze_sentiment_textblob(text)

    if spacy_sentiment == blob_sentiment:
        return spacy_sentiment
    elif spacy_sentiment == "neutral":
        return blob_sentiment
    elif blob_sentiment == "neutral":
        return spacy_sentiment
    else:
        return "conflict"


def extract_entities(text):
    """Извлечение именованных сущностей с классификацией тем"""
    doc = nlp(text)
    entities = {
        'persons': [],
        'locations': [],
        'orgs': [],
        'dates': [],
        'topics': []
    }

    # Стандартные сущности
    for ent in doc.ents:
        if ent.label_ == 'PER':
            entities['persons'].append(ent.text)
        elif ent.label_ == 'LOC':
            entities['locations'].append(ent.text)
        elif ent.label_ == 'ORG':
            entities['orgs'].append(ent.text)
        elif ent.label_ == 'DATE':
            entities['dates'].append(ent.text)

    # Определение тем
    topics = {
        'игры': ['игра', 'гейм', 'steam', 'игровой'],
        'музыка': ['музыка', 'песн', 'альбом', 'концерт'],
        'математика': ['математ', 'алгебр', 'геометр', 'уравнен']
    }

    for token in doc:
        lemma = token.lemma_.lower()
        for topic, keywords in topics.items():
            if any(kw in lemma for kw in keywords):
                entities['topics'].append(topic)

    return entities

def log_conversation(user_input, bot_response):
    """Логирование диалога"""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"{timestamp} Вы: {user_input}\n")
        f.write(f"{timestamp} {BOT_NAME}: {bot_response}\n")
        f.write("-" * 40 + "\n")

def get_emotional_response(sentiment, text):
    """Генерация ответа на основе настроения"""
    if sentiment == "positive":
        return random.choice([
            "Рад, что у вас хорошее настроение!",
            "Здорово это слышать! Чем могу помочь?",
            "Отличные новости! 😊"
        ])
    elif sentiment == "negative":
        if "одинок" in text.lower():
            return "Одиночество может быть тяжелым. Помните, вы не одиноки - я всегда здесь."
        elif "устал" in text.lower():
            return "Похоже, вам нужно отдохнуть. Попробуйте сделать перерыв."
        else:
            return random.choice([
                "Мне жаль это слышать. Хотите поговорить об этом?",
                "Вижу, вам грустно. Может, расскажете мне об этом?",
                "Я здесь, чтобы помочь. Может, шутку расскажу?",
                "Попробуйте сделать глубокий вдох. Хотите, помогу с чем-то?"
            ])
    return ""


def translate_city_name(city_ru):
    """Улучшенный перевод с обработкой составных названий"""
    try:
        # Первый вариант: прямой перевод
        translated = translator.translate(city_ru, src='ru', dest='en').text
        if " " in translated:
            return translated.replace(" ", "%20")

    except:
        return city_ru.replace(" ", "%20")


def get_weather(city_ru):
    """Обновлённый запрос погоды с уточнением города"""
    try:
        # Корректируем русское название (Нижний Новгород -> Nizhny Novgorod)
        city_en = translate_city_name(city_ru)

        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_en}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        response = requests.get(url)
        data = response.json()

        if data['cod'] == 200:
            return True, round(data['main']['temp']), data['weather'][0]['description'].capitalize()

        return False, f"Город '{city_ru}' не найден", ""

    except Exception as e:
        return False, f"Ошибка: {str(e)}", ""


def extract_city_from_query(text):
    """Извлечение полного названия города с использованием NER и улучшенного regex"""
    doc = nlp(text)

    # Поиск географических объектов через NER
    locations = [ent.text for ent in doc.ents if ent.label_ in ("LOC", "GPE")]

    if locations:
        return locations[0].strip().rstrip('е').rstrip('у')  # "Нижнем" -> "Нижний"

    # Улучшенный regex для составных названий
    match = re.search(
        r"погода в ((?:[а-яё]+)(?:\s[а-яё-]+)+)",
        text,
        re.IGNORECASE
    )

    if match:
        city = match.group(1)
        # Удаляем модификаторы типа "город", "село" и т.д.
        city = re.sub(r"\b(город|деревня|село|посёлок)\b", "", city, flags=re.I).strip()
        return city

    return None


def process_math(text):
    """Ищет все математические выражения в тексте"""
    matches = re.findall(r"(\d+)\s*([-+*/])\s*(\d+)", text)
    results = []
    for match in matches:
        try:
            num1 = float(match[0])
            operator = match[1]
            num2 = float(match[2])

            operations = {
                '+': num1 + num2,
                '-': num1 - num2,
                '*': num1 * num2,
                '/': num1 / num2 if num2 != 0 else "ошибка (деление на ноль)"
            }

            result = operations.get(operator, "неподдерживаемая операция")
            results.append(f"🔢 {num1} {operator} {num2} = {result}")
        except:
            continue
    return "\n".join(results) if results else None


def process_message(text):
    """Обработка всех команд в одном сообщении"""
    response_parts = []
    entities = extract_entities(text)
    sentiment = get_combined_sentiment(text)

    # Приветствие
    if re.search(patterns["greeting"], text, re.I):
        response_parts.append(random.choice(responses["greeting"]))

    # Поиск
    if search_match := re.search(patterns["search"], text, re.I):
        query = search_match.group(2).strip()
        webbrowser.open(f"https://google.com/search?q={query}")
        response_parts.append(f"🔍 Поиск: '{query}'")

    # Погода
    if weather_match := re.search(patterns["weather"], text, re.I):
        city = extract_city_from_query(text)
        if city:
            success, temp, desc = get_weather(city)
            if success:
                response_parts.append(f"🌤 {random.choice(responses['weather']).format(city=city, temp=temp, description=desc)}")
            else:
                response_parts.append(f"⚠ {random.choice(responses['weather_error']).format(city=city)}")

    # Математика
    if math_response := process_math(text):
        response_parts.append(math_response)

    # Время/дата
    if re.search(patterns["time"], text, re.I):
        now = datetime.now()
        response_parts.append(f"🕒 {now.strftime('%H:%M')}, {now.strftime('%d.%m.%Y')}")

    # Темы и персонализация
    if entities['topics']:
        topics = list(set(entities['topics']))
        response_parts.append(f"🎮 Темы: {', '.join(topics)}")

    if entities['persons']:
        response_parts.insert(0, f"👋 Приветствую, {entities['persons'][0]}!")

    # Эмоциональная реакция
    if sentiment in responses["sentiment"]:
        response_parts.append(f"🎭 {random.choice(responses['sentiment'][sentiment])}")

    # Формирование ответа
    final_response = "\n".join(filter(None, response_parts))
    return final_response if final_response.strip() else random.choice(responses["default"])


# Основной цикл бота
print(f"{BOT_NAME}: Привет! Я ваш виртуальный помощник. Скажите 'пока' для выхода.")

while True:
    user_input = input("Вы: ").strip()

    if user_input.lower() in ["пока", "выход"]:
        print(f"{BOT_NAME}: До свидания!")
        break

    try:
        response = process_message(user_input)
        print(f"{BOT_NAME}: {response}")
    except Exception as e:
        print(f"{BOT_NAME}: Произошла ошибка: {str(e)}")