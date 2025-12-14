# Sends unread messages from mit.dk to an e-mail.
import requests
import json 
import smtplib                                      # Sending e-mails
from email.mime.multipart import MIMEMultipart      # Creating multipart e-mails
from email.mime.text import MIMEText                # Attaching text to e-mails
from email.mime.application import MIMEApplication  # Attaching files to e-mails
from email.utils import formataddr                  # Used for correct encoding of senders with special characters in name (e.g. Københavns Kommune)
from mit_dk_configuration import email_data, tokens_filename
import time
import pickle

base_url = 'https://post.mit.dk/internal-api/rest/api/v1/'
session = requests.Session()
session.headers['X-CSRF'] = "1"
session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0'
with open('cookies.pickle', 'rb') as f:
    session.cookies.update(pickle.load(f))

def get_simple_endpoint(endpoint):
    tries = 1
    while tries <= 3:
        response = session.get(base_url + endpoint)
        response.raise_for_status()
        try:
            response_json = response.json()
            return response.json()
        except:
            tries += 1
            time.sleep(1)
            pass
    if tries == 3:
        print(f'Unable to get a succesful response for endpoint {endpoint}. Here is the response:')
        print(response.text)
        return False
    
def get_message_list(mailbox):
    endpoint = 'mailboxes/messages'
    params = {
        'privateOffset': 0,
        'publicOffset': 0,
        'size': 10,
        'mailboxIds': mailbox['mailboxId'],
        'messageState': "RECEIVED",
        'deleted': "false",
        'sortFields': 'messageDateTime:DESC'
    }
    tries = 1
    while tries < 3:
        try:
            messages = session.get(base_url + endpoint, params=params)
            messages.raise_for_status()
            messages_json = messages.json()
            return messages_json
        except:
            tries += 1
            time.sleep(1)
            pass            
    print('Unable to convert response to json when getting messages after 3 tries. Here is the response:')
    print(messages.status_code, messages.text)        

def get_folders(mailboxes):
    endpoint = 'mailboxes/folders'
    mailboxes_and_folders = {}
    breakpoint()
    for mailbox in mailboxes:
        mailboxes_and_folders[mailbox['mailboxId']] = []
        params = {
            'mailboxId': mailbox['mailboxId']
        }
        tries = 1
        while tries < 3:
            try:
                folders = session.get(base_url + endpoint, params=params)
                folders.raise_for_status()
                folders_json = folders.json()
                for folder in folders_json['folders']:
                    mailboxes_and_folders[mailbox['mailboxId']].append(folder['id'])
            except:
                tries += 1
                time.sleep(1)
                pass        
    return mailboxes_and_folders

def get_message(mailbox, message):
    endpoint = f"mailboxes/{mailbox['mailboxId']}/messages/{message['id']}"
    tries = 1
    while tries < 3:
        try:
            message = session.get(base_url + endpoint)
            message.raise_for_status()
            message_json = message.json()
            return message_json
        except:
            tries += 1
            time.sleep(1)
            pass            
    print('Unable to download message metadata. Here is the response:')
    print(message.status_code, message.text)     

def get_file(mailbox, message, document, file):
    endpoint = f"mailboxes/{mailbox['mailboxId']}/messages/{message['id']}/documents/{document['id']}/files/{file['id']}/content"
    tries = 1
    while tries < 3:
        try:
            file = session.get(base_url + endpoint)
            file.raise_for_status()
            return file
        except:
            tries += 1
            time.sleep(1)
            pass            
    print('Unable to download message contents. Here is the response:')
    print(message.status_code, message.text)   

def mark_message_as_unread(mailbox, message):
    endpoint = f"mailboxes/{mailbox['mailboxId']}/messages/{message['id']}/unread"
    tries = 1
    while tries < 3:
        try:
            request = session.patch(base_url + endpoint)
            request.raise_for_status()
            return request
        except:
            tries += 1
            time.sleep(1)
            pass            
    print('Unable to mark message as unread. Here is the response:')
    print(request.status_code, request.text)  

mailserver_connect = False            
try:
    mailboxes = get_simple_endpoint('mailboxes')
    for mailbox in mailboxes['mailboxes']:
        messages = get_message_list(mailbox)
        for message in messages['searchResults']:
            if message['read'] == False:
                try:
                    if mailserver_connect == False:
                        server = smtplib.SMTP(email_data['emailserver'], email_data['emailserverport'])
                        server.ehlo()
                        server.starttls()
                        server.login(email_data['emailusername'], email_data['emailpassword'])
                        mailserver_connect  = True               
                    label = message['label']
                    sender = message['senderName']
                    message_data = get_message(mailbox, message)
                    msg = MIMEMultipart('alternative')
                    msg['From'] = formataddr((sender, email_data['emailfrom']))
                    msg['To'] = email_data['emailto']
                    msg['Subject'] = "mit.dk: " + label
                    for document in message_data['message']['documents']:
                        for file_data in document['files']:
                            file = get_file(mailbox, message, document, file_data)
                            if file_data['encodingFormat'] == 'text/plain':
                                body = file.text
                                msg.attach(MIMEText(body, 'plain')) 
                                part = MIMEApplication(file.content)
                                part.add_header('Content-Disposition', 'attachment', filename=file_data['filename'])
                                msg.attach(part) 
                            elif file_data['encodingFormat'] == 'text/html':
                                body = file.text
                                msg.attach(MIMEText(body, 'html'))
                                part = MIMEApplication(file.content)
                                part.add_header('Content-Disposition', 'attachment', filename=file_data['filename'])
                                msg.attach(part)                         
                            elif file_data['encodingFormat'] == 'application/pdf' or file['encoding_format'] == 'text/xml':  
                                part = MIMEApplication(file.content)
                                part.add_header('Content-Disposition', 'attachment', filename=file_data['filename'])
                                msg.attach(part)
                    print(f'Sender en mail fra mit.dk fra {sender} med emnet {label}')
                    server.sendmail(email_data['emailfrom'], email_data['emailto'], msg.as_string())
                except Exception as error:
                    print('FEJL')
                    print(error)
                    mark_message = mark_message_as_unread(mailbox, message)  
finally:
    with open('cookies.pickle', 'wb') as f:
        pickle.dump(session.cookies, f)        
    if mailserver_connect:
        server.quit()