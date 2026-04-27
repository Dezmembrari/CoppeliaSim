import keyboard
from time import sleep
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

# NOUA FUNCTIE: Miscare industriala lina (Liniara)
def move_tcp_smoothly(sim, tcp_handle, waypoint_handle, steps=50, delay=0.01):
    # Citim unde suntem
    start_pos = sim.getObjectPosition(tcp_handle, -1)
    start_ori = sim.getObjectOrientation(tcp_handle, -1)

    # Citim unde vrem sa ajungem
    end_pos = sim.getObjectPosition(waypoint_handle, -1)
    end_ori = sim.getObjectOrientation(waypoint_handle, -1)

    # Mutam "magnetul" pas cu pas (interpolare liniara)
    for i in range(1, steps + 1):
        t = i / steps
        # Calculam pozitia intermediara
        current_pos = [
            start_pos[0] + (end_pos[0] - start_pos[0]) * t,
            start_pos[1] + (end_pos[1] - start_pos[1]) * t,
            start_pos[2] + (end_pos[2] - start_pos[2]) * t
        ]
        # Calculam orientarea intermediara
        current_ori = [
            start_ori[0] + (end_ori[0] - start_ori[0]) * t,
            start_ori[1] + (end_ori[1] - start_ori[1]) * t,
            start_ori[2] + (end_ori[2] - start_ori[2]) * t
        ]
        # Aplicam pasul curent
        sim.setObjectPosition(tcp_handle, -1, current_pos)
        sim.setObjectOrientation(tcp_handle, -1, current_ori)
        sleep(delay) # Mica pauza ca sa dam timp robotului sa se miste


client = RemoteAPIClient()
sim = client.require('sim')

# Definirea obiectelor:
sensorHandle = sim.getObject('/visionSensor')
conveyor = sim.getObject('/conveyor')
conveyor_speed = 0.1

baskets = []
for i in range(1, 5):
    baskets.append(sim.getObject(f'/Baskets/b{i}'))
    
tcp_handle = sim.getObject('/TCP')
safe_handle = sim.getObject('/SAFE')
pick_handle = sim.getObject('/PICK')
place_b1_handle = sim.getObject('/PLACE_b3')
    
print("ON")

# --- MODIFICAREA ORDINII (EVITAM RACE CONDITION) ---
# 1. Ne asiguram ca robotul incepe direct de la SAFE inainte sa apasam PLAY
sim.setObjectPosition(tcp_handle, -1, sim.getObjectPosition(safe_handle, -1))
sim.setObjectOrientation(tcp_handle, -1, sim.getObjectOrientation(safe_handle, -1))

# 2. Acum pornim simularea
sim.startSimulation()
sleep(0.5) # Stabilizare camera (banda INCA sta pe loc)

# 3. Facem poza de calibrare (stim sigur ca e goala acum!)
empty_view, resolution = sim.getVisionSensorImg(sensorHandle)
sum_empty = sum(empty_view)

# 4. Abia acum ii dam comanda benzii sa plece
sim.setBufferProperty(conveyor, 'customData.__ctrl__', sim.packTable({'vel': conveyor_speed}))

is_running = True
try:
    while is_running:
        current_view, resolution = sim.getVisionSensorImg(sensorHandle)
        sum_current = sum(current_view)
        
        diff = abs(sum_current - sum_empty)
        
        # Toleranta 
        if diff > 1230000 and diff < 1240000:
            print(f"Obiect detectat! (Diferenta culori: {diff})")
            print("Oprim conveior...")
            # Oprim banda
            sim.setBufferProperty(conveyor, 'customData.__ctrl__', sim.packTable({'vel': 0.0}))
            
            sleep(0.5) # Asteptam sa se opreasca inertia cubului
            
            # --- MISCARE LINA ROBOT ---
            print("Coboram la PICK...")
            move_tcp_smoothly(sim, tcp_handle, pick_handle, steps=50)
            sleep(1) # Aici se va activa ventuza mai incolo
            
            print("Mutam la PLACE...")
            move_tcp_smoothly(sim, tcp_handle, place_b1_handle, steps=80) # Mai multi pasi ptr distanta mare
            sleep(1) # Aici se dezactiveaza ventuza
            
            print("Revenim la SAFE...")
            move_tcp_smoothly(sim, tcp_handle, safe_handle, steps=50)
            sleep(1)
            
            break # Terminam ciclul pentru moment
            
        sleep(0.1)

        if keyboard.is_pressed('esc'):
            print("Iesire...")
            is_running = False
            break
except KeyboardInterrupt:
    print("Oprit fortat din tastatura.")

sim.stopSimulation()
print("OFF")