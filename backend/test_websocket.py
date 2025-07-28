#!/usr/bin/env python3
"""
Simple WebSocket test script to verify the connection works
"""
import asyncio
import json
import websockets
import uuid

async def test_websocket():
    # Use a test simulation ID
    test_simulation_id = str(uuid.uuid4())
    uri = f"ws://localhost:8000/api/v1/ws/simulations/{test_simulation_id}"
    
    print(f"Testing WebSocket connection to: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connection successful!")
            
            # Wait for any initial messages
            try:
                initial_message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print(f"📨 Received initial message: {initial_message}")
            except asyncio.TimeoutError:
                print("⏰ No initial message (this might be expected)")
            
            # Keep connection alive for a few seconds
            await asyncio.sleep(2)
            print("✅ Connection remained stable")
            
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_websocket()) 