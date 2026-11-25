from django import forms
import re
from . models import Bill, Department, EmergencyCase, LabReport, Medicine, RegisterModel,Appointment,Doctor,Bed, StaffMember

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = RegisterModel
        fields = ['profile', 'full_name', 'username', 'email', 'phone', 'password']
        
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

        return cleaned_data

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        if not re.match(r'^[a-zA-Z\s]+$', full_name):
            raise forms.ValidationError("Full name should only contain letters and spaces.")
        return full_name

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise forms.ValidationError("Username should only contain letters, numbers, and underscores.")
        return username

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if len(str(phone)) != 10:
            raise forms.ValidationError("Phone number must be 10 digits long.")
        return phone

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[a-z]', password):
            raise forms.ValidationError("Password must contain at least one lowercase letter.")
        if not re.search(r'[0-9]', password):
            raise forms.ValidationError("Password must contain at least one digit.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise forms.ValidationError("Password must contain at least one special character.")
        return password


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "Enter username"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Enter password"})
    )

    def clean_username(self):
        username = self.cleaned_data["username"]
        if not RegisterModel.objects.filter(username=username).exists():
            raise forms.ValidationError("User with this username does not exist.")
        return username


class AppointmentForm(forms.ModelForm):
    doctor_name = forms.ChoiceField(choices=[])

    class Meta:
        model = Appointment
        fields = ["doctor_name", "appointment_date", "reason"]
        widgets = {
            "appointment_date": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M"
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        doctors = Doctor.objects.filter(is_available=True).order_by("full_name")
        self.fields["doctor_name"].choices = [
            ("", "Choose a doctor")
        ] + [
            (str(doctor.id), f"Dr. {doctor.full_name} - {doctor.specialization}")
            for doctor in doctors
        ]


class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ["name", "description", "price", "stock_quantity", "expiry_date"]
        widgets = {
            "expiry_date": forms.DateInput(attrs={"type": "date"})
        }




class BedForm(forms.ModelForm):
    class Meta:
        model = Bed
        fields = ["bed_number", "ward", "bed_type", "status"]


class EmergencyCaseForm(forms.ModelForm):
    class Meta:
        model = EmergencyCase
        fields = [
            "patient",
            "patient_name",
            "contact_phone",
            "description",
            "priority",
        ]


class StaffMemberForm(forms.ModelForm):
    class Meta:
        model = StaffMember
        fields = ["full_name", "role", "email", "phone", "is_active"]


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "description", "is_active"]


class AppointmentStatusForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["status"]


class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ["patient", "description", "amount", "bill_date", "due_date", "status"]

class LabReportForm(forms.ModelForm):
    class Meta:
        model = LabReport
        fields = ["patient", "test_name", "report_date", "result", "notes"]

class OTPVerificationForm(forms.Form):
    otp = forms.CharField(
        label="Email OTP",
        min_length=6,
        max_length=6,
        widget=forms.TextInput(attrs={
            "autocomplete": "one-time-code",
            "inputmode": "numeric",
        }),
    )