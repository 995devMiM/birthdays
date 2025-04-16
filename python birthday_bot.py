import logging
import json
import jdatetime
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BIRTHDAY_FILE = 'birthdays.json'
CONFIG_FILE = 'config.json'

def load_birthdays():
    try:
        with open(BIRTHDAY_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_birthdays(data):
    with open(BIRTHDAY_FILE, 'w') as f:
        json.dump(data, f)

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f)

# فقط داخل گروه خاص کار کنه
def group_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        config = load_config()
        if update.effective_chat.id == config['group_id']:
            return await func(update, context)
    return wrapper

@group_only
async def set_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if len(context.args) != 1:
        await update.message.reply_text("مثال: /setbirthday 1402-02-28")
        return
    date_str = context.args[0]
    try:
        jdatetime.datetime.strptime(date_str, '%Y-%m-%d')
        birthdays = load_birthdays()
        birthdays[user_id] = {
            'name': update.effective_user.first_name,
            'date': date_str
        }
        save_birthdays(birthdays)
        await update.message.reply_text("تاریخ تولدت ثبت شد.")
    except ValueError:
        await update.message.reply_text("تاریخ معتبر نیست. مثال درست: 1402-02-28")

@group_only
async def toggle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_config()
    config['birthday_messages_enabled'] = not config['birthday_messages_enabled']
    save_config(config)
    status = "فعال شد" if config['birthday_messages_enabled'] else "غیرفعال شد"
    await update.message.reply_text(f"ارسال پیام تبریک {status}.")

@group_only
async def set_custom_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("لطفاً متن پیام رو وارد کن.")
        return
    config = load_config()
    message = ' '.join(context.args)
    config['custom_message'] = message
    save_config(config)
    await update.message.reply_text("پیام تبریک جدید ثبت شد.")

async def check_birthdays(app):
    config = load_config()
    if not config.get('birthday_messages_enabled', True):
        return
    today = jdatetime.date.today().strftime('%m-%d')
    birthdays = load_birthdays()
    for user_id, info in birthdays.items():
        birthday_md = '-'.join(info['date'].split('-')[1:])
        if birthday_md == today:
            text = config.get('custom_message', "تولدت مبارک {name}").replace('{name}', info['name'])
            try:
                await app.bot.send_message(chat_id=config['group_id'], text=text)
            except:
                pass

TOKEN = '7407416518:AAEujLGcvgoNgfS-7fMfkoz-N8_e9sYMPmQ'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! با /setbirthday تاریخ تولدت رو ثبت کن.")

def main():
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setbirthday", set_birthday))
    app.add_handler(CommandHandler("togglebirthdays", toggle_messages))
    app.add_handler(CommandHandler("setmessage", set_custom_message))

    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: app.create_task(check_birthdays(app)), 'cron', hour=7)
    scheduler.start()

    app.run_polling()

if __name__ == '__main__':
    main()