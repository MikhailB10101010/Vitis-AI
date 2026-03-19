from extract_vineyards import extract_vineyards_main
from pathlib import Path

current_path = Path(__file__).resolve().parent
OSM_path = current_path.parent

data_name = "south-fed-district-krasnodar.osm.pbf"
data_pbf = OSM_path / "source_file" / data_name

output_name = data_name[:-4]
output_data = current_path / "results" / output_name

if not data_pbf.is_file():
    print(f"Файл не найден: {data_pbf}")
    exit(-2)

vineyards = extract_vineyards_main(
    input_file=Path(data_pbf),
    output_prefix=Path(output_data),
    formats=["geojson"],
    show_stats=True,
    skip_count=True
)

