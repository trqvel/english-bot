from telegram import Update
from telegram.ext import CallbackContext
from .start import load_user_data


async def list_words(update: Update, context: CallbackContext):
    user_data = await load_user_data()
    user_id = str(update.message.from_user.id)

    if user_id in user_data and user_data[user_id]:
        words_list = []
        for word_info in user_data[user_id]:
            word_str = f"{word_info['word']}  -  {word_info['translation']}  -  {word_info['practice_count']}"
            words_list.append(word_str)
        message_text = "\n".join(words_list)
        await update.message.reply_text(message_text)
    else:
        await update.message.reply_text('Ваш словарь пуст.')
