from django.contrib import admin
from django.urls import path ,include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt import views as jwt_views
from cab_g import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('hello/', views.HelloView.as_view(), name='hello'),
    path('api/register/', views.RegisterView.as_view(), name='auth_register'),

    path('api/create-doctor/',views.CreateDoctorView.as_view(),name='create-doctor'),
    path('api/create-cabinet/',views.CreateCabinetView.as_view(),name='create-cabinet'),
    path('api/create-specialite/',views.createSpecialiteView.as_view(),name='create-specialite'),
    path('api/create-patient/',views.CreatePatientView.as_view(),name='create-patient'),
    path('api/create-acte-demander/',views.CreateActeDemanderView.as_view(),name='create-acte-demander'),
    path('api/create-acte-fait/',views.CreateActeFaitView.as_view(),name='create-acte-fait'),
    path('api/create-medicament/',views.CreateMedicamentView.as_view(),name='create-medicament'),
    path('api/create-appointment/',views.CreateAppointmentView.as_view(),name='create-appointment'),
    path('api/create-ordonnance/',views.CreateOrdonnanceView.as_view(),name='create-ordonnance'),
    path('api/create-invoice/',views.CreateInvoiceView.as_view(),name='create-invoice'),

    
    path('api/get-patient/',views.GetPatientView.as_view(),name='get-patient'),
    path('api/get-cabinet/',views.GetCabinetView.as_view(),name='get-cabinet'),
    path('api/get-specialite/',views.GetSpecialitetView.as_view(),name='get-specialite'),
    path('api/get-acte-demander/',views.GetActeDemandertView.as_view(),name='get-acte-demander'),
    path('api/get-acte-fait/',views.GetActeFaitView.as_view(),name='get-acte-fait'),
    path('api/get-medicament/',views.GetMedicamentView.as_view(),name='get-medicament'),
    path('api/get-appointment/',views.GetAppointmentView.as_view(),name='get-appointment'),
    path('api/get-ordonnance/',views.GetOrdonnanceView.as_view(),name='get-ordonnance'),
    path('api/get-invoice/',views.GetInvoiceView.as_view(),name='get-Invoice'),

    #path('api/update-user/<int:id>/',views.UserUpdateView.as_view(),name='update-user'),
    
    path('api/update-doctor/<int:id>/',views.DoctorUpdateView.as_view(),name='update-doctor'),
    path('api/update-cabinet/<int:id>/',views.CabinetUpdateView.as_view(),name='update-cabinet'),
    path('api/update-patient/<int:id>/',views.PatientUpdateView.as_view(),name='update-Patient'),
    path('api/update-acte-demander/<int:id>/',views.ActeDemanderUpdateView.as_view(),name='update-acte-demander'),
    path('api/update-acte-fait/<int:id>/',views.ActeFaitUpdateView.as_view(),name='update-acte-fait'),
    path('api/update-medicament/<int:id>/',views.MedicamentUpdateView.as_view(),name='update-medicament'),
    path('api/update-appointment/<int:id>/',views.AppointmentUpdateView.as_view(),name='update-appointment'),
    path('api/update-ordonnance/<int:id>/',views.OrdonnanceUpdateView.as_view(),name='update-ordonnance'),
    path('api/update-invoice/<int:id>/',views.InvoiceUpdateView.as_view(),name='update-invoice'),

    path('api/delete-specialite/<int:id>/',views.SpecialiteDeleteView.as_view(),name='delete-specialite'),
    path('api/delete-doctor/<int:id>/',views.DoctorDeleteView.as_view(),name='delete-doctor'),
    path('api/delete-cabinet/<int:id>/',views.CabinetDeleteView.as_view(),name='delete-cabinet'),
    path('api/delete-patient/<int:id>/',views.PatientDeleteView.as_view(),name='delete-Patient'),
    path('api/delete-acte-demander/<int:id>/',views.ActeDemanderDeleteView.as_view(),name='delete-acte-demander'),
    path('api/delete-acte-fait/<int:id>/',views.ActeFaitDeleteView.as_view(),name='delete-acte-fait'),
    path('api/delete-medicament/<int:id>/',views.MedicamentDeleteView.as_view(),name='delete-medicament'),
    path('api/delete-appointment/<int:id>/',views.AppointmentDeleteView.as_view(),name='delete-appointment'),
    path('api/delete-ordonnance/<int:id>/',views.OrdonnanceDeleteView.as_view(),name='delete-ordonnance'),
    path('api/delete-invoice/<int:id>/',views.InvoiceDeleteView.as_view(),name='delete-invoice'),

    path('api/get-assistant/',views.AssistantGetView.as_view(),name='get-assistant'),
    path('api/create-assistant/',views.CreateAssistantView.as_view(),name='create-assistant'),
    path('api/update-assistant/<int:id>/',views.AssistantUpdateView.as_view(),name='update-assistant'),
    path('api/delete-assistant/<int:id>/',views.AssistantDeleteView.as_view(),name='delete-assistant'),
    
    path('api/get-doctor/',views.AllDoctorsView.as_view(),name='get-doctor'),

    path('api/get-user/',views.AllUsersView.as_view(),name='get-user'),
    path('api/get-connected-user/',views.GetUserView.as_view(),name='get-connected-user'),
    path('do',views.DoTest.as_view(),name='r'),# just i wel  check if its works

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)