import click
import json
import os
import requests

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from time import sleep, time


class Alarm:

    URL = "https://www.oref.org.il/WarningMessages/alert/alerts.json"

    HEADERS = {
        "Referer": "https://www.oref.org.il/11226-he/pakar.aspx",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
    }

    def __init__(
        self,
        language="he",
        polling_delay=1,
        routine_delay=60 * 5,
        alarm_id=False,
        repeat_alarms=False,
        quiet=False,
        desktop_notifications=False,
    ):
        self.language = language
        self.polling_delay = polling_delay
        self.last_routine_delay = routine_delay
        self.alarm_id = alarm_id
        self.repeat_alarms = repeat_alarms
        self.quiet = quiet

        if desktop_notifications and not os.path.exists("/usr/bin/osascript"):
            self.output_error(
                "Desktop notifications are currently only available for MacOS"
            )
            desktop_notifications = False
        self.desktop_notifications = desktop_notifications

        self.current_alarms = []
        self.last_routine_output = 0

        self.session = self.init_session()
        self.labels = self.load_labels()

    def init_session(self):
        return requests.Session()

    def load_labels(self):
        DATA_DIR = Path(__file__).parent / "data"
        with open(DATA_DIR / "labels.json", "r") as f:
            return json.load(f)

    def start(self):
        while True:
            try:
                cities, alarm_id = self.fetch()
                self.update(cities, alarm_id)
            except Exception as e:  # pylint: disable=broad-except
                self.output_error(f"Exception: {e}")
            finally:
                sleep(self.polling_delay)

    def fetch(self):
        try:
            res = self.session.get(self.URL, headers=self.HEADERS, timeout=1)
            if not res.ok and "Access Denied" in res.text:
                self.output_error(
                    "API endpoint has denied access. This might be due to geolocation limitations, please try running from an Israeli-based IP or proxy."
                )
                exit(1)
        except requests.Timeout as e:
            raise Exception("HTTP request timed out") from e

        if not res.content:
            # empty content means no alarms
            return [], None

        try:
            data = res.json()
            alarm_id = data["id"]
            cities = data["data"]
            return cities, alarm_id
        except ValueError as ve:
            raise Exception(f"Error parsing JSON: {res.content}") from ve
        except KeyError as ke:
            raise Exception(f"Missing keys in JSON data: {data}") from ke

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

    def output_leading_timestamp(self, nl=False):
        now = datetime.now()
        ts = now.strftime("%Y-%m-%d %H:%M:%S")
        click.secho(f"{ts} ", nl=nl)

    def output_error(self, err):
        if not self.quiet:
            self.output_leading_timestamp()
            click.secho(err, fg="yellow")

    def output_routine(self):
        if not self.quiet:
            self.output_leading_timestamp()
            click.secho("No active alarms", fg="green")

    def output_alarms(self, cities, alarm_id):
        areas = self.group_areas_and_localize(cities)
        self.output_leading_timestamp(nl=True)
        for area, cities in areas.items():
            cities_str = ", ".join(cities)
            click.secho(f"\t{area:<20} ", fg="red", bold=True, nl=False)
            click.secho(f"\t{cities_str} ", fg="red")
            if self.desktop_notifications:
                os.system(
                    f'/usr/bin/osascript -e \'display notification "{cities_str}" with title "Alarms at {area}"\''
                )
        if self.alarm_id:
            click.secho(f"({alarm_id})")

    def group_areas_and_localize(self, cities):
        res = defaultdict(list)
        for city in cities:
            labels = self.labels.get(city, {})
            area = labels.get(f"areaname_{self.language}", "")
            label = labels.get(f"label_{self.language}", city)
            res[area].append(label)
        return res

    def localize_cities(self, cities):
        localized_cities = [
            self.labels.get(city, {}).get(f"label_{self.language}", city)
            for city in cities
        ]
        return ", ".join(localized_cities)


@click.command()
@click.option(
    "--language",
    default="he",
    type=click.Choice(["en", "he", "ar", "ru"]),
    help="Alert language",
)
@click.option("--polling-delay", default=1, help="Polling delay in seconds")
@click.option(
    "--routine-delay", default=60 * 5, help="Routine message delay in seconds"
)
@click.option("--alarm-id", is_flag=True, help="Print alarm IDs")
@click.option("--repeat-alarms", is_flag=True, help="Do not suppress ongoing alarms")
@click.option("--quiet", is_flag=True, help="Print only active alarms")
@click.option(
    "--desktop-notifications",
    is_flag=True,
    help="Create push notifications on your desktop notification center (currently only in Mac OS)",
)
def cli(**kwargs):
    Alarm(**kwargs).start()


if __name__ == "__main__":
    cli()
