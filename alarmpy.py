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

    def __init__(self, delay=1, routine_delay=5, alarm_id=False, repeat_alarms=False):
        self.delay = delay
        self.last_routine_delay = routine_delay
        self.alarm_id = alarm_id
        self.repeat_alarms = repeat_alarms

        self.active_alarm = False
        self.last_routine = 0

        self.last = None

    def start(self):
        while True:
            self.fetch()
            sleep(self.delay)

    def fetch(self):
        now = datetime.now()
        ts = now.strftime("%Y-%m-%d %H:%M:%S")

        try:
            res = requests.get(self.URL, headers=self.HEADERS, timeout=1)
        except Exception as e:
            click.secho(f"{ts} ", nl=False)
            click.secho(f"Exception: {e}", fg="yellow")
            return

        if res.content:

            try:
                data = res.json()
                self.active_alarm = True
                alarm_id = data["id"]
                cities = data["data"]

                cities_str = ", ".join(cities)
                if self.repeat_alarms or cities_str != self.last:
                    click.secho(f"{ts} ", nl=False)
                    click.secho(f"{cities_str} ", fg="red", nl=not self.alarm_id)
                    if self.alarm_id:
                        click.secho(f"({alarm_id})")
                    self.last = cities_str
            except:
                click.secho(f"{ts} ", nl=False)
                click.secho(f"Error parsing JSON {res.content}", fg="yellow", bold=True)
        else:
            self.last = None
            if self.active_alarm or (
                time() - self.last_routine > self.last_routine_delay
            ):
                click.secho(f"{ts} ", nl=False)
                click.secho(f"No active alarms", fg="green")
                self.last_routine = time()

            self.active_alarm = False


@click.command()
@click.option("--delay", default=1, help="Polling delay in seconds")
@click.option(
    "--routine-delay", default=60 * 5, help="Routine message delay in seconds"
)
@click.option("--alarm-id", is_flag=True, help="Print alarm ID")
@click.option("--repeat-alarms", is_flag=True, help="Do not suppress ongoing alarms")
def alarm(delay=1, routine_delay=60 * 5, alarm_id=False, repeat_alarms=False):
    Alarm(
        delay=delay,
        routine_delay=routine_delay,
        alarm_id=alarm_id,
        repeat_alarms=repeat_alarms,
    ).start()


if __name__ == "__main__":
    alarm()  # pylint: disable=no-value-for-parameter
