# SIA-DC Broker Testing Guide

This guide will help you test your FastAPI SIA-DC alarm notification broker using the included simulator.

## Prerequisites

1. Python 3.10 or higher
2. All dependencies installed: `pip install -r app/requirements.txt`

## Quick Start

### 1. Configure the Application

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your settings. For testing locally, minimal config:

```env
LOG_LEVEL=INFO
SIA_HOST=
SIA_PORT=65100
SIA_ACCOUNTS=AAA
SIA_KEYS=
FORWARD_URL=http://localhost:9000/ingest
```

### 2. Start the FastAPI Application

```bash
# Using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Or with reload for development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see output like:
```
INFO:sia-server:Allowing account=AAA (encrypted=False)
INFO:sia-server:SIA-DC TCP server listening on 0.0.0.0:65100
INFO:     Application startup complete.
```

### 3. Verify the Application is Running

Open another terminal and check health:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"ok"}
```

### 4. Run the SIA-DC Simulator

In a new terminal, run the simulator:

```bash
# Run all test scenarios
python sia_simulator.py

# Custom host/port
python sia_simulator.py --host 127.0.0.1 --port 65100 --account AAA

# Interactive mode
python sia_simulator.py --mode interactive
```

## Test Scenarios

The simulator will automatically test these alarm types:

| Code | Zone | Description |
|------|------|-------------|
| BA | 001 | Burglary Alarm |
| FA | 002 | Fire Alarm |
| PA | 003 | Panic Alarm |
| OP | 001 | Opening |
| CL | 001 | Closing |
| TA | 004 | Tamper Alarm |
| CA | 001 | Cancel Alarm |
| BR | 001 | Burglary Restore |
| YK | 000 | Heartbeat/Test |

## Expected Behavior

### 1. Server Logs

When the simulator sends messages, you should see logs in the FastAPI terminal:

```
INFO:sia-server:SIA event: {'account': 'AAA', 'message_type': 'SIA-DCS', 'code': 'BA', 'zone': '001', ...}
INFO:forwarder:Forwarding event to http://localhost:9000/ingest
```

### 2. Simulator Output

```
============================================================
SIA-DC Protocol Simulator
============================================================
Target: 127.0.0.1:65100
Account: AAA
============================================================

📡 Test: Burglary Alarm - Zone 001
✓ Sent: "SIA-DCS"0001100028AAA[#NBA001|20251020151030]
✓ Response: *ACK"0001L0R0A0[]

...
```

## Interactive Testing

Use interactive mode for manual testing:

```bash
python sia_simulator.py --mode interactive
```

Commands:
- `send BA 005` - Send Burglary Alarm for zone 005
- `send FA 012` - Send Fire Alarm for zone 012
- `test` - Run all test scenarios
- `quit` - Exit

## Testing with Encryption

To test AES-encrypted messages:

1. Update `.env`:
```env
SIA_ACCOUNTS=AAA
SIA_KEYS=1234567890123456    # Must be 16, 24, or 32 characters
```

2. Restart the FastAPI app

3. The simulator currently sends unencrypted messages, but you can verify the server correctly rejects mismatched encryption

## Troubleshooting

### Connection Refused

**Problem:** `ConnectionRefusedError: [Errno 61] Connection refused`

**Solution:** Ensure the FastAPI app is running and listening on the correct port

```bash
# Check if port is listening
lsof -i :65100
```

### No Response from Server

**Problem:** Simulator shows "No response received"

**Solution:**
- Check server logs for errors
- Verify account ID matches (case-sensitive)
- Check firewall settings

### Account Not Allowed

**Problem:** Server logs show "Account not found" or similar

**Solution:** Add the account to `SIA_ACCOUNTS` in `.env`:
```env
SIA_ACCOUNTS=AAA,BBB,CCC
```

### Forwarding Fails

**Problem:** Server receives messages but forwarding fails

**Solution:**
- Check `FORWARD_URL` is correct
- Verify the target API is running
- Check network connectivity
- Review authentication headers

## Monitoring Events

### Check Health Endpoint

```bash
curl http://localhost:8000/health
```

### View Received Events (if replay endpoint is available)

```bash
curl http://localhost:8000/replay/events
```

## Common SIA Event Codes

| Code | Description |
|------|-------------|
| BA | Burglary Alarm |
| BR | Burglary Restore |
| CA | Cancel |
| CL | Close |
| FA | Fire Alarm |
| FR | Fire Restore |
| OP | Open |
| PA | Panic Alarm |
| PR | Panic Restore |
| TA | Tamper Alarm |
| TR | Tamper Restore |
| YK | Heartbeat/Periodic Test |

## Advanced Testing

### Multiple Accounts

Test with multiple accounts:

```env
SIA_ACCOUNTS=AAA,BBB,CCC
```

Run simulator for each:
```bash
python sia_simulator.py --account AAA
python sia_simulator.py --account BBB
python sia_simulator.py --account CCC
```

### Load Testing

Send multiple rapid messages:

```python
# Create a custom script based on sia_simulator.py
for i in range(100):
    await sim.send_custom("BA", f"{i:03d}")
    await asyncio.sleep(0.1)
```

### Testing Heartbeat Filtering

Configure heartbeat codes to be ignored:

```env
HEARTBEAT_CODES=YK,RP
```

Send YK events - they should be received but not forwarded.

## Integration Testing

1. Start your downstream API (the system that receives forwarded events)
2. Configure `FORWARD_URL` to point to it
3. Run the simulator
4. Verify events arrive at the downstream system

## Next Steps

- Monitor logs for any errors
- Test with real SIA-DC alarm panels once simulator testing is successful
- Set up proper authentication for production
- Configure appropriate retry and timeout values
- Set up monitoring/alerting for production use
