import telebot
from loguru import logger
import os
import sys
import time
from telebot.types import InputFile
from img_proc import Img


class Bot:

    def __init__(self, token, telegram_chat_url):
        # create a new instance of the TeleBot class.
        # all communication with Telegram servers are done using self.telegram_bot_client
        self.telegram_bot_client = telebot.TeleBot(token)

        # remove any existing webhooks configured in Telegram servers
        self.telegram_bot_client.remove_webhook()
        time.sleep(0.5)

        # set the webhook URL
        self.telegram_bot_client.set_webhook(url=f'{telegram_chat_url}/'
                                                 f'{token}/', timeout=60,
                                             certificate=open("polybot/cert.pem", "r"))

        logger.info(f'Telegram Bot information\n\n{self.telegram_bot_client.get_me()}')

    def send_text(self, chat_id, text):
        self.telegram_bot_client.send_message(chat_id, text)

    def send_text_with_quote(self, chat_id, text, quoted_msg_id):
        self.telegram_bot_client.send_message(chat_id, text, reply_to_message_id=quoted_msg_id)

    def is_current_msg_photo(self, msg):
        return 'photo' in msg

    def download_user_photo(self, msg):
        """
        Downloads the photos that sent to the Bot to `photos` directory (should be existed)
        :return:
        """
        if not self.is_current_msg_photo(msg):
            raise RuntimeError(f'Message content of type \'photo\' expected')

        file_info = self.telegram_bot_client.get_file(msg['photo'][-1]['file_id'])
        data = self.telegram_bot_client.download_file(file_info.file_path)
        folder_name = file_info.file_path.split('/')[0]

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        with open(file_info.file_path, 'wb') as photo:
            photo.write(data)

        return file_info.file_path

    def send_photo(self, chat_id, img_path):
        if not os.path.exists(img_path):
            raise RuntimeError("Image path doesn't exist")

        self.telegram_bot_client.send_photo(
            chat_id,
            InputFile(img_path)
        )

    def handle_message(self, msg):
        """Bot Main message handler"""
        logger.info(f'Incoming message: {msg}')
        self.send_text(msg['chat']['id'], f'Your original message: {msg["text"]}')


class QuoteBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        if msg["text"] != 'Please don\'t quote me':
            self.send_text_with_quote(msg['chat']['id'], msg["text"], quoted_msg_id=msg["message_id"])


class ImageProcessingBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')
        choices_msg = ('- Blur\n'
                        '- Contour\n'
                        '- Rotate [number of rotations]\n'
                        '- Salt and pepper\n'
                        '- Segment\n'
                        '- Concat')
        usage_msg = ('Please send a photo, with a caption of the '
                        'filter you want to apply on it.\n'
                        f'{choices_msg}')
        if "text" in msg:
            if msg["text"] == '/start':
                self.send_text(msg['chat']['id'],
                               'Hello! I am your bot. How can I help you today?')
                self.send_text(msg['chat']['id'], usage_msg)
            elif msg["text"] == 'Hi':
                self.send_text(msg['chat']['id'], 'Hi there, how can i help you today?')
            elif msg["text"] == 'you':
                self.send_text(msg['chat']['id'], 'Noooo, Yooooou')
            else:
                self.send_text(msg['chat']['id'], f'Heeeey, Don\'t \"{msg["text"]}\" me!!')
        else:
            is_photo = self.is_current_msg_photo(msg)
            try:
                if is_photo:
                    self.send_text(msg['chat']['id'], 'processing the image...')
                    img_path = self.download_user_photo(msg)
                    img = Img(img_path)
                    process_option = msg['caption'].strip().lower()
                    if process_option == 'blur':
                        img.blur()
                    elif process_option == 'contour':
                        img.contour()
                    elif 'rotate' in process_option:
                        num_of_rotations = int(process_option.split(' ')[1])
                        for _ in range(num_of_rotations):
                            img.rotate()
                    elif process_option == 'salt and pepper':
                        img.salt_n_pepper()
                    elif process_option == 'segment':
                        img.segment()
                    elif process_option == 'concat':
                        img2_path = self.download_user_photo(msg)
                        img2 = Img(img2_path)
                        img.concat(img2)
                    else:
                        invalid_msg = ('Invalid option\n'
                                       'You can just choose:\n'
                                       f'{choices_msg}')
                        self.send_text(msg['chat']['id'], invalid_msg)
                        return
                    new_img_path = img.save_img()
                    self.send_photo(msg['chat']['id'], new_img_path)
                else:
                    self.send_text(msg['chat']['id'], usage_msg)
            except Exception as e:
                logger.error(f'Error: {e}')
                self.send_text(msg['chat']['id'], 'something went wrong...\n'
                                                  'please try again\n\n'
                                                  '{usage_msg}')
