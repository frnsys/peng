function makeMap(id, name, dims, center, zoom) {
  const map = L.map(id, {
    minZoom: 2,
    maxZoom: 7
  });
  // map.scrollWheelZoom.disable();
  const rc = new L.RasterCoords(map, dims);
  map.setView(rc.unproject([dims[0] * center[0], dims[1] * center[1]]), zoom);

  L.tileLayer('tiles/' + name + '/{z}/{x}/{y}.png', {
    noWrap: true,
    attribution: ''
  }).addTo(map);
}

// Example
makeMap('brazil', 'brazil', [10052, 9166], [0.5, 0.5], 3);