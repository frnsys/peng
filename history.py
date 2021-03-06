"""
A very janky way to automate extraction of historical satellite imagery from Google Earth Pro.
This kind of UI automation can be *very* finicky, so be sure to follow the instructions below:

Usage:

1. Open Google Earth Pro and ensure it is anchored to the top-left corner of the screen.
2. Go to Save Image and make sure the map options and resolution are set correctly.
3. Follow through and save an image to the `/tmp` directory, so that it's the default save location. Then turn off the save image mode (by clicking "Save Image" again).
4. Run this script and then click on the Google Earth Pro window.

__You can't interact with your computer while this is running, otherwise things will go wrong!__
"""

import os
from xdo import Xdo
from PIL import Image
from time import sleep
from tqdm import tqdm
import pyscreenshot as ImageGrab

SAVE_IMAGE_MODE = False

xdo = Xdo()
win_id = xdo.select_window_with_click()


def go_to(lat, lng):
    """Go to a lat, lng by entering it into the search field"""
    text = '{},{}'.format(lat, lng)

    # Click on text input
    xdo.move_mouse(150, 125)
    xdo.click_window(win_id, 1)
    xdo.enter_text_window(win_id, text.encode('utf8'))

    sleep(0.5)

    # Click search button
    # move_reulative segfaults for some reason
    # xdo.move_mouse_relative_to_window(win_id, 50, 50)
    xdo.move_mouse(350, 125)
    sleep(0.25)
    xdo.click_window(win_id, 1)

    # Hide yellow pin
    xdo.move_mouse(375, 400)
    xdo.click_window(win_id, 1)
    xdo.move_mouse(375, 450)
    xdo.click_window(win_id, 1)


def clear_search():
    """Clear search field"""
    # Click on text input
    xdo.move_mouse(150, 125)
    xdo.click_window(win_id, 1)
    xdo.send_keysequence_window(win_id, b'ctrl+a')
    xdo.send_keysequence_window(win_id, b'Delete')


def toggle_save_image_mode():
    # There isn't (as far as I can tell)
    # a way to track if the save image mode is active
    # through the interface/Xdo.
    # Try to keep track of it manually, though
    # if the user toggles it manually through the UI
    # then this will be out-of-sync.
    SAVE_IMAGE_MODE = !SAVE_IMAGE_MODE

    # For some reason this doesn't work
    # xdo.send_keysequence_window(win_id, b'Control_L+Alt_L+s')

    # Click "Save Image" icon
    xdo.move_mouse(1250, 50)
    xdo.click_window(win_id, 1)

    sleep(0.25)


def save_image(path):
    # Ensure save image mode is active
    if !SAVE_IMAGE_MODE:
        toggle_save_image_mode()

    filename = os.path.basename(path)

    # Move to "Save Image..."
    xdo.move_mouse(1000, 100)
    xdo.click_window(win_id, 1)
    sleep(2)

    # Click "Save" button to open save dialog
    save_dialog_id = xdo.get_active_window()
    xdo.send_keysequence_window(save_dialog_id, b'ctrl+a')
    xdo.send_keysequence_window(save_dialog_id, b'Delete')
    sleep(1)
    xdo.enter_text_window(save_dialog_id, filename.strip('.jpg').encode('utf8'))
    sleep(1)

    # Manually click "Save" button.
    # Sending the 'Return' key causes libxdo to spam Return
    # for some reason, breaking everything
    xdo.move_mouse(1400, 850)
    sleep(0.5)
    xdo.click_window(save_dialog_id, 1)
    sleep(8)

    # Move to specified location
    os.rename('/tmp/{}'.format(filename), path)

    # Turn off save image mode
    toggle_save_image_mode()


def save_historical(ticks, dir):
    """Save historical images
    - ticks: how many images to save, starting from most recent to oldest"""

    # Historical imagery must already be enabled
    for i in tqdm(range(ticks)):
        # Click back on historical timeline
        # If save image bar is not active, this is the correct y position
        xdo.move_mouse(480, 175)
        # Otherwise, use:
        # xdo.move_mouse(480, 225)
        sleep(0.5)
        xdo.click_window(win_id, 1)
        sleep(3)

        # Save the image
        name = '{}'.format(ticks-i).zfill(4)
        path = os.path.join(dir, '{}.jpg'.format(name))
        save_image(path)

        # Extract the imagery date
        size = xdo.get_window_size(win_id)
        shot = ImageGrab.grab(bbox=(0, 0, size.width, size.height))
        bar_size = (1025, 50)
        shot = shot.crop((size.width-bar_size[0], size.height-bar_size[1], size.width, size.height))
        shot = shot.crop((0, 15, 260, 40))

        # Paste imagery date onto extracted image
        im = Image.open(path)
        im.paste(shot, (im.width-260, im.height-40))
        im.save(path)


if __name__ == '__main__':
    import sys
    try:
        coords = [
                (8.9492814, 38.7928534)
        ]
        for c in coords:
            clear_search()
            go_to(*c)

            # Wait for animation to complete
            sleep(5)

            save_historical(80, '/tmp/testing')
    except Exception as e:
        print(e)
        sys.exit(1)
