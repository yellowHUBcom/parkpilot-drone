import asyncio
from mavsdk import System

async def run():
    drone= System()
    print("Connecting to px4......")
    await drone.connect(system_address="udp://:14540")
    print("drone connected")

    print("arming....")
    await drone.action.arm()
    
    #takeoff
    print("taking off....")
    await drone.action.takeoff()
    await asyncio.sleep(10)

    #land
    print("loading.....")
    await drone.action.land()
    print("dront loaded! ")
asyncio.run(run())