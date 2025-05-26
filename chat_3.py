import re
import random
from datetime import datetime
import spacy
from textblob import TextBlob
from googletrans import Translator
import webbrowser
import requests

# Инициализация моделей и сервисов ============================================
translator = Translator()
nlp = spacy.load("ru_core_news_lg")  # Загрузка модели для русского языка

# Конфигурация бота ===========================================================
BOT_NAME = "Чат-бот"
LOG_FILE = "chat_log.txt"
WEATHER_API_KEY = '7a4443cf1174bbbd8262b389c0e57fda'  # Замените на ваш ключ

# Тематические категории для анализа контекста ================================
TOPICS_CONFIG = {
    'игры': ['игра', 'гейм', 'steam', 'игровой'],
    'музыка': ['музыка', 'песн', 'альбом', 'концерт'],
    'математика': ['математ', 'алгебр', 'геометр', 'уравнен']
}

# Шаблоны и ответы ===========================================================
PATTERNS = {
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

RESPONSES = {
    "greeting": ["Привет!", "Здравствуйте!", f"Привет! Я {BOT_NAME}. Как я могу вам помочь?"],
    "time": ["Сейчас {time}, сегодня {date}.", "Время: {time}, дата: {date}."],
    "weather": [
        "В городе {city} сейчас {temp}°C, {description}.",
        "Погода в {city}: температура {temp}°C, {description}."
    ],
    "weather_error": [
        "Не удалось получить данные о погоде для города '{city}'.",
        "Город '{city}' не найден. Проверьте написание."
    ],
    "name": [f"Меня зовут {BOT_NAME}.", "Я — ваш виртуальный помощник."],
    "function": [
        "Я могу: сообщать время/дату, рассказывать о погоде, искать информацию, выполнять вычисления.",
        "Мои функции: поиск информации, прогноз погоды, математические расчеты, эмоциональная поддержка."
    ],
    "math": ["Результат: {result}.", "Ответ: {result}.", "Получается {result}."],
    "search": ["Ищу информацию по запросу: '{query}'.", "Открываю результаты для: '{query}'."],
    "how_are_you": [
        "У меня все отлично, спасибо что спросили!",
        "Прекрасно! Готов вам помочь."
    ],
    "joke": [
        "Почему программисты путают Хэллоуин и Рождество? Потому что Oct 31 == Dec 25!",
        "Как объяснить разницу между Java и JavaScript? Это как горячая плита и слон!",
        "Почему Python не нужен косметолог? Потому что у него отличные 'классы'!",
        "Что говорит администратор баз данных, когда уходит? 'Я скоро commit вернусь!'",
        "Почему разработчики любят темные темы? Потому что свет притягивает баги!",
        "Какой любимый фрукт веб-разработчика? JS-апельсин!",
        "Почему React-разработчик не мог заснуть? Потому что он думал о пропсах и state!"
    ],
    "default": [
        "Извините, я не совсем понимаю. Можете уточнить?",
        "Интересный вопрос. Попробуйте задать его по-другому."
    ],
    "sentiment": {
        "positive": ["Рад, что вам весело! 😊", "Отличное настроение!"],
        "negative": ["Мне жаль это слышать... Может, рассказать вам анекдот? 😔",
                     "Похоже, вам нужна поддержка... Хотите поднять настроение шуткой?"],
        "conflict": [
            "Чувствую противоречивые эмоции... Может, расскажете подробнее?",
            "Кажется, у вас смешанные чувства. Хотите обсудить это?"
        ],
        "neutral": ["❓ Чем могу помочь?", "💬 Расскажите, что вас интересует?"]
    }
}


# Вспомогательные функции =====================================================
def log_conversation(user_input: str, bot_response: str) -> None:
    """Логирует диалог в файл"""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"{timestamp} Вы: {user_input}\n")
        f.write(f"{timestamp} {BOT_NAME}: {bot_response}\n")
        f.write("-" * 40 + "\n")


# Функции анализа контента =====================================================
def analyze_sentiment(text: str) -> str:
    """Анализ тональности через TextBlob с переводом на английский"""
    try:
        translated = translator.translate(text, src='ru', dest='en').text
        blob = TextBlob(translated)
        polarity = blob.sentiment.polarity

        if polarity > 0.2:
            return "positive"
        elif polarity < -0.2:
            return "negative"
        return "neutral"
    except Exception as e:
        print(f"Ошибка анализа: {e}")
        return "neutral"


def extract_entities(text: str) -> dict:
    """Извлекает именованные сущности и темы через spaCy"""
    doc = nlp(text)
    entities = {
        'persons': [ent.text for ent in doc.ents if ent.label_ == 'PER'],
        'locations': [ent.text for ent in doc.ents if ent.label_ in ('LOC', 'GPE')],
        'orgs': [ent.text for ent in doc.ents if ent.label_ == 'ORG'],
        'dates': [ent.text for ent in doc.ents if ent.label_ == 'DATE'],
        'verbs': [token.lemma_ for token in doc if token.pos_ == 'VERB'],
        'topics': []
    }
    # Выявление тематик через лемматизацию
    for token in doc:
        lemma = token.lemma_.lower()
        for topic, keywords in TOPICS_CONFIG.items():
            if any(kw in lemma for kw in keywords):
                entities['topics'].append(topic)

    return entities


