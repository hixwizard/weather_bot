import telebot
import requests
import os
from dotenv import load_dotenv
from telebot import types
from constants import msg  # Исправлено использование

load_dotenv()
TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)
START_TXT = os.getenv('START_TXT')
ERROR_TXT = os.getenv('ERROR_TXT')
DIGIT_REQUEST = msg.DIGIT_REQUEST
WEATHER_URL = os.getenv('WEATHER_URL')
detailed_weather_data = {}  # Словарь для хранения данных о погоде


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.from_user.id,
        START_TXT,
        parse_mode='Markdown'
    )


@bot.message_handler(content_types=['text'])
def weather(message):
    if any(char.isdigit() for char in message.text):
        return bot.send_message(
            message.from_user.id,
            DIGIT_REQUEST
        )
    city = message.text
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&lang=ru&appid=79d1ca96933b0328e1c7e3e7a26cb347'  # noqa
    response = requests.get(url)
    if response.status_code != 200:
        return bot.send_message(message.from_user.id, ERROR_TXT)

    weather_data = response.json()
    humidity = weather_data['main']['humidity']
    temperature_feels = round((weather_data['main']['feels_like']), 1)
    wind_speed = round(weather_data['wind']['speed'], 1)
    wind_deg = weather_data['wind']['deg']
    temperature = round(weather_data['main']['temp'], 1)
    temp_min = round(weather_data['main']['temp_min'], 1)
    temp_max = round(weather_data['main']['temp_max'], 1)
    pressure = weather_data['main']['pressure']
    description = weather_data['weather'][0]['description']
    clouds = weather_data['clouds']['all']

    comments = []
    match temperature:
        case _ if _ <= -30:
            comments.append(msg.COLD_30)
        case _ if -30 < _ <= -20:
            comments.append(msg.COLD_20)
        case _ if -20 < _ <= -10:
            comments.append(msg.COLD_10)
        case _ if -10 < _ < 0:
            comments.append(msg.COLD_0)
        case _ if 0 <= _ <= 15:
            comments.append(msg.HOT_15)
        case _ if 15 < _ <= 25:
            comments.append(msg.HOT_25)
        case _:
            comments.append(msg.HOT_HOT)

    match wind_speed:
        case _ if _ > 10:
            comments.append(msg.WIND_10)
        case _ if _ > 5:
            comments.append(msg.WIND_5)
        case _:
            comments.append(msg.JUST_WIND)

    def get_wind_direction(degree):
        """Направление ветра по углу."""
        match degree:
            case _ if _ >= 337.5 or _ < 22.5:
                return "северный ветер"
            case _ if 22.5 <= _ < 67.5:
                return "северо-восточный ветер"
            case _ if 67.5 <= _ < 112.5:
                return "восточный ветер"
            case _ if 112.5 <= _ < 157.5:
                return "юго-восточный ветер"
            case _ if 157.5 <= _ < 202.5:
                return "южный ветер"
            case _ if 202.5 <= _ < 247.5:
                return "юго-западный ветер"
            case _ if 247.5 <= _ < 292.5:
                return "западный ветер"
            case _ if 292.5 <= _ < 337.5:
                return "северо-западный ветер"

    wind_direction = get_wind_direction(wind_deg)

    # Сохраняем подробные данные в словарь
    detailed_weather_data[message.from_user.id] = {
        "temperature": temperature,
        "temperature_feels": temperature_feels,
        "temp_min": temp_min,
        "temp_max": temp_max,
        "humidity": humidity,
        "pressure": pressure,
        "wind_speed": wind_speed,
        "wind_direction": wind_direction,
        "clouds": clouds,
        "comments": comments
    }

    weather_message = (
        f"{city.capitalize()} {temperature} °C\n"
        f"{description.capitalize()}\n"
    )

    # Создаем кнопку для развертывания подробного сообщения
    keyboard = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(
        msg.FULL_ANS,
        callback_data=f"show_details"
    )
    keyboard.add(button)

    # Отправляем основное сообщение с кнопкой
    bot.send_message(
        message.from_user.id, weather_message, reply_markup=keyboard
    )


# Обработчик для кнопки
@bot.callback_query_handler(func=lambda call: call.data == "show_details")
def show_details(call):
    data = detailed_weather_data.get(call.message.chat.id)
    if data:
        details = (
            f"🌡 Ощущается как: {data['temperature_feels']} °C\n"
            f"⬇️ Мин.: {data['temp_min']} °C, ⬆️ Макс.: {data['temp_max']} °C\n" # noqa
            f"💧 Влажность: {data['humidity']}%\n"
            f"💨 Ветер: {data['wind_speed']} м/с, {data['wind_direction']}\n\n"
            f"Что я думаю об этой погодке:\n"
            f"{'\n'.join(data['comments'])}"
        )
        bot.send_message(call.message.chat.id, details)
        # Удаляем кнопку после нажатия
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None
        )


if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True, interval=1)
        except Exception as e:
            print(e)
