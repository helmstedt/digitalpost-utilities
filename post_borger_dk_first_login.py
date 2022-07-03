# Logs in to post.borger.dk and saves cookies needed for further
# API requests and authorization renewal.
from seleniumwire import webdriver
import requests
import http.cookies
import pickle
from post_borger_dk_configuration import cookies_filename

def login():
    session = requests.Session()
    options = webdriver.ChromeOptions()
    options.add_argument("--log-level=3")
    driver = webdriver.Chrome(chrome_options=options)
    login_url = 'https://post.borger.dk/'
    login = driver.get(login_url)

    print('Opening browser window. Log in to post.borger.dk using MitID or NemID in the browser.')
    print('When you see your inbox in the browser, you are finished.')
    input('Press ENTER once you are finished.')

    # Set necessary cookies
    try:
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
        driver.close()
        with open(cookies_filename, 'wb') as cookie_file:
            pickle.dump(session.cookies, cookie_file)
        print('Login to post.borger.dk went fine.')
        print(f'Cookies saved to {cookies_filename}.')
    except:
        print('Something did not work as expected.')
        print('Did you remember to complete your login before pressing ENTER?')
        print('Try running the program again.')

if __name__ == "__main__":
    login()