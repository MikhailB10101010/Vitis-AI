from src.vineyard_detector import get_vineyard_info
import pandas as pd
from tqdm import tqdm  # progress bar


def process_dataframe(df, cache, local_osm):
    results = []

    iterator = tqdm(
        df.itertuples(),
        total=len(df),
        desc="Processing vineyards",
        unit="point",
        ncols=100,
        smoothing=0.1
    )

    for row in iterator:
        res = get_vineyard_info(row.latitude, row.longitude, cache, local_osm)

        results.append({
            **row._asdict(),
            **res
        })

    return pd.DataFrame(results)
