from django.shortcuts import render, redirect

from PulsePoint.models import RegisterModel
from . forms import RegisterForm,LoginForm

def home(request):
    return render(request, 'home.html')

def login(request):
    if request.method=="POST":
        form=LoginForm(request.POST)
        if form.is_valid():
             return redirect('patient_dashboard')
    else:
            form=LoginForm()
    return render(request,"login.html",{'form':form})

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST,request.FILES)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def patient_dashboard(request):

    patient_id = request.session.get('patient_id')

    if not patient_id:
        return redirect('login')

    patient = RegisterModel.objects.get(id=patient_id)

    context = {
        'username': patient.full_name,
        'patient': patient,
        'appointments': []
    }

    return render(request, 'patient_dashboard.html', context)


def admin_dashboard(request):
    context={'total_patients':0,'total_doctors':0,'total_appointments':0,'available_beds':0,'pending_payments':0,'emergency_cases':0}
    return render(request, 'admin_dashboard.html', context)

def beds(request):
    return render(request, 'beds.html')

def billing(request):
    return render(request, 'billing.html')

def book_appointment(request):
    return render(request, 'book_appointment.html')

def doctor_dashboard(request):
    context={'appointments':[]}
    return render(request, 'doctor_dashboard.html', context)


def pharmacy_dashboard(request):
    context={'medicines':[]}
    return render(request, 'pharmacy_dashboard.html', context)

def laboratory_dashboard(request):
    context={'lab_tests':[]}
    return render(request, 'laboratory_dashboard.html', context)
def receptionist_dashboard(request):
    context={'appointments':[]}
    return render(request, 'receptionist_dashboard.html', context)

def emergency(request):
    return render(request, 'emergency.html')

def lab_reports(request):
    return render(request, 'lab_reports.html')

def medical_records(request):
    return render(request, 'medical_records.html')

def patient_profile(request):
    return render(request, 'patient_profile.html')

def pharmacy(request):
    return render(request, 'pharmacy.html')

def prescriptions(request):
    return render(request, 'prescriptions.html')

def doctors(request):
    return render(request, 'doctors.html')

# Placeholder handlers for sub-actions to ensure all template reverse URLs resolve safely
def placeholder_action(request, *args, **kwargs):
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('home')
