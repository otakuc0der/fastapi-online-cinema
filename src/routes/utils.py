from urllib.parse import urlencode

from fastapi import Request


def build_url(
    request: Request,
    base_url: str,
    route_name: str,
    **query_params: str,
) -> str:
    path = request.app.url_path_for(route_name)
    url = f"{base_url}{path}"

    if query_params:
        url = f"{url}?{urlencode(query_params)}"

    return url
