from ..alarmpy import Alarm


def test_parse():
    alarm = Alarm()
    res = b'\xef\xbb\xbf{\r\n  "id": "132949694460000000",\r\n  "cat": "1",\r\n  "title": "\xd7\x99\xd7\xa8\xd7\x99 \xd7\x98\xd7\x99\xd7\x9c\xd7\x99\xd7\x9d \xd7\x95\xd7\xa8\xd7\xa7\xd7\x98\xd7\x95\xd7\xaa",\r\n  "data": [\r\n    "\xd7\xa9\xd7\x93\xd7\xa8\xd7\x95\xd7\xaa, \xd7\x90\xd7\x99\xd7\x91\xd7\x99\xd7\x9d, \xd7\xa0\xd7\x99\xd7\xa8 \xd7\xa2\xd7\x9d",\r\n    "\xd7\x90\xd7\xa8\xd7\x96",\r\n    "\xd7\x9e\xd7\xa4\xd7\x9c\xd7\xa1\xd7\x99\xd7\x9d",\r\n    "\xd7\x9e\xd7\x98\xd7\x95\xd7\x95\xd7\x97 \xd7\xa0\xd7\x99\xd7\xa8 \xd7\xa2\xd7\x9d"\r\n  ],\r\n  "desc": "\xd7\x94\xd7\x99\xd7\x9b\xd7\xa0\xd7\xa1\xd7\x95 \xd7\x9c\xd7\x9e\xd7\xa8\xd7\x97\xd7\x91 \xd7\x94\xd7\x9e\xd7\x95\xd7\x92\xd7\x9f"\r\n}\r\n'
    assert alarm.parse(res) == (
        ["שדרות, איבים, ניר עם", "ארז", "מפלסים", "מטווח ניר עם"],
        "132949694460000000",
    )


def test_empty_parse():
    alarm = Alarm()
    assert alarm.parse(None) == ([], None)
    assert alarm.parse(b"") == ([], None)
