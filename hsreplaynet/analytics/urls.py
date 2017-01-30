from django.conf.urls import url
from .views import card_inventory as inv, get_filters
from .views import fetch_query_results as query
from .views import evict_query_from_cache as evict_from_cache
from .views import available_data

urlpatterns = [
	url(r"^filters$", get_filters, name="analytics_filters"),
	url(r"^inventory/card/(?P<card_id>\w+)$", inv, name="analytics_card_inventory"),
	url(r"^query/(?P<name>\w+)$", query, name="analytics_fetch_query_results"),
	url(r"^available-data/(?P<name>\w+)$", available_data, name="analytics_available_data"),
	url(r"^evict/(?P<name>\w+)$", evict_from_cache, name="analytics_evict_from_cache"),
]
