import os
import zipfile
import requests
from PIL import Image
from uuid import uuid1


def download(url, outfile):
    """download a file"""
    fname = url.split('/')[-1]
    with requests.get(url, stream=True) as r:
        if r.status_code != 200:
            print(r.json())
            r.raise_for_status()
        with open(outfile, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
                    # f.flush()
    return outfile


def download_ee_image(url, id, impath, working_dir='/tmp', keep_files=False):
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)
    outdir = os.path.join(working_dir, id)

    # Download zip
    zipf = '/tmp/{}.zip'.format(id)

    ok = False
    while not ok:
        download(url, zipf)
        try:
            zfile = zipfile.ZipFile(zipf)
        except zipfile.BadZipFile:
            print('Bad zip (retrying):', zipf, url)
            continue
        zfile.extractall(outdir)
        ok = True

    # Merge RGB images
    chans = [
        os.path.join(outdir, 'download.vis-{}.tif'.format(chan))
        for chan in ['red', 'green', 'blue']
    ]

    rgb = [Image.open(ch) for ch in chans]
    im = Image.merge('RGB', rgb)
    im.save(impath, optimize=False, compress_level=0)

    if not keep_files:
        # Clean up zipfile
        os.remove(zipf)
        for ch in chans:
            os.remove(ch)
    return impath


def get_bounds(polygons):
    xmin, ymin, xmax, ymax = None, None, None, None
    for coords in polygons:
        for x, y in coords:
            if xmin is None or x < xmin:
                xmin = x
            if xmax is None or x > xmax:
                xmax = x
            if ymin is None or y < ymin:
                ymin = y
            if ymax is None or y > ymax:
                ymax = y
    return xmin, ymin, xmax, ymax


def intersects(bbox_a, bbox_b):
    xmin_a, ymin_a, xmax_a, ymax_a = bbox_a
    xmin_b, ymin_b, xmax_b, ymax_b = bbox_b
    return (xmax_a >= xmin_b and xmax_b >= xmin_a) and \
        (ymax_a >= ymin_b and ymax_b >= ymin_a)


def uuid():
    return uuid1().hex