#!/usr/bin/env python3
"""
SIA-DC Protocol Simulator
Sends test alarm messages to your FastAPI SIA-DC broker for testing.
"""
import asyncio
import socket
import sys
from datetime import datetime


def calculate_crc(data: str) -> str:
    """Calculate CRC-16-CCITT checksum for SIA message."""
    crc = 0xFFFF
    for char in data:
        crc ^= ord(char) << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
            crc &= 0xFFFF
    return f"{crc:04X}"


class SIASimulator:
    """Simulates a SIA-DC alarm device sending events."""

    def __init__(self, host: str = "127.0.0.1", port: int = 65100, account: str = "AAA"):
        self.host = host
        self.port = port
        self.account = account
        self.sequence = 0

    def build_sia_message(self, code: str, zone: str = "001", partition: str = "1",
                         receiver: str = "1", extra_data: str = "") -> str:
        """
        Build a SIA-DC protocol message.

        Format: <CRC><LENGTH>"SIA-DCS"<SEQ>R<RECEIVER>L<LINE>#<ACCOUNT>[<MESSAGE>]
        Message format: [#<account>|N<ri>/<Event code><message>]<timestamp>

        Based on pysiaalarm regex:
        (?P<crc>[A-Fa-f0-9]{4})(?P<length>[A-Fa-f0-9]{4})"
        (?P<message_type>SIA-DCS)\"(?P<sequence>[0-9]{4})
        (?P<receiver>R[A-Fa-f0-9]{1,6})?(?P<line>L[A-Fa-f0-9]{1,6})
        [#]?(?P<account>[A-Fa-f0-9]{3,16})?[\[](?P<rest>.*)
        """
        self.sequence += 1
        seq = f"{self.sequence:04d}"

        # Build timestamp (_HH:MM:SS,MM-DD-YYYY format, but often omitted in modern systems)
        timestamp = datetime.now().strftime("_%H:%M:%S,%m-%d-%Y")

        # Build message content
        # Simplified SIA content: [#<account>|N<code><zone info>]
        # Zone info can be just text after the code
        zone_text = f"{zone.zfill(3)}" if zone != "000" else ""
        message_content = f"N{code}{zone_text}{extra_data}"
        message_block = f'[#{self.account}|{message_content}]{timestamp}'

        # Build the body (everything after length): "SIA-DCS"<seq>R<receiver>L<line>#<account>[...]
        body = f'"SIA-DCS"{seq}R{receiver}L{partition}#{self.account}{message_block}'

        # Calculate length in hex (length of everything after the length field itself)
        content_for_length = body
        length_hex = f"{len(content_for_length):04X}"

        # Build message without CRC
        message_without_crc = f"{length_hex}{body}"

        # Calculate CRC
        crc = calculate_crc(message_without_crc)

        # Full SIA-DCS message
        full_message = f"{crc}{message_without_crc}"

        return full_message

    async def send_message(self, message: str) -> str:
        """Send a SIA-DC message and wait for response."""
        try:
            reader, writer = await asyncio.open_connection(self.host, self.port)

            # Send message with CRLF terminator
            writer.write(f"{message}\r\n".encode())
            await writer.drain()

            print(f"✓ Sent: {message}")

            # Wait for ACK response
            response = await asyncio.wait_for(reader.read(1024), timeout=5.0)
            response_str = response.decode().strip()

            print(f"✓ Response: {response_str}")

            writer.close()
            await writer.wait_closed()

            return response_str
        except Exception as e:
            print(f"✗ Error: {e}")
            return ""

    async def test_scenarios(self):
        """Run various test scenarios."""

        print("=" * 60)
        print("SIA-DC Protocol Simulator")
        print("=" * 60)
        print(f"Target: {self.host}:{self.port}")
        print(f"Account: {self.account}")
        print("=" * 60)

        scenarios = [
            ("BA", "001", "Burglary Alarm - Zone 001"),
            ("FA", "002", "Fire Alarm - Zone 002"),
            ("PA", "003", "Panic Alarm - Zone 003"),
            ("OP", "001", "Opening - Zone 001"),
            ("CL", "001", "Closing - Zone 001"),
            ("TA", "004", "Tamper Alarm - Zone 004"),
            ("CA", "001", "Cancel Alarm - Zone 001"),
            ("BR", "001", "Burglary Restore - Zone 001"),
            ("YK", "000", "Heartbeat/Test Message"),
        ]

        for code, zone, description in scenarios:
            print(f"\n📡 Test: {description}")
            message = self.build_sia_message(code=code, zone=zone)
            response = await self.send_message(message)

            if not response:
                print("✗ No response received - server may not be running")
                break

            # Small delay between messages
            await asyncio.sleep(1)

        print("\n" + "=" * 60)
        print("Testing complete!")
        print("=" * 60)

    async def send_custom(self, code: str, zone: str = "001"):
        """Send a custom event code."""
        print(f"\n📡 Custom event: Code={code}, Zone={zone}")
        message = self.build_sia_message(code=code, zone=zone)
        await self.send_message(message)


async def interactive_mode(sim: SIASimulator):
    """Interactive mode for manual testing."""
    print("\n" + "=" * 60)
    print("Interactive Mode")
    print("=" * 60)
    print("Commands:")
    print("  send <code> <zone> - Send custom event (e.g., 'send BA 005')")
    print("  test - Run all test scenarios")
    print("  quit - Exit")
    print("=" * 60)

    while True:
        try:
            cmd = input("\n> ").strip()

            if not cmd:
                continue

            if cmd.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break

            if cmd.lower() == "test":
                await sim.test_scenarios()
                continue

            parts = cmd.split()
            if parts[0].lower() == "send" and len(parts) >= 2:
                code = parts[1]
                zone = parts[2] if len(parts) > 2 else "001"
                await sim.send_custom(code, zone)
            else:
                print("Unknown command. Try 'send BA 001' or 'test'")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="SIA-DC Protocol Simulator")
    parser.add_argument("--host", default="127.0.0.1", help="Target host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=65100, help="Target port (default: 65100)")
    parser.add_argument("--account", default="AAA", help="Account ID (default: AAA)")
    parser.add_argument("--mode", choices=["test", "interactive"], default="test",
                       help="Mode: 'test' runs all scenarios, 'interactive' for manual testing")

    args = parser.parse_args()

    sim = SIASimulator(host=args.host, port=args.port, account=args.account)

    if args.mode == "test":
        await sim.test_scenarios()
    else:
        await interactive_mode(sim)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)
