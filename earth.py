"""
From: <https://www.gearthblog.com/blog/archives/2017/04/fun-stuff-new-google-earth-url.html>

https://earth.google.com/web/@48.858,2.294,146.726a,666.616d,35y,0h,45t,0r/data=KAI

What we have identified so far:
The first two numbers are latitude and longitude. The next numbers end with a single letter and are as follows:
a: altitude of the location you are viewing.
d: distance of your eye from the point being viewed.
y: the field of view.
h: height exaggeration. [ Update: h: is actually ‘heading’. Thank you to GEB reader Tyler for the correction (see comments)]
t: the ’tilt’ or the angle you are viewing at with 0 being straight down, 90 being horizontal and >90 looking up. You can even go past 180 for some interesting views (see links below).
r: the rotation of the view.

The last section starting with /data= can include a long string of characters relating to any information windows you have open, or it may simply have ‘KAI’ which means ‘rotate clockwise around the point being viewed’. If anyone finds out how to rotate counter clockwise, please let us know in the comments.

---

Usage guidelines:

- <https://www.google.com/permissions/geoguidelines/>
- <https://www.google.com/permissions/geoguidelines/attr-guide/>

---

Usage:
1. You should first log in to <https://earth.google.com>, then export `cookies.txt`, e.g. using the `cookies.txt` Chrome extension.
2. Then:

    # Sometimes this doesn't work with the virtual display.
    earth = EarthWeb('path/to/cookies.txt', virtual_display=False)
    earth.screenshot({'lat': 40.7188, 'lng': -73.8052}, '/tmp/shot.png')
    earth.close()

Note on cookies: it seems many cookie prefixed with '__' don't load correctly, so I deleted them from cookies.txt.
"""

from time import sleep
from browser import Browser

URL_TMPL = 'https://earth.google.com/web/@{lat},{lng},2219.58838331a,1350.77250487d,35y,124.67647195h,0t,0r/data=CigiJgokCcwv6r_SvDVAEcov6r_SvDXAGdVXxIMUsEdAIcVzI_96RUzA'

class EarthWeb:
    def __init__(self, cookies_path, virtual_display=True, sleep=10):
        # Need to load the cookies
        self.browser = Browser(virtual_display=virtual_display)
        self.browser.visit('https://google.com')
        self.browser.load_cookies(cookies_path)

        # How long to pause between actions
        self.sleep = sleep

    def screenshot(self, point, fname):
        url = URL_TMPL.format(**point)
        self.browser.visit(url)
        sleep(self.sleep)

        # Set to clean view
        self.browser.execute_script('''
            document.querySelector('earth-app').shadowRoot.querySelector('earth-toolbar').shadowRoot.querySelector('#mapStyle').click()
            document.querySelector('earth-app').shadowRoot.querySelector('earth-drawer').shadowRoot.querySelector('#mapstyle').shadowRoot.querySelector('aside earth-radio-card').click()
            document.querySelector('earth-app').shadowRoot.querySelector('earth-drawer').shadowRoot.querySelector('earth-map-styles-view').shadowRoot.querySelector('#backButton').click()
        ''')

        sleep(self.sleep)

        # Hide toolbar UI
        self.browser.execute_script('''
            document.querySelector('earth-app').shadowRoot.querySelector('#toolbar').style.display = 'none';
            document.querySelector('earth-app').shadowRoot.querySelector('#earthNavigationElements').style.display = 'none';
            document.querySelector('earth-app').shadowRoot.querySelector('earth-drawing-tools').style.display = 'none';
            document.querySelector('earth-app').shadowRoot.querySelector('earth-view-status').style.display = 'none'
        ''')

        self.browser.screenshot(fname)

    def close(self):
        self.browser.quit()