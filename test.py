import asyncio
from mavsdk import System
from mavsdk.mission import MissionItem, MissionPlan
import random
import cv2
import numpy as np
import time

def create_dummy_image(is_violation):
    img = np.zeros((600, 800, 3), dtype=np.uint8)
    img[:] = (34, 139, 34)  # خلفية خضراء
    cv2.rectangle(img, (100, 0), (700, 600), (50, 50, 50), -1)
    # رسم سيارة
    cv2.rectangle(img, (250, 200), (550, 450), (180, 180, 180), -1)
    
    if is_violation:
        cv2.putText(img, "VIOLATION", (250, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
    return img

# --- دالة الرسم والحفظ ---
async def inspect_and_draw(spot_number):
    is_violation = random.random() < 0.7
    img = create_dummy_image(is_violation)
    if is_violation:
        # رسم المربع الأحمر كدليل
        cv2.rectangle(img, (190, 190), (610, 510), (0, 0, 255), 8)
        filename = f"evidence_spot_{spot_number}.jpg"
        cv2.imwrite(filename, img)
        print(f"🚨 Violation detected at spot {spot_number}, image saved.")
    return is_violation

async def main():
    drone = System()
    print("Connecting to drone...")
    await drone.connect(system_address="udp://:14540")

    print("Arming drone...")
    await drone.action.arm()
    await asyncio.sleep(2)

    print("Taking off...")
    await drone.action.takeoff()
    await asyncio.sleep(5)

    home = await anext(drone.telemetry.home())
    # الإحداثيات الأصلية
    lat = home.latitude_deg
    lon = home.longitude_deg
    alt = 5.0

    # --- تعديل المسار ليمشي يميناً (Longitude) بدلاً من فوق المباني ---
    # نستخدم زيادة في الـ Longitude فقط ليمشي بمحاذاة الشارع
    mission_items = [
        # الموقف 1 (إزاحة بسيطة لليمين)
        MissionItem(lat, lon + 10 * 1e-5, alt, 5.0, False, float('nan'), float('nan'), 
                    MissionItem.CameraAction.NONE, float('nan'), float('nan'), 
                    float('nan'), float('nan'), float('nan'), MissionItem.VehicleAction.NONE),
        # الموقف 2 (زيادة لليمين أكثر)
        MissionItem(lat, lon + 20 * 1e-5, alt, 5.0, False, float('nan'), float('nan'), 
                    MissionItem.CameraAction.NONE, float('nan'), float('nan'), 
                    float('nan'), float('nan'), float('nan'), MissionItem.VehicleAction.NONE),
        # الموقف 3
        MissionItem(lat, lon + 30 * 1e-5, alt, 5.0, False, float('nan'), float('nan'), 
                    MissionItem.CameraAction.NONE, float('nan'), float('nan'), 
                    float('nan'), float('nan'), float('nan'), MissionItem.VehicleAction.NONE),
    ]

    mission_plan = MissionPlan(mission_items)
    print("Uploading linear mission path...")
    await drone.mission.upload_mission(mission_plan)
    
    print("Starting mission...")
    await drone.mission.start_mission()

    async for progress in drone.mission.mission_progress():
        print(f"Progress: {progress.current}/{progress.total}")
        if progress.current > 0 and progress.current <= len(mission_items):
            # تنفيذ الفحص والرسم عند كل نقطة
            await inspect_and_draw(progress.current)
            await asyncio.sleep(2)
        
        if progress.current == progress.total:
            break

    print("Mission done. Returning to Launch...")
    await drone.action.return_to_launch()

    if __name__ == "_main_":
     asyncio.run(main())