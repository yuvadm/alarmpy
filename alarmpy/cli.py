import click

from alarm import Alarm
from display import Display


@click.command()
@click.option(
    "--language",
    default="he",
    type=click.Choice(["en", "he", "ar", "ru"]),
    help="Alert language ",
)
@click.option("--delay", default=1, help="Polling delay in seconds")
@click.option(
    "--routine-delay", default=60 * 5, help="Routine message delay in seconds"
)
@click.option("--alarm-id", is_flag=True, help="Print alarm IDs")
@click.option("--repeat-alarms", is_flag=True, help="Do not suppress ongoing alarms")
@click.option("--quiet", is_flag=True, help="Print only active alarms")
def cli(**kwargs):
    _d = Display(**kwargs)
    Alarm(**kwargs).start()


if __name__ == "__main__":
    cli()
