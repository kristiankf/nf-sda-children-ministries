from datetime import datetime
from zoneinfo import ZoneInfo

from apps.core.dates import greeting_for
from django.test import SimpleTestCase

ACCRA = ZoneInfo("Africa/Accra")


class GreetingTests(SimpleTestCase):
    def test_saturday_morning_is_happy_sabbath(self):
        moment = datetime(2026, 10, 3, 9, 0, tzinfo=ACCRA)
        self.assertEqual(moment.weekday(), 5)
        self.assertEqual(greeting_for(moment), "Happy Sabbath!!")

    def test_saturday_afternoon_is_happy_sabbath(self):
        moment = datetime(2026, 10, 3, 15, 0, tzinfo=ACCRA)
        self.assertEqual(greeting_for(moment), "Happy Sabbath!!")

    def test_monday_morning_is_good_morning(self):
        moment = datetime(2026, 10, 5, 9, 0, tzinfo=ACCRA)
        self.assertEqual(greeting_for(moment), "Good morning")

    def test_monday_afternoon_is_good_afternoon(self):
        moment = datetime(2026, 10, 5, 14, 0, tzinfo=ACCRA)
        self.assertEqual(greeting_for(moment), "Good afternoon")

    def test_monday_evening_is_good_evening(self):
        moment = datetime(2026, 10, 5, 18, 0, tzinfo=ACCRA)
        self.assertEqual(greeting_for(moment), "Good evening")
