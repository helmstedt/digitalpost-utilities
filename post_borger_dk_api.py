# API functions for mailboxes, folders, messages and files on post.borger.dk.
api_base_url = 'https://api.post.borger.dk/api/'

def get_mailboxes(session):
    mailboxes = session.get(api_base_url + 'mailboxes?size=1000')
    mailboxes_response = mailboxes.json()
    return mailboxes_response
    
def get_folders(session, mailbox_id):
    folders_url = api_base_url + 'mailboxes/' + mailbox_id + '/folders?sortFields=name:asc&size=1000'
    folders = session.get(folders_url)
    folders_response = folders.json()
    return folders_response

def get_all_messages(session, mailbox_id, folder_id, page):
    messages_url = api_base_url + 'mailboxes/' + mailbox_id + '/messages?folderId=' + folder_id + '&sortFields=receivedDateTime:ASC,sendDateTime:ASC,lastUpdated:ASC&size=100&page=' + str(page)
    messages = session.get(messages_url)
    messages_response = messages.json()
    return messages_response

def get_unread_messages(session, mailbox_id, folder_id):
    messages_url = api_base_url + 'mailboxes/' + mailbox_id + '/messages?read=false&folderId=' + folder_id + '&sortFields=receivedDateTime:DESC,sendDateTime:DESC,lastUpdated:DESC&size=100'
    messages = session.get(messages_url)
    messages_response = messages.json()
    return messages_response

def get_file(session, mailbox_id, folder_id, message_id, document_id, file_id):
    file_url = api_base_url + 'mailboxes/' + mailbox_id + '/messages/' + message_id + '/documents/' + document_id + '/files/' + file_id + '/content'
    file = session.get(file_url)
    return file
 
def mark_message_as_read(session, mailbox_id, message_id, version):
    mark_as_read_url = api_base_url + 'bulk'
    json = {
        "time-out": 30000,
        "requests": [
            {
                "headers": [
                    {
                        "key": "If-Match",
                        "value": version
                    },
                    {
                        "key": "Content-Type",
                        "value": "application/json; charset=UTF-8"
                    }
                ],
                "id": message_id,
                "method": "PATCH",
                "path": "/api/mailboxes/" + mailbox_id + "/messages/" + message_id,
                "body": {
                    "read": True
                }
            }
        ]
    }
    mark_as_read = session.post(mark_as_read_url, json=json)