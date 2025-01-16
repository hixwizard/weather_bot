import telebot
import aiohttp
import asyncio
import threading
import os
from dotenv import load_dotenv
from telebot import types
from constants import msg  # Импортируем экземпляр

load_dotenv()
TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)
START_TXT = os.getenv('START_TXT')
ERROR_TXT = os.getenv('ERROR_TXT')
DIGIT_REQUEST = os.getenv('DIGIT_REQUEST')
WEATHER_URL = os.getenv('WEATHER_URL')
detailed_weather_data = {}  # Словарь для хранения данных о погоде


# Асинхронный запрос для получения погоды
async def fetch_weather(city):
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&lang=ru&appid=79d1ca96933b0328e1c7e3e7a26cb347'  # noqa
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return None
            return await response.json()


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

    # Запускаем асинхронную функцию в потоке
    asyncio.run_coroutine_threadsafe(_handle_weather(message), asyncio.get_event_loop())


async def _handle_weather(message):
    city = message.text
    weather_data = await fetch_weather(city)
    if not weather_data:
        return await bot.send_message(message.from_user.id, ERROR_TXT)

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
        case t if t <= -30:
            comments.append(msg.COLD_30)
        case t if -30 < t <= -20:
            comments.append(msg.COLD_20)
        case t if -20 < t <= -10:
            comments.append(msg.COLD_10)
        case t if -10 < t < 0:
            comments.append(msg.COLD_0)
        case t if 0 <= t <= 15:
            comments.append(msg.HOT_15)
        case t if 15 < t <= 25:
            comments.append(msg.HOT_25)
        case _:
            comments.append(msg.HOT_HOT)

    match wind_speed:
        case ws if ws > 10:
            comments.append(msg.WIND_10)
        case ws if ws > 5:
            comments.append(msg.WIND_5)
        case _:
            comments.append(msg.JUST_WIND)

    def get_wind_direction(degree):
        """Направление ветра по углу."""
        match degree:
            case d if d >= 337.5 or d < 22.5:
                return "северный ветер"
            case d if 22.5 <= d < 67.5:
                return "северо-восточный ветер"
            case d if 67.5 <= d < 112.5:
                return "восточный ветер"
            case d if 112.5 <= d < 157.5:
                return "юго-восточный ветер"
            case d if 157.5 <= d < 202.5:
                return "южный ветер"
            case d if 202.5 <= d < 247.5:
                return "юго-западный ветер"
            case d if 247.5 <= d < 292.5:
                return "западный ветер"
            case d if 292.5 <= d < 337.5:
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
    await bot.send_message(
        message.from_user.id, weather_message, reply_markup=keyboard
    )


# Обработчик для кнопки
@bot.callback_query_handler(func=lambda call: call.data == "show_details")
def show_details(call):
    data = detailed_weather_data.get(call.message.chat.id)
    if data:
        details = (
            f"🌡 Ощущается как: {data['temperature_feels']} °C\n"
            f"⬇️ Мин.: {data['temp_min']} °C, ⬆️ Макс.: {data['temp_max']} °C\n"
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


# Запускаем бота в отдельном потоке
def run_bot():
    # Устанавливаем event loop в текущем потоке
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    bot.polling(none_stop=True, interval=1)


if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
