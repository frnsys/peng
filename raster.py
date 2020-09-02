import rasterio
import tempfile
import matplotlib
import rasterio.warp
import rasterio.features
import numpy as np
import matplotlib.pyplot as plt
from rasterio.windows import Window
from rasterio.enums import Resampling
from rasterio.plot import show, reshape_as_image
from pyproj import CRS, Transformer
from PIL import Image

# For X11 forwarding
matplotlib.use('TkAgg')

class GeoTIFF:
    def __init__(self, path):
        self.dataset = rasterio.open(path)
        print('width', self.dataset.width)
        print('height', self.dataset.height)
        print('bounds', self.dataset.bounds)

    @property
    def dataset(self):
        return self._dataset

    @dataset.setter
    def dataset(self, dataset):
        self._dataset = dataset
        self.proj = CRS(dataset.crs.to_string())
        self.transformers = {}

    def _window_for_bounds(self, bounds, from_proj='epsg:4326'):
        """Calculate the correct window based on the specified bounds
        Helpful reference: <https://epsg.io/transform>"""
        lat0, lon0, lat1, lon1 = bounds
        pr0, pc0 = self.point_to_index((lat0, lon0), from_proj=from_proj)
        pr1, pc1 = self.point_to_index((lat1, lon1), from_proj=from_proj)
        w = pc1 - pc0
        h = pr1 - pr0
        return Window(pc0, pr0, w, h)

    def data_for_bounds(self, index, bounds, from_proj):
        """Retrieve data for the specified bounds"""
        window = self._window_for_bounds(bounds, from_proj)
        return self.dataset.read(index, window=window)

    def _apply(self, data, meta):
        # Don't see a way to apply in-place,
        # so mock it by saving to a temp file
        # and then loading that.
        kwargs = self.dataset.meta.copy()
        kwargs.update(meta)
        with tempfile.NamedTemporaryFile(suffix='.tif') as tf:
            with rasterio.open(tf.name, 'w', **kwargs) as dst:
                dst.write(data)
            self.dataset = rasterio.open(tf.name)

    def apply_bounds(self, bounds, from_proj='epsg:4326'):
        """Apply bounds in-place"""
        window = self._window_for_bounds(bounds, from_proj)
        self._apply(self.dataset.read(window=window), {
            'height': window.height,
            'width': window.width,
            'transform': self.dataset.window_transform(window)
        })

    def data_for_scale(self, scale, resampling=Resampling.bilinear):
        """Retrieve data scaled by the specified amount"""
        # Resampling methods: <https://rasterio.readthedocs.io/en/latest/api/rasterio.enums.html#rasterio.enums.Resampling>
        # More details: <https://desktop.arcgis.com/en/arcmap/latest/manage-data/raster-and-images/resample-function.htm>
        data = self.dataset.read(
            out_shape=(
                int(self.dataset.height * scale),
                int(self.dataset.width * scale)
            ),
            resampling=resampling
        )

        transform = self.dataset.transform * self.dataset.transform.scale(
            (self.dataset.width / data.shape[-1]),
            (self.dataset.height / data.shape[-2])
        )
        return data, transform

    def apply_scale(self, scale):
        """Apply scale in-place"""
        data, transform = self.data_for_scale(scale)
        self._apply(data, {
            'height': self.dataset.height * scale,
            'width': self.dataset.width * scale,
            'transform': transform
        })

    def to_features(self):
        """Generate geojson features"""
        # Mask out no data areas
        mask = self.dataset.dataset_mask()

        # Extract feature shapes and values from the array.
        feats = []
        for geom, val in rasterio.features.shapes(
                mask, transform=self.dataset.transform):

            # Transform shapes from the dataset's own coordinate
            # reference system to CRS84 (EPSG:4326).
            geom = rasterio.warp.transform_geom(
                self.dataset.crs, 'EPSG:4326', geom, precision=6)
            feats.append(geom)

        return feats

    def to_image(self, colormap=None):
        data = reshape_as_image(self.dataset.read())

        # Normalize
        mn = data.min(axis=(0, 1), keepdims=True)
        mx = data.max(axis=(0, 1), keepdims=True)
        data = (data - mn)/(mx - mn)

        # Grayscale
        if data.shape[-1] == 1:
            # Use colormap, if specified
            if colormap is not None:
                cm = plt.get_cmap(colormap)
                data = cm(data)

            # Otherwise, just convert to RGB
            else:
                data = np.concatenate((data,)*3, axis=-1)

        # Convert to RGBA
        if data.shape[-1] == 3:
            data = np.dstack((data, np.full(data.shape[:2], 1.)))

        return Image.fromarray((data*255).astype('uint8'), 'RGBA')

    def show(self, cmap='viridis'):
        show(self.dataset, transform=self.dataset.transform, cmap=cmap)

    def point_to_index(self, point, from_proj='epsg:4326'):
        """EPSG:4326 is eqiuvalent to WGS:84.
        `point` is expected to be (lat, lon)"""
        if from_proj not in self.transformers:
            self.transformers[from_proj] = Transformer.from_crs(CRS(from_proj), self.proj)

        x, y = self.transformers[from_proj].transform(*point)
        row, col = self.dataset.index(x, y)
        print('row, col:', row, col)
        return row, col

    def apply_features_mask(self, feats, invert=False):
        """Mask feature shapes
        <https://rasterio.readthedocs.io/en/latest/topics/masking-by-shapefile.html>"""
        shapes = [feat['geometry'] for feat in feats]
        data, transform = rasterio.mask.mask(self.dataset, shapes, invert=invert)
        self._apply(data, {
            'height': data.shape[1],
            'width': data.shape[2],
            'transform': transform
        })
