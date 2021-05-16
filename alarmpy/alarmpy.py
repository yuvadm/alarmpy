import click
import json
import requests

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
        polling_delay=1,
        routine_delay=60 * 5,
        alarm_id=False,
        repeat_alarms=False,
        quiet=False,
        mqtt_server="",
        mqtt_client_id="alarmPyClient",
        mqtt_port=1883,
        mqtt_topic="",
        mqtt_filter=None,
    ):
        self.language = language
        self.polling_delay = polling_delay
        self.last_routine_delay = routine_delay
        self.alarm_id = alarm_id
        self.repeat_alarms = repeat_alarms
        self.quiet = quiet
        self.mqtt_server = mqtt_server
        self.mqtt_client_id = mqtt_client_id
        self.mqtt_port = mqtt_port
        self.mqtt_topic = mqtt_topic
        self.mqtt_filter = mqtt_filter

        self.current_alarms = []
        self.last_routine_output = 0

        self.session = self.init_session()
        self.labels = self.load_labels()

        self.mqtt = mqtt.Client(self.mqtt_client_id)
        self.filters = None
        if self.mqtt_server != None:
            self.mqtt.connect(self.mqtt_server, self.mqtt_port)
            self.mqtt.loop_start()
            if self.mqtt_filter != None:
                self.filters = self.mqtt_filter.split(";")

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

        data = {} # To avoid warning in KeyError
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
        multiple_areas = len(areas) > 1
        self.output_leading_timestamp(nl=multiple_areas)
        for area, cities in areas.items():
            cities_str = ", ".join(cities)
            leading_tab = "\t" if multiple_areas else ""
            click.secho(f"{leading_tab}{area} ", fg="red", bold=True, nl=False)
            click.secho(f"\t{cities_str} ", fg="red")
        if self.alarm_id:
            click.secho(f"({alarm_id})")

    def notify_alarms(self, cities):
        if self.mqtt_server != None and self.mqtt_topic != None:
            for city in cities:
                if self.filters == None or self.check_filter(city):
                    self.mqtt.publish(self.mqtt_topic, city)

    def check_filter(self, city):
        for filter in self.filters:
            if filter in city:
                return True
        
        return False

    def group_areas_and_localize(self, cities):
        res = defaultdict(list)
        for city in cities:
            try:
                area = self.labels[city][f"areaname_{self.language}"]
                label = self.labels[city][f"label_{self.language}"]
            except KeyError:
                area = ""
                label = city
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
@click.option("--mqtt-server", default=None, help="Hostname / IP of MQTT server (optional)")
@click.option("--mqtt-client-id", default="alarmPyClient", help="MQTT client identifier")
@click.option("--mqtt-port", default=1883, help="Port for MQTT server")
@click.option("--mqtt-topic", default=None, help="Topic on which to send MQTT messages")
@click.option("--mqtt-filter", default=None, help="Payload value to filter before sending as a message (semicolon separated)")
def cli(**kwargs):
    Alarm(**kwargs).start()


if __name__ == "__main__":
    cli()
