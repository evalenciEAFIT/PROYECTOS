window.spatialMaps = {
    styleHandle: function (feature) {
        return {
            fillColor: feature.properties.fillColor,
            weight: 1,
            opacity: 1,
            color: 'white',
            dashArray: '',
            fillOpacity: 0.7
        };
    },
    onEachFeatureHandle: function (feature, layer) {
        if (feature.properties && feature.properties.tooltip) {
            layer.bindTooltip(feature.properties.tooltip, { sticky: true });
        }
    }
};
