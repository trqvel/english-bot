from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import random
from .start import load_user_data, save_user_data
import asyncio


async def learn(update: Update, context: CallbackContext, with_delay=False, message=None):
    user_id = str(update.effective_user.id)
    user_data = await load_user_data()

    if user_id not in user_data or len(user_data[user_id]) < 4:
        await (message or update.message).reply_text(
            'Недостаточно слов в словаре для начала обучения. Добавьте минимум 4 слова.'
        )
        return

    words_to_learn = [word for word in user_data[user_id] if not word['is_sent']]

    if not words_to_learn:
        await (message or update.message).reply_text('Вы изучили все слова в вашем словаре!')
        return

    if with_delay:
        await asyncio.sleep(3)

    word = random.choice(words_to_learn)
    correct_translation = word['translation']

    all_translations = [w['translation'] for w in user_data[user_id] if w['word'] != word['word']]
    random_translations = random.sample(all_translations, 3) if len(all_translations) > 3 else all_translations[:3]
    random_translations.append(correct_translation)
    random.shuffle(random_translations)

    context.user_data['available_translations'] = random_translations

    attempts_key = f'attempts_{user_id}_{word["word"]}'
    context.user_data[attempts_key] = 3

    keyboard = [[InlineKeyboardButton(translation, callback_data=f"learn_{word['word']}_{translation}")]
                for translation in random_translations]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await (message or update.message).reply_text(
        f'Как переводится слово "{word["word"]}"?', reply_markup=reply_markup
    )
    context.user_data['correct_translation'] = correct_translation
    context.user_data['word_to_learn'] = word['word']
    context.user_data['user_id'] = user_id

async def handle_translation_choice(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    user_data = await load_user_data()

    _, word_to_learn, chosen_translation = query.data.split('_')
    word_data = next((word for word in user_data[user_id] if word['word'] == word_to_learn), None)

    if not word_data:
        await query.message.edit_text("Произошла ошибка, попробуйте снова.")
        return

    attempts_key = f'attempts_{user_id}_{word_to_learn}'

    if attempts_key not in context.user_data:
        context.user_data[attempts_key] = 3
    
    available_translations = context.user_data.get('available_translations', [])

    if chosen_translation == word_data['translation']:
        word_data['is_sent'] = True
        word_data['practice_count'] += 3
        await save_user_data(user_data)
        await query.message.edit_text(f"Отлично! Правильный перевод: '{chosen_translation}'. Отправляю следующее слово...")
        context.user_data.pop('available_translations', None)
        await learn(update, context, with_delay=True, message=query.message)
        
    else:
        word_data['is_sent'] = True
        context.user_data[attempts_key] -= 1
        if chosen_translation in available_translations:
            available_translations.remove(chosen_translation)
            context.user_data['available_translations'] = available_translations

        if context.user_data[attempts_key] > 0:
            keyboard = [[InlineKeyboardButton(translation, callback_data=f"learn_{word_to_learn}_{translation}")]
                        for translation in available_translations]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(
                text=f"Неверный перевод. Попробуйте снова: как переводится слово '{word_to_learn}'?",
                reply_markup=reply_markup
            )
        else:
            word_data['practice_count'] += 5
            await save_user_data(user_data)
            await query.message.edit_text(
                text=f"Попытки закончились. Cлово '{word_to_learn}' надо практиковать, вот как оно переводится: '{word_to_learn}' - '{word_data['translation']}'!"
            )
            context.user_data.pop('available_translations', None)
            await learn(update, context, with_delay=True, message=query.message)