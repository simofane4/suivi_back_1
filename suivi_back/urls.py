from django.contrib import admin
from django.urls import path ,include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt import views as jwt_views
from cab_g import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('hello/', views.HelloView.as_view(), name='hello'),
    path('api/register/', views.RegisterView.as_view(), name='auth_register'),
    path('api/create-doctor/',views.CreateDoctorView.as_view(),name='create-doctor')
   
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)