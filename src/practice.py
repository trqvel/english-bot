from .start import load_user_data, save_user_data 
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import asyncio
import random


async def practice(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    user_data = await load_user_data()

    words_to_practice = [word for word in user_data[user_id] if word['is_sent'] and word['practice_count'] > 0]

    if not words_to_practice:
        await update.message.reply_text('На данный момент нет слов для практики.')
        return

    context.user_data['words_to_practice'] = words_to_practice
    context.user_data['current_word_index'] = 0

    await send_practice_word(update, context, words_to_practice[0], user_id)


async def send_practice_word(update: Update, context: CallbackContext, word, user_id):
    await asyncio.sleep(2)
    correct_translation = word['translation']
    all_translations = [w['translation'] for w in context.user_data['words_to_practice'] if w['word'] != word['word']]
    random_translations = random.sample(all_translations, 3) if len(all_translations) > 3 else all_translations[:3]
    random_translations.append(correct_translation)
    random.shuffle(random_translations)

    keyboard = [[InlineKeyboardButton(translation, callback_data=f"practice_{user_id}_{word['word']}_{translation}")]
                for translation in random_translations]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        message = await update.callback_query.message.reply_text(
            f'Практика перевода слова "{word["word"]}". Выберите правильный перевод:', reply_markup=reply_markup
        )
    else:
        message = await update.message.reply_text(
            f'Практика перевода слова "{word["word"]}". Выберите правильный перевод:', reply_markup=reply_markup
        )

    context.user_data['last_practice_message_id'] = message.message_id


async def handle_practice_choice(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    _, user_id, word_to_practice, chosen_translation = query.data.split('_')

    user_data = await load_user_data()
    word_data = next((word for word in user_data[user_id] if word['word'] == word_to_practice), None)

    if not word_data:
        await query.edit_message_text("Произошла ошибка, попробуйте снова.")
        return

    if chosen_translation == word_data['translation']:
        word_data['practice_count'] -= 1
        if word_data['practice_count'] <= 0:
            user_data[user_id] = [word for word in user_data[user_id] if word['word'] != word_to_practice]
            response_text = f"Отлично! Правильный перевод слова '{word_to_practice}'. Слово удалено из списка."
        else:
            response_text = f"Отлично! Правильный перевод слова '{word_to_practice}'. Его нужно практиковать ещё {word_data['practice_count']} раз(а)."
        await save_user_data(user_data)
    else:
        word_data['practice_count'] += 1
        response_text = f"Неверно. Попробуйте снова при следующем вызове команды '/practice'"
        await save_user_data(user_data)

    await query.edit_message_text(response_text)

    await asyncio.sleep(3)

    context.user_data['current_word_index'] += 1
    words_to_practice = context.user_data['words_to_practice']
    current_word_index = context.user_data['current_word_index']

    if current_word_index < len(words_to_practice):
        next_word = words_to_practice[current_word_index]
        await send_practice_word(update, context, next_word, user_id)
    else:
        await query.message.reply_text("Все слова для практики пройдены!")