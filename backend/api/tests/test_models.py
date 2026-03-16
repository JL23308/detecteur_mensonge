from django.test import TestCase
from django.contrib.auth.models import User
from api.models import Device, Session, Measure

class DeviceModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.device = Device.objects.create(user=self.user, mac_address="AA:BB:CC", name="Test Device")

    def test_device_creation(self):
        self.assertEqual(self.device.name, "Test Device")
        self.assertEqual(self.device.user.username, "testuser")
        self.assertTrue(isinstance(self.device, Device))
        self.assertEqual(str(self.device), "Test Device (AA:BB:CC)")

class SessionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.device = Device.objects.create(user=self.user, mac_address="AA:BB:CC:DD")
        self.session = Session.objects.create(user=self.user, device=self.device, calibration_base_bpm=75.5)

    def test_session_creation(self):
        self.assertTrue(self.session.is_active)
        self.assertEqual(self.session.calibration_base_bpm, 75.5)
        self.assertEqual(str(self.session), f"Session {self.session.id} (User: testuser)")

class MeasureModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.device = Device.objects.create(user=self.user, mac_address="A1")
        self.session = Session.objects.create(user=self.user, device=self.device)
        self.measure = Measure.objects.create(
            session=self.session,
            device_mac="A1",
            bpm=80,
            base_bpm=75,
            is_lie=False
        )

    def test_measure_creation(self):
        self.assertEqual(self.measure.bpm, 80)
        self.assertFalse(self.measure.is_lie)
        self.assertIn("TRUTH", str(self.measure))
