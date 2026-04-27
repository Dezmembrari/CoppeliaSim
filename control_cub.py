import keyboard
from time import sleep
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

client = RemoteAPIClient()
sim = client.require('sim')

cub = sim.getObject('/Cuboid')  # Numele obiectului din scena. Din CoppeliaSim trebuie debifat Body is dynamic

step= 0.05

print("Controleaza cubul cu W/A/S/D si Q/E. ESC pentru iesire")

try:
    while True:
        pos= sim.getObjectPosition(cub, sim.handle_world) #returneaza pozitia in raport cu sistemul de coordonate ABSOLUT X=Y=Z=0. "sim.handle_world" - se poate inlocui cu valoarea "-1"
        # Axa Y inainte/inapoi
        if keyboard.is_pressed('w'):
            pos[1] += step
        if keyboard.is_pressed('s'):
            pos[1] -= step
        # Axa X inainte/inapoi
        if keyboard.is_pressed('a'):
            pos[0] -= step
        if keyboard.is_pressed('d'):
            pos[0] += step
        # Axa Z sus/jos
        if keyboard.is_pressed('q'):
            pos[2] += step
        if keyboard.is_pressed('e'):
            pos[2] -= step
                
        sim.setObjectPosition(cub, -1, pos)
        
        if keyboard.is_pressed('esc'):
            print("Iesire...")
            break
            
        sleep(0.05)
except KeyboardInterrupt:
    print("Oprit.")

       
        