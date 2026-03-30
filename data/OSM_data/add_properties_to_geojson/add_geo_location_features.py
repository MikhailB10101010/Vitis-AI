from pathlib import Path
import geopandas as gpd


def load_geojson(filepath: Path) -> gpd.GeoDataFrame:
    """Загрузка исходного geojson"""
    gdf = gpd.read_file(filepath)
    return gdf


def load_layers(gpkg_path: Path):
    """Загрузка слоев Natural Earth"""

    continents = gpd.read_file(gpkg_path, layer="ne_110m_admin_0_countries")[["CONTINENT", "geometry"]]
    countries = gpd.read_file(gpkg_path, layer="ne_10m_admin_0_countries")[["NAME", "geometry"]]
    cities = gpd.read_file(gpkg_path, layer="ne_10m_populated_places")[["NAME", "geometry"]]

    continents = continents.rename(columns={"CONTINENT": "continent"})
    countries = countries.rename(columns={"NAME": "country"})
    cities = cities.rename(columns={"NAME": "city"})

    return continents, countries, cities


def ensure_crs(gdf: gpd.GeoDataFrame, crs="EPSG:4326") -> gpd.GeoDataFrame:
    """Приведение к одной системе координат"""
    if gdf.crs != crs:
        gdf = gdf.to_crs(crs)
    return gdf


def compute_centroids(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Создаем центроиды для spatial join"""
    gdf = gdf.copy()
    gdf["centroid"] = gdf.geometry.centroid
    return gdf.set_geometry("centroid")


def spatial_join_points(points_gdf, polygons_gdf, column_name):
    """Универсальный spatial join"""
    joined = gpd.sjoin(points_gdf, polygons_gdf, how="left", predicate="within")
    return joined[[column_name]]


def enrich_with_location(vineyards_gdf, continents, countries, cities):
    """Основное обогащение"""

    # центроиды
    centroids = compute_centroids(vineyards_gdf)

    # join по континенту
    continent_join = spatial_join_points(centroids, continents, "continent")

    # join по стране
    country_join = spatial_join_points(centroids, countries, "country")

    # ближайший город (через nearest)
    city_join = gpd.sjoin_nearest(
        centroids,
        cities,
        how="left",
        distance_col="dist"
    )[["city"]]

    # объединяем обратно
    vineyards_gdf["continent"] = continent_join.values
    vineyards_gdf["country"] = country_join.values
    vineyards_gdf["city"] = city_join.values

    return vineyards_gdf


def save_geojson(gdf: gpd.GeoDataFrame, output_path: Path):
    """Сохранение результата"""
    gdf.to_file(output_path, driver="GeoJSON")


def main():
    # OSM folder
    OSM_folder = Path(__file__).resolve().parent.parent
    base_path = Path(__file__).resolve().parent

    input_geojson = OSM_folder / "extracts_osm_py" / "results_combine" / "merged.geojson"
    gpkg_file = OSM_folder.parent / "natural_earth_vector" / "natural_earth_vector.gpkg"
    output_geojson = base_path / "vineyards_enriched_location.geojson"

    # загрузка
    vineyards = load_geojson(input_geojson)
    continents, countries, cities = load_layers(gpkg_file)

    # CRS
    vineyards = ensure_crs(vineyards)
    continents = ensure_crs(continents)
    countries = ensure_crs(countries)
    cities = ensure_crs(cities)

    # обработка
    enriched = enrich_with_location(
        vineyards,
        continents,
        countries,
        cities
    )

    # сохранение
    save_geojson(enriched, output_geojson)


if __name__ == "__main__":
    main()