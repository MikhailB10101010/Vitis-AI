import os
from src.loader import load_csv, save_csv
from src.processor import process_dataframe
from src.cache import Cache
from src.osm_local_client import LocalOSM

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

input_csv = os.path.join(BASE_DIR, "data/vineyards_enriched.csv")    # input.csv
output_csv = os.path.join(BASE_DIR, "data/output.csv")
osm_file = os.path.join(BASE_DIR, "data/osm/south-fed-district-krasnodar.osm.pbf")
cache_file = os.path.join(BASE_DIR, "cache/cache.db")


def main():
    df = load_csv(input_csv)
    print(f"{input_csv} - загружен")
    cache = Cache(cache_file)
    print("cache")
    local_osm = LocalOSM(osm_file)
    print("local_osm")

    result_df = process_dataframe(df, cache, local_osm)
    save_csv(result_df, output_csv)


if __name__ == "__main__":
    main()
