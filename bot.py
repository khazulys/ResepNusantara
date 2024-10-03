import telebot
from telebot import types
import requests
import os
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from keep_alive import keep_alive
import random

load_dotenv()

keep_alive()

API_TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(API_TOKEN)

def user_agent():
    for kanjut in range(1000):
        rr = random.randint
        rc = random.choice
        device = random.choice(['SM-M115F','SM-A600A','SM-S911B','SM-A127F','SM-S911N','SM-A528B','SM-A515U','SM-A137F','SM-A528B','SM-A125U1','SM-A346N','SM-A015U1','SM-G986U1','SM-R925U','SM-G715A','SM-S911B','SM-A528B','SM-M215F','SM-A515F','SM-S911B','SM-N770F','SM-A256U1','SM-S111DL','SM-A750FN','SM-A546B','SM-A035G','SM-S911B','SM-A202F','SM-A528B','SM-G991B'])
        build = random.choice(['UP1A.231005.007','TP1A.220624.014','SP1A.210812.015','RP1A.200720.009','QP1A.190711.019','PPR1.180610.009','OPM1.171019.011'])
        uaku1 = f'Mozilla/5.0 (Linux; Android {str(rr(8,14))}; {device} Build/{build}; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/{str(rr(70,123))}.0.{str(rr(2000,6899))}.{str(rr(70,150))} Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/{str(rr(390,455))}.0.0.{str(rr(30,45))}.{str(rr(100,155))};]'
        uaku2 = f'Mozilla/5.0 (Linux; Android {str(rr(7,14))}; {device}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{str(rr(70,123))}.0.{str(rr(2000,6899))}.{str(rr(70,150))} Mobile Safari/537.36'
        uaqu = random.choice([uaku1,uaku2])
        
        return uaqu

# Generate random User-Agent for headers
headers = {
    'User-Agent': UserAgent().random,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://cookpad.com/id',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

USER_DATA_FILE = 'users.txt'

def search_receipt(query):
    """Search for recipes based on a query."""
    url = f'https://cookpad.com/id/cari/{query.replace(" ", "%20")}?event=search.suggestion&order=recent'
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    find = soup.find_all('a', class_='block-link__main')

    receipts = [(link.get_text(strip=True), link.get('href')) for link in find]
    print(soup)
    print(find)
    print(receipts)
    return receipts


def get_ingredients_and_steps(url):
    """Retrieve ingredients and steps from a specific recipe URL."""
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Get image, title, ingredients, and steps
    image_url = soup.find('img', attrs={'loading': 'eager'})
    image_url = image_url.get("src") if image_url else None

    title = soup.find('h1').get_text(strip=True)

    ingredients = [item.get_text(strip=True) for item in soup.find('div', id='ingredients').find_all('li')]

    steps = []
    find_steps = soup.find('div', id='steps')
    if find_steps:
        steps = [step.find('p').text.strip() for step in find_steps.find_all('li', class_='step')]

    return image_url, title, ingredients, steps


def split_and_send_message(chat_id, text, parse_mode='Markdown'):
    """Split long messages to fit Telegram's character limit."""
    max_length = 4096
    while text:
        if len(text) > max_length:
            bot.send_chat_action(chat_id, 'typing')
            bot.send_message(chat_id, text[:max_length], parse_mode=parse_mode)
            text = text[max_length:]
        else:
            bot.send_chat_action(chat_id, 'typing')
            bot.send_message(chat_id, text, parse_mode=parse_mode)
            break


def send_photo_with_long_caption(chat_id, photo, caption, parse_mode='Markdown'):
    """Send photos with captions that exceed Telegram's character limit."""
    max_caption_length = 1024
    if len(caption) > max_caption_length:
        bot.send_chat_action(chat_id, 'upload_photo')
        bot.send_photo(chat_id, photo, caption[:max_caption_length], parse_mode=parse_mode)
        split_and_send_message(chat_id, caption[max_caption_length:], parse_mode=parse_mode)
    else:
        bot.send_chat_action(chat_id, 'upload_photo')
        bot.send_photo(chat_id, photo, caption, parse_mode=parse_mode)


def send_menu(chat_id, message_id, page, receipts, query):
    """Display paginated menu for search results."""
    items_per_page = 5
    start = page * items_per_page
    end = start + items_per_page
    menu_page = receipts[start:end]

    # Format menu
    menu_text = "*Hasil Pencarian :*\n\n"
    for i, (name, _) in enumerate(menu_page, start=1):
        menu_text += f"{start + i}. {name}\n"

    # Create inline keyboard
    markup = types.InlineKeyboardMarkup()
    buttons_row = [types.InlineKeyboardButton(str(start + i + 1), callback_data=f"menu_{start + i}_{query}") for i in range(len(menu_page))]
    markup.add(*buttons_row)

    # Navigation buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton("<", callback_data=f"page_{page - 1}_{query}"))
    if end < len(receipts):
        nav_buttons.append(types.InlineKeyboardButton(">", callback_data=f"page_{page + 1}_{query}"))
    markup.add(*nav_buttons)

    #bot.send_chat_action(chat_id, 'typing')
    bot.edit_message_text(menu_text, chat_id, message_id, reply_markup=markup, parse_mode="Markdown")

def update_user_list(user_id):
    """Update user list by adding new user if not exists."""
    if not os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'w') as f:
            f.write('')

    with open(USER_DATA_FILE, 'r') as f:
        users = f.read().splitlines()

    if str(user_id) not in users:
        with open(USER_DATA_FILE, 'a') as f:
            f.write(f"{user_id}\n")

    return len(users) + 1 if str(user_id) not in users else len(users)
    
@bot.message_handler(commands=['start'])
def welcome_message(message):
    username = message.from_user.username
    user_id = message.from_user.id
    
    # Update and get total users
    total_users = update_user_list(user_id)

    teks = (f"Hai ibu *@{username}*, terima kasih sudah menggunakan bot ini. "
            f"Untuk memulai mencari resep masakan silahkan ketik perintah */cari_resep <nama masakan>*.\n\n"
            f"Contoh :\n\n*/cari_resep gulai ikan kakap*\n\n"
            f"Total pengguna bot ini: *{total_users}*")
    
    bot.send_chat_action(message.chat.id, 'typing')
    bot.reply_to(message, teks, parse_mode='Markdown')
    
@bot.message_handler(commands=['cari_resep'])
def search_command(message):
    """Handle the /search command."""
    query = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    if not query:
        bot.send_chat_action(message.chat.id, 'typing')
        bot.send_message(message.chat.id, "Silakan masukkan nama resep yang ingin dicari setelah perintah /cari_resep.")
        return

    receipts = search_receipt(query)
    if not receipts:
        bot.send_chat_action(message.chat.id, 'typing')
        bot.send_message(message.chat.id, "Resep tidak ditemukan.")
        return

    initial_message = bot.send_message(message.chat.id, "Loading...")
    send_menu(message.chat.id, initial_message.message_id, 0, receipts, query)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """Handle callback queries for pagination and menu selection."""
    if call.data.startswith("page_"):
        page, query = call.data.split("_")[1:3]
        receipts = search_receipt(query)
        send_menu(call.message.chat.id, call.message.message_id, int(page), receipts, query)

    elif call.data.startswith("menu_"):
        item_index, query = call.data.split("_")[1:3]
        receipts = search_receipt(query)

        if 0 <= int(item_index) < len(receipts):
            selected_name, selected_href = receipts[int(item_index)]
            image_url, title, ingredients, steps = get_ingredients_and_steps(f"https://cookpad.com{selected_href}")

            # Build and send recipe details
            caption = f"Judul: *{title.capitalize()}*\n\n*Bahan-bahan:*\n\n" + "\n".join(ingredients) + "\n\n*Langkah-langkah:*\n\n" + "\n".join(f"Langkah {i + 1}: {step}" for i, step in enumerate(steps))
            if image_url:
                send_photo_with_long_caption(call.message.chat.id, image_url, caption, parse_mode='Markdown')
            else:
                split_and_send_message(call.message.chat.id, caption, parse_mode='Markdown')

            bot.answer_callback_query(call.id, text=f"Kamu memilih: {selected_name}")
        else:
            bot.answer_callback_query(call.id, text="Invalid selection.")


# Start the bot
bot.infinity_polling()
