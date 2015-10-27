import re

from livestreamer.plugin import Plugin
from livestreamer.plugin.api import http, validate
from livestreamer.stream import (
    HTTPStream, HLSStream
)

STATUS_ONLINE = 4
STATUS_OFFLINE = 0

_url_re = re.compile("""
    http(s)?://(www\.)?zhanqi.tv
    /(?P<channel>[^/]+)
""", re.VERBOSE)

_json_re = re.compile("window\.oPageConfig\.oRoom\s=\s\{(.+)\};")

_room_schema = validate.Schema(
    validate.all(
        validate.transform(_json_re.search),
        validate.any(None, {
        "status": validate.all(
            validate.text,
            validate.transform(int)
        ),
        "videoId": validate.text
        })
    )
)


class Zhanqi(Plugin):
    @classmethod
    def can_handle_url(self, url):
        return _url_re.match(url)

    def _get_streams(self):
        match = _url_re.match(self.url)
        channel = match.group("channel")

        room = http.get(self.url, schema=_room_schema)
        if not room:
            return

        if room["status"] != STATUS_ONLINE:
            return

        hls_url = "http://dlhls.cdn.zhanqi.tv/zqlive/{room[videoId]}_1024/index.m3u8?Dnion_vsnae={room[videoId]}".format(room=room)
        hls_stream = HLSStream(self.session, hls_url)
        if hls_stream:
            yield "hls", hls_stream

        http_url = "http://wshdl.load.cdn.zhanqi.tv/zqlive/{room[videoId]}.flv?get_url=".format(room=room)
        http_stream = HTTPStream(self.session, http_url)
        if http_stream:
            yield "http", http_stream

__plugin__ = Zhanqi
