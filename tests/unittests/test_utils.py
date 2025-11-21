#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

import os
from unittest.mock import patch
from ssk.utils import (
    get_safe_string,
    set_const,
    get_padding,
    get_ago,
    get_timestamp_str,
    parse_time,
    sec_to_str,
    now,
    timestamp_str
)
from ssk.globals.setting_parser import SettingParser


def test_get_safe():
    """Test get_safe_string function"""
    assert get_safe_string("AAA") == "AAA"
    assert get_safe_string("AAA1") == "AAA1"
    assert get_safe_string("111") == "111"
    assert get_safe_string("!111") == ""
    assert get_safe_string("some longer text") == 'some longer text'
    # Special characters without space are rejected
    assert get_safe_string("<script>") == ""


def test_set_const_with_env_var():
    """Test set_const when environment variable is set"""
    with patch.dict(os.environ, {'TEST_VAR': 'env_value'}):
        result = set_const('TEST_VAR', 'default_value')
        assert result == 'env_value'


def test_set_const_with_default():
    """Test set_const when environment variable is not set, using default"""
    with patch.dict(os.environ, {}, clear=True):
        result = set_const('NONEXISTENT_VAR', 'default_value')
        assert result == 'default_value'


def test_set_const_with_type_conversion():
    """Test set_const with type conversion"""
    with patch.dict(os.environ, {}, clear=True):
        # Integer type
        result = set_const('TEST_INT', 42, SettingParser.INT_TYPE)
        assert result == 42
        assert isinstance(result, int)
        
        # Boolean type
        result = set_const('TEST_BOOL', True, SettingParser.BOOL_TYPE)
        assert result is True
        assert isinstance(result, bool)


def test_set_const_no_default_exits():
    """Test set_const exits when no default and env var not set"""
    with patch.dict(os.environ, {}, clear=True):
        with patch('sys.exit') as mock_exit:
            set_const('NONEXISTENT_VAR', None)
            mock_exit.assert_called_once_with(1)


def test_get_padding_basic():
    """Test get_padding with basic strings"""
    assert get_padding("hello", 10) == "hello     "
    assert get_padding("hi", 5) == "hi   "
    assert get_padding("x", 3) == "x  "


def test_get_padding_none():
    """Test get_padding with None input"""
    assert get_padding(None, 5) == "-    "


def test_get_padding_truncation():
    """Test get_padding truncates long strings"""
    long_string = "this is a very long string"
    result = get_padding(long_string, 10)
    assert result == "this is **"
    assert len(result) == 10


def test_get_padding_exact_length():
    """Test get_padding with string matching padding length"""
    result = get_padding("hello", 5)
    assert len(result) == 5


def test_get_ago_now():
    """Test get_ago with 0 or negative seconds"""
    assert get_ago(0) == "now"
    assert get_ago(-5) == "now"


def test_get_ago_seconds():
    """Test get_ago with seconds"""
    assert get_ago(30) == "30 secs ago"
    assert get_ago(45, "earlier") == "45 secs earlier"


def test_get_ago_minutes():
    """Test get_ago with minutes"""
    assert get_ago(120) == "2 mins ago"
    assert get_ago(300) == "5 mins ago"


def test_get_ago_days():
    """Test get_ago with days"""
    result = get_ago(86401)  # Just over 1 day
    assert "days" in result
    result = get_ago(172801)  # Just over 2 days
    assert "days" in result
    result = get_ago(259201, "before")  # Just over 3 days
    assert "days" in result and "before" in result


def test_get_timestamp_str():
    """Test get_timestamp_str returns formatted time"""
    result = get_timestamp_str()
    # Should be in format HH:MM:SS
    assert len(result) == 8
    assert result.count(':') == 2


def test_parse_time_with_colon():
    """Test parse_time with minutes:seconds format"""
    assert parse_time("1:30") == 90.0
    assert parse_time("2:15.5") == 135.5
    assert parse_time("0:45") == 45.0


def test_parse_time_without_colon():
    """Test parse_time with seconds only"""
    assert parse_time("30") == 30.0
    assert parse_time("45.5") == 45.5
    assert parse_time("120") == 120.0


def test_parse_time_invalid(app):
    """Test parse_time with invalid input"""
    with app.app_context():
        result = parse_time("invalid")
        assert result == 0
        
        result = parse_time("1:2:3:4")  # Too many colons
        # Should handle gracefully and return 0 or reasonable value
        assert isinstance(result, float)


def test_sec_to_str_seconds_only():
    """Test sec_to_str with seconds only"""
    result = sec_to_str(30)
    assert "30" in result
    result = sec_to_str(45.5)
    assert "45.5" in result


def test_sec_to_str_with_minutes():
    """Test sec_to_str with minutes"""
    result = sec_to_str(90)  # 1:30
    assert "1:" in result
    assert "30" in result
    
    result = sec_to_str(150)  # 2:30
    assert "2:" in result


def test_sec_to_str_with_hours():
    """Test sec_to_str with hours"""
    result = sec_to_str(3600)  # 1 hour
    assert "60" in result or "1h" in result
    
    result = sec_to_str(3661)  # 1h 1m 1s
    # Should contain hour and minute/second info
    assert ":" in result or "h" in result


def test_sec_to_str_complex():
    """Test sec_to_str with hours, minutes, and seconds"""
    result = sec_to_str(7265)  # 2h 1m 5s
    assert "2h" in result


def test_now_without_time_travel(app):
    """Test now function without time travel"""
    with app.app_context():
        from datetime import datetime
        result = now()
        assert isinstance(result, datetime)
        # Should be close to current time
        assert (datetime.now() - result).total_seconds() < 1


def test_now_with_minutes(app):
    """Test now function with minutes offset"""
    with app.app_context():
        from datetime import datetime, timedelta
        result = now(a_mins=5)
        expected = datetime.now() - timedelta(minutes=5)
        # Should be approximately 5 minutes in the past
        assert abs((expected - result).total_seconds()) < 2


def test_timestamp_str(app):
    """Test timestamp_str function"""
    with app.app_context():
        result = timestamp_str()
        # Should be in format HH:MM:SS
        assert len(result) == 8
        assert result.count(':') == 2
