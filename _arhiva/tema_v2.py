import keyboard
from time import sleep
from coppeliasim_zmqremoteapi_client import RemoteAPIClient


def move_tcp_to_waypoint(sim, tcp_handle, waypoint_handle):
    # Citim pozitia si orientarea Waypoint-ului in raport cu sistemul global
    position = sim.getObjectPosition(waypoint_handle, -1)
    orientation = sim.getObjectOrientation(waypoint_handle, -1)

    # Suprascriem coordonatele TCP-ului cu cele ale Waypoint-ului
    sim.setObjectPosition(tcp_handle, -1, position)
    sim.setObjectOrientation(tcp_handle, -1, orientation)
    



client = RemoteAPIClient()
sim = client.require('sim')
#definirea obiectelor:
sensorHandle = sim.getObject('/visionSensor')

conveyor= sim.getObject('/conveyor')
conveyor_speed = 0.1

baskets= []

for i in range (1,5):
    object_name= f'/Baskets/b{i}'
    handle=sim.getObject(object_name)
    baskets.append(handle)
    
tcp_handle = sim.getObject('/TCP')
safe_handle = sim.getObject('/SAFE')
pick_handle = sim.getObject('/PICK')
    
'''
b1=sim.getObject('/Baskets/b1')
b2=sim.getObject('/Baskets/b2')
b3=sim.getObject('/Baskets/b3')
b4=sim.getObject('/Baskets/b4')
'''
print("ON")
sim.startSimulation()
sleep(0.5) #Stabilizare imagine

print("Testare cinematica: deplasare spre SAFE.")
move_tcp_to_waypoint(sim, tcp_handle, safe_handle)
sleep(2)

print("Testare cinematica: coborare la PICK.")
move_tcp_to_waypoint(sim, tcp_handle, pick_handle)
sleep(2)

print("Testare cinematica: revenire la SAFE.")
move_tcp_to_waypoint(sim, tcp_handle, safe_handle)
sleep(2)

# Pornim banda din Python folosind comanda gasita in scriptul ei intern
sim.setBufferProperty(conveyor, 'customData.__ctrl__', sim.packTable({'vel': conveyor_speed}))


# Calculam suma tuturor numerelor (culorilor) din imaginea capturata in cazul in care nu este detectat niciun obiect
empty_view, resolution= sim.getVisionSensorImg(sensorHandle)
sum_empty=sum(empty_view)


is_running = True
try:
    while is_running:
        current_view, resolution = sim.getVisionSensorImg(sensorHandle)
        sum_current = sum(current_view)
        
        #Calculam diferenta pentru a compara valorile si a detecta efectiv obiectul
        diff= abs(sum_current-sum_empty)
        
        #Toleranta de 10000 
        #RedCub= 1232896
        if diff>1230000 and diff<1240000 :
            print(f"Obiect detectat! (Diferenta culori: {diff})")
            print("Oprim conveior...")
            sim.setBufferProperty(conveyor, 'customData.__ctrl__',sim.packTable({'vel': 0.0}))
            break
            
        #Limitam citirea la 10 ori pe secunda
        sleep(0.1)

        if keyboard.is_pressed('esc'):
            print("Iesire...")
            is_running=False
            break
except KeyboardInterrupt:
    print("Oprit fortat din tastatura.")

sim.stopSimulation()

print("OFF")




