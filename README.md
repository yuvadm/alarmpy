# Pikud Ha'oref Alarm Tracking

A simple CLI tool for tracking Pikud Ha'oref alarms.

Polls the unofficial API endpoint every second for incoming alarms. Prints active alarms as they occur. Prints routine messages once every 5 minutes by default.

## Usage

```bash
$ pipenv sync
$ pipenv run alarmpy
```

Advanced flags can be set as described in the usage:

```bash
$ pipenv run alarmpy --help
Usage: alarmpy.py [OPTIONS]

Options:
  --delay INTEGER          Polling delay in seconds
  --routine-delay INTEGER  Routine message delay in seconds
  --alarm-id               Print alarm ID
  --help                   Show this message and exit.
```
