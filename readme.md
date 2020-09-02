# peng

![](peng.jpg)

WIP small library for acquiring satellite imagery.

If you don't already have an Earth Engine account, sign up for one: <https://signup.earthengine.google.com/>

```python
import ee
ee.Authenticate()
```

# Generating tiles

Install GDAL for python:

```
pip install GDAL==$(gdal-config --version) --global-option=build_ext --global-option="-I/usr/include/gdal"
```

Tools:

- <https://gdal.org/programs/gdal2tiles.html>
- <https://github.com/commenthol/gdal2tiles-leaflet>

Generate tiles:

```
python gdal2tiles-leaflet/gdal2tiles.py -l -p raster -z 0-7 -w none img/concessions/src/BRA.png tiles/brazil
```

These can be viewed in the browser using `leaflet` and the `rastercoords` plugin (see the `tiles` folder).