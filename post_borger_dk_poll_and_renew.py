# Check and renew auth on post.borger.dk.
from bs4 import BeautifulSoup
import pickle
from post_borger_dk_configuration import cookies_filename

def set_poll_headers(session):
    session.headers['X-XSRF-TOKEN'] = session.cookies['XSRF-REQUEST-TOKEN']
    session.headers['CorrelationId'] = session.cookies['CorrelationId']
    session.headers['RequestIdKey'] = session.cookies['CorrelationId']
    return session

def delete_poll_headers(session):
    del session.headers['X-XSRF-TOKEN']
    del session.headers['CorrelationId']
    del session.headers['RequestIdKey']
    return session

def poll_and_renew_authorization(session):
    poll_success = True
    session = set_poll_headers(session)
    poll = session.get('https://auth.post.borger.dk/web/auth/poll')
    if poll.status_code == 204:
        return session 
    elif poll.status_code == 401:
        poll_success = False        
    if poll_success == False:
        session = delete_poll_headers(session)
        renew = session.get('https://auth.post.borger.dk/web/auth/login?returnurl=https://post.borger.dk')
        if 'https://nemlog-in.mitid.dk/adfs/ls/?SAMLRequest=' in renew.url:
            fobs = session.get('https://idp.fobs.dk/write.aspx')
            soup = BeautifulSoup(renew.text, "html.parser")
            input = soup.find_all('input', {"name":"SAMLResponse"})
            samlresponse = input[0]["value"]
            auth_request = session.post('https://gateway.digitalpost.dk/auth/s9/nemlogin/ssoack', data={'SAMLResponse': samlresponse})
            # Fix for a duplicate cookie issue causing auth to fail. Ensures no duplicates.
            for request in auth_request.history:
                if 'https://gateway.digitalpost.dk/auth/oauth/authorize?client_id=borger-dk-web-post-visningsklient-oidc-prod-id' in request.url:
                    del session.cookies['QueueITAccepted-SDFrts345E-V3_prod01']
                    new_cookies = request.headers['Set-Cookie'].split(';,')
                    for cookie in new_cookies:
                        if 'QueueITAccepted' in cookie:
                            real_cookie = http.cookies.BaseCookie(cookie)
                            for key in real_cookie.keys():
                                if 'expires' in real_cookie[key]:
                                    expiry = real_cookie[key]['expires']
                                    if expiry:
                                        expiry_list = list(expiry)
                                        expiry_list[7] = '-'
                                        expiry_list[11] = '-'
                                        real_cookie[key]['expires'] = ''.join(expiry_list)
                            session.cookies.update(real_cookie)
                            break
                    break        
        with open(cookies_filename, 'wb') as cookie_file:
            pickle.dump(session.cookies, cookie_file)
        return session
    return session        