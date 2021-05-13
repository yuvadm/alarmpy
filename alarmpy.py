import click
import requests

from datetime import datetime
from time import sleep


class Alarm(object):

    URL = "https://www.oref.org.il/WarningMessages/alert/alerts.json"

    HEADERS = {
        "Referer": "https://www.oref.org.il/11226-he/pakar.aspx",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
    }

    def __init__(self, delay=1):
        self.delay = delay

    def start(self):
        while True:
            self.fetch()
            sleep(self.delay)

    def fetch(self):
        res = requests.get(self.URL, headers=self.HEADERS)
        if res.content:
            try:
                print(datetime.now().isoformat(), res.json())
            except:
                print(datetime.now().isoformat(), res.content)
        else:
            pass


@click.command()
@click.option("--delay", default=1, help="Polling delay in seconds")
def alarm(delay):
    Alarm().start()


if __name__ == "__main__":
    alarm()  # pylint: disable=no-value-for-parameter
