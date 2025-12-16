//+------------------------------------------------------------------+
//|                                           MT4 Bridge Server      |
//|                                       HTTP Server for Python     |
//|                                                                  |
//| Description: HTTP server that exposes MT4 functionality to      |
//|              external applications via REST API                  |
//|                                                                  |
//| Installation:                                                    |
//|   1. Copy to MT4/MQL4/Experts/                                  |
//|   2. Compile in MetaEditor (F7)                                  |
//|   3. Attach to any chart                                         |
//|   4. Enable AutoTrading                                          |
//|                                                                  |
//| Requirements:                                                    |
//|   - MT4 build 600+ (for HTTP server support)                    |
//|   - DLL imports must be allowed in EA settings                   |
//|                                                                  |
//+------------------------------------------------------------------+

#property copyright "TradingMTQ"
#property link      "https://github.com/yourusername/tradingmtq"
#property version   "1.00"
#property strict

// EA Input Parameters
input int ServerPort = 8080;                    // HTTP Server Port
input string AllowedIPs = "127.0.0.1";         // Allowed IP addresses (comma separated)
input bool EnableAutoTrading = true;            // Enable auto trading
input int MagicNumber = 20241215;              // Magic number for orders
input string LogLevel = "INFO";                // Log level (DEBUG, INFO, WARN, ERROR)

// Global variables
int g_socket = -1;
datetime g_last_heartbeat;
bool g_is_running = false;

