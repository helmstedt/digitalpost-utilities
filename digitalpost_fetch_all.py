'''
Logs in to post.borger.dk and downloads all mail to the same folder as the program.
The program will try to keep the authorization for post.borger.dk alive, but is currently
not able to work for more than approximately an hour. If your mailbox takes more than an
hour to download, you will need to modify the API queries for subsequent runs to be able
to download everything.
By Morten Helmstedt (https://helmstedt.dk, helmstedt@gmail.com)
'''
from seleniumwire import webdriver
import requests
import http.cookies
from slugify import slugify
import time
from bs4 import BeautifulSoup

session = requests.Session()

options = webdriver.ChromeOptions()
options.add_argument("--log-level=3")
driver = webdriver.Chrome(chrome_options=options)
login_url = 'https://post.borger.dk/'
login = driver.get(login_url)

start_time = time.time()

print("Opening browser window. Log in to post.borger.dk using MitID or NemID in the browser.")
print("When you see your inbox in the browser, you're finished.")
input("Press ENTER once you're finished.")

### SET NECESSARY COOKIES FOR REQUESTS LIBRARY ###
session.cookies.set('cookiecheck', 'Test', domain='nemlog-in.mitid.dk')
session.cookies.set('loginMethod', 'noeglekort', domain='nemlog-in.mitid.dk')
for request in driver.requests:
    if '/api/mailboxes' in request.url and request.method == 'GET' and request.response.status_code == 200:
        cookies = request.headers['Cookie'].split("; ")
        for cookie in cookies:
            if 'LoggedInBorgerDk' in cookie or 'CorrelationId' in cookie:
                key_value = cookie.split('=')
                session.cookies.set(key_value[0], key_value[1], domain='.post.borger.dk')
    if request.response:
        headers_string = str(request.response.headers)
        headers_list = headers_string.split('\n')
        for header in headers_list:
            if 'set-cookie' in header:
                domain = False
                cookie_string = header.replace('set-cookie: ','')
                if 'expires=' in cookie_string.lower():
                    expires_location = cookie_string.lower().index('expires=')
                    try:
                        expires_end = cookie_string.index('; ',expires_location)
                        cookie_string = cookie_string[:expires_location-1] + cookie_string[expires_end+1:]
                    except:
                        expires_end = cookie_string.index(';',expires_location)
                        cookie_string = cookie_string[:expires_location-1] + cookie_string[expires_end:]
                try:
                    cookie = http.cookies.BaseCookie(cookie_string)
                except:
                    breakpoint()
                try:
                    session.cookies.update(cookie)
                except:
                    breakpoint()                
driver.close()

### RENEW AUTHORIZATION ###
def time_to_renew(start_time):
    execution_time = (time.time() - start_time)
    if execution_time > 240:
        try:
            renew_authorization()
            start_time = time.time()
        except:
            pass
    return start_time

def renew_authorization():
    print('Trying to renew authorization')
    try:
        renew = session.get('https://auth.post.borger.dk/web/auth/login?returnurl=https://post.borger.dk')
        if 'https://nemlog-in.mitid.dk/adfs/ls/?SAMLRequest=' in renew.url:
            fobs = session.get('https://idp.fobs.dk/write.aspx')
            soup = BeautifulSoup(test.text, "html.parser")
            input = soup.find_all('input', {"name":"SAMLResponse"})
            samlresponse = input[0]["value"]
            auth_request = session.post('https://gateway.digitalpost.dk/auth/s9/nemlogin/ssoack', data={'SAMLResponse': samlresponse})
        if session.cookies['XSRF-REQUEST-TOKEN'] != session.headers['X-XSRF-TOKEN']:
            session.headers['X-XSRF-TOKEN'] = session.cookies['XSRF-REQUEST-TOKEN']
    except:
        print('Something went wrong when trying to renew. The program will try to continue.')
    
### API REQUESTS ###
def download_messages(mailbox_number, mailbox_id, folder_name, folder_id, messages_response):
    print('Downloading and saving messages')
    for message in messages_response['messages']:
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
                file_url = api_base_url + 'mailboxes/' + mailbox_id + '/messages/' + message_id + '/documents/' + document_id + '/files/' + file_id + '/content'
                file_request = session.get(file_url)
                save_file_name = mailbox_number + '-' + folder_name + '-' + message_date + '-' + sender_filename + '-' + label_filename + '-' + filename_filename
                if len(save_file_name) > 255:
                    save_file_name = mailbox_number + '-' + folder_name + '-' + message_date + '-' + sender_filename + '-' + label_filename[-20:] + '-' + filename_filename[-20:]
                with open(save_file_name, "wb") as local_file:
                    local_file.write(file_request.content)

api_base_url = 'https://api.post.borger.dk/api/'
session.headers['User-Agent'] = 'digitalpost-utilities'
session.headers['Origin'] = 'https://post.borger.dk'
session.headers['Referer'] = 'https://post.borger.dk/'
session.headers['X-XSRF-TOKEN'] = session.cookies['XSRF-REQUEST-TOKEN']
mailboxes = session.get(api_base_url + 'mailboxes?size=1000')
mailboxes_response = mailboxes.json()
number_of_mailboxes = len(mailboxes_response['mailboxes'])
for i, mailbox in enumerate(mailboxes_response['mailboxes']):
    current_mailbox = i + 1
    print(f'Mailbox {current_mailbox} of {number_of_mailboxes}')
    mailbox_number = str(current_mailbox)
    mailbox_id = mailbox['id']
    folders_url = api_base_url + 'mailboxes/' + mailbox_id + '/folders?sortFields=name:asc&size=1000'
    folders = session.get(folders_url)
    folders_response = folders.json()
    for folder in folders_response['folders']:
        start_time = time_to_renew(start_time)
        folder_name = folder['name']
        print(f'Fetching messages in folder {folder_name}')
        folder_id = folder['id']
        messages_url = api_base_url + 'mailboxes/' + mailbox_id + '/messages?folderId=' + folder_id + '&sortFields=receivedDateTime:ASC,sendDateTime:ASC,lastUpdated:ASC&size=100'
        messages = session.get(messages_url)
        messages_response = messages.json()
        total_elements = messages_response['totalElements']
        print(f'{total_elements} messages in the folder')
        download_messages(mailbox_number, mailbox_id, folder_name, folder_id, messages_response)
        total_pages = int(messages_response['totalPages'])
        if total_pages > 1:
            number_of_requests = total_pages - 1
            for page_number in range(1, total_pages + 1):
                start_time = time_to_renew(start_time)
                print(f'Fetching more messages: {page_number} of {number_of_requests}')
                messages_url = 'https://api.post.borger.dk/api/mailboxes/' + mailbox_id + '/messages?folderId=' + folder_id + '&sortFields=receivedDateTime:ASC,sendDateTime:ASC,lastUpdated:ASC&size=100&page=' + str(page_number)
                messages = session.get(messages_url)
                messages_response = messages.json()
                download_messages(mailbox_number, mailbox_id, folder_name, folder_id, messages_response)