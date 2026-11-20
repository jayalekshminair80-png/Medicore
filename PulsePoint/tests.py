from django.test import TestCase
from django.urls import reverse

from .models import RegisterModel


class RegisterViewTests(TestCase):
    def test_registration_saves_values_and_redirects(self):
        response = self.client.post(reverse('register'), {
            'full_name': 'Test Patient',
            'username': 'test_patient',
            'email': 'patient@example.com',
            'phone': '1234567890',
            'password': 'StrongPass1!',
            'confirm_password': 'StrongPass1!',
        })

        self.assertRedirects(response, reverse('login'), fetch_redirect_response=False)
        patient = RegisterModel.objects.get(username='test_patient')
        self.assertEqual(patient.full_name, 'Test Patient')
        self.assertEqual(patient.email, 'patient@example.com')
        self.assertEqual(patient.phone, 1234567890)

    def test_registration_renders_password_confirmation_error(self):
        response = self.client.post(reverse('register'), {
            'full_name': 'Test Patient',
            'username': 'test_patient',
            'email': 'patient@example.com',
            'phone': '1234567890',
            'password': 'StrongPass1!',
            'confirm_password': 'DifferentPass1!',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Passwords do not match.')
        self.assertFalse(RegisterModel.objects.filter(username='test_patient').exists())
