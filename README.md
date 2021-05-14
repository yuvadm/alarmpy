# Pikud Ha'oref Alarm Tracking

A simple CLI tool for tracking Pikud Ha'oref alarms.

Polls the unofficial API endpoint every second for incoming alarms. Prints active alarms as they occur. Prints routine messages once every 5 minutes by default.

![example.png](example.png)

## ⚠️ Disclaimer ⚠️

This tool is based on an unofficial API, and cannot be guaranteed to show correct or timely data. **Do not** use it if human life is at stake. **Do not** assume it shows you correct data. **Do not** assume it works properly, or even works at all. Always follow official guidelines and procedures published by [Pikud Ha'oref](https://www.oref.org.il/).

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
  --repeat-alarms          Do not suppress ongoing alarms
  --help                   Show this message and exit.
```

## License

[GPLv3](LICENSE)
