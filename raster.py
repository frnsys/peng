import rasterio
import tempfile
import matplotlib
import rasterio.warp
import rasterio.features
from rasterio.windows import Window
from rasterio.enums import Resampling
from pyproj import CRS, Transformer
from rasterio.plot import show, reshape_as_image
from PIL import Image, ImageFont, ImageDraw

# For X11 forwarding
matplotlib.use('TkAgg')


class GeoTIFF:
    def __init__(self, path):
        self.dataset = rasterio.open(path)
        print('width', self.dataset.width)
        print('height', self.dataset.height)
        print('bounds', self.dataset.bounds)

    def _window_for_bounds(self, bounds, from_proj):
        """Calculate the correct window based on the specified bounds
        Helpful reference: <https://epsg.io/transform>"""
        to_proj = CRS(self.dataset.crs.to_string())
        transformer = Transformer.from_crs(from_proj, to_proj)
        lat0, lon0, lat1, lon1 = bounds
        x0, y0 = transformer.transform(lat0, lon0)
        x1, y1 = transformer.transform(lat1, lon1)
        py0, px0 = self.dataset.index(x0, y0)
        py1, px1 = self.dataset.index(x1, y1)
        w = px1 - px0
        h = py1 - py0
        return Window(px0, py0, w, h)

    def data_for_bounds(self, index, bounds, from_proj):
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

    def apply_bounds(self, bounds, from_proj):
        """Apply bounds in-place"""
        window = self._window_for_bounds(bounds, from_proj)
        self._apply(self.dataset.read(window=window), {
            'height': window.height,
            'width': window.width,
            'transform': self.dataset.window_transform(window)
        })

    def data_for_scale(self, scale, resampling=Resampling.bilinear):
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

    def to_image(self):
        data = reshape_as_image(self.dataset)
        return Image.fromarray(data)

    def show(self, cmap='viridis'):
        show(self.dataset, transform=self.dataset.transform, cmap=cmap)


if __name__ == '__main__':
    # equivalent to wgs:84
    from_proj = CRS('epsg:4326')

    # (very) rough bounding box for Addis Ababa
    bounds = (9.089963, 38.653849, 8.822045, 38.898295)

    scale = 2

    # Note: this is for the whole of Ethiopia
    gt = GeoTIFF('data/PopulationDensity2015EJRC/etnaejrcpopd2015.tif')

    gt.apply_bounds(bounds, from_proj)
    gt.apply_scale(scale)

    index = gt.dataset.indexes[0]
    data = gt.dataset.read(index)
    # Convert to population per sqm
    data /= 5000

    # Show data
    gt.show()