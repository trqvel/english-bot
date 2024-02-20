from telegram import Update
from telegram.ext import CallbackContext
import json
import aiofiles


DICT_PATH = 'dictionary.json'

# Функция для загрузки данных из JSON файла
async def load_user_data():
    try:
        async with aiofiles.open(DICT_PATH, 'r', encoding='utf-8') as file:
            data = await file.read()
            return json.loads(data)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Функция для сохранения данных в JSON файл
async def save_user_data(user_data):
    async with aiofiles.open(DICT_PATH, 'w', encoding='utf-8') as file:
        await file.write(json.dumps(user_data, ensure_ascii=False, indent=4))

async def start(update: Update, context: CallbackContext):
    user_data = await load_user_data()  # Асинхронная загрузка данных
    user_id = str(update.message.from_user.id)  # Преобразование в строку для JSON ключа

    if user_id not in user_data:
        user_data[user_id] = []  # Создание пустого списка для нового пользователя
        await save_user_data(user_data)  # Асинхронное сохранение данных
        await update.message.reply_text('Ваш словарь успешно создан!')
    else:
        await update.message.reply_text('У вас уже есть словарь. Можете добавлять в него новые слова!')
