import click
import requests

from datetime import datetime
from time import sleep, time


class Alarm(object):

    URL = "https://www.oref.org.il/WarningMessages/alert/alerts.json"

    HEADERS = {
        "Referer": "https://www.oref.org.il/11226-he/pakar.aspx",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
    }

    def __init__(self, delay=1, alarm_id=False, routine_delay=5):
        self.delay = delay
        self.alarm_id = alarm_id
        self.last_routine_delay = routine_delay

        self.active_alarm = False
        self.last_routine = 0

    def start(self):
        while True:
            self.fetch()
            sleep(self.delay)

    def fetch(self):
        res = requests.get(self.URL, headers=self.HEADERS, timeout=1)
        now = datetime.now()
        ts = now.strftime("%Y-%m-%d %H:%M:%S")

        if res.content:
            click.secho(f"{ts} ", nl=False)
            try:
                data = res.json()
                self.active_alarm = True
                alarm_id = data["id"]
                cities = data["data"]

                click.secho(
                    f"{', '.join(cities)} ", fg="red", bold=True, nl=not self.alarm_id
                )

                if self.alarm_id:
                    click.secho(f"({alarm_id})")
            except:
                click.secho(f"Error parsing JSON {res.content}", fg="red", bold=True)
        else:
            if self.active_alarm or (
                time() - self.last_routine > self.last_routine_delay
            ):
                click.secho(f"{ts} ", nl=False)
                click.secho(f"No active alarms", fg="green")
                self.last_routine = time()

            self.active_alarm = False


@click.command()
@click.option("--delay", default=1, help="Polling delay in seconds")
@click.option("--alarm-id", is_flag=True, help="Print alarm ID")
@click.option(
    "--routine-delay", default=60 * 5, help="Routine message delay in seconds"
)
def alarm(delay, alarm_id, routine_delay):
    Alarm(delay=delay, alarm_id=alarm_id, routine_delay=routine_delay).start()


if __name__ == "__main__":
    alarm()  # pylint: disable=no-value-for-parameter
