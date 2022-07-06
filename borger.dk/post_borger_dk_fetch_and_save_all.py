# Logs in to post.borger.dk and downloads all mail to the same folder as the program.
# The program will keep the authorization for post.borger.dk alive during the download.
import requests
from slugify import slugify
import pickle
import time
import post_borger_dk_poll_and_renew
from post_borger_dk_configuration import cookies_filename
from post_borger_dk_first_login import login
from post_borger_dk_api import get_mailboxes, get_folders, get_all_messages, get_file

session = requests.Session()

def open_cookies():
    with open(cookies_filename, 'rb') as cookie_file:
        session.cookies.update(pickle.load(cookie_file))
        session.headers['X-XSRF-TOKEN'] = session.cookies['XSRF-REQUEST-TOKEN']
try:
    open_cookies()
    session = post_borger_dk_poll_and_renew.poll_and_renew_authorization(session)
except (FileNotFoundError, requests.exceptions.TooManyRedirects):
    login()
    open_cookies()

start_time = time.time()

### RENEW AUTHORIZATION PROCEDURE ###
def time_to_renew(start_time, session):
    execution_time = (time.time() - start_time)
    if execution_time > 60:
        session = post_borger_dk_poll_and_renew.poll_and_renew_authorization(session)
        start_time = time.time()
        try:
            with open(cookies_filename, 'wb') as cookie_file:
                pickle.dump(session.cookies, cookie_file)
        except:
            print('Could not save cookie file.')
    return start_time, session

### API REQUESTS ###
def download_messages(mailbox_number, mailbox_id, folder_name, folder_id, messages):
    print('Downloading and saving messages')
    for message in messages['messages']:
        message_id = message['id']
        label = message['label']
        label_filename = slugify(label)
        if 'receivedDateTime' in message:
            created = message['receivedDateTime']
            message_date = created[:10]
        elif 'sendDateTime' in message:
            sent = message['sendDateTime']
            message_date = sent[:10]            
        sender = message['sender']['label']
        sender_filename = slugify(sender)
        documents = message['documents']
        for document in documents:
            document_id = document['id']
            files = document['files']
            for file in files:
                file_id = file['id']
                filename = file['filename']
                filename_filename = slugify(filename, separator=".")
                file_request = get_file(session, mailbox_id, folder_id, message_id, document_id, file_id)
                save_file_name = mailbox_number + '-' + folder_name + '-' + message_date + '-' + sender_filename + '-' + label_filename + '-' + filename_filename
                if len(save_file_name) > 255:
                    save_file_name = mailbox_number + '-' + folder_name + '-' + message_date + '-' + sender_filename + '-' + label_filename[-20:] + '-' + filename_filename[-20:]
                with open(save_file_name, "wb") as local_file:
                    local_file.write(file_request.content)

mailboxes = get_mailboxes(session)
number_of_mailboxes = len(mailboxes['mailboxes'])
for i, mailbox in enumerate(mailboxes['mailboxes']):
    current_mailbox = i + 1
    print(f'Mailbox {current_mailbox} of {number_of_mailboxes}')
    mailbox_number = str(current_mailbox)
    mailbox_id = mailbox['id']
    folders = get_folders(session, mailbox_id)
    for folder in folders['folders']:
        page = 0
        start_time, session = time_to_renew(start_time, session)
        folder_name = folder['name']
        print(f'Fetching messages in folder {folder_name}')
        folder_id = folder['id']
        messages = get_all_messages(session, mailbox_id, folder_id, page)
        total_elements = messages['totalElements']
        print(f'{total_elements} messages in the folder')
        download_messages(mailbox_number, mailbox_id, folder_name, folder_id, messages)
        total_pages = int(messages['totalPages'])
        if total_pages > 1:
            number_of_requests = total_pages - 1
            for page_number in range(1, total_pages + 1):
                start_time, session = time_to_renew(start_time, session)
                print(f'Fetching more messages: {page_number} of {number_of_requests}')
                messages = get_all_messages(session, mailbox_id, folder_id, page_number)
                download_messages(mailbox_number, mailbox_id, folder_name, folder_id, messages)               