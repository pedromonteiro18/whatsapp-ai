"""Filters for booking system API."""

import django_filters

from .models import Activity


class ActivityFilter(django_filters.FilterSet):
    """
    Filter for Activity model with price range support.

    Supports:
    - category: Exact match filter
    - price_min: Minimum price (inclusive)
    - price_max: Maximum price (inclusive)
    """

    price_min = django_filters.NumberFilter(
        field_name="price", lookup_expr="gte", label="Minimum Price"
    )
    price_max = django_filters.NumberFilter(
        field_name="price", lookup_expr="lte", label="Maximum Price"
    )

    class Meta:
        model = Activity
        fields = ["category", "price_min", "price_max"]
