from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.entry.views import (
    IdusFlatCachedView,
    IdusAllFlatCachedView,
    IdusAllDisasterCachedView,
)
from apps.gidd.views import (
    CountryViewSet,
    ConflictViewSet,
    DisasterViewSet,
)

router = DefaultRouter()
router.register("countries", CountryViewSet, "countries-view")
router.register("conflicts", ConflictViewSet, "conflicts-view")
router.register("disasters", DisasterViewSet, "diasters-view")

urlpatterns = [
    path('idus', IdusFlatCachedView.as_view()),
    path('idus-all', IdusAllFlatCachedView.as_view()),
    path('idus-all-disaster', IdusAllDisasterCachedView.as_view()),
    path('gidd', include(router.urls)),
]
