"""
Comprehensive tests for src.connectors.error_descriptions module
Tests for trade server return codes and runtime error descriptions
"""
import pytest
import MetaTrader5 as mt5
from src.connectors.error_descriptions import (
    trade_server_return_code_description,
    error_description
)


class TestTradeServerReturnCodes:
    """Test suite for trade_server_return_code_description"""
    
    def test_requote(self):
        """Test REQUOTE return code"""
        desc = trade_server_return_code_description(mt5.TRADE_RETCODE_REQUOTE)
        assert desc == "Requote"
    
    def test_reject(self):
        """Test REJECT return code"""
        desc = trade_server_return_code_description(mt5.TRADE_RETCODE_REJECT)
        assert desc == "Request rejected"
    
    def test_cancel(self):
        """Test CANCEL return code"""
        desc = trade_server_return_code_description(mt5.TRADE_RETCODE_CANCEL)
        assert desc == "Request canceled by trader"
    
    def test_placed(self):
        """Test PLACED return code"""
        desc = trade_server_return_code_description(mt5.TRADE_RETCODE_PLACED)
        assert desc == "Order placed"
    
    def test_done(self):
        """Test DONE return code"""
        desc = trade_server_return_code_description(mt5.TRADE_RETCODE_DONE)
        assert desc == "Request completed"
    
    def test_done_partial(self):
        """Test DONE_PARTIAL return code"""
        desc = trade_server_return_code_description(mt5.TRADE_RETCODE_DONE_PARTIAL)
        assert desc == "Only part of the request was completed"
    
    def test_error(self):
        """Test ERROR return code"""
        desc = trade_server_return_code_description(mt5.TRADE_RETCODE_ERROR)
        assert desc == "Request processing error"
    
    def test_timeout(self):
        """Test TIMEOUT return code"""
        desc = trade_server_return_code_description(mt5.TRADE_RETCODE_TIMEOUT)
        assert desc == "Request canceled by timeout"
    
    def test_invalid_request(self):
        """Test INVALID return code"""
        desc = trade_server_return_code_description(mt5.TRADE_RETCODE_INVALID)
        assert desc == "Invalid request"
    
    def test_invalid_volume(self):
        """Test INVALID_VOLUME return code"""
        desc = trade_server_return_code_description(mt5.TRADE_RETCODE_INVALID_VOLUME)
        assert desc == "Invalid volume in the request"
    
    def test_no_money(self):
        """Test NO_MONEY return code"""
        desc = trade_server_return_code_description(mt5.TRADE_RETCODE_NO_MONEY)
        assert desc == "There is not enough money to complete the request"
    
    def test_market_closed(self):
        """Test MARKET_CLOSED return code"""
        desc = trade_server_return_code_description(mt5.TRADE_RETCODE_MARKET_CLOSED)
        assert desc == "Market is closed"
    
    def test_unknown_code(self):
        """Test unknown return code"""
        desc = trade_server_return_code_description(99999)
        assert "Unknown return code: 99999" in desc


class TestErrorDescriptions:
    """Test suite for error_description"""
    
    def test_success(self):
        """Test success code 0"""
        desc = error_description(0)
        assert desc == "The operation completed successfully"
    
    def test_unexpected_error(self):
        """Test unexpected internal error"""
        desc = error_description(1)
        assert desc == "Unexpected internal error"
    
    def test_wrong_parameter(self):
        """Test wrong parameter error"""
        desc = error_description(2)
        assert "Wrong parameter" in desc
    
    def test_not_enough_memory(self):
        """Test not enough memory error"""
        desc = error_description(4)
        assert "Not enough memory" in desc
    
    def test_chart_error(self):
        """Test chart error codes"""
        desc = error_description(4001)
        assert desc == "Wrong chart ID"
        
        desc = error_description(4003)
        assert desc == "Chart not found"
    
    def test_graphical_object_error(self):
        """Test graphical object error codes"""
        desc = error_description(4201)
        assert "graphical object" in desc.lower()
    
    def test_marketinfo_error(self):
        """Test MarketInfo error codes"""
        desc = error_description(4301)
        assert desc == "Unknown symbol"
        
        desc = error_description(4302)
        assert "MarketWatch" in desc
    
    def test_history_error(self):
        """Test history access error codes"""
        desc = error_description(4401)
        assert "history" in desc.lower()
    
    def test_global_variable_error(self):
        """Test global variable error codes"""
        desc = error_description(4501)
        assert "Global variable" in desc
    
    def test_account_error(self):
        """Test account error codes"""
        desc = error_description(4701)
        assert "account property" in desc.lower()
        
        desc = error_description(4704)
        assert desc == "Position not found"
        
        desc = error_description(4705)
        assert desc == "Order not found"
    
    def test_indicator_error(self):
        """Test indicator error codes"""
        desc = error_description(4801)
        assert desc == "Unknown symbol"
        
        desc = error_description(4802)
        assert "Indicator cannot be created" in desc
    
    def test_file_operation_error(self):
        """Test file operation error codes"""
        desc = error_description(5001)
        assert "64 files" in desc
        
        desc = error_description(5004)
        assert "File opening error" in desc
        
        desc = error_description(5019)
        assert desc == "File does not exist"
    
    def test_string_casting_error(self):
        """Test string casting error codes"""
        desc = error_description(5201)
        assert "date" in desc.lower()
        
        desc = error_description(5203)
        assert "time" in desc.lower()
    
    def test_array_operation_error(self):
        """Test array operation error codes"""
        desc = error_description(5401)
        assert "array" in desc.lower()
        
        desc = error_description(5404)
        assert desc == "An array of zero length"
    
    def test_opencl_error(self):
        """Test OpenCL error codes"""
        desc = error_description(5601)
        assert "OpenCL" in desc
        
        desc = error_description(5603)
        assert "OpenCL handle" in desc
    
    def test_user_defined_error(self):
        """Test user-defined error codes (>= 65536)"""
        desc = error_description(65536)
        assert desc == "User error 0"
        
        desc = error_description(65540)
        assert desc == "User error 4"
        
        desc = error_description(70000)
        assert "User error" in desc
    
    def test_unknown_error(self):
        """Test unknown error code (not user-defined)"""
        # Use a code that's not user-defined and not in the dict
        desc = error_description(50000)
        assert "Unknown error: 50000" in desc
    
    def test_various_error_codes(self):
        """Test various specific error codes"""
        # Test specific important codes
        assert "Invalid file name" in error_description(5002)
        assert "Too long file name" in error_description(5003)
        assert "Wrong date in the string" in error_description(5202)
        assert "Too large number" in error_description(5207)
