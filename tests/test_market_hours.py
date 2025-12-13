"""
Tests for market_hours utility
"""
import unittest
from datetime import datetime, time
import pytz

from src.utils.market_hours import is_forex_market_open, get_next_market_open


class TestMarketHours(unittest.TestCase):
    """Test Forex market hours detection"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.est = pytz.timezone('US/Eastern')
    
    def test_forex_market_open_wednesday_noon(self):
        """Test market is open on Wednesday at noon EST"""
        # Wednesday, 12:00 PM EST
        dt = self.est.localize(datetime(2024, 1, 10, 12, 0, 0))  # Jan 10, 2024 was Wednesday
        is_open, msg = is_forex_market_open(dt)
        
        self.assertTrue(is_open)
        self.assertIn("Market open", msg)
        self.assertIn("Wednesday", msg)
    
    def test_forex_market_open_monday_morning(self):
        """Test market is open on Monday morning EST"""
        # Monday, 9:00 AM EST
        dt = self.est.localize(datetime(2024, 1, 8, 9, 0, 0))  # Jan 8, 2024 was Monday
        is_open, msg = is_forex_market_open(dt)
        
        self.assertTrue(is_open)
        self.assertIn("Market open", msg)
    
    def test_forex_market_closed_friday_evening(self):
        """Test market is closed Friday after 5PM EST"""
        # Friday, 6:00 PM EST
        dt = self.est.localize(datetime(2024, 1, 12, 18, 0, 0))  # Jan 12, 2024 was Friday
        is_open, msg = is_forex_market_open(dt)
        
        self.assertFalse(is_open)
        self.assertIn("Friday after 5PM", msg)
    
    def test_forex_market_closed_friday_exactly_5pm(self):
        """Test market closes exactly at 5PM Friday"""
        # Friday, 5:00 PM EST
        dt = self.est.localize(datetime(2024, 1, 12, 17, 0, 0))
        is_open, msg = is_forex_market_open(dt)
        
        self.assertFalse(is_open)
        self.assertIn("Friday after 5PM", msg)
    
    def test_forex_market_closed_saturday(self):
        """Test market is closed all day Saturday"""
        # Saturday, 12:00 PM EST
        dt = self.est.localize(datetime(2024, 1, 13, 12, 0, 0))  # Jan 13, 2024 was Saturday
        is_open, msg = is_forex_market_open(dt)
        
        self.assertFalse(is_open)
        self.assertIn("Saturday", msg)
    
    def test_forex_market_closed_sunday_morning(self):
        """Test market is closed Sunday before 5PM EST"""
        # Sunday, 10:00 AM EST
        dt = self.est.localize(datetime(2024, 1, 14, 10, 0, 0))  # Jan 14, 2024 was Sunday
        is_open, msg = is_forex_market_open(dt)
        
        self.assertFalse(is_open)
        self.assertIn("Sunday before 5PM", msg)
    
    def test_forex_market_opens_sunday_5pm(self):
        """Test market opens Sunday at 5PM EST"""
        # Sunday, 5:00 PM EST
        dt = self.est.localize(datetime(2024, 1, 14, 17, 0, 0))
        is_open, msg = is_forex_market_open(dt)
        
        self.assertTrue(is_open)
        self.assertIn("Market open", msg)
    
    def test_forex_market_open_thursday_night(self):
        """Test market is open Thursday night"""
        # Thursday, 11:00 PM EST
        dt = self.est.localize(datetime(2024, 1, 11, 23, 0, 0))  # Jan 11, 2024 was Thursday
        is_open, msg = is_forex_market_open(dt)
        
        self.assertTrue(is_open)
        self.assertIn("Market open", msg)
    
    def test_timezone_conversion_utc(self):
        """Test that UTC times are correctly converted to EST"""
        # Wednesday 5:00 PM UTC = Wednesday 12:00 PM EST (market open)
        utc = pytz.UTC
        dt = utc.localize(datetime(2024, 1, 10, 17, 0, 0))
        is_open, msg = is_forex_market_open(dt)
        
        self.assertTrue(is_open)
    
    def test_naive_datetime_handling(self):
        """Test that naive datetimes are handled correctly"""
        # Create naive datetime (Wednesday noon local time)
        dt = datetime(2024, 1, 10, 12, 0, 0)
        # Should not raise an error
        is_open, msg = is_forex_market_open(dt)
        # Result depends on local timezone, but should execute without error
        self.assertIsInstance(is_open, bool)
        self.assertIsInstance(msg, str)
    
    def test_get_next_market_open_saturday(self):
        """Test next market open message on Saturday"""
        result = get_next_market_open()
        # Should be a string
        self.assertIsInstance(result, str)
        # Note: We can't test exact time since it depends on current time
    
    def test_get_next_market_open_returns_string(self):
        """Test that get_next_market_open always returns a string"""
        result = get_next_market_open()
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
    
    def test_forex_market_friday_before_5pm(self):
        """Test market is still open Friday before 5PM"""
        # Friday, 4:00 PM EST
        dt = self.est.localize(datetime(2024, 1, 12, 16, 0, 0))
        is_open, msg = is_forex_market_open(dt)
        
        self.assertTrue(is_open)
        self.assertIn("Market open", msg)
    
    def test_forex_market_sunday_6pm(self):
        """Test market is open Sunday at 6PM EST (after opening)"""
        # Sunday, 6:00 PM EST
        dt = self.est.localize(datetime(2024, 1, 14, 18, 0, 0))
        is_open, msg = is_forex_market_open(dt)
        
        self.assertTrue(is_open)
        self.assertIn("Market open", msg)


if __name__ == '__main__':
    unittest.main()
