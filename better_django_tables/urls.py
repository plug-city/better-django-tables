from django.urls import path
from better_django_tables import views

app_name = 'better_django_tables'

urlpatterns = [

    # Reports
    path('reports/', views.ReportListView.as_view(), name='report_list'),
    path('reports/<int:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
    path('reports/<int:pk>/delete/', views.ReportDeleteView.as_view(), name='report_delete'),
]
