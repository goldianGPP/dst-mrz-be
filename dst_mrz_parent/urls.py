from django.urls import path, include

urlpatterns = [
    path('api/', include('modules.dst_mrz_app.urls')),
]