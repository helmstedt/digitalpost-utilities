# Logs in to mit.dk og saves tokens needed for further requests.
# Method from https://github.com/dk/Net-MitDK/. Thank you.
from seleniumwire import webdriver
import requests
from bs4 import BeautifulSoup
import http.cookies
import gzip
import json 
import base64
from hashlib import sha256
import string
import secrets
from mit_dk_configuration import tokens_filename

def random_string(size):        
    letters = string.ascii_lowercase+string.ascii_uppercase+string.digits+string.punctuation+string.whitespace           
    random_string = ''.join(secrets.choice(letters) for i in range(size))
    encoded_string = random_string.encode(encoding="ascii")
    url_safe_string = base64.urlsafe_b64encode(encoded_string).decode()
    url_safe_string_no_padding = url_safe_string.replace('=','')
    return url_safe_string_no_padding

def save_tokens(response):
    with open(tokens_filename, "wt", encoding="utf8") as token_file:
        token_file.write(response)

state = random_string(23)
nonce = random_string(93)
code_verifier = random_string(93)
code_challenge = base64.urlsafe_b64encode(sha256(code_verifier.encode('ascii')).digest()).decode().replace('=','')
 
login_url = 'https://gateway.mit.dk/view/client/authorization/login?client_id=view-client-id-mobile-prod-1-id&response_type=code&scope=openid&state=' + state + '&code_challenge=' + code_challenge + '&code_challenge_method=S256&response_mode=query&nonce=' + nonce + '&redirect_uri=com.netcompany.mitdk://nem-callback&deviceName=digitalpost-utilities&deviceId=pc&lang=en_US' 

options = webdriver.ChromeOptions()
options.add_argument("--log-level=3")
driver = webdriver.Chrome(chrome_options=options)
login = driver.get(login_url)

print("Opening browser window. Log in to mit.dk using MitID or NemID in the browser.")
print("When you see a blank page in your browser at https://nemlog-in.mitid.dk/LoginOption.aspx, you're finished.")
input("Press ENTER once you're finished.")

session = requests.Session()

for request in driver.requests:
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
                    cookie_string = header.replace('set-cookie: ','')
                    cookie = http.cookies.BaseCookie(cookie_string)
                    for key in cookie.keys():
                        # Requests is picky about dashes in cookie expiration dates. Fix.
                        if 'expires' in cookie[key]:
                            expiry = cookie[key]['expires']
                            if expiry:
                                expiry_list = list(expiry)
                                expiry_list[7] = '-'
                                expiry_list[11] = '-'
                                cookie[key]['expires'] = ''.join(expiry_list)
                    session.cookies.update(cookie)

        if request.method == 'POST' and request.url == 'https://nemlog-in.mitid.dk/LoginOption.aspx' and request.response.status_code == 200:
            if request.response.headers['content-encoding'] == 'gzip':
                response = gzip.decompress(request.response.body).decode()
            else:
                response = request.response.body.decode()
            soup = BeautifulSoup(response, "html.parser")
            input = soup.find_all('input', {"name":"SAMLResponse"})
            samlresponse = input[0]["value"]

driver.close()
request_code_part_one = session.post('https://gateway.digitalpost.dk/auth/s9/mit-dk-nemlogin/ssoack', data={'SAMLResponse': samlresponse}, allow_redirects=False)
request_code_part_one_redirect_location = request_code_part_one.headers['Location']
request_code_part_two = session.get(request_code_part_one_redirect_location, allow_redirects=False)
request_code_part_two_redirect_location = request_code_part_two.headers['Location']
request_code_part_three = session.get(request_code_part_two_redirect_location, allow_redirects=False)
request_code_part_three_redirect_location = request_code_part_three.headers['Location']
code_start = request_code_part_three_redirect_location.index('code=') + 5
code_end = request_code_part_three_redirect_location.index('&', code_start)
code = request_code_part_three_redirect_location[code_start:code_end]
redirect_url = 'com.netcompany.mitdk://nem-callback'
token_url = 'https://gateway.mit.dk/view/client/authorization/token?grant_type=authorization_code&redirect_uri=' + redirect_url + '&client_id=view-client-id-mobile-prod-1-id&code=' + code + '&code_verifier=' + code_verifier
request_tokens = session.post(token_url)
save_tokens(request_tokens.text)    
print('Login to mit.dk went fine.')
print(f'Tokens saved to {tokens_filename}.')