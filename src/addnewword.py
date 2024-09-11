from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, CallbackContext, filters
from .start import load_user_data, save_user_data
import re


ADDING_WORD = 0

async def add_new_word_start(update: Update, context: CallbackContext):
    await update.message.reply_text('Выпишите список слов, которые надо добавить в словарь. Формат: слово - перевод')
    return ADDING_WORD

async def add_word(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    words_input = update.message.text.split('\n')
    user_data = await load_user_data()

    english_pattern = re.compile(r'^[A-Za-z\s]+$')
    russian_pattern = re.compile(r'^[А-Яа-я\s]+$')

    if user_id not in user_data:
        user_data[user_id] = []

    for word_pair in words_input:

        try:
            english_word, russian_translation = [part.strip() for part in word_pair.split('-')]

            if not english_pattern.fullmatch(english_word) or not russian_pattern.fullmatch(russian_translation):
                await update.message.reply_text('Ошибка при обработке ввода. Убедитесь, что формат соответствует: слово - перевод')
                continue

            english_word = english_word.lower()
            russian_translation = russian_translation.lower()

            if any(word['word'].lower() == english_word for word in user_data[user_id]):
                await update.message.reply_text(f"Слово '{english_word}' уже есть в вашем словаре.")
                continue

            if any(word['translation'].lower() == russian_translation for word in user_data[user_id]):
                await update.message.reply_text(f"Перевод '{russian_translation}' уже используется в вашем словаре.")
                continue

            if any(word['word'] == english_word for word in user_data[user_id]):
                await update.message.reply_text(f"Слово '{english_word}' уже есть в вашем словаре.")
                continue

            if any(word['translation'] == russian_translation for word in user_data[user_id]):
                await update.message.reply_text(f"Перевод '{russian_translation}' уже используется в вашем словаре.")
                continue

            user_data[user_id].append({
                "word": english_word,
                "translation": russian_translation,
                "is_sent": False,
                "practice_count": 0
            })
            await update.message.reply_text(f"Слово '{english_word}' с переводом '{russian_translation}' добавлено в ваш словарь.")

        except ValueError:
            await update.message.reply_text('Ошибка при обработке ввода. Убедитесь, что формат соответствует: слово - перевод')

    await save_user_data(user_data)
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text('Добавление слов отменено.')
    return ConversationHandler.END

add_word_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('addnewword', add_new_word_start)],
    states={
        ADDING_WORD: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, add_word)
        ],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
