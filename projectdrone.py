# cd ~/PX4-Autopilot
#  export PX4_HOME_LAT=24.87471396502799
#  export PX4_HOME_LON=46.63820766785802
# export PX4_HOME_ALT=650
# make px4_sitl jmavsim
#24.87471396502799, 46.63820766785802

import asyncio
from mavsdk import System
import logging
from mavsdk.mission import MissionItem, MissionPlan
import random, cv2, numpy as np, tkinter as tk
from datetime import datetime  
import pyttsx3 

logging.getLogger('mavsdk').setLevel(logging.ERROR)
engine = pyttsx3.init()

async def create_mission(lat, lon):
    return MissionItem(
        lat,
        lon,
        10.0,         
        5.0,         
        False,         
        float('nan'), 
        float('nan'), 
        MissionItem.CameraAction.NONE, 
        2.5,
        float('nan'), 
        float('nan'), 
        float('nan'),
        float('nan'), 
        MissionItem.VehicleAction.NONE    )

def create_ui(drone):
    root = tk.Tk()
    root.title(" PARKPILOT MONITOR ")
    root.geometry("250x180")
    root.attributes("-topmost", True)
    
    label = tk.Label(root, text="Parking Violations: 0", font=("Arial", 15), fg="red")
    label.pack(pady=10)
    
    btn = tk.Button(root, text="Emergency Landing", bg="red", fg="white", 
                    command=lambda: asyncio.ensure_future(drone.action.return_to_launch()))
    btn.pack(pady=10)
    
    return root, label

def create_parkpilot_image(is_violation, spot_num, lat, lon):
    img = np.zeros((600, 800, 3), dtype=np.uint8) 
    img[:] = (34, 139, 34) # Green grass
    
    # Asphalt and Parking lines
    cv2.rectangle(img, (100, 0), (700, 600), (50, 50, 50), -1) 
    cv2.line(img, (150, 0), (150, 600), (255, 255, 255), 3)
    cv2.line(img, (650, 0), (650, 600), (255, 255, 255), 3)

    # Gray Car Body
    cv2.rectangle(img, (250, 200), (550, 450), (180, 180, 180), -1) 
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    cv2.putText(img, f"Time: {timestamp}", (200, 30), font, 0.5, (255, 255, 255), 2)
    cv2.putText(img, f"LAT: {lat:.6f}", (200, 550), font, 0.6, (255, 255, 0), 2)
    cv2.putText(img, f"LON: {lon:.6f}", (200, 580), font, 0.6, (255, 255, 0), 2)

    if is_violation:
        cv2.rectangle(img, (300, 250), (500, 400), (0, 0, 255), 3) 
        cv2.putText(img, f"VIOLATION: SPOT {spot_num}", (180, 100), font, 0.8, (0, 0, 255), 3)
    else:
        cv2.putText(img, f"PASS: SPOT {spot_num}", (250, 100), font, 1.2, (0, 255, 0), 3)
        
    return img

async def battery_checker(drone: System):
    async for battery in drone.telemetry.battery():
        if battery.remaining_percent < 20:
            print("Battery low! Returning to launch...")
            await drone.action.return_to_launch()
            break
        
    print("="*30)

async def main():
    drone = System()
    await drone.connect(system_address="udp://:14540")
    
    root, label = create_ui(drone)
    violation_count = 0

    print("="*30)
    print("Connecting to ParkPilot drone...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("="*30)
            print("ParkPilot is Connected!")
            battery_task = asyncio.create_task(battery_checker(drone))
            break
    print("="*30)
    print("Waiting for GPS...")
    print("="*30)

    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            break

    print("Taking off...")
    await drone.action.arm()
    await drone.action.takeoff()
    await asyncio.sleep(10)

    home = await anext(drone.telemetry.home())
    h_lat, h_lon = home.latitude_deg, home.longitude_deg
    
    items = []
    items.append(await create_mission(h_lat, h_lon - 15*1e-5))
    items.append(await create_mission(h_lat + 10*1e-5, h_lon - 10*1e-5))
    items.append(await create_mission(h_lat + 20*1e-5, h_lon - 5*1e-5))
    items.append(await create_mission(h_lat + 30*1e-5, h_lon - 3*1e-5))
    items.append(await create_mission(h_lat + 30*1e-5, h_lon - 2*1e-5))
    items.append(await create_mission(h_lat, h_lon - 15*1e-5))
    items.append(await create_mission(h_lat, h_lon))

    print("="*30)
    print("Uploading mission to ParkPilot..")
    await drone.mission.upload_mission(MissionPlan(items))
    await drone.mission.start_mission()

    async for progress in drone.mission.mission_progress():
        root.update() 
        
        if 0 < progress.current <= len(items):
            async for pos in drone.telemetry.position():
                curr_lat, curr_lon = pos.latitude_deg, pos.longitude_deg
                break

            is_v = random.random() < 0.7
            
            if is_v:
                violation_count += 1
                label.config(text=f"Violations: {violation_count}")
                engine.say(f"Violation detected at spot {progress.current}")
                engine.runAndWait()
            
            img = create_parkpilot_image(is_v, progress.current, curr_lat, curr_lon)
            
            filename = f"spot_{progress.current}.jpg"
            cv2.imwrite(filename, img)
            
            await asyncio.sleep(5)
            root.update()
            
        if progress.current == progress.total: 
            break
    print("="*30)
    print("parkpilot Mission complete! all violation was sent to Facility Management and Traffic Police System")
    print("="*30)
    print("Returning ...")
    print("="*30)

    engine.say(f"all violation was sent to Facility Management and Traffic Police System {progress.current}")
    engine.runAndWait()
    await drone.action.return_to_launch()
    root.mainloop() 

    battery_task.cancel()
if __name__ == "__main__":
    asyncio.run(main())