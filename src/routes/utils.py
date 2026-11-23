from urllib.parse import urlencode

from fastapi import HTTPException, Request, status


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


def normalize_optional_text(
    value: str | None,
    error_message: str,
) -> str | None:
    if value is None:
        return None

    cleaned_value = value.strip()

    if not cleaned_value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=error_message,
        )

    return cleaned_value


def build_pagination_links(
    path: str,
    page: int,
    total_pages: int,
    query_params: dict[str, int | float | str | None],
) -> tuple[str | None, str | None]:
    params_dict = {
        key: value for key, value in query_params.items() if value is not None
    }

    prev_page_link = None
    if page > 1:
        prev_params = {**params_dict, "page": page - 1}
        prev_page_link = f"{path}?{urlencode(prev_params)}"

    next_page_link = None
    if page < total_pages:
        next_params = {**params_dict, "page": page + 1}
        next_page_link = f"{path}?{urlencode(next_params)}"

    return prev_page_link, next_page_link
