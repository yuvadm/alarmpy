import click
import requests

from datetime import datetime
from requests.exceptions import ReadTimeout
from time import sleep, time


class Alarm(object):

    URL = "https://www.oref.org.il/WarningMessages/alert/alerts.json"

    HEADERS = {
        "Referer": "https://www.oref.org.il/11226-he/pakar.aspx",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
    }

    def __init__(
        self, delay=1, routine_delay=60 * 5, alarm_id=False, repeat_alarms=False
    ):
        self.delay = delay
        self.last_routine_delay = routine_delay
        self.alarm_id = alarm_id
        self.repeat_alarms = repeat_alarms

        self.current_alarms = []
        self.last_routine_output = 0

    def start(self):
        while True:
            try:
                cities, alarm_id = self.fetch()
                self.update(cities, alarm_id)
            except Exception as e:
                self.output_error(f"Exception: {e}")
            finally:
                sleep(self.delay)

    def fetch(self):
        try:
            res = requests.get(self.URL, headers=self.HEADERS, timeout=1)
        except ReadTimeout:
            raise Exception("HTTP request timed out")

        if not res.content:
            # empty content means no alarms
            return [], None

        try:
            data = res.json()
            alarm_id = data["id"]
            cities = data["data"]
            return cities, alarm_id
        except ValueError:
            raise Exception(f"Error parsing JSON: {res.content}")
        except KeyError:
            raise Exception(f"Missing keys in JSON data: {data}")

    def update(self, cities, alarm_id):
        if cities:
            self.update_alarm(cities, alarm_id)
        else:
            self.update_routine()

    def update_alarm(self, cities, alarm_id):
        if self.repeat_alarms or set(cities) != set(self.current_alarms):
            self.output_alarms(cities, alarm_id)
        self.current_alarms = cities

    def update_routine(self):
        now = time()
        if (
            self.current_alarms
            or now - self.last_routine_output > self.last_routine_delay
        ):
            self.output_routine()
            self.last_routine_output = now
        self.current_alarms = []

    def output_leading_timestamp(self):
        now = datetime.now()
        ts = now.strftime("%Y-%m-%d %H:%M:%S")
        click.secho(f"{ts} ", nl=False)

    def output_error(self, err):
        self.output_leading_timestamp()
        click.secho(err, fg="yellow", bold=True)

    def output_routine(self):
        self.output_leading_timestamp()
        click.secho(f"No active alarms", fg="green")

    def output_alarms(self, cities, alarm_id):
        self.output_leading_timestamp()
        cities_str = ", ".join(cities)
        click.secho(f"{cities_str} ", fg="red", nl=not self.alarm_id)
        if self.alarm_id:
            click.secho(f"({alarm_id})")


@click.command()
@click.option("--delay", default=1, help="Polling delay in seconds")
@click.option(
    "--routine-delay", default=60 * 5, help="Routine message delay in seconds"
)
@click.option("--alarm-id", is_flag=True, help="Print alarm IDs")
@click.option("--repeat-alarms", is_flag=True, help="Do not suppress ongoing alarms")
def alarm(**kwargs):
    Alarm(**kwargs).start()


if __name__ == "__main__":
    alarm()
