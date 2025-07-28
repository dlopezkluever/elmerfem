"""
Quick WebSocket test - checks if the endpoint is accessible

Usage: python test_websocket_quick.py
"""

import asyncio
import websockets
import json
import uuid


async def quick_test():
    """Quick test to verify WebSocket endpoint is accessible"""
    
    # Generate a fake job ID
    fake_job_id = str(uuid.uuid4())
    uri = f"ws://localhost:8000/api/v1/ws/simulations/{fake_job_id}"
    
    print(f"Testing WebSocket endpoint: {uri}")
    print("-" * 60)
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connection established!")
            
            # The connection should close immediately with error 4004 (not found)
            # since we're using a fake job ID
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print(f"Received message: {message}")
            except websockets.exceptions.ConnectionClosed as e:
                if e.code == 4004:
                    print("✅ Server correctly rejected non-existent job ID (code 4004)")
                else:
                    print(f"❌ Unexpected close code: {e.code} - {e.reason}")
            except asyncio.TimeoutError:
                print("❌ No response received (timeout)")
                
    except ConnectionRefusedError:
        print("❌ Connection refused - is the backend server running?")
        print("   Start it with: cd backend && python -m uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")


async def test_with_invalid_uuid():
    """Test with invalid UUID format"""
    uri = f"ws://localhost:8000/api/v1/ws/simulations/not-a-valid-uuid"
    
    print(f"\nTesting with invalid UUID format...")
    
    try:
        async with websockets.connect(uri) as websocket:
            try:
                await asyncio.wait_for(websocket.recv(), timeout=2.0)
            except websockets.exceptions.ConnectionClosed as e:
                if e.code == 4003:
                    print("✅ Server correctly rejected invalid UUID format (code 4003)")
                else:
                    print(f"❌ Unexpected close code: {e.code} - {e.reason}")
            except asyncio.TimeoutError:
                print("❌ No response received (timeout)")
                
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")


async def test_endpoint_exists():
    """Test if the WebSocket endpoint exists in the routing"""
    import httpx
    
    print(f"\nChecking if WebSocket endpoint is registered...")
    
    try:
        # Try to access the HTTP version (should fail but indicate endpoint exists)
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/v1/ws/simulations/test")
            
            # We expect this to fail since it's a WebSocket endpoint
            if response.status_code == 400 or "WebSocket" in response.text:
                print("✅ WebSocket endpoint is registered in the application")
            else:
                print(f"❓ Unexpected response: {response.status_code}")
                
    except httpx.ConnectError:
        print("❌ Cannot connect to backend server")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("Quick WebSocket Test")
    print("=" * 60)
    
    # Run tests
    asyncio.run(quick_test())
    asyncio.run(test_with_invalid_uuid())
    asyncio.run(test_endpoint_exists())
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("- If all tests show ✅, the WebSocket endpoint is working correctly")
    print("- If you see connection refused, start the backend server first")
    print("- The endpoint should reject non-existent jobs with code 4004")
    print("- The endpoint should reject invalid UUIDs with code 4003")
    print("=" * 60) 