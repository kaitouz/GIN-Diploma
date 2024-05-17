import logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

import os
import json
import telebot
from telebot import types
from telebot.util import quick_markup

from data_manager import Database_manager



# ========== Init ==========
bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"))
STORAGE_PATH = '../ImagesData/Storage'
DBManager = Database_manager()

# def set_chat_menu_button


# ========== /Start, /Help ==========
@bot.message_handler(commands=['menu'])
def start_handler(message):
    if DBManager.check_user_exists(message.from_user.id):
        text = 'Hi, I am GIN, welcome back\n'
        pass
    else:
        DBManager.create_user_id(user_id = message.from_user.id)
        text = 'Hi, I am GIN\n'
    bot.send_message(message.from_user.id, text)

@bot.message_handler(commands=['help', 'menu'])
def help_handler(message):
    text = "List of Commands:"
    text += '\n/start_upload - Get ready to send an image. This command prepares the bot to receive and add an upcoming image to your collection.'
    text += '\n/show_uploads - View a gallery or list of all your uploaded images, allowing you to review your previously submitted content.'
    text += '\n/delete_image - Remove a specific image from your collection using the image ID.'
    text += '\n/generate - Send a prompt after this command, and I will generate a new image based on your creative input.'
    text += '\n/popular_prompts - Explore the prompts most frequently used by other users to get inspired for your own creations.'
    text += '\n/top_rated_prompts - Discover the highest-rated prompts, as chosen by users, to find particularly successful or inspiring examples.'
    bot.send_message(message.from_user.id, text)


# ========== /Uploads ==========
@bot.message_handler(commands=['start_upload', 'add', 'upload'])
def start_upload_handler(message):
    text = '''❕ Send me your photo!'''
    bot.send_message(message.from_user.id, text)
    bot.register_next_step_handler_by_chat_id(message.chat.id, receive_photo)

def receive_photo(message):
    if message.content_type != 'photo':
        text = '''❗ Send me your photo!'''
        bot.send_message(message.from_user.id, text)
        bot.register_next_step_handler_by_chat_id(message.chat.id, receive_photo)
    else:
        photo_id = message.photo[-1].file_id
        photo_info = bot.get_file(message.photo[-1].file_id)

        downloaded_file_data = bot.download_file(photo_info.file_path)
        with open(f'{STORAGE_PATH}/{photo_id}.jpg', 'wb') as new_file:
            new_file.write(downloaded_file_data)
        DBManager.create_upload_by_user_id(photo_id, message.from_user.id)
        text = '''✅ Upload successful! You can now use /show_uploads to view your uploaded photos.'''
        bot.send_message(message.from_user.id, text)


# ========== /Show_uploads ==========
@bot.message_handler(commands=['show_uploads', 'photos'])
def show_uploads_handler(message):
    photos_list = DBManager.get_uploads_by_user_id(message.from_user.id)
    if len(photos_list) == 0:
        text = '''❗ You didn't upload any photo. Please use /start_upload to upload a new photo and let the magic happen!'''
        bot.send_message(message.from_user.id, text)
    else:
        show_uploads(message)

def show_uploads(message, page=0, messageid=None):
    photos_list = DBManager.get_uploads_by_user_id(message.chat.id)

    current_show_page = f'{page + 1}'
    markup = quick_markup({
        '◄'                 : {'callback_data': 'page:-1'},
        current_show_page   : {'callback_data': 'page:0'},
        '►'                 : {'callback_data': 'page:1'},
        'Delete image'      : {'callback_data': 'page:2'},
        'Start upload'      : {'callback_data': 'page:3'}
    }, row_width= 3)


    photo_to_show = open(f'{STORAGE_PATH}/{photos_list[page]}.jpg', 'rb')

    if messageid is not None:
        bot.edit_message_media( 
            media        =   types.InputMedia(type='photo', media=photo_to_show), 
            chat_id      =   message.chat.id, 
            message_id   =   messageid,             
            reply_markup =   markup
        )
    else:
        bot.send_photo(
            chat_id         =   message.chat.id,
            photo           =   photo_to_show,
            caption         =   f"You've uploaded {len(photos_list)} image(s)!!!",
            reply_markup    =   markup,
            parse_mode      =   'Markdown'
        )


def check_page(call):
    if call.data.split(':')[0] != 'page':
        return False
    if call.data.split(':')[1] == '0':
        return False
    if call.data.split(':')[1] == '2' or call.data.split(':')[1] == '3':
        return True
    
    next_page = int(call.message.reply_markup.keyboard[0][1].text) + int(call.data.split(':')[1])

    number_of_photos = len(DBManager.get_uploads_by_user_id(call.message.chat.id))
    return  (next_page > 0) and (next_page <= number_of_photos)

@bot.callback_query_handler(func=check_page)
def page_callback(call):
    if call.data.split(':')[1] == '3':
        text = '''❕ Send me your photo!'''
        bot.send_message(call.message.chat.id, text)
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, receive_photo)        
        return

    if call.data.split(':')[1] == '2':
        current_page = int(call.message.reply_markup.keyboard[0][1].text) - 1
        photos_list = DBManager.get_uploads_by_user_id(call.message.chat.id)
        remove_photo_id = photos_list[current_page]
        DBManager.delete_photo_by_user_id(remove_photo_id)

        if len(photos_list) == 1:
            bot.delete_message(
                call.message.chat.id,
                call.message.message_id
            )
            return

        if current_page == len(photos_list) - 1:
            show_uploads(call.message, current_page - 1, call.message.message_id)
        else:
            show_uploads(call.message, current_page, call.message.message_id)
        return

    next_page = int(call.message.reply_markup.keyboard[0][1].text) + int(call.data.split(':')[1])
    show_uploads(call.message, next_page - 1, call.message.message_id)


# ========== /Delete_image ==========
@bot.message_handler(commands=['delete_photo', 'delete'])
def delete_photo_handler(message):
    photos_list = DBManager.get_uploads_by_user_id(message.from_user.id)
    text = f'''❕ Give me the order of the photo you want to delete (1-{len(photos_list)}).'''
    bot.send_message(message.from_user.id, text)
    bot.register_next_step_handler_by_chat_id(message.chat.id, receive_id_to_delete)


def receive_id_to_delete(message):
    if message.content_type != 'text' or not message.text.isdigit():
        text = '''❗ Give me the order of the photo you want to delete (1-{len(photos_list)}).'''
        bot.send_message(message.from_user.id, text)
        bot.register_next_step_handler_by_chat_id(message.chat.id, receive_id_to_delete)
    else:
        photos_list = DBManager.get_uploads_by_user_id(message.from_user.id)
        order_photo = int(message.text)
        if len(photos_list) == 0 or order_photo < 1 or order_photo > len(photos_list):
            text = '''❗ Give me the order of the photo you want to delete (1-{len(photos_list)}).'''
            bot.send_message(message.from_user.id, text)
            bot.register_next_step_handler_by_chat_id(message.chat.id, receive_id_to_delete)
        else:
            remove_photo_id = photos_list[order_photo - 1]
            DBManager.delete_photo_by_user_id(remove_photo_id)
            text = '''❎ Photo removed successfully!'''
            bot.send_message(message.from_user.id, text)


# ========== /Generate ==========
from redis import Redis
import time

from rq import Queue

redis_connection = Redis(host='redis', port=6379, db=0)
queue = Queue('generate_tasks', connection=redis_connection)

# redis_client = Redis(host='redis', port=6379, db=0)

@bot.message_handler(commands=['generate', 'prompt'])
def generate_handler(message):
    photos_list = DBManager.get_uploads_by_user_id(message.from_user.id)
    if len(photos_list) == 0:
        text = '''❕ You didn't upload any photo. Please use /start_upload to upload a new photo and let the magic happen!'''
        bot.send_message(message.from_user.id, text)
        return
    
    text = '''❕ Send me your creative prompt!'''
    bot.send_message(message.from_user.id, text)
    bot.register_next_step_handler_by_chat_id(message.chat.id, receive_prompt)

def receive_prompt(message):
    if message.content_type != 'text':
        text = '''❗ Send me your creative prompt!'''
        bot.send_message(message.from_user.id, text)
        bot.register_next_step_handler_by_chat_id(message.chat.id, receive_prompt)
        return

    prompt = message.text
    photos_list = DBManager.get_uploads_by_user_id(message.from_user.id)
    task_data = json.dumps({'message_id'    : message.chat.id, 
                            'prompt'        : prompt, 
                            'photos_path'   : photos_list})
    

    job = queue.enqueue('worker.generate_image', task_data)
    
    while True:
        if job.is_finished:
            logging.info(f"Job finish")
            logging.info(job.return_value())
            return_data = json.loads(job.return_value())
            generated_photo = open(f"../ImagesData/Outputs/{return_data['generated_path']}.jpg", 'rb')
            
            # '➀', '➁', '➂', '➃', '➄'
            markup = quick_markup({
                '➀' : {'callback_data': 'rating:1'},
                '➁' : {'callback_data': 'rating:2'},
                '➂' : {'callback_data': 'rating:3'},
                '➃' : {'callback_data': 'rating:4'},
                '➄' : {'callback_data': 'rating:5'}
            }, row_width= 5)
            
            mess = bot.send_photo(
                chat_id         =   message.from_user.id,
                photo           =   generated_photo,
                caption         =   "Congratulations on your new creation! Can you please rate this prompt to help improve our service?",
                reply_markup    =   markup,
                parse_mode      =   'Markdown'
            )
            
            DBManager.create_prompt_by_user_id(user_id      =   message.from_user.id,
                                               mesaage_id   =   mess.message_id, 
                                               prompt_text  =   return_data['prompt'])
            
            return
        elif job.is_failed:
            text = '''Job failed - something went wrong. Let's try that again, or you can contact support for help.'''
            bot.send_message(message.from_user.id, text)
            logging.info(f"Job failed")
            return
        else:
            # text = '''running'''
            # bot.send_message(message.from_user.id, text)
            logging.info(f"Job still running")
        time.sleep(2)

# ========== /Rating ==========
@bot.message_handler(commands=['popular_prompts', 'popular'])
def popular_prompts_handler(message):
    prompts_list = DBManager.get_popular_prompts(limit=5)
    
    text = '''Here is a list of popular prompts that our users love! 
                Get inspired and see if any of these spark your creativity for your next art piece.'''
    for prompt in prompts_list:
        text = text + '\n' + prompt
    bot.send_message(message.from_user.id, text)

@bot.message_handler(commands=['top_rated_prompts', 'top_rated'])
def top_rated_prompts_handler(message):
    prompts_list = DBManager.get_top_rated_prompts(limit=5)
    
    text = f'''Check out this list of top-rated prompts!
                These are favorites among our users and might inspire your next amazing creation."'''
    for prompt in prompts_list:
        text = text + '\n' + prompt
    bot.send_message(message.from_user.id, text)

def check_rating(call):
    if call.data.split(':')[0] != 'rating':
        return False
    if int(call.data.split(':')[1]) == 0:
        return False
    
    old_rating = DBManager.get_rating_by_message_id(call.message.message_id)
    if old_rating is None:
        return True
    if int(call.data.split(':')[1]) != old_rating:
        return True
    return False

@bot.callback_query_handler(func=check_rating)
def rating_callback(call):
    old_rating = DBManager.get_rating_by_message_id(call.message.message_id)
    rating = int(call.data.split(':')[1])

    DBManager.update_rating_by_message_id(call.message.message_id, rating)

    interface = ['➀', '➁', '➂', '➃', '➄']
    interface_black = ['➊', '➋', '➌', '➍', '➎']
    values = ['rating:1', 'rating:2', 'rating:3', 'rating:4', 'rating:5']
    
    interface[rating - 1] = interface_black[rating - 1]
    values[rating - 1] = 'rating:0'

    markup = quick_markup({
        interface[0] : {'callback_data': values[0]},
        interface[1] : {'callback_data': values[1]},
        interface[2] : {'callback_data': values[2]},
        interface[3] : {'callback_data': values[3]},
        interface[4] : {'callback_data': values[4]}
    }, row_width= 5)

    bot.edit_message_caption( 
        chat_id      =   call.message.chat.id, 
        message_id   =   call.message.message_id,             
        caption      =  f'Thank you for your rating! You rated this as: {rating}',
        reply_markup = markup,
        parse_mode   =   'Markdown'
    )
    
# ========== Main ==========
bot.infinity_polling()