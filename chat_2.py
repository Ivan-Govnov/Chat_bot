import re
import random
import datetime
import webbrowser
import requests

WEATHER_API_KEY = '7a4443cf1174bbbd8262b389c0e57fda'
LOG_FILE = 'chat_log.txt'

patterns = {
    "greeting": r"\b(привет|здравствуйте|хей|добрый день|доброе утро|добрый вечер)\b",
    "time": r"\b(время|который час|сколько времени|дата|какой сегодня день)\b",
    "weather": r"\b(погода|температура|прогноз|погода в [а-яё\s]+|погода на улице)\b",
    "name": r"\b(как тебя зовут|твоё имя|кто ты)\b",
    "function": r"\b(что ты умеешь|твои функции|чем помочь|помощь)\b",
    "math": r"([-+]?\d*\.?\d+|\d+)\s*([-+*/])\s*([-+]?\d*\.?\d+|\d+)",
    "search": r"\b(найди|поиск|ищи|найти|гугли)\b (.+)",
    "how_are_you": r"\b(как дела|как жизнь|как ты|как настроение)\b"
}

responses = {
    "greeting": ["Привет!", "Здравствуйте!", "Хей!", "Здравствуйте, чем могу помочь?"],
    "time": ["Сейчас {time}, сегодня {date}.", "Время: {time}, дата: {date}."],
    "weather": [
        "В городе {city} сейчас {temp}°C, {description}.",
        "Погода в {city}: температура {temp}°C, {description}."
    ],
    "weather_error": [
        "Не удалось получить данные о погоде для города '{city}'. Пожалуйста, проверьте название города и попробуйте снова.",
        "Город '{city}' не найден. Убедитесь, что название введено правильно, например: 'погода в Санкт-Петербурге'."
    ],
    "weather_instruction": [
        "Чтобы узнать погоду, введите запрос вида 'погода в [название города]', например: 'погода в Москве'.",
        "Для получения прогноза погоды укажите город после 'погода в', например: 'погода в Новосибирске'."
    ],
    "name": ["Меня зовут ЧатБот.", "Я — ваш виртуальный помощник.", "Мое имя — Ассистент."],
    "function": [
        "Я могу: сообщать время и дату, рассказывать о погоде, искать в интернете, выполнять вычисления.",
        "Мои функции: поиск информации, прогноз погоды, простые расчеты."
    ],
    "math": ["Результат: {result}.", "Ответ: {result}.", "Получается {result}."],
    "search": ["Ищу информацию по запросу: '{query}'.", "Открываю результаты поиска для: '{query}'."],
    "how_are_you": [
        "У меня все отлично, спасибо что спросили!",
        "Как у цифрового существа, у меня все хорошо!",
        "Прекрасно! Готов вам помочь.",
        "Все работает, никаких ошибок!"
    ],
    "default": [
        "Извините, я не совсем понимаю.",
        "Можете переформулировать вопрос?",
        "Я не уверен, что понял вас правильно."
    ]
}


def log_conversation(user_input, bot_response):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"{timestamp} Вы: {user_input}\n")
        f.write(f"{timestamp} Бот: {bot_response}\n\n")


def get_weather(city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        response = requests.get(url)
        data = response.json()
        if data['cod'] == 200:
            temperature = round(data['main']['temp'])
            description = data['weather'][0]['description']
            return True, temperature, description
        else:
            error_msg = f"Ошибка {data.get('cod')}: {data.get('message', 'Unknown error')}"
            return False, error_msg, ""
    except Exception as e:
        return False, f"Ошибка при запросе погоды: {str(e)}", ""


def extract_city_from_query(user_input):
    weather_pattern = r"погода в ([а-яё\s]+)"
    match = re.search(weather_pattern, user_input, re.IGNORECASE)

    if match:
        city = match.group(1).strip()
        return city if city else None
    return None


def process_input(user_input):
    user_input = user_input.lower().strip()

    if user_input in ["выход", "exit", "quit", "пока"]:
        return False, "До свидания! Было приятно пообщаться."

    for key, pattern in patterns.items():
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            if key == "time":
                now = datetime.datetime.now()
                response = random.choice(responses[key]).format(
                    time=now.strftime('%H:%M'),
                    date=now.strftime('%d.%m.%Y')
                )
                return True, response

            elif key == "math":
                try:
                    num1 = float(match.group(1))
                    operator = match.group(2)
                    num2 = float(match.group(3))

                    if operator == '+':
                        result = num1 + num2
                    elif operator == '-':
                        result = num1 - num2
                    elif operator == '*':
                        result = num1 * num2
                    elif operator == '/':
                        result = num1 / num2 if num2 != 0 else "ошибка (деление на ноль)"

                    response = random.choice(responses[key]).format(result=result)
                    return True, response
                except:
                    return True, "Не удалось выполнить вычисление."

            elif key == "weather":
                city = extract_city_from_query(user_input)

                if not city:
                    # Если город не извлечен, но запрос был о погоде
                    if re.search(r"\b(погода|температура|прогноз)\b", user_input):
                        return True, random.choice(responses["weather_instruction"])
                    return True, random.choice(responses["default"])

                success, temp, desc = get_weather(city)
                if success:
                    response = random.choice(responses[key]).format(
                        city=city.capitalize(),
                        temp=temp,
                        description=desc
                    )
                else:
                    response = random.choice(responses["weather_error"]).format(city=city.capitalize())
                return True, response

            elif key == "search":
                query = match.group(2)
                url = f"https://www.google.com/search?q={query}"
                webbrowser.open(url)
                response = random.choice(responses[key]).format(query=query)
                return True, response

            elif key in ["greeting", "name", "function", "how_are_you"]:
                return True, random.choice(responses[key])

    return True, random.choice(responses["default"])


print("Чат-бот: Привет! Я ваш виртуальный помощник. Скажите 'выход' чтобы завершить общение.")
while True:
    user_input = input("Вы: ")
    continue_chat, bot_response = process_input(user_input)

    print(f"Чат-бот: {bot_response}")
    log_conversation(user_input, bot_response)

    if not continue_chat:
        break
