# Check and renew auth on post.borger.dk.
from bs4 import BeautifulSoup
import http.cookies

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
    set_poll_headers(session)
    poll = session.get('https://auth.post.borger.dk/web/auth/poll')
    if poll.status_code == 204 or poll.status_code == 200:
        delete_poll_headers(session)
        return session 
    elif poll.status_code == 401:
        delete_poll_headers(session)
        renew_step_one = session.get('https://auth.post.borger.dk/web/auth/login?returnurl=https://post.borger.dk', allow_redirects=False)
        step_one_redirect_location = renew_step_one.headers['Location']
        renew_step_two = session.get(step_one_redirect_location, allow_redirects=False)
        step_two_redirect_location = renew_step_two.headers['Location']
        # Simple auth without nemlog-in reauthorization
        if 'https://auth.post.borger.dk/signin-oidc' in step_two_redirect_location:
            renew_step_three = session.get(step_two_redirect_location, allow_redirects=False)
            step_three_redirect_location = renew_step_three.headers['Location']
            renew_step_four = session.get(step_three_redirect_location, allow_redirects=False)
        # Complex auth with nemlog-in reauthorization
        elif 'https://login.nemlog-in.dk/adfs/ls/?SAMLRequest=' in step_two_redirect_location:
            renew_step_three = session.get(step_two_redirect_location, allow_redirects=False)
            step_three_redirect_location = renew_step_three.headers['Location']
            renew_step_four = session.get(step_three_redirect_location, allow_redirects=False)
            fobs = session.get('https://idp.fobs.dk/write.aspx')
            soup = BeautifulSoup(renew_step_four.text, "html.parser")
            input = soup.find_all('input', {"name":"SAMLResponse"})
            try:
                samlresponse = input[0]["value"]
            except IndexError:
                print('Error: Unexpected SAMLresponse')
                print(renew_step_four.status_code)
                print(renew_step_four.text)
                print(renew_step_four.headers)
            renew_step_five = session.post('https://gateway.digitalpost.dk/auth/s9/nemlogin/ssoack', data={'SAMLResponse': samlresponse}, allow_redirects=False)
            step_five_redirect_location = renew_step_five.headers['Location']
            renew_step_six = session.get(step_five_redirect_location, allow_redirects=False)
            # Duplicate cookie fix
            del session.cookies['QueueITAccepted-SDFrts345E-V3_prod01']
            new_cookies = renew_step_six.headers['Set-Cookie'].split(';,')
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
            step_six_redirect_location = renew_step_six.headers['Location']
            renew_step_seven = session.get(step_six_redirect_location, allow_redirects=False)
            step_seven_redirect_location = renew_step_seven.headers['Location']
            renew_step_eight = session.get(step_seven_redirect_location, allow_redirects=False)
        else:
            print('Something went wrong renewing authorization at or before step two.')
    else:
        print('Unknown error during poll.')
        print(poll.status_code)
        print(poll.headers)
    return session        