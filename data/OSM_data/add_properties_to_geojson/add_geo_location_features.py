import geopandas as gpd
import pandas as pd
from pathlib import Path
import logging
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_geojson(filepath: Path) -> gpd.GeoDataFrame:
    """Загружает GeoJSON файл через GeoPandas."""
    logger.info(f"Загрузка GeoJSON: {filepath}")
    gdf = gpd.read_file(filepath)
    logger.info(f"Загружено {len(gdf)} объектов, CRS: {gdf.crs}")
    return gdf


def save_geojson(gdf: gpd.GeoDataFrame, filepath: Path) -> None:
    """Сохраняет GeoDataFrame в GeoJSON файл."""
    logger.info(f"Сохранение GeoJSON: {filepath}")
    gdf.to_file(filepath, driver="GeoJSON")
    logger.info(f"Сохранено {len(gdf)} объектов")


def load_countries(gpkg_path: Path, layer_name: str = "ne_10m_admin_0_countries") -> gpd.GeoDataFrame:
    """Загружает слой стран из GeoPackage."""
    logger.info(f"Загрузка слоя '{layer_name}' из {gpkg_path}")
    countries = gpd.read_file(gpkg_path, layer=layer_name)
    countries = countries[["NAME", "CONTINENT", "geometry"]].copy()

    if countries.crs is None or countries.crs.to_epsg() != 4326:
        countries = countries.to_crs(epsg=4326)

    logger.info(f"Загружено {len(countries)} стран")
    return countries


def build_centroids_gdf(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Строит GeoDataFrame центроидов из исходного GeoDataFrame."""
    logger.info("Вычисление центроидов...")

    centroids_gdf = gpd.GeoDataFrame(
        {"feature_idx": np.arange(len(gdf))},
        geometry=gdf.geometry.centroid.values,
        crs=gdf.crs
    )

    logger.info(f"Создано {len(centroids_gdf)} центроидов")
    return centroids_gdf


def spatial_join_countries(
    centroids_gdf: gpd.GeoDataFrame,
    countries: gpd.GeoDataFrame
) -> pd.DataFrame:
    """Батч point-in-polygon через sjoin."""
    logger.info("Spatial join: point-in-polygon...")

    joined = gpd.sjoin(
        centroids_gdf,
        countries[["NAME", "CONTINENT", "geometry"]],
        how="left",
        predicate="within"
    )

    joined = joined.drop_duplicates(subset="feature_idx", keep="first")

    found = joined['NAME'].notna().sum()
    logger.info(f"Найдено совпадений: {found} / {len(joined)}")
    return joined[["feature_idx", "NAME", "CONTINENT"]]


def prepare_projected_countries(countries: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Перепроецирует страны в метрическую CRS один раз."""
    logger.info("Перепроецирование стран в EPSG:3857...")
    return countries[["NAME", "CONTINENT", "geometry"]].to_crs(epsg=3857)


def find_nearest_single(
    centroid_4326,
    countries_projected: gpd.GeoDataFrame,
    sindex
) -> tuple[str, str]:
    """
    Поиск ближайшей страны для одной точки.
    Расширяющийся буфер + sindex.
    """
    pt_series = gpd.GeoSeries([centroid_4326], crs="EPSG:4326").to_crs(epsg=3857)
    pt_projected = pt_series.iloc[0]

    for buffer_m in [50_000, 200_000, 1_000_000, 5_000_000, 20_000_000]:
        buffered = pt_projected.buffer(buffer_m)
        candidates_idx = list(sindex.intersection(buffered.bounds))
        if candidates_idx:
            candidates = countries_projected.iloc[candidates_idx]
            distances = candidates.geometry.distance(pt_projected)
            nearest_idx = distances.idxmin()
            row = candidates.loc[nearest_idx]
            return row["NAME"], row["CONTINENT"]

    # Fallback
    distances = countries_projected.geometry.distance(pt_projected)
    nearest_idx = distances.idxmin()
    row = countries_projected.loc[nearest_idx]
    return row["NAME"], row["CONTINENT"]


def fill_missing_with_nearest(
    centroids_gdf: gpd.GeoDataFrame,
    result_df: pd.DataFrame,
    countries: gpd.GeoDataFrame
) -> pd.DataFrame:
    """Поточечный поиск ближайшей страны для промахов."""
    missing_mask = result_df["NAME"].isna() | result_df["CONTINENT"].isna()
    missing_count = missing_mask.sum()

    if missing_count == 0:
        logger.info("Все объекты определены, поиск ближайших не требуется")
        return result_df

    logger.info(f"Поиск ближайшей страны для {missing_count} объектов...")

    countries_projected = prepare_projected_countries(countries)
    proj_sindex = countries_projected.sindex

    missing_indices = result_df.loc[missing_mask, "feature_idx"].values
    centroids_lookup = centroids_gdf.set_index("feature_idx")

    processed = 0
    for feat_idx in missing_indices:
        centroid_4326 = centroids_lookup.loc[feat_idx, "geometry"]

        country, continent = find_nearest_single(
            centroid_4326, countries_projected, proj_sindex
        )

        mask = result_df["feature_idx"] == feat_idx
        if pd.isna(result_df.loc[mask, "NAME"].values[0]):
            result_df.loc[mask, "NAME"] = country
        if pd.isna(result_df.loc[mask, "CONTINENT"].values[0]):
            result_df.loc[mask, "CONTINENT"] = continent

        processed += 1
        if processed % 100 == 0:
            logger.info(f"  Обработано ближайших: {processed}/{missing_count}")

    logger.info(f"Поиск ближайших завершён: {processed}/{missing_count}")
    return result_df


def apply_results_to_gdf(gdf: gpd.GeoDataFrame, result_df: pd.DataFrame) -> gpd.GeoDataFrame:
    """Добавляет столбцы country и continent в исходный GeoDataFrame."""
    logger.info("Запись результатов...")

    # Приводим result_df к тому же порядку что и gdf
    result_sorted = result_df.sort_values("feature_idx").reset_index(drop=True)

    gdf = gdf.copy()
    gdf["country"] = result_sorted["NAME"].values
    gdf["continent"] = result_sorted["CONTINENT"].values

    return gdf


def enrich_geodataframe(gdf: gpd.GeoDataFrame, countries: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Основной пайплайн обогащения данных."""

    # 1. Центроиды — векторизованно
    centroids_gdf = build_centroids_gdf(gdf)

    # 2. Батч sjoin
    result_df = spatial_join_countries(centroids_gdf, countries)

    # 3. Заполнение пропусков
    result_df = fill_missing_with_nearest(centroids_gdf, result_df, countries)

    # 4. Добавление столбцов в исходный GeoDataFrame
    enriched_gdf = apply_results_to_gdf(gdf, result_df)

    return enriched_gdf


def main():
    # OSM folder
    OSM_folder = Path(__file__).resolve().parent.parent
    base_path = Path(__file__).resolve().parent

    geojson_input_path = OSM_folder / "extracts_osm_py" / "results_combine" / "merged.geojson"
    gpkg_path = OSM_folder.parent / "natural_earth_vector" / "natural_earth_vector.gpkg"
    geojson_output_path = base_path / "vineyards_enriched_location.geojson"

    geojson_output_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Загрузка стран (один раз)
    countries = load_countries(gpkg_path)

    # 2. Загрузка GeoJSON как GeoDataFrame (один раз)
    gdf = load_geojson(geojson_input_path)

    # 3. Обогащение
    enriched_gdf = enrich_geodataframe(gdf, countries)

    # 4. Сохранение
    save_geojson(enriched_gdf, geojson_output_path)

    logger.info("Готово!")


if __name__ == "__main__":
    main()