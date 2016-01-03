#/usr/bin/env python

from oauth2client.client import OAuth2WebServerFlow, OAuth2Credentials
import webbrowser
import gspread
import getpass
import keyring

SERVICE_NAME = "aptsnatch"
USER_NAME = "aptsnatch"

def get_credentials():
    credentials_json = keyring.get_password(SERVICE_NAME, USER_NAME)
    if credentials_json:
        credentials = OAuth2Credentials.from_json(credentials_json)
    else:
        flow = OAuth2WebServerFlow(redirect_uri='urn:ietf:wg:oauth:2.0:oob', scope='https://www.googleapis.com/auth/spreadsheets https://spreadsheets.google.com/feeds https://www.googleapis.com/auth/drive', client_id='48126220434-b74n98cga04lrb1kj9jef66ti7iqre9g.apps.googleusercontent.com', client_secret='ar_CTcRWCBlflK3JDoJ4-3ko')
        flow.params['access_type'] = 'offline'
        auth_uri = flow.step1_get_authorize_url()
        webbrowser.open(auth_uri)
        oauth_token = getpass.getpass("Paste oauth token here: ")
        credentials = flow.step2_exchange(oauth_token)
    if not credentials_json:
        save_in_keyring = raw_input("Save in keyring? [Y/n]: ")
        if not save_in_keyring or save_in_keyring.lower() == "y":
            keyring.set_password(SERVICE_NAME, USER_NAME, credentials.to_json())
    return credentials

def clear_credentials():
    keyring.delete_password(SERVICE_NAME, USER_NAME)
