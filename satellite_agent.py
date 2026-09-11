"""
Satellite/NDVI agent: builds direct image URLs from NASA GIBS (Global Imagery
Browse Services) -- a free, no-API-key service showing real MODIS satellite
imagery. "best" in the URL path auto-selects the most recent available date,
so no date parameter is needed.
"""

def get_satellite_urls(lat, lon, box_deg=0.25, size=400):
    bbox = f"{lon - box_deg},{lat - box_deg},{lon + box_deg},{lat + box_deg}"
    base = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"
    common = f"SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&FORMAT=image/png&STYLES=&HEIGHT={size}&WIDTH={size}&SRS=epsg:4326&BBOX={bbox}"

    true_color_url = f"{base}?{common}&LAYERS=MODIS_Terra_CorrectedReflectance_TrueColor"
    ndvi_url = f"{base}?{common}&LAYERS=MODIS_Terra_NDVI_8Day&TRANSPARENT=TRUE"

    return {"true_color_url": true_color_url, "ndvi_url": ndvi_url}


if __name__ == "__main__":
    urls = get_satellite_urls(26.8467, 80.9462)
    print("True color:", urls["true_color_url"])
    print("NDVI:", urls["ndvi_url"])
