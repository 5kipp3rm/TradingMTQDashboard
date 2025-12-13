"""
Forex Market Hours Utility
Checks if the Forex market is currently open based on standard trading hours
"""
from datetime import datetime, time
import pytz


def is_forex_market_open(dt: datetime = None) -> tuple[bool, str]:
    """
    Check if Forex market is open
    
    Args:
        dt: Datetime to check (defaults to current time)
        
    Returns:
        tuple: (is_open, message)
        
    Forex Market Hours (EST):
    - Opens: Sunday 5:00 PM EST
    - Closes: Friday 5:00 PM EST
    """
    if dt is None:
        dt = datetime.now()
    
    # Convert to EST (Forex market standard)
    est = pytz.timezone('US/Eastern')
    if dt.tzinfo is None:
        # Assume local timezone
        dt = dt.astimezone(est)
    else:
        dt = dt.astimezone(est)
    
    # Get day of week (0=Monday, 6=Sunday)
    weekday = dt.weekday()
    current_time = dt.time()
    
    # Market closed on Friday 5PM to Sunday 5PM
    if weekday == 4:  # Friday
        if current_time >= time(17, 0):
            return False, "Market closed - Friday after 5PM EST"
    
    elif weekday == 5:  # Saturday
        return False, "Market closed - Saturday (no trading)"
    
    elif weekday == 6:  # Sunday
        if current_time < time(17, 0):
            return False, f"Market closed - Sunday before 5PM EST (opens at 5PM, currently {current_time.strftime('%I:%M %p')})"
    
    # Market is open
    return True, f"Market open - {dt.strftime('%A %I:%M %p EST')}"


def get_next_market_open() -> str:
    """Get human-readable time until market opens"""
    now = datetime.now(pytz.timezone('US/Eastern'))
    weekday = now.weekday()
    current_time = now.time()
    
    if weekday == 4 and current_time >= time(17, 0):
        # Friday after 5PM - opens Sunday 5PM
        return "Sunday at 5:00 PM EST"
    
    elif weekday == 5:  # Saturday
        return "Sunday at 5:00 PM EST"
    
    elif weekday == 6 and current_time < time(17, 0):
        # Sunday before 5PM
        hours_left = 17 - current_time.hour
        mins_left = (60 - current_time.minute) if current_time.minute > 0 else 0
        if mins_left == 60:
            hours_left += 1
            mins_left = 0
        return f"Today at 5:00 PM EST (in {hours_left}h {mins_left}m)"
    
    return "Market is currently open"


if __name__ == "__main__":
    is_open, msg = is_forex_market_open()
    print(f"Status: {msg}")
    print(f"Market Open: {is_open}")
    
    if not is_open:
        print(f"Next Open: {get_next_market_open()}")
