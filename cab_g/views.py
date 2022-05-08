from cgitb import lookup
from http.client import UNSUPPORTED_MEDIA_TYPE
from turtle import update
from urllib import request
from webbrowser import get
from django.shortcuts import render
from rest_framework.views import APIView, status 
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny
from django.contrib.auth.models import User
from .serializers import (
                            ActeFaitSerializer,
                            AppointmentSerializer,
                            AssistantSerializer,
                            CabinetSerializer,
                            InvoiceSerializer,
                            MedicamentSerializer,
                            OrdonnanceSerializer,
                            PatientSerializer, 
                            RegisterSerializer,
                            DoctorSerializer, 
                            SpecialiteSerializer,
                            ActeDemanderSerializer,)
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

from cab_g import serializers


# Create your views here.

class HelloView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        content = {'message': 'Hello, World!', "user": request.user.doctor.cabinet.id}
        return Response(content)


class CreateDoctorView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = DoctorSerializer
    # authentication_classes = (SessionAuthentication, BasicAuthentication)
    
    

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
        data['cabinet'] = request.user.doctor.cabinet.id
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
        data['cabinet'] = request.user.doctor.cabinet.id
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
        data['cabinet'] = request.user.doctor.cabinet.id
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
        data['cabinet'] = request.user.doctor.cabinet.id
        # Default behavior but pass our modified data instead
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class CreateAppointmentView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = AppointmentSerializer

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
        data['recipient'] = request.user.id
        # Default behavior but pass our modified data instead
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)




class GetPatientView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        patient_data = Patient.objects.filter(cabinet=request.user.doctor.cabinet.id)
        serializer = PatientSerializer(patient_data, many=True)        
        return Response(serializer.data, status=status.HTTP_200_OK) 

class GetSpecialitetView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self):
        specialite_data = Specialite.objects.all()
        serializer = SpecialiteSerializer(specialite_data, many=True)        
        return Response(serializer.data, status=status.HTTP_200_OK)

class GetActeDemandertView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        acte_demander_data = ActeDemander.objects.filter(cabinet=request.user.doctor.cabinet.id)
        serializer = ActeDemanderSerializer(acte_demander_data, many=True)        
        return Response(serializer.data, status=status.HTTP_200_OK) 



class GetActeFaitView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        acte_fait_data = ActeFait.objects.filter(cabinet=request.user.doctor.cabinet.id)
        serializer = ActeFaitSerializer(acte_fait_data, many=True)        
        return Response(serializer.data, status=status.HTTP_200_OK) 

class GetMedicamentView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        medicament_data = Medicament.objects.filter(cabinet=request.user.doctor.cabinet.id)
        serializer = MedicamentSerializer(medicament_data, many=True)        
        return Response(serializer.data, status=status.HTTP_200_OK) 

class GetAppointmentView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        patient = Patient.objects.filter(cabinet=request.user.doctor.cabinet.id)
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
    serializer_class = DoctorSerializer
    lookup_field = 'id'
    def retrieve(self, request,*args, **kwargs):
        instance = self.get_object()
        serializer = DoctorSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def perform_update(self, serializer):
        return serializer.save()
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial',False)
        instance = self.get_object()
        serializer = self.get_serializer(instance,data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)    
        instance = self.perform_update(serializer)
        serializer = DoctorSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

        
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
        data['cabinet'] = request.user.doctor.cabinet.id
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
        data['cabinet'] = request.user.doctor.cabinet.id
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
        data['cabinet'] = request.user.doctor.cabinet.id
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
        data['cabinet'] = request.user.doctor.cabinet.id
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
        data['cabinet'] = request.user.doctor.cabinet.id
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
        data['recipient'] = request.user.id
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

class AssistantCreateView(generics.ListCreateAPIView):
    permission_classes =  (IsAuthenticated,)
    serializer_class = AssistantSerializer

class AssistantGetView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        assistant = Assistant.objects.all()
        serializer = AssistantSerializer(assistant,many=True)
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
        serializer = DoctorSerializer(doctor,many=True)
        return Response(serializer.data , status=status.HTTP_200_OK)