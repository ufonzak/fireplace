import time
import requests
import json
from dataclasses import dataclass
from datetime import datetime
from smbus import SMBus
from typing import Optional
from threading import Condition


TEMPERATURE_HOST = "10.0.0.101:80"


@dataclass
class EnvData:
    temperature: float
    humidity: float
    pressure: float


def get_data():
    try:
        response = requests.get(f"http://{TEMPERATURE_HOST}", timeout=10)
        data = json.loads(response.text)
        return EnvData(temperature=data['temperature'], humidity=data['humidity'], pressure=data['pressure'])
    except Exception as e:
        print("Error getting data", e)
        return None


SET_POINT = 22.5  # C
HYSTERESIS = 0.5  # C
DAY_START = 4  # h
DAY_END = 21  # h
MIN_TIME_ON = 20 # m

DEVICE_BUS = 1
DEVICE_ADDR = 0x10
DEVICE_RELAY = 1

class Fireplace:
    _is_on = None
    _time_on_left = 0
    _time_disabled = 0
    _current: Optional[EnvData] = None
    _fire_now = False
    _condition = Condition()

    def __init__(self):
        self._bus = SMBus(DEVICE_BUS)

    def _set_relay(self, on: bool):
        self._bus.write_byte_data(DEVICE_ADDR, DEVICE_RELAY, 0xFF if not on else 0)

    @property
    def current(self):
        return self._current

    def fire_now(self):
        with self._condition:
            self._fire_now = True
            self._time_disabled = 0
            self._time_on_left = MIN_TIME_ON
            self._condition.notify()

    def disable(self):
        with self._condition:
            self._fire_now = False
            self._time_disabled = 30
            self._time_on_left = 0
            self._condition.notify()

    def loop(self):
        with self._condition:
            while True:
                self.tick()

    def tick(self):
        self._current = get_data()
        if self._current is None:
            self._condition.wait(timeout=30)
            return

        now = datetime.now()
        set_on = False
        if self._fire_now:
            self._fire_now = False
            set_on = True
        elif (now.hour < DAY_START or now.hour >= DAY_END):
            set_on = False
        elif self._time_disabled <= 0:
            set_on = self._current.temperature < SET_POINT + (HYSTERESIS if self._is_on else 0)

        if self._time_on_left > 0:
            self._time_on_left -= 1

        if self._time_disabled > 0:
            self._time_disabled -= 1

        if set_on != self._is_on:
            if set_on:
                self._is_on = set_on
                if self._time_on_left <= 0:
                    self._time_on_left = MIN_TIME_ON
            else:
                if self._time_on_left <= 0:
                    self._is_on = set_on

            if set_on == self._is_on:
                self._set_relay(self._is_on)

        print("t", self._current.temperature, "h", self._current.humidity, "heat", int(self._is_on))
        self._condition.wait(timeout=60)


if __name__ == "__main__":
    Fireplace().loop()
