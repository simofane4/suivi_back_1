from cmath import rect
from statistics import median_grouped
from rest_framework.views import APIView, status 
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny
from django.contrib.auth.models import User,Group
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
import datetime
from datetime import date

from .serializers import (
                            ActeFaitSerializer,
                            AppointmentSerializer,
                            AssistantSerializer,
                            CabinetSerializer,
                            GetAssistantSerializer,
                            GetDoctorSerialzer,
                            InvoiceSerializer,
                            MedicamentSerializer,
                            OrdonnanceSerializer,
                            PatientSerializer, 
                            RegisterSerializer,
                            DoctorSerializer, 
                            SpecialiteSerializer,
                            ActeDemanderSerializer,
                            UpdateDoctorSerializer,
                            UserSerializer,)
from .models import (
                        ActeDemander,
                        ActeFait,
                        Appointment,
                        Assistant, 
                        Cabinet, 
                        Doctor, 
                        Invoice, 
                        Medicament, 
                        Ordonnance, 
                        Patient, 
                        Specialite)

from rest_framework import generics



class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        groups_list = user.groups.all().values_list('name',flat =True).distinct()
        # Add custom claims
        token['name'] = user.username
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['email'] = user.email
        token['active'] = user.is_active
        try:
            token['groups'] = groups_list[0]
        except IndexError:
            token['groups'] = None
        return token

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class HelloView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        content = {'message': 'Hello, World!', "user": request.user.doctor.cabinet.id}
        return Response(content)


class CreateDoctorView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = DoctorSerializer
    # authentication_classes = (SessionAuthentication, BasicAuthentication)
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        user = User.objects.create_user(data['username'], password=data['password'])
        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.is_superuser = False
        user.is_staff = False
        user.email = data['email']
        gr = Group.objects.get(name='doctor')
        user.groups.add(gr) 
        user.save()
        last_user = User.objects.last()
        get_specialite = Specialite.objects.get(pk=data['specialite'])
        cabinet = Cabinet.objects.get(pk=data['cabinet'])
        create_doctor  = Doctor.objects.create(
            user= last_user,
            cabinet = cabinet,
            inp = data['inp'],
            gender=data['gender'],
            phone= data['phone'],
            address = data['address'],
            specialiste = get_specialite,

        )
        last_doctor = Doctor.objects.last()
        user_serializer =UserSerializer(last_user)
        doctor_serializer = DoctorSerializer(last_doctor)
        content = {'message':"votre compte a été créé !!"}
        return Response(content, status=status.HTTP_201_CREATED)
    
    

# user registrations
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

class CreateCabinetView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CabinetSerializer
    

class createSpecialiteView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class =  SpecialiteSerializer

# last test __________________________________________________________
class DoTest(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = GetDoctorSerialzer

class CreatePatientView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PatientSerializer
        else:
            return PatientSerializer

    def create(self, request, *args, **kwargs):
        # Copy parsed content from HTTP request
        data = request.data.copy()
        # Add id of currently logged user
        try:
            data['cabinet'] = request.user.doctor.cabinet.id
        except User.related_field.RelatedObjectDoesNotExist : 
            data['cabinet'] = request.user.assistant.cabinet.id
        # Default behavior but pass our modified data instead
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class CreateActeDemanderView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ActeDemanderSerializer
        else:
            return ActeDemanderSerializer

    def create(self, request, *args, **kwargs):
        # Copy parsed content from HTTP request
        data = request.data.copy()
        # Add id of currently logged user
        try:
            data['cabinet'] = request.user.doctor.cabinet.id
        except User.related_field.RelatedObjectDoesNotExist : 
            data['cabinet'] = request.user.assistant.cabinet.id
        # Default behavior but pass our modified data instead
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class CreateActeFaitView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ActeFaitSerializer
        else:
            return ActeFaitSerializer

    def create(self, request, *args, **kwargs):
        # Copy parsed content from HTTP request
        data = request.data.copy()
        # Add id of currently logged user
        try:
            data['cabinet'] = request.user.doctor.cabinet.id
        except User.related_field.RelatedObjectDoesNotExist : 
            data['cabinet'] = request.user.assistant.cabinet.id
        # Default behavior but pass our modified data instead
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class CreateMedicamentView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MedicamentSerializer
        else:
            return MedicamentSerializer

    def create(self, request, *args, **kwargs):
        # Copy parsed content from HTTP request
        data = request.data.copy()
        # Add id of currently logged user
        try:
            data['cabinet'] = request.user.doctor.cabinet.id
        except User.related_field.RelatedObjectDoesNotExist : 
            data['cabinet'] = request.user.assistant.cabinet.id
        # Default behavior but pass our modified data instead
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

def get_date(datestr):
        datet = datetime.datetime.strptime(datestr,"%Y-%m-%d").date()
        return datet
class CreateAppointmentView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = AppointmentSerializer
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AppointmentSerializer
        else:
            return AppointmentSerializer
    

    def create(self, request, *args, **kwargs):
        data = self.request.data.copy()
        dat = data['date']
        try:
            patient = Patient.objects.filter(cabinet=request.user.doctor.cabinet.id)
        except User.related_field.RelatedObjectDoesNotExist : 
            patient = Patient.objects.filter(cabinet=request.user.assistant.cabinet.id) 
        
        list_filter = patient.values_list('appointment',flat=True).distinct()
        appoint = Appointment.objects.filter(id__in=list_filter).filter(date=dat)
        check = False
        print("hadi 9bel " ,type(dat),dat)
        print("hadi menbe3de",type(get_date(dat)),get_date(dat))
        print(date.today())
        if date.today() <= get_date(dat):
            for app in appoint:
                if  datetime.datetime.strptime(data['fm'],"%H:%M").time()  >= app.fm and  datetime.datetime.strptime(data['fm'],"%H:%M").time() < app.To:
                    check = True
                    content = {"message":f"Cet  heur {data['fm']} est déjà  réservé, veuillez choisir un autre heure"}
                    return Response( content , status=status.HTTP_201_CREATED)
                if  datetime.datetime.strptime(data['To'],"%H:%M").time() >  app.fm and  datetime.datetime.strptime(data['To'],"%H:%M").time()<=  app.To:
                    check = True
                    content = {"message":f"Cet heur {data['To']} est déjà  réservé,veuillez choisir un autre heure "}
                    return Response( content , status=status.HTTP_201_CREATED)
                if  app.fm >=  datetime.datetime.strptime(data['fm'],"%H:%M").time() and  app.fm <  datetime.datetime.strptime(data['To'],"%H:%M").time():
                    check = True
                    content = {"message":"ce rendez-vous a un rendez-vous entre eux, veuillez choisir un autre rendez-vous"}
                    return Response( content , status=status.HTTP_201_CREATED)
        else:
            content = {"message":f"ce jour {data['date']}  est  déjà passé, veuillez choisir un autre jour"}
            return Response( content , status=status.HTTP_201_CREATED)
        if not check:
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED,headers = headers)


class CreateOrdonnanceView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrdonnanceSerializer
        else:
            return OrdonnanceSerializer

    def create(self, request, *args, **kwargs):
        # Copy parsed content from HTTP request
        data = request.data.copy()
        # Add id cabinet  of currently logged user
        data['cabinet'] = request.user.doctor.cabinet.id
        # Default behavior but pass our modified data instead
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class CreateInvoiceView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return InvoiceSerializer
        else:
            return InvoiceSerializer

    def create(self, request, *args, **kwargs):
        # Copy parsed content from HTTP request
        data = request.data.copy()
        # Add id cabinet  of currently logged user
        try:
            data['cabinet'] = request.user.doctor.cabinet.id
        except User.related_field.RelatedObjectDoesNotExist : 
            data['cabinet'] = request.user.assistant.cabinet.id
        # Default behavior but pass our modified data instead
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)




class GetPatientView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        try:
            patient_data = Patient.objects.filter(cabinet=request.user.doctor.cabinet.id)
        except User.related_field.RelatedObjectDoesNotExist : 
            patient_data = Patient.objects.filter(cabinet=request.user.assistant.cabinet.id)
        
        serializer = PatientSerializer(patient_data, many=True)        
        return Response(serializer.data, status=status.HTTP_200_OK) 

class GetSpecialitetView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        specialite_data = Specialite.objects.all()
        serializer = SpecialiteSerializer(specialite_data, many=True)        
        return Response(serializer.data, status=status.HTTP_200_OK)

class GetActeDemandertView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        try:
            acte_demander_data = ActeDemander.objects.filter(cabinet=request.user.doctor.cabinet.id)
        except User.related_field.RelatedObjectDoesNotExist :
            acte_demander_data = ActeDemander.objects.filter(cabinet=request.user.assistant.cabinet.id)
        
        serializer = ActeDemanderSerializer(acte_demander_data, many=True)        
        return Response(serializer.data, status=status.HTTP_200_OK) 



class GetActeFaitView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        try:
            acte_fait_data = ActeFait.objects.filter(cabinet=request.user.doctor.cabinet.id)
        except User.related_field.RelatedObjectDoesNotExist :
            acte_fait_data = ActeFait.objects.filter(cabinet=request.user.assistant.cabinet.id)
        serializer = ActeFaitSerializer(acte_fait_data, many=True)        
        return Response(serializer.data, status=status.HTTP_200_OK) 

class GetMedicamentView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        try:
            medicament_data = Medicament.objects.filter(cabinet=request.user.doctor.cabinet.id)
        except User.related_field.RelatedObjectDoesNotExist :
            medicament_data = Medicament.objects.filter(cabinet=request.user.assistant.cabinet.id)
        serializer = MedicamentSerializer(medicament_data, many=True)        
        return Response(serializer.data, status=status.HTTP_200_OK) 

class GetAppointmentView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        try:
            patient = Patient.objects.filter(cabinet=request.user.doctor.cabinet.id)
        except User.related_field.RelatedObjectDoesNotExist :
            patient = Patient.objects.filter(cabinet=request.user.assitant.cabinet.id)

        list_filter = patient.values_list('appointment',flat=True).distinct()
        appointment_data = Appointment.objects.filter(id__in=list_filter)
        serializer = AppointmentSerializer(appointment_data, many = True)
              
        return Response( serializer.data ,status=status.HTTP_200_OK) 

class GetCabinetView(APIView):
    permission_classes = (IsAuthenticated, )
    def get(self, request):
        cabinet = Cabinet.objects.all()
        serializer = CabinetSerializer(cabinet,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetOrdonnanceView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        ordonnacne_data = Ordonnance.objects.filter(cabinet=request.user.doctor.cabinet.id)

        serializer = OrdonnanceSerializer(ordonnacne_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GetInvoiceView(APIView):
    permission_classes = (IsAuthenticated, )
    def get(self, request): 
        try:
            invoice_data = Invoice.objects.filter(recipient=request.user.doctor.cabinet.id)
            serializer = InvoiceSerializer(invoice_data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.related_field.RelatedObjectDoesNotExist : 
            invoice_data = Invoice.objects.filter(recipient=request.user.assistant.cabinet.id)
            serializer = InvoiceSerializer(invoice_data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
         

class UserUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    lookup_field = 'id'
    def retrieve(self, request,*args, **kwargs):
        instance = self.get_object()
        serializer = RegisterSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def perform_update(self, serializer):
        return serializer.save()
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial',False)
        instance = self.get_object()
        serializer = self.get_serializer(instance,data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)    
        instance = self.perform_update(serializer)
        serializer = RegisterSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

class SpecialiteUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Specialite.objects.all()
    serializer_class = SpecialiteSerializer
    lookup_field = 'id'
    def retrieve(self, request,*args, **kwargs):
        instance = self.get_object()
        serializer = CabinetSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CabinetUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Cabinet.objects.all()
    serializer_class = CabinetSerializer
    lookup_field = 'id'
    def retrieve(self, request,*args, **kwargs):
        instance = self.get_object()
        serializer = CabinetSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def perform_update(self, serializer):
        return serializer.save()
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial',False)
        instance = self.get_object()
        serializer = self.get_serializer(instance,data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)    
        instance = self.perform_update(serializer)
        serializer = CabinetSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DoctorUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Doctor.objects.all()
    serializer_class = UpdateDoctorSerializer
    lookup_field = 'id'
    
        
class PatientUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    lookup_field = 'id'
    def retrieve(self, request,*args, **kwargs):
        instance = self.get_object()
        serializer = PatientSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial',False)
        instance = self.get_object()
        data = request.data.copy()
        # Add id of currently logged user
        try:
            data['cabinet'] = request.user.doctor.cabinet.id
        except User.related_field.RelatedObjectDoesNotExist : 
            data['cabinet'] = request.user.assistant.cabinet.id
        # Default behavior but pass our modified data instead
        serializer = self.get_serializer(instance,data=data, partial=partial)
        serializer.is_valid(raise_exception=True)    
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


    

class SpecialiteUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Specialite.objects.all()
    serializer_class =  SpecialiteSerializer
    lookup_field = 'id'
    def retrieve(self, request,*args, **kwargs):
        instance = self.get_object()
        serializer = SpecialiteSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def perform_update(self, serializer):
        return serializer.save()
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial',False)
        instance = self.get_object()
        serializer = self.get_serializer(instance,data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)    
        instance = self.perform_update(serializer)
        serializer = SpecialiteSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ActeDemanderUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = ActeDemander.objects.all()
    serializer_class =  ActeDemanderSerializer
    lookup_field = 'id'
    def retrieve(self, request,*args, **kwargs):
        instance = self.get_object()
        serializer =  ActeDemanderSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial',False)
        instance = self.get_object()
        data = request.data.copy()
        # Add id of currently logged user
        try:
            data['cabinet'] = request.user.doctor.cabinet.id
        except User.related_field.RelatedObjectDoesNotExist : 
            data['cabinet'] = request.user.assistant.cabinet.id
        # Default behavior but pass our modified data instead
        serializer = self.get_serializer(instance,data=data, partial=partial)
        serializer.is_valid(raise_exception=True)    
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

class ActeFaitUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = ActeFait.objects.all()
    serializer_class =  ActeFaitSerializer
    lookup_field = 'id'
    def retrieve(self, request,*args, **kwargs):
        instance = self.get_object()
        serializer =  ActeFaitSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def perform_update(self, serializer):
        return serializer.save()
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial',False)
        instance = self.get_object()
        data = request.data.copy()
        # Add id of currently logged user
        try:
            data['cabinet'] = request.user.doctor.cabinet.id
        except User.related_field.RelatedObjectDoesNotExist : 
            data['cabinet'] = request.user.assistant.cabinet.id
        # Default behavior but pass our modified data instead
        serializer = self.get_serializer(instance,data=data, partial=partial)
        serializer.is_valid(raise_exception=True)    
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class MedicamentUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Medicament.objects.all()
    serializer_class =  MedicamentSerializer
    lookup_field = 'id'
    def retrieve(self, request,*args, **kwargs):
        instance = self.get_object()
        serializer =    MedicamentSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial',False)
        instance = self.get_object()
        data = request.data.copy()
        # Add id of currently logged user
        try:
            data['cabinet'] = request.user.doctor.cabinet.id
        except User.related_field.RelatedObjectDoesNotExist : 
            data['cabinet'] = request.user.assistant.cabinet.id
        # Default behavior but pass our modified data instead
        serializer = self.get_serializer(instance,data=data, partial=partial)
        serializer.is_valid(raise_exception=True)    
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

class AppointmentUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Appointment.objects.all()
    serializer_class =  AppointmentSerializer
    lookup_field = 'id'
    def retrieve(self, request,*args, **kwargs):
        instance = self.get_object()
        serializer =  AppointmentSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def perform_update(self, serializer):
        return serializer.save()
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial',False)
        instance = self.get_object()
        serializer = self.get_serializer(instance,data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)    
        instance = self.perform_update(serializer)
        serializer = AppointmentSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

class OrdonnanceUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Ordonnance.objects.all()
    serializer_class =  OrdonnanceSerializer
    lookup_field = 'id'
    def retrieve(self, request,*args, **kwargs):
        instance = self.get_object()
        serializer =  OrdonnanceSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial',False)
        instance = self.get_object()
        data = request.data.copy()
        # Add id of currently logged user
        try:
            data['cabinet'] = request.user.doctor.cabinet.id
        except User.related_field.RelatedObjectDoesNotExist : 
            data['cabinet'] = request.user.assistant.cabinet.id
        # Default behavior but pass our modified data instead
        serializer = self.get_serializer(instance,data=data, partial=partial)
        serializer.is_valid(raise_exception=True)    
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

class InvoiceUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Invoice.objects.all()
    serializer_class =  InvoiceSerializer
    lookup_field = 'id'
    def retrieve(self, request,*args, **kwargs):
        instance = self.get_object()
        serializer = InvoiceSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial',False)
        instance = self.get_object()
        data = request.data.copy()
        # Add id of currently logged user
        try:
            data['cabinet'] = request.user.doctor.cabinet.id
        except User.related_field.RelatedObjectDoesNotExist : 
            data['cabinet'] = request.user.assistant.cabinet.id
        # Default behavior but pass our modified data instead
        serializer = self.get_serializer(instance,data=data, partial=partial)
        serializer.is_valid(raise_exception=True)    
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class CabinetDeleteView(generics.RetrieveDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Cabinet.objects.all()
    serializer_class = CabinetSerializer
    lookup_field = 'id'
    

class SpecialiteDeleteView(generics.RetrieveDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Specialite.objects.all()
    serializer_class = SpecialiteSerializer
    lookup_field = 'id'



class DoctorDeleteView(generics.RetrieveDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    lookup_field = 'id'

class PatientDeleteView(generics.RetrieveDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    lookup_field = 'id'
   
class ActeDemanderDeleteView(generics.RetrieveDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = ActeDemander.objects.all()
    serializer_class =  ActeDemanderSerializer
    lookup_field = 'id'

class ActeFaitDeleteView(generics.RetrieveDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = ActeFait.objects.all()
    serializer_class =  ActeFaitSerializer
    lookup_field = 'id'

class MedicamentDeleteView(generics.RetrieveDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Medicament.objects.all()
    serializer_class =  MedicamentSerializer
    lookup_field = 'id'

class AppointmentDeleteView(generics.RetrieveDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Appointment.objects.all()
    serializer_class =  AppointmentSerializer
    lookup_field = 'id'

class OrdonnanceDeleteView(generics.RetrieveDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Ordonnance.objects.all()
    serializer_class =  OrdonnanceSerializer
    lookup_field = 'id'

class InvoiceDeleteView(generics.RetrieveDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Invoice.objects.all()
    serializer_class =  InvoiceSerializer
    lookup_field = 'id'

class CreateAssistantView(generics.ListCreateAPIView):
    permission_classes =  (IsAuthenticated,)
    serializer_class = AssistantSerializer
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        user = User.objects.create_user(data['username'], password=data['password'])
        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.is_superuser = False
        user.is_staff = False
        user.email = data['email']
        gr = Group.objects.get(name = 'assistant')
        user.groups.add(gr) 
        user.save()
        last_user = User.objects.last()
        cabinet = Cabinet.objects.get(pk=data['cabinet'])
        create_doctor  = Assistant.objects.create(
            user= last_user,
            cabinet = cabinet,
            img = data['img'],
            cin = data['cin'],
            gender=data['gender'],
            phone= data['phone'],
            address = data['address'],
        )
    
        content = {'message':"votre compte a été créé !!"}
        return Response(content, status=status.HTTP_201_CREATED)

class AssistantGetView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        assistant = Assistant.objects.all()
        serializer = GetAssistantSerializer(assistant,many=True)
        return Response(serializer.data , status=status.HTTP_200_OK)

class AssistantUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class  = AssistantSerializer
    ookup_field = 'id'
    def retrieve(self, request,*args, **kwargs):
        instance = self.get_object()
        serializer =  AssistantSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial',False)
        instance = self.get_object()
        serializer = AssistantSerializer(instance,data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)    
        serializer.save()
        serializer = AssistantSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)



class AssistantDeleteView(generics.RetrieveDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Assistant.objects.all()
    serializer_class = AssistantSerializer
    lookup_field = 'id'


class AllDoctorsView(APIView):

    permission_classes = (IsAuthenticated,)
    def get(self, request):
        doctor = Doctor.objects.all()
        serializer = GetDoctorSerialzer(doctor,many=True)
        return Response(serializer.data , status=status.HTTP_200_OK)


class AllUsersView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        user = User.objects.all()
        serializer = UserSerializer(user,many=True)
        return Response(serializer.data , status=status.HTTP_200_OK)

class GetUserView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        user = User.objects.get(pk=request.user.id)
        serializer = UserSerializer(user)
        return Response(serializer.data , status=status.HTTP_200_OK)
