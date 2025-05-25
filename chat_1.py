import re
import random
import datetime

patterns = {
    "greeting": r"\b(привет|здравствуйте|хей)\b",
    "time": r"\b(какое сейчас время|сколько времени|какой сегодня день)\b",
    "weather": r"\b(какая погода|как там погода|что за погода на улице)\b",
    "name": r"\b(как тебя зовут|твоё имя|кто ты)\b",
    "function": r"\b(что ты умеешь делать|какие у тебя функции|чем ты можешь помочь)\b",
    "math": r"([-+]?\d*\.?\d+|\d+)\s*([-+*/])\s*([-+]?\d*\.?\d+|\d+)"
}

responses = {
    "greeting": ["Привет!", "Здравствуйте!", "Хей!", "Здравствуйте, чем могу помочь?"],
    "time": ["Текущее время: {time}, дата: {date}."],
    "weather": ["Извините, не могу предоставить информацию о погоде."],
    "name": ["Меня зовут Бот.", "Я — чат-бот.", "Мое имя — ЧатБот."],
    "function": ["Я могу отвечать на вопросы и выполнять простые вычисления."],
    "math": ["Результат: {result}."],
    "default": ["Извините, я не понимаю."]
}

while True:
    user_input = input("Вы: ")

    if user_input.lower() in ["выход", "exit"]:
        print("Чат-бот: До свидания!")
        break

    matched = False
    for key, pattern in patterns.items():
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            matched = True
            if key == "time":
                now = datetime.datetime.now()
                response = responses[key][0].format(time=now.strftime('%H:%M'), date=now.strftime('%Y-%m-%d'))
                print(f"Чат-бот: {response}")
            elif key == "math":
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
                    result = num1 / num2
                response = responses[key][0].format(result=result)
                print(f"Чат-бот: {response}")
            else:
                print(f"Чат-бот: {random.choice(responses[key])}")
            break

    if not matched:
        print(f"Чат-бот: {random.choice(responses['default'])}")
