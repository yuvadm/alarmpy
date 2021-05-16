# Pikud Ha'oref Alarm Tracking

![https://github.com/yuvadm/alarmpy/actions/workflows/build.yml](https://github.com/yuvadm/alarmpy/workflows/Build/badge.svg)
![https://pypi.org/project/alarmpy/](https://img.shields.io/pypi/v/alarmpy)

A simple CLI tool for tracking Pikud Ha'oref alarms.

Polls the unofficial API endpoint every second for incoming alarms. Prints active alarms as they occur. Prints routine messages once every 5 minutes by default.

![example.png](example.png)

## ⚠️ Disclaimer ⚠️

This tool is based on an unofficial API, and cannot be guaranteed to show correct or timely data. **Do not** use it if human life is at stake. **Do not** assume it shows you correct data. **Do not** assume it works properly, or even works at all. Always follow official guidelines and procedures published by [Pikud Ha'oref](https://www.oref.org.il/).

Further fine-print covering the terms of use of this tool can be found in the [GPLv3 license](LICENSE) file.

## Install

### Pip

The easiest way to install is from PyPI with `pip`:

```bash
$ pip install alarmpy
```

You can then run the `alarmpy` executable directly:

```bash
$ alarmpy --help
```

### Pipenv

For development usage it's recommended to clone the git repo and use `pipenv`:

```bash
$ git clone https://github.com/yuvadm/alarmpy
$ cd alarmpy
$ pipenv sync -d
$ pipenv run alarmpy
```

## Usage

Advanced flags can be set as described in the usage:

```bash
$ pipenv run alarmpy --help
Usage: alarmpy.py [OPTIONS]

Options:
  --language [en|he|ar|ru]  Alert language
  --polling-delay INTEGER   Polling delay in seconds
  --routine-delay INTEGER   Routine message delay in seconds
  --alarm-id                Print alarm IDs
  --repeat-alarms           Do not suppress ongoing alarms
  --quiet                   Print only active alarms
  --help                    Show this message and exit.
```

## License

[GPLv3](LICENSE)