//+------------------------------------------------------------------+
//| Expert initialization function                                     |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("=== MT4 Bridge Server Initializing ===");
    Print("Port: ", ServerPort);
    Print("Allowed IPs: ", AllowedIPs);
    Print("AutoTrading: ", EnableAutoTrading);

    // Check if AutoTrading is enabled
    if(!IsTradeAllowed())
    {
        Alert("AutoTrading is disabled! Enable it in EA settings or toolbar.");
        return INIT_FAILED;
    }

    // Initialize server
    if(!StartServer())
    {
        Alert("Failed to start HTTP server on port ", ServerPort);
        return INIT_FAILED;
    }

    g_is_running = true;
    g_last_heartbeat = TimeCurrent();

    Print("=== MT4 Bridge Server Started ===");
    Print("Listening on http://localhost:", ServerPort);
    Print("Send test request: http://localhost:", ServerPort, "/ping");

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                   |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("=== MT4 Bridge Server Shutting Down ===");
    g_is_running = false;

    if(g_socket >= 0)
    {
        SocketClose(g_socket);
        g_socket = -1;
    }

    Print("Server stopped. Reason: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                               |
//+------------------------------------------------------------------+
void OnTick()
{
    // Process incoming HTTP requests
    ProcessRequests();

    // Heartbeat every 30 seconds
    if(TimeCurrent() - g_last_heartbeat > 30)
    {
        g_last_heartbeat = TimeCurrent();
        if(LogLevel == "DEBUG")
            Print("Heartbeat - Server running, waiting for requests...");
    }
}

//+------------------------------------------------------------------+
//| Start HTTP Server                                                  |
//+------------------------------------------------------------------+
bool StartServer()
{
    // Note: MQL4 doesn't have native HTTP server support
    // This is a simplified implementation using socket communication
    // For production, consider using a more robust solution

    // Create socket
    g_socket = SocketCreate();

    if(g_socket < 0)
    {
        Print("ERROR: Failed to create socket");
        return false;
    }

    // Bind to port
    if(!SocketBind(g_socket, ServerPort))
    {
        Print("ERROR: Failed to bind to port ", ServerPort);
        SocketClose(g_socket);
        g_socket = -1;
        return false;
    }

    // Listen for connections
    if(!SocketListen(g_socket))
    {
        Print("ERROR: Failed to listen on socket");
        SocketClose(g_socket);
        g_socket = -1;
        return false;
    }

    return true;
}

//+------------------------------------------------------------------+
//| Process HTTP Requests                                              |
//+------------------------------------------------------------------+
void ProcessRequests()
{
    if(g_socket < 0)
        return;

    // Accept connection
    int client_socket = SocketAccept(g_socket);

    if(client_socket < 0)
        return;  // No pending connections

    // Read request
    string request = "";
    char buffer[];
    ArrayResize(buffer, 4096);

    int bytes_read = SocketRead(client_socket, buffer, 4096, 100);

    if(bytes_read > 0)
    {
        request = CharArrayToString(buffer, 0, bytes_read);

        if(LogLevel == "DEBUG")
            Print("Request received: ", StringSubstr(request, 0, 100), "...");

        // Parse and handle request
        string response = HandleRequest(request);

        // Send response
        SendHttpResponse(client_socket, response);
    }

    // Close client socket
    SocketClose(client_socket);
}

//+------------------------------------------------------------------+
//| Handle HTTP Request                                                |
//+------------------------------------------------------------------+
string HandleRequest(string request)
{
    // Parse HTTP method and path
    string lines[];
    int num_lines = StringSplit(request, '\n', lines);

    if(num_lines == 0)
        return CreateErrorResponse(400, "Invalid request");

    string request_line = lines[0];
    string parts[];
    StringSplit(request_line, ' ', parts);

    if(ArraySize(parts) < 2)
        return CreateErrorResponse(400, "Invalid request line");

    string method = parts[0];
    string path = parts[1];

    if(LogLevel == "DEBUG")
        Print("Method: ", method, ", Path: ", path);

    // Route request
    if(method == "GET" && path == "/ping")
        return HandlePing();
    else if(method == "GET" && path == "/status")
        return HandleStatus();
    else if(method == "GET" && path == "/account/info")
        return HandleAccountInfo();
    else if(method == "GET" && StringFind(path, "/symbols") == 0)
        return HandleSymbols(path);
    else if(method == "GET" && StringFind(path, "/ticks/") == 0)
        return HandleTick(path);
    else if(method == "GET" && StringFind(path, "/bars/") == 0)
        return HandleBars(path);
    else if(method == "GET" && path == "/positions")
        return HandleGetPositions();
    else if(method == "POST" && path == "/orders")
        return HandleSendOrder(request);
    else if(method == "DELETE" && StringFind(path, "/positions/") == 0)
        return HandleClosePosition(path);
    else if(method == "PUT" && StringFind(path, "/positions/") == 0)
        return HandleModifyPosition(path, request);
    else
        return CreateErrorResponse(404, "Endpoint not found");
}

//+------------------------------------------------------------------+
//| Handle: GET /ping                                                  |
//+------------------------------------------------------------------+
string HandlePing()
{
    return CreateJsonResponse(true, "pong", "");
}

//+------------------------------------------------------------------+
//| Handle: GET /status                                                |
//+------------------------------------------------------------------+
string HandleStatus()
{
    string data = StringFormat(
        "{\"is_connected\": %s, \"account\": {\"login\": %d, \"server\": \"%s\", \"balance\": %.2f}}",
        IsConnected() ? "true" : "false",
        AccountNumber(),
        AccountServer(),
        AccountBalance()
    );

    return CreateJsonResponse(true, "Status retrieved", data);
}

//+------------------------------------------------------------------+
//| Handle: GET /account/info                                          |
//+------------------------------------------------------------------+
string HandleAccountInfo()
{
    string data = StringFormat(
        "{\"login\": %d, \"server\": \"%s\", \"name\": \"%s\", "
        "\"balance\": %.2f, \"equity\": %.2f, \"margin\": %.2f, "
        "\"margin_free\": %.2f, \"margin_level\": %.2f, \"profit\": %.2f, "
        "\"currency\": \"%s\", \"leverage\": %d, \"company\": \"%s\"}",
        AccountNumber(),
        AccountServer(),
        AccountName(),
        AccountBalance(),
        AccountEquity(),
        AccountMargin(),
        AccountFreeMargin(),
        AccountMargin() > 0 ? (AccountEquity() / AccountMargin() * 100) : 0,
        AccountProfit(),
        AccountCurrency(),
        AccountLeverage(),
        AccountCompany()
    );

    return CreateJsonResponse(true, "Account info retrieved", data);
}

//+------------------------------------------------------------------+
//| Handle: GET /symbols                                               |
//+------------------------------------------------------------------+
string HandleSymbols(string path)
{
    string symbols = "[";
    int total = SymbolsTotal(true);

    for(int i = 0; i < total; i++)
    {
        string symbol = SymbolName(i, true);
        if(i > 0) symbols += ", ";
        symbols += "\"" + symbol + "\"";
    }

    symbols += "]";

    string data = "{\"symbols\": " + symbols + "}";
    return CreateJsonResponse(true, "Symbols retrieved", data);
}

//+------------------------------------------------------------------+
//| Handle: GET /ticks/{symbol}                                        |
//+------------------------------------------------------------------+
string HandleTick(string path)
{
    string symbol = StringSubstr(path, 7);  // Remove "/ticks/"

    if(!SymbolSelect(symbol, true))
        return CreateErrorResponse(404, "Symbol not found");

    double bid = MarketInfo(symbol, MODE_BID);
    double ask = MarketInfo(symbol, MODE_ASK);
    datetime time = TimeCurrent();

    string data = StringFormat(
        "{\"symbol\": \"%s\", \"time\": \"%s\", \"bid\": %.5f, \"ask\": %.5f, \"last\": %.5f}",
        symbol,
        TimeToString(time, TIME_DATE|TIME_SECONDS),
        bid,
        ask,
        bid
    );

    return CreateJsonResponse(true, "Tick retrieved", data);
}

//+------------------------------------------------------------------+
//| Handle: GET /bars/{symbol}                                         |
//+------------------------------------------------------------------+
string HandleBars(string path)
{
    // Parse: /bars/{symbol}?timeframe=H1&count=100
    string symbol = StringSubstr(path, 6);
    int question_mark = StringFind(symbol, "?");

    if(question_mark > 0)
        symbol = StringSubstr(symbol, 0, question_mark);

    // TODO: Parse query parameters for timeframe and count
    int timeframe = PERIOD_H1;
    int count = 100;

    string bars = "[";

    for(int i = 0; i < count; i++)
    {
        datetime time = iTime(symbol, timeframe, i);
        double open = iOpen(symbol, timeframe, i);
        double high = iHigh(symbol, timeframe, i);
        double low = iLow(symbol, timeframe, i);
        double close = iClose(symbol, timeframe, i);
        long volume = iVolume(symbol, timeframe, i);

        if(i > 0) bars += ", ";

        bars += StringFormat(
            "{\"time\": \"%s\", \"open\": %.5f, \"high\": %.5f, \"low\": %.5f, "
            "\"close\": %.5f, \"tick_volume\": %d}",
            TimeToString(time, TIME_DATE|TIME_SECONDS),
            open, high, low, close, volume
        );
    }

    bars += "]";

    string data = "{\"bars\": " + bars + "}";
    return CreateJsonResponse(true, "Bars retrieved", data);
}

//+------------------------------------------------------------------+
//| Handle: GET /positions                                             |
//+------------------------------------------------------------------+
string HandleGetPositions()
{
    string positions = "[";
    int total = OrdersTotal();
    int count = 0;

    for(int i = 0; i < total; i++)
    {
        if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
            continue;

        if(OrderType() > OP_SELL)  // Skip pending orders
            continue;

        if(count > 0) positions += ", ";

        positions += StringFormat(
            "{\"ticket\": %d, \"symbol\": \"%s\", \"type\": \"%s\", "
            "\"volume\": %.2f, \"price_open\": %.5f, \"price_current\": %.5f, "
            "\"sl\": %.5f, \"tp\": %.5f, \"profit\": %.2f, \"swap\": %.2f, "
            "\"commission\": %.2f, \"magic\": %d, \"comment\": \"%s\", "
            "\"time\": \"%s\"}",
            OrderTicket(),
            OrderSymbol(),
            OrderType() == OP_BUY ? "BUY" : "SELL",
            OrderLots(),
            OrderOpenPrice(),
            OrderClosePrice() == 0 ? (OrderType() == OP_BUY ? MarketInfo(OrderSymbol(), MODE_BID) : MarketInfo(OrderSymbol(), MODE_ASK)) : OrderClosePrice(),
            OrderStopLoss(),
            OrderTakeProfit(),
            OrderProfit(),
            OrderSwap(),
            OrderCommission(),
            OrderMagicNumber(),
            OrderComment(),
            TimeToString(OrderOpenTime(), TIME_DATE|TIME_SECONDS)
        );

        count++;
    }

    positions += "]";

    string data = "{\"positions\": " + positions + "}";
    return CreateJsonResponse(true, "Positions retrieved", data);
}

//+------------------------------------------------------------------+
//| Handle: POST /orders                                               |
//+------------------------------------------------------------------+
string HandleSendOrder(string request)
{
    // TODO: Parse JSON body from request
    // For now, return not implemented
    return CreateErrorResponse(501, "Order sending not yet implemented in EA. Please implement JSON parsing.");
}

//+------------------------------------------------------------------+
//| Handle: DELETE /positions/{ticket}                                 |
//+------------------------------------------------------------------+
string HandleClosePosition(string path)
{
    string ticket_str = StringSubstr(path, 11);  // Remove "/positions/"
    int ticket = (int)StringToInteger(ticket_str);

    if(!OrderSelect(ticket, SELECT_BY_TICKET))
        return CreateErrorResponse(404, "Position not found");

    bool success = false;

    if(OrderType() == OP_BUY)
        success = OrderClose(ticket, OrderLots(), MarketInfo(OrderSymbol(), MODE_BID), 3);
    else if(OrderType() == OP_SELL)
        success = OrderClose(ticket, OrderLots(), MarketInfo(OrderSymbol(), MODE_ASK), 3);

    if(success)
        return CreateJsonResponse(true, "Position closed", "{}");
    else
        return CreateErrorResponse(500, "Failed to close position: " + IntegerToString(GetLastError()));
}

//+------------------------------------------------------------------+
//| Handle: PUT /positions/{ticket}                                    |
//+------------------------------------------------------------------+
string HandleModifyPosition(string path, string request)
{
    // TODO: Parse ticket and JSON body
    return CreateErrorResponse(501, "Position modification not yet implemented in EA");
}

//+------------------------------------------------------------------+
//| Create JSON Response                                               |
//+------------------------------------------------------------------+
string CreateJsonResponse(bool success, string message, string data)
{
    string json = StringFormat(
        "{\"success\": %s, \"message\": \"%s\"%s}",
        success ? "true" : "false",
        message,
        data != "" ? ", \"data\": " + data : ""
    );

    return CreateHttpResponse(200, json);
}

//+------------------------------------------------------------------+
//| Create Error Response                                              |
//+------------------------------------------------------------------+
string CreateErrorResponse(int code, string message)
{
    string json = StringFormat(
        "{\"success\": false, \"error\": %d, \"message\": \"%s\"}",
        code,
        message
    );

    return CreateHttpResponse(code, json);
}

//+------------------------------------------------------------------+
//| Create HTTP Response                                               |
//+------------------------------------------------------------------+
string CreateHttpResponse(int status_code, string body)
{
    string status_text = "OK";

    if(status_code == 400) status_text = "Bad Request";
    else if(status_code == 404) status_text = "Not Found";
    else if(status_code == 500) status_text = "Internal Server Error";
    else if(status_code == 501) status_text = "Not Implemented";

    string response = StringFormat(
        "HTTP/1.1 %d %s\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: %d\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Connection: close\r\n"
        "\r\n"
        "%s",
        status_code,
        status_text,
        StringLen(body),
        body
    );

    return response;
}

//+------------------------------------------------------------------+
//| Send HTTP Response                                                 |
//+------------------------------------------------------------------+
void SendHttpResponse(int socket, string response)
{
    uchar data[];
    StringToCharArray(response, data);

    SocketSend(socket, data, ArraySize(data));
}
//+------------------------------------------------------------------+
