from dataclasses import field
from pydoc import doc
from ssl import create_default_context
from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from .models import  ActeDemander, ActeFait, Appointment, Assistant, Cabinet, Doctor, Invoice, Medicament, Ordonnance, Patient, Specialite
from cab_g import models


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
            required=True,
            validators=[UniqueValidator(queryset=User.objects.all())]
            )

    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('id' , 'username', 'password', 'password2', 'email', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )

        
        user.set_password(validated_data['password'])
        user.save()

        return user

class UpdateUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('pk' , 'username', 'email', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }
       




class DoctorSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    class Meta:
        model = Doctor
        fields = '__all__'
    



class CabinetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cabinet
        fields = '__all__'


class SpecialiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialite
        fields = '__all__'


class PatientSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Patient
        fields = '__all__'

class ActeDemanderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActeDemander
        fields = '__all__'  

class ActeFaitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActeFait
        fields = '__all__'

class MedicamentSerializer(serializers.ModelSerializer):
    class Meta : 
        model = Medicament
        fields = '__all__'

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta :
        model = Appointment
        fields = '__all__'

class OrdonnanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ordonnance
        fields = '__all__'

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'
class AssistantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assistant
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta :
        model = User
        fields = (
        "id", 
        "last_login",
        "username", 
        "first_name", 
        "last_name", 
        "email", 
        "groups",)

class UserSz(serializers.ModelSerializer):
    class Meta :
        model = User
        fields = (
        "username", 
        "first_name", 
        "last_name", 
        "email" 
        )

class SZer(serializers.ModelSerializer):
    class Meta:
        model = Specialite
        fields = "__all__"

class CaZer(serializers.ModelSerializer):
    class Meta:
        model = Cabinet
        fields = '__all__'

class GetDoctorSerialzer(serializers.ModelSerializer):
    user = RegisterSerializer(required=True, many=False)
    class Meta:
        model = Doctor
        fields = '__all__'  
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data.pop('password2')
        create_user =  User.objects.create(**user_data)
        create_doctor = Doctor.objects.create(user=create_user,**validated_data)
        return create_doctor

class UpdateDoctorSerializer(serializers.ModelSerializer):
    user = UpdateUserSerializer()
    class Meta:
        model = Doctor
        fields = '__all__'
        read_only_fields = ('phone', )
    
    def update(self, instance, validated_data):
        user_serializer = self.fields['user']
        user_instance = instance.user
        user_data = validated_data.pop('user')
        user_serializer.update(user_instance,user_data)
        instance = super().update(instance, validated_data)
        return instance

class GetAssistantSerializer(serializers.ModelSerializer):
    user = UserSz()
    cabinet = serializers.SlugRelatedField(slug_field='name',read_only=True)
    class Meta : 
        model = Assistant
        fields = '__all__'
    