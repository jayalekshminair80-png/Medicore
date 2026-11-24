from django.db import models


class RegisterModel(models.Model):
    profile=models.ImageField(upload_to='profile_images/')
    full_name=models.CharField(max_length=100)
    username=models.CharField(max_length=100)
    email=models.EmailField()
    phone=models.CharField(max_length=10)
    password=models.CharField(max_length=128)

    def str(self):
        return self.username




class Doctor(models.Model):
    full_name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"Dr. {self.full_name} - {self.specialization}"



class Appointment(models.Model):
    STATUS_CHOICES = [
        ("Scheduled", "Scheduled"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    ]

    patient = models.ForeignKey(
        RegisterModel,
        on_delete=models.CASCADE,
        related_name="appointments"
    )
    doctor_name = models.CharField(max_length=100)
    doctor_specialization = models.CharField(max_length=100, blank=True)
    appointment_date = models.DateTimeField()
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Scheduled"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.full_name} - {self.appointment_date}"


class MedicalRecord(models.Model):
    patient = models.ForeignKey(
        RegisterModel,
        on_delete=models.CASCADE,
        related_name="medical_records"
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="medical_records"
    )
    record_date = models.DateField()
    title = models.CharField(max_length=150)
    details = models.TextField()

    def __str__(self):
        return f"{self.title} - {self.patient.full_name}"

class Prescription(models.Model):
    patient = models.ForeignKey(
        RegisterModel,
        on_delete=models.CASCADE,
        related_name="prescriptions"
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prescriptions"
    )
    medication_name = models.CharField(max_length=150)
    dosage = models.CharField(max_length=100)
    instructions = models.TextField(blank=True)
    prescribed_date = models.DateField()

    def __str__(self):
        return f"{self.medication_name} - {self.patient.full_name}"


class LabReport(models.Model):
    patient = models.ForeignKey(
        RegisterModel,
        on_delete=models.CASCADE,
        related_name="lab_reports"
    )
    test_name = models.CharField(max_length=150)
    report_date = models.DateField()
    result = models.TextField()
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.test_name} - {self.patient.full_name}"


class Medicine(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    expiry_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name


class Bill(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Paid", "Paid"),
    ]

    patient = models.ForeignKey(
        RegisterModel,
        on_delete=models.CASCADE,
        related_name="bills"
    )
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bill_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    def __str__(self):
        return f"Bill #{self.id} - {self.patient.full_name}"



class Bed(models.Model):
    STATUS_CHOICES = [
        ("Available", "Available"),
        ("Occupied", "Occupied"),
        ("Maintenance", "Maintenance"),
    ]

    bed_number = models.CharField(max_length=20, unique=True)
    ward = models.CharField(max_length=100)
    bed_type = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Available"
    )

    def __str__(self):
        return f"{self.bed_number} - {self.ward}"


class EmergencyCase(models.Model):
    PRIORITY_CHOICES = [
        ("Low", "Low"),
        ("Medium", "Medium"),
        ("High", "High"),
        ("Critical", "Critical"),
    ]

    STATUS_CHOICES = [
        ("Open", "Open"),
        ("In Progress", "In Progress"),
        ("Resolved", "Resolved"),
    ]

    patient = models.ForeignKey(
        RegisterModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emergency_cases"
    )
    patient_name = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=15, blank=True)
    description = models.TextField()
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="Medium"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Open"
    )
    reported_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient_name} - {self.priority}"



class StaffMember(models.Model):
    full_name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.full_name} - {self.role}"



class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name



class PendingRegistration(models.Model):
    profile = models.ImageField(upload_to="profile_images/pending/")
    full_name = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=10)
    password = models.CharField(max_length=128)
    otp_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)