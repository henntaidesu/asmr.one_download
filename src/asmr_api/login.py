import requests

def login():

    url = 'https://api.asmr-200.com/api/auth/me'
    data = {
        'name': "makuro2",
        'password': "Gcf001800",
    }
    req = requests.post(url, data=data).json()

    if req['user']['loggedIn']:
        print(req['user']['recommenderUuid'])
        print(req['token'])


