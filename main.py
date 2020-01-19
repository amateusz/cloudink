#!/usr/bin/env python3

from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

import pyowm
import requests
from PIL import Image, ImageDraw, ImageFont

cwd_root = Path(__file__).parent.absolute()

owm = None


# http://api.openweathermap.org/data/2.5/weather?q=warsaw,pl&appid=06056367d0061e003264ced903bb2921

class Align(Enum):
    CENTER = 0
    LEFT = 1
    RIGHT = 2


class Papierek():
    size = (400, 300)
    center = (size[0] // 2, size[1] // 2)

    def __init__(self):
        self.set_bright_theme(True)
        self.canvas = Image.new('P', self.size, self.major_colour)
        self.canvas.putpalette((255, 255, 255, 0, 0, 0, 255, 0, 0) + (0, 0, 0) * 252)
        self.canvas_draw = ImageDraw.Draw(self.canvas)
        self.bg = None
        self.inky_display = self.try_real_hw()
        self.generate_fonts()
        self.coords = self.fetch_coords()

    def set_bg(self, bg_im, bg_bright):
        self.bg = bg_im
        self.set_bright_theme(bg_bright)

    def set_bright_theme(self, switch=True):
        if switch:
            self.major_colour = 0
            self.minor_colour = 1
        else:
            self.major_colour = 1
            self.minor_colour = 0

    def calc_text_pos(self, text_str, font, align=Align.CENTER):
        if align == Align.CENTER:
            w, h = font.getsize(text_str)
            pos = (-w // 2, -h // 2)
        elif align == Align.LEFT:
            w, h = font.getsize(text_str)
            pos = (0, -h // 2)
        elif align == Align.RIGHT:
            w, h = font.getsize(text_str)
            pos = (-w, -h // 2)
        return pos

    @staticmethod
    def fetch_coords():
        coords = None
        try:
            response = requests.get("https://geolocation-db.com/json/")
            coords = (response.json()['latitude'], response.json()['longitude'])
        except pyowm.exceptions.api_call_error.APICallTimeoutError:
            from sys import stderr
            print('Cannot connect to the weather API', file=stderr)
            coords = None
        finally:
            return coords

    def generate_fonts(self, size=None):
        if not size:
            sizes = [15, 20, 60]
            self.fonts = {}
        else:
            sizes = [size]
        for size_n in sizes:
            self.fonts.update({size_n: ImageFont.truetype(str(cwd_root / 'fonts' / 'Lato-Regular.ttf'), size_n)})

    def get_font(self, size, **kwargs):
        if 'bold' in kwargs:
            if kwargs.get('bold') == True:
                font = ImageFont.truetype(str(cwd_root / 'fonts' / 'Lato-Bold.ttf'), size)
                return font

        else:
            try:
                return self.fonts[size]
            except KeyError:
                self.generate_fonts(size)
                return self.fonts[size]

    def update_canvas(self):
        time_now = datetime.now()
        time_str = time_now.strftime("%_H:%M")

        self.clear_working_canvas()

        if not self.coords:
            self.coords = self.fetch_coords()

        try:
            if not self.coords:
                raise pyowm.exceptions.api_call_error.APICallTimeoutError('dane pogodowe z internetu błąd')
            observation = owm.weather_at_coords(*self.coords)
            last_updated = datetime.fromtimestamp(observation.get_reception_time())
            weather = observation.get_weather()
            weather_measuremnt = datetime.fromtimestamp(weather.get_reference_time())

            # sections to blit
            sunrise_dt = datetime.fromtimestamp(weather.get_sunrise_time())
            sunset_dt = datetime.fromtimestamp(weather.get_sunset_time())

            sunrise_str = None
            sunset_str = None

            # determine whether ew are after past 0:00
            if time_now < sunrise_dt:
                # before sunrise
                if not self.bg:
                    self.set_bright_theme(False)

                sunrise_str = f'Słońce wzejdzie o {sunrise_dt.strftime("%-H:%M")}'
                diff = (sunset_dt - sunrise_dt).seconds / 60 / 60
                diff = int(round(diff, 0))
                sunset_str = f'dzień potrwa {str(diff) + " " if diff > 1 else ""}godzin{self.godziny(diff)}'
            elif time_now < sunset_dt:
                # mid day
                self.set_bright_theme(True)

                if sunset_dt - time_now > timedelta(hours=1):
                    diff = (sunset_dt - time_now).seconds / 60 / 60
                    diff = round(diff, 0)
                    sunset_str = f'Słońce zajdzie za {str(diff) + " " if diff > 1 else ""}godzin{self.godziny(diff)}'
                else:
                    diff = (sunset_dt - time_now).seconds / 60
                    diff = round(diff, 0)
                    sunset_str = f'Słońce zajdzie za {str(diff) + " " if diff > 1 else ""}minut{self.godziny(diff)}'
            else:
                # evening
                if not self.bg:
                    self.set_bright_theme(False)

                if time_now - sunset_dt > timedelta(hours=1):
                    diff = (time_now - sunset_dt).seconds / 60 / 60
                    diff = int(round(diff, 0))
                    sunset_str = f'Słońce zaszło {str(diff) + " " if diff > 1 else ""}godzin{self.godziny(diff)} temu'
                else:
                    diff = (time_now - sunset_dt).seconds / 60
                    diff = int(round(diff, 0))
                    sunset_str = f'Słońce zaszło {str(diff) + " " if diff > 1 else ""}minut{self.godziny(diff)} temu'

            # clear
            self.clear_working_canvas()

            if sunrise_str:
                self.canvas_draw.text(self.tuple_add(
                    self.calc_text_pos(sunrise_str, self.get_font(17, bold=True), Align.LEFT),
                    (0 + 15, 181 + 100)
                )
                    , sunrise_str,
                    font=self.get_font(17, bold=True),
                    fill=self.minor_colour)
            if sunset_str:
                self.canvas_draw.text(self.tuple_add(
                    self.calc_text_pos(sunset_str, self.get_font(17, bold=True), Align.RIGHT),
                    (self.size[0] - 15, 181 + 100)
                )
                    , sunset_str,
                    font=self.get_font(17, bold=True),
                    fill=self.minor_colour)

            detailed_status = weather.get_detailed_status()
            detailed_status = detailed_status.split(' ')
            detailed_status.append(detailed_status.pop(0))
            detailed_status = ' '.join(detailed_status)
            detailed_status = detailed_status.replace('zachmurzenie', 'zachmurkowanie')
            detailed_status = detailed_status.replace('pochmurno', 'pochmurko')
            self.canvas_draw.text(self.tuple_add(
                self.calc_text_pos(detailed_status, self.get_font(18, bold=True)),
                self.center
            )
                , detailed_status,
                font=self.get_font(18, bold=True),
                fill=self.minor_colour)

            temperature = f'{weather.get_temperature(unit="celsius")["temp"]}'
            temperature = str(round(float(temperature), 1))
            temperature = temperature.replace('.', ',')
            temperature += '°C'
            self.canvas_draw.text(self.tuple_add(
                self.calc_text_pos(temperature, self.get_font(29)),
                (self.center[0], 180)
            )
                , temperature,
                font=self.get_font(29),
                fill=self.minor_colour)

            rel_humidity = weather.get_humidity()
            h_desc = None
            if rel_humidity < 20:
                h_desc = 'całkiem suche powietrze'
            elif rel_humidity < 30:
                h_desc = 'coś tam wilgoć'
            elif rel_humidity < 40:
                h_desc = 'nawet wilgoć'
            elif rel_humidity < 55:
                h_desc = 'idealnie wilogotno'
            elif rel_humidity < 65:
                h_desc = 'dosyć wilgotno'
            elif rel_humidity < 75:
                h_desc = 'bardziej wilgotno'
            elif rel_humidity < 85:
                h_desc = 'wilgotno wilgotno'
            elif rel_humidity < 92:
                h_desc = 'nie wilogtno, a mokro'
            else:
                h_desc = 'bardzo wilgotne powietrze'

            rel_humidity_str = f'{h_desc} ({str(rel_humidity)}%)'
            self.canvas_draw.text(self.tuple_add(
                self.calc_text_pos(rel_humidity_str, self.get_font(19)),
                (self.center[0], self.center[1] + 65)
            )
                , rel_humidity_str,
                font=self.get_font(19),
                fill=self.minor_colour)

            # response = requests.get(weather.get_weather_icon_url())
            # weather_icon = Image.open(BytesIO(response.content))
            # self.canvas.paste(weather_icon, (50, 50))
        except pyowm.exceptions.api_call_error.APICallTimeoutError as e:
            self.clear_working_canvas()

            from sys import stderr
            print(e._message, file=stderr)
            self.canvas_draw.text(self.tuple_add(
                self.calc_text_pos(e._message, font=self.get_font(19, bold=True)),
                (self.center[0], self.center[1])
            )
                , e._message, font=self.get_font(19, bold=True),
                fill=self.minor_colour)

        except:
            self.clear_working_canvas()
            raise

        finally:
            self.canvas_draw.text(self.tuple_add(
                self.calc_text_pos(time_str, self.fonts[60]),
                (self.center[0], self.center[1] - 52)
            )
                , time_str, font=self.fonts[60],
                fill=self.minor_colour)

    def godziny(self, num):
        if num <= 20 and num >= 10:
            return ''
        elif num % 10 == 1:
            return 'ę'
        elif num % 10 in (2, 3, 4):
            return 'y'
        else:
            return ''

    def show(self):
        if self.inky_display:
            self.inky_display.set_image(self.canvas)  # .rotate(180))
            self.inky_display.show(busy_wait=True)
        else:
            self.canvas.putpalette((190, 190, 190, 25, 25, 25, 150, 20, 60) + (0, 0, 0) * 252)
            self.canvas.show(title=__class__.__name__)

    @staticmethod
    def try_real_hw():
        try:
            from inky import InkyWHAT
            inky_display = InkyWHAT('red')
            inky_display.set_border(inky_display.WHITE)
            return inky_display
        except ImportError:
            return None

    @staticmethod
    def tuple_add(tup1, tup2):
        ret = []
        for i, el in enumerate(tup1):
            ret.append(tup1[i] + tup2[i])
        return tuple(ret)

    def clear_working_canvas(self):
        if self.bg:
            self.canvas = self.bg.copy()
            self.canvas_draw = ImageDraw.Draw(self.canvas)
        else:
            self.canvas_draw.rectangle((0, 0, *self.size), self.major_colour)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--image', '-i', type=str, required=False, help="Input image to be displayed as background")
    parser.add_argument('--apikey', '-a', type=str, required=True, help='OpenWeatherMap API key')
    parser.add_argument('--oneshot', '-1', type=bool, required=False, help='to loop or not')
    args = parser.parse_args()

    owm_apikey = args.apikey
    owm = pyowm.OWM(API_key=owm_apikey, language='pl')

    papierek = Papierek()

    if args.image:
        # oh, there is a image.
        # threshold it and then:
        # - if it is dark, then make it even darker
        # - if it is bright, make it brighter
        bg = Image.open(cwd_root / args.image)

        from prepare_brightness import threshold, get_modified

        if_brighter = threshold(bg)
        bg_1_stage = get_modified(bg, if_brighter)

        # transform to eink colourspace
        import prepare_colourspace

        bg_2_stage = prepare_colourspace.prepare(bg_1_stage)
        papierek.set_bg(bg_2_stage, if_brighter)

    from time import sleep

    while True:
        papierek.update_canvas()
        if not datetime.now().minute%2:
            papierek.show()
        sleep(1)
        target_time = datetime.now()
        target_time = target_time.replace(minute=(target_time.minute + 1) % 59, second=0)
        to_sleep = target_time - datetime.now()
        if args.oneshot:
            exit(0)
        sleep(to_sleep.seconds)
        # wait until full minute
        while datetime.now().second != 0:
            pass
