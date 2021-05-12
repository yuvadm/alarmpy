from datetime import datetime
from time import sleep

import requests

HEADERS = {
    'Referer': 'https://www.oref.org.il/11226-he/pakar.aspx',
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
}

URL = 'https://www.oref.org.il/WarningMessages/alert/alerts.json'

def fetch():
    res = requests.get(URL, headers=HEADERS)
    if res.content:
        try:
            print(datetime.now().isoformat(), res.json())
        except:
            print(datetime.now().isoformat(), res.content)
    else:
        # print("good")
        pass


if __name__ == "__main__":
    while True:
        sleep(1)
        fetch()
