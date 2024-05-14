import telebot
import requests
import os

from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)
START_TXT = os.getenv('START_TXT')
ERROR_TXT = os.getenv('ERROR_TXT')


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
            ('Ввод содержит цифры.'
             ' \nОтправь название или населённый пункт,'
             ' чтобы я прислал прогноз.')
        )
    city = message.text
    url = ('https://api.openweathermap.org/data/2.5/weather?q='+city+'&units=metric&lang=ru&appid=79d1ca96933b0328e1c7e3e7a26cb347')
    response = requests.get(url)
    if response.status_code != 200:
        return bot.send_message(message.from_user.id, ERROR_TXT)

    weather_data = response.json()
    humidity = (weather_data['main']['humidity'])
    wind_speed = round((weather_data['wind']['speed']), 1)
    temperature_feels = round((weather_data['main']['feels_like']), 1)
    temperature = round((weather_data['main']['temp']), 1)
    description = weather_data['weather'][0]['description']
    bot.send_message(
        message.from_user.id,
        city + ' ' + str(
            temperature
            ) + ' °C\n' + str(
                description
                ) + '\nОщущается как ' + str(
            temperature_feels
        ) + ' °C\nВлажность воздуха ' + str(
            humidity
        ) + ' %\nСкорость верта ' + str(wind_speed) + ' м/с'
    )


if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True, interval=1)
        except Exception as e:
            print(e)
