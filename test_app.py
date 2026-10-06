import unittest
from app import app

class TestParkingAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_health_check(self):
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'OK', response.data)

if __name__ == '__main__':
    unittest.main()