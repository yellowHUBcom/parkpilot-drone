import asyncio
from mavsdk import System

async def battery(drone):
    drone=System()
    async for bat in drone.telemetry.battery():
        print(f"labatteryt: "{"b.percent remain*100:"}%)
        
