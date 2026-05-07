def fire_pusher(sim, pusher_handle, distance=0.35):
    """Extends the pusher."""
    sim.setJointTargetPosition(pusher_handle, distance)

def retract_pusher(sim, pusher_handle):
    """Retracts the pusher."""
    sim.setJointTargetPosition(pusher_handle, 0.0)

def set_conveyor_speed(sim, handles, speed):
    """Brute-forces the speed command across all known CoppeliaSim formats."""
    if not isinstance(handles, list):
        handles = [handles]
        
    for h in handles:
        # 1. Force the modern __ctrl__ dict (Guarantees Short Belts stop)
        try:
            sim.writeCustomTableData(h, '__ctrl__', {'vel': float(speed)})
        except:
            pass
            
        # 2. Force the Packed Float (Guarantees Main Belts stop)
        try:
            sim.writeCustomDataBlock(h, 'conveyorVelocity', sim.packFloatTable([float(speed)]))
        except:
            pass
            
        # 3. Force the Legacy Strings (Safety Fallback)
        try:
            sim.writeCustomDataBlock(h, 'conveyor_velocity', str(speed).encode('utf-8'))
            sim.writeCustomDataBlock(h, 'velocity', str(speed).encode('utf-8'))
        except:
            pass

def trigger_robot(sim, signal_name, target_basket):
    """Sends a signal to the Lua script attached to the UR3 Robot."""
    # We send the basket destination as a string signal
    sim.setStringSignal(signal_name, target_basket)