from src.overpass_client import query as query_api


def get_vineyard_info(lat, lon, cache, local_osm):
    cached = cache.get(lat, lon)
    if cached:
        return cached

    # local
    local_result = local_osm.query(lat, lon)
    if local_result:
        cache.set(lat, lon, local_result)
        return local_result

    # api
    api_result = query_api(lat, lon)
    cache.set(lat, lon, api_result)

    return api_result
