from rest_framework.pagination import PageNumberPagination


class StandardResultsPagination(PageNumberPagination):
    """Pagination matching the frontend contract: `{count, next, previous, results}`."""

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200