# Обновлённые обработчики команд ==============================================
def handle_time() -> str:
    """Возвращает текущее время и дату"""
    now = datetime.now()
    return f"🕒 {now.strftime('%H:%M')}, {now.strftime('%d.%m.%Y')}"


def handle_math(text: str) -> str:
    """Обрабатывает математические выражения"""
    matches = re.findall(r"(\d+)\s*([-+*/])\s*(\d+)", text)
    results = []

    for match in matches:
        try:
            num1, op, num2 = match
            operations = {
                '+': float(num1) + float(num2),
                '-': float(num1) - float(num2),
                '*': float(num1) * float(num2),
                '/': float(num1) / float(num2) if num2 != '0' else "ошибка (деление на ноль)"
            }
            result = operations.get(op, "неподдерживаемая операция")
            results.append(f"🔢 {num1} {op} {num2} = {result}")
        except Exception as e:
            continue

    return "\n".join(results) if results else ""


def handle_search(text: str) -> str:
    """Обрабатывает поисковые запросы"""
    if match := re.search(PATTERNS["search"], text, re.I):
        query = match.group(2).strip()
        webbrowser.open(f"https://google.com/search?q={query}")
        return f"🌐 {random.choice(RESPONSES['search']).format(query=query)}"
    return ""


def handle_function_info() -> str:
    """Возвращает информацию о возможностях бота"""
    return random.choice(RESPONSES["function"])


def handle_name() -> str:
    """Возвращает информацию об имени бота"""
    return random.choice(RESPONSES["name"])

def translate_city_name(city_ru):
    """Улучшенный перевод с обработкой составных названий"""
    try:
        # Первый вариант: прямой перевод
        translated = translator.translate(city_ru, src='ru', dest='en').text
        if " " in translated:
            return translated.replace(" ", "%20")

    except:
        return city_ru.replace(" ", "%20")


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


def get_weather(city_ru):
    """Обновлённый запрос погоды с уточнением города"""
    try:
        # Корректируем русское название
        city_en = translate_city_name(city_ru)

        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_en}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        response = requests.get(url)
        data = response.json()

        if data['cod'] == 200:
            return True, round(data['main']['temp']), data['weather'][0]['description'].capitalize()

        return False, f"Город '{city_ru}' не найден", ""

    except Exception as e:
        return False, f"Ошибка: {str(e)}", ""

def handle_joke() -> str:
    """Возвращает случайную шутку"""
    return f"🎭 {random.choice(RESPONSES['joke'])}"


def handle_sentiment(sentiment: str) -> str:
    """Ответы в зависимости от настроения"""
    return random.choice(RESPONSES["sentiment"].get(sentiment, [""]))


# Главная функция обработки сообщений =========================================
def process_message(text: str) -> str:
    """Обрабатывает входящее сообщение и формирует ответ с новым порядком обработки"""
    response_parts = []
    entities = extract_entities(text)
    sentiment = analyze_sentiment(text)

    # 1. Контекстные операции (персонализация и темы)
    if entities['persons']:
        response_parts.append(f"👋 Приветствую, {entities['persons'][0]}!")

    if unique_topics := list(set(entities['topics'])):
        response_parts.append(f"🎮 Темы: {', '.join(unique_topics)}")

    # 2. Обработка основных команд и паттернов
    command_handlers = [
        (PATTERNS["greeting"], lambda: random.choice(RESPONSES["greeting"])),
        (PATTERNS["time"], handle_time),
        (PATTERNS["name"], handle_name),
        (PATTERNS["function"], handle_function_info),
        (PATTERNS["how_are_you"], lambda: random.choice(RESPONSES["how_are_you"])),
        (PATTERNS["joke"], handle_joke)
    ]

    for pattern, handler in command_handlers:
        if re.search(pattern, text, re.I):
            response_parts.append(handler())

    # Обработка специальных команд с возвратом значения
    if math_response := handle_math(text):
        response_parts.append(math_response)

    if search_response := handle_search(text):
        response_parts.append(search_response)

    if weather_match := re.search(PATTERNS["weather"], text, re.I):
        city = extract_city_from_query(text)
        if city:
            success, temp, desc = get_weather(city)
            if success:
                response_parts.append(f"🌤 {random.choice(RESPONSES['weather']).format(city=city, temp=temp, description=desc)}")
            else:
                response_parts.append(f"⚠ {random.choice(RESPONSES['weather_error']).format(city=city)}")

    # 3. Эмоциональная реакция (добавляется последней)
    if sentiment_response := handle_sentiment(sentiment):
        response_parts.append(sentiment_response)

    # Формирование финального ответа
    final_response = "\n".join(filter(None, response_parts))
    return final_response if final_response.strip() else random.choice(RESPONSES["default"])


# Основной цикл бота ==========================================================
if __name__ == "__main__":
    print(f"{BOT_NAME}: Привет! Я ваш виртуальный помощник. Скажите 'пока' для выхода.")

    while True:
        user_input = input("Вы: ").strip()

        if user_input.lower() in ["пока", "выход"]:
            print(f"{BOT_NAME}: До свидания!")
            break

        try:
            response = process_message(user_input)
            print(f"{BOT_NAME}: {response}")
            log_conversation(user_input, response)
        except Exception as e:
            print(f"{BOT_NAME}: Произошла ошибка: {str(e)}")