from extract_vineyards import extract_vineyards_main
from pathlib import Path

current_path = Path(__file__).resolve().parent
OSM_path = current_path.parent

# data_name = "australia-oceania-260321.osm.pbf"
# data_pbf = OSM_path / "source_file" / data_name
#
# output_name = data_name[:-4]
# output_data = current_path / "results" / output_name
#
# if not data_pbf.is_file():
#     print(f"Файл не найден: {data_pbf}")
#     exit(-2)
#
# if file[-4:] != ".pbf":
#     print(f'{file} is not .pbf file')
#     exit(-3)
#
#
# vineyards = extract_vineyards_main(
#     input_file=Path(data_pbf),
#     output_prefix=Path(output_data),
#     formats=["geojson"],
#     show_stats=True,
#     skip_count=True
# )

folder = OSM_path / "source_file" / "europe_asia_osm_data"
files = [f.name for f in folder.iterdir() if f.is_file()]
for file in files:
    file_path = folder / file
    # print(file_path)

    if not file_path.is_file():
        print(f"Файл не найден: {file}")
        exit(-2)

    if file[-4:] != ".pbf":
        print(f'{file} is not .pbf file')
        break

    output_name = file[:-4]
    output_data = current_path / "results" / "europe_asia_osm_data" / output_name

    if not output_data.exists():
        vineyards = extract_vineyards_main(
            input_file=Path(file_path),
            output_prefix=Path(output_data),
            formats=["geojson"],
            show_stats=True,
            skip_count=True
        )
    else:
        print(f"Существует - {output_name}.geojson")