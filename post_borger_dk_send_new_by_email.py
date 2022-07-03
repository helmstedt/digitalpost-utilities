# Sends new messages from https://post.borger.dk to an e-mail address.
# Run every 1-2 minutes to ensure authorization is renewed regularly.
import requests
import pickle
import smtplib										# Sending e-mails
from email.mime.multipart import MIMEMultipart		# Creating multipart e-mails
from email.mime.text import MIMEText				# Attaching text to e-mails
from email.mime.application import MIMEApplication	# Attaching files to e-mails
from email.utils import formataddr					# Used for correct encoding of senders with special characters in name (e.g. Københavns Kommune)
import post_borger_dk_poll_and_renew
from post_borger_dk_configuration import cookies_filename, email_data
from post_borger_dk_api import get_mailboxes, get_folders, get_unread_messages, get_file, mark_message_as_read

session = requests.Session()
try:
    with open(cookies_filename, 'rb') as cookie_file:
        session.cookies.update(pickle.load(cookie_file))
except:
    print('Could not load cookie file. Did you run post_borger_dk_first_login.py?')

try:
    session = post_borger_dk_poll_and_renew.poll_and_renew_authorization(session)
    session.headers['X-XSRF-TOKEN'] = session.cookies['XSRF-REQUEST-TOKEN']
except requests.exceptions.TooManyRedirects:
    print('Could not renew authorization. Try running post_borger_dk_first_login.py to refresh cookie file.')
    
mailserver_connect = False
mailboxes = get_mailboxes(session)
for mailbox in mailboxes['mailboxes']:
    mailbox_id = mailbox['id']
    folders = get_folders(session, mailbox_id)
    for folder in folders['folders']:
        folder_id = folder['id']
        unread_messages = get_unread_messages(session, mailbox_id, folder_id)
        total_elements = unread_messages['totalElements']
        if total_elements:
            if mailserver_connect == False:
                server = smtplib.SMTP(email_data['emailserver'], email_data['emailserverport'])
                server.ehlo()
                server.starttls()
                server.login(email_data['emailusername'], email_data['emailpassword'])
                mailserver_connect = True
            print(f'Getting and sending {total_elements} unread messages')
            for message in unread_messages['messages']:
                sender = message['sender']['label']
                label = message['label']
                message_id = message['id']
                version = message['version']
                msg = MIMEMultipart('alternative')
                msg['From'] = formataddr((sender, email_data['emailfrom']))
                msg['To'] = email_data['emailto']
                msg['Subject'] = "Digital Post: " + label
                documents = message['documents']
                for document in documents:
                    document_id = document['id']
                    files = document['files']
                    for file in files:
                        encoding_format = file['encodingFormat']
                        file_id = file['id']
                        filename = file['filename']
                        file_content = get_file(session, mailbox_id, folder_id, message_id, document_id, file_id)
                        if encoding_format == 'text/plain':
                            body = file_content.text
                            msg.attach(MIMEText(body, 'plain')) 
                            part = MIMEApplication(file_content.content)
                            part.add_header('Content-Disposition', 'attachment', filename=filename)
                            msg.attach(part) 
                        elif encoding_format == 'text/html':
                            body = file_content.text
                            msg.attach(MIMEText(body, 'html'))
                            part = MIMEApplication(file_content.content)
                            part.add_header('Content-Disposition', 'attachment', filename=filename)
                            msg.attach(part) 
                        elif encoding_format == 'application/pdf':   
                            part = MIMEApplication(file_content.content)
                            part.add_header('Content-Disposition', 'attachment', filename=filename)
                            msg.attach(part)
                        else:    
                            part = MIMEApplication(file_content.content)
                            part.add_header('Content-Disposition', 'attachment', filename=filename)
                            msg.attach(part)
                print(f'Sending an e-mail from post.borger.dk from {sender} with the subject {label}')
                server.sendmail(email_data['emailfrom'], email_data['emailto'], msg.as_string())
                mark_message_as_read(session, mailbox_id, message_id, version)        
                        