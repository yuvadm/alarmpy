import click
import json
import os
import requests
import random

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from time import sleep, time

try:
    import paho.mqtt.client as mqtt
except ImportError:
    pass


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
        highlight=None,
        reverse=False,
        polling_delay=1,
        routine_delay=60 * 5,
        alarm_id=False,
        repeat_alarms=False,
        quiet=False,
        desktop_notifications=False,
        mqtt_server="",
        mqtt_client_id="alarmPyClient",
        mqtt_port=1883,
        mqtt_topic="",
        mqtt_filter=None,
        **_kwargs,
    ):
        self.language = language
        self.highlight = highlight
        self.reverse = reverse
        self.polling_delay = polling_delay
        self.last_routine_delay = routine_delay
        self.alarm_id = alarm_id
        self.repeat_alarms = repeat_alarms
        self.quiet = quiet
        self.desktop_notifications = desktop_notifications

        self.mqtt_server = mqtt_server
        self.mqtt_client_id = mqtt_client_id
        self.mqtt_port = mqtt_port
        self.mqtt_topic = mqtt_topic
        self.mqtt_filter = mqtt_filter

        self.current_alarms = []
        self.last_routine_output = 0

        self.session = self.init_session()
        self.labels = self.load_labels()

        self.init_desktop_notifications()
        self.init_mqtt()

    def init_session(self):
        return requests.Session()

    def init_desktop_notifications(self):
        if self.desktop_notifications:
            if os.path.exists("/usr/bin/notify-send"):
                self.desktop_notifications = "linux"
            elif os.path.exists("/usr/bin/osascript"):
                self.desktop_notifications = "osx"
            else:
                self.output_error(
                    "Desktop notifications are currently only available for Linux and MacOS"
                )
                self.desktop_notifications = False

    def init_mqtt(self):
        try:
            self.mqtt = mqtt.Client(self.mqtt_client_id)
        except NameError:
            self.mqtt = None

        self.filters = None
        if self.mqtt_server and self.mqtt:
            if not self.mqtt:
                self.output_error(
                    "MQTT support cannot be instantiated without the paho-mqtt library installed"
                )
            self.mqtt.connect(self.mqtt_server, self.mqtt_port)
            self.mqtt.loop_start()
            if self.mqtt_filter:
                self.filters = self.mqtt_filter.lower().split(";")

    def load_labels(self):
        DATA_DIR = Path(__file__).parent / "data"
        with open(DATA_DIR / "labels.json", "r", encoding="utf-8") as f:
            return json.load(f)

    def start(self):
        while True:
            try:
                res = self.fetch()
                cities, alarm_id = self.parse(res)
                self.update(cities, alarm_id)
            except Exception as e:  # pylint: disable=broad-except
                self.output_error(f"Exception: {e}")
            finally:
                sleep(self.polling_delay)

    def fetch(self):
        try:
            res = self.session.get(self.URL, headers=self.HEADERS, timeout=1)
            if not res.ok:
                if "Access Denied" in res.text:
                    self.output_error(
                        "API endpoint has denied access. This might be due to geolocation limitations, please try running from an Israeli-based IP or proxy."
                    )
                    exit(1)
                else:
                    raise Exception("HTTP request has failed")
            return res.content
        except requests.Timeout as e:
            raise Exception("HTTP request timed out") from e

    def parse(self, res):
        if not res:
            # empty content means no alarms
            return [], None

        if res == b"\xef\xbb\xbf\r\n":
            # some weird binary content that also means no alarms
            return [], None

        data = {}  # To avoid warning in KeyError
        try:
            data = json.loads(res[3:-2])  # strip leading and trailing bytes
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
            self.notify_alarms(cities)
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
        for area, cities in sorted(areas.items()):
            bg = "yellow" if self.highlight and self.highlight in area else None
            click.secho(f"\t{area:<20} ", fg="red", bg=bg, bold=True, nl=False)
            click.secho("\t", nl=False)
            for i, city in enumerate(cities):
                bg = "yellow" if self.highlight and self.highlight in city else None
                click.secho(f"{city}", fg="red", bg=bg, nl=False)
                suffix = ", " if i < len(cities) - 1 else ""
                click.secho(f"{suffix}", fg="red", nl=False)
            click.secho("")
            if self.desktop_notifications:
                areas_str = "\U0001f6a8" + ", ".join(areas.keys())
                if self.desktop_notifications == "osx":
                    os.system(
                        f'/usr/bin/osascript -e \'display notification "{areas_str}" with title "Alarmpy"\''
                    )
                else:
                    os.system(f'/usr/bin/notify-send "{areas_str}"')
        if self.alarm_id:
            click.secho(f"({alarm_id})")

    def notify_alarms(self, cities):
        if self.mqtt_server and self.mqtt_topic:
            for city in cities:
                labels = self.labels.get(city, {})
                area = labels.get(f"areaname_{self.language}", "")
                label = labels.get(f"label_{self.language}", city)
                if self.filters is None or self.check_filter(label, area):
                    self.mqtt.publish(self.mqtt_topic, label)

    def check_filter(self, city, area):
        for flt in self.filters:
            if flt in city.lower() or flt in area.lower():
                return True
        return False

    def group_areas_and_localize(self, cities):
        res = defaultdict(list)
        for city in cities:
            labels = self.labels.get(city, {})
            area = labels.get(f"areaname_{self.language}", "")
            label = labels.get(f"label_{self.language}", city)
            if self.reverse:
                area = area[::-1]
                label = label[::-1]
            res[area].append(label)
        return res

    def output_test(self):
        self.output_error("Output test started...")
        self.output_routine()
        alarms = random.sample(list(self.labels.keys()), 8)
        self.output_alarms(alarms, 9999)
        self.output_routine()
        self.highlight = "ה" if self.language == "he" else "s"
        alarms = random.sample(list(self.labels.keys()), 10)
        self.output_alarms(alarms, 9999)
        self.output_routine()
        self.output_routine()
        self.output_error("Output test complete, exiting.")


@click.command()
@click.option(
    "--language",
    default="he",
    type=click.Choice(["en", "he", "ar", "ru"]),
    help="Alert language",
)
@click.option(
    "--highlight",
    help="String to search for and highlight in case of alarm",
)
@click.option(
    "--reverse",
    is_flag=True,
    help="Reverse Hebrew/Arabic output for terminals with RTL bugs",
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
@click.option(
    "--mqtt-server", default=None, help="Hostname / IP of MQTT server (optional)"
)
@click.option(
    "--mqtt-client-id", default="alarmPyClient", help="MQTT client identifier"
)
@click.option("--mqtt-port", default=1883, help="Port for MQTT server")
@click.option("--mqtt-topic", default=None, help="Topic on which to send MQTT messages")
@click.option(
    "--mqtt-filter",
    default=None,
    help="Payload value to filter before sending as a message (semicolon separated)",
)
@click.option(
    "--output-test",
    is_flag=True,
    help="Print a debug output and exit",
)
def cli(**kwargs):
    alarm = Alarm(**kwargs)
    if kwargs["output_test"]:
        alarm.output_test()
    else:
        alarm.start()


if __name__ == "__main__":
    cli()
