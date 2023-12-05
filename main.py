# подключаем модуль для Телеграма
import telebot
import requests

# подключаем токен бота
bot = telebot.TeleBot('6691252717:AAHpMuCC337fl_4U4ucKz_jJlwk8r8b2AIs')

start_txt = (f'Привет!'
'\n\nОтправь название города, чтобы узнать прогрноз погоды.')


# обрабатываем старт бота
@bot.message_handler(commands=['start'])
def start(message):
    # выводим приветственное сообщение
    bot.send_message(message.from_user.id, start_txt, parse_mode='Markdown')

# обрабатываем любой текстовый запрос
@bot.message_handler(content_types=['text'])
def weather(message):
    # получаем город из сообщения пользователя
  city = message.text
  # формируем запрос
  url = 'https://api.openweathermap.org/data/2.5/weather?q='+city+'&units=metric&lang=ru&appid=79d1ca96933b0328e1c7e3e7a26cb347'
  # отправляем запрос на сервер и сразу получаем результат
  weather_data = requests.get(url).json()
  # получаем данные о температуре и о том, как она ощущается
  temperature = round(weather_data['main']['temp'])
  temperature_feels = round(weather_data['main']['feels_like'])
  # формируем ответы
  w_now = 'Сейчас в городе ' + city + ' ' + str(temperature) + ' °C'
  w_feels = 'Ощущается как ' + str(temperature_feels) + ' °C'
  # отправляем значения пользователю
  bot.send_message(message.from_user.id, w_now)
  bot.send_message(message.from_user.id, w_feels)

  wind_speed = round(weather_data['wind']['speed'])
  if wind_speed < 5:
      bot.send_message(message.from_user.id, '✅ Погода хорошая, ветра почти нет')
  elif wind_speed < 10:
      bot.send_message(message.from_user.id, '🤔 На улице ветрено, оденьтесь чуть теплее')
  elif wind_speed < 20:
      bot.send_message(message.from_user.id, '❗️ Ветер очень сильный, будьте осторожны, выходя из дома')
  else:
      bot.send_message(message.from_user.id, '❌ На улице шторм, на улицу лучше не выходить')
# запускаем бота
if __name__ == '__main__':
    while True:
        # в бесконечном цикле постоянно опрашиваем бота — есть ли новые сообщения
        try:
            bot.polling(none_stop=True, interval=0)
        # если возникла ошибка — сообщаем про исключение и продолжаем работу
        except Exception as e: 
            print('❌ Сработало исключение! ❌')