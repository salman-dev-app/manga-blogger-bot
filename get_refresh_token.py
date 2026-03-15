# get_refresh_token.py (Manual Flow for Termux)

from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES = ['https://www.googleapis.com/auth/blogger', 'https://www.googleapis.com/auth/photoslibrary.appendonly']
CLIENT_SECRETS_FILE = "client_secret_652211411379-2fb5ug8om5qdg0sifih8dfmcd4i31di3.apps.googleusercontent.com.json"

def main():
    
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        SCOPES,
    
        redirect_uri='urn:ietf:wg:oauth:2.0:oob'
    )

    
    auth_url, _ = flow.authorization_url(prompt='consent')

    print('--- Step 1: Authorize your application ---')
    print('Please go to this URL in your browser and authorize the application:')
    print(f'\n{auth_url}\n')

    
    print('--- Step 2: Enter the code ---')
    code = input('After authorization, Google will show you a code. Paste that code here and press Enter:\n> ')

    try:
        
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        print('\n----------------------------------------------')
        print('SUCCESS! Here is your REFRESH TOKEN:')
        print('----------------------------------------------')
        print(creds.refresh_token)
        print('----------------------------------------------')
        print('Please copy this token and save it to your GitHub Secrets.')

    except Exception as e:
        print(f'\nAn error occurred: {e}')

if __name__ == '__main__':
    main()
