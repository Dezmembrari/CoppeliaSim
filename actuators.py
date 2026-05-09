# Cache to store the correct API method for each specific conveyor handle
_conveyor_methods = {}

def fire_pusher(sim, pusher_handle, distance=0.35):
    """Extends the pusher."""
    sim.setJointTargetPosition(pusher_handle, distance)

def retract_pusher(sim, pusher_handle):
    """Retracts the pusher."""
    sim.setJointTargetPosition(pusher_handle, 0.0)

def set_conveyor_speed(sim, handles, speed):
    """
    Sets the conveyor speed using a cached API method to avoid 
    redundant network calls and exception handling.
    """
    global _conveyor_methods
    
    if not isinstance(handles, list):
        handles = [handles]
        
    for h in handles:
        # ==========================================
        # 1. ONE-TIME DISCOVERY & CACHING
        # ==========================================
        if h not in _conveyor_methods:
            method = 'packFloat'  # Safe default
            
            try:
                # Check 1: Modern parameterized conveyors use the __ctrl__ custom table
                try:
                    if sim.readCustomTableData(h, '__ctrl__') is not None:
                        method = 'ctrl'
                except Exception:
                    pass  # API might not exist in older CoppeliaSim versions
                
                # Check 2: If not modern, read the tags to see what the Lua script expects
                if method != 'ctrl':
                    tags = sim.readCustomDataBlockTags(h)
                    if tags:
                        if 'conveyorVelocity' in tags:
                            method = 'packFloat'
                        elif 'conveyor_velocity' in tags or 'velocity' in tags:
                            method = 'legacy'
                            
            except Exception as e:
                print(f"[Actuators] Setup warning for conveyor {h}: {e}")
                
            _conveyor_methods[h] = method
            # Optional: Print to terminal so you know exactly what your factory is running!
            print(f"[Actuators] Conveyor handle {h} cached as type: '{method}'")

        # ==========================================
        # 2. HIGH-PERFORMANCE EXECUTION
        # ==========================================
        method = _conveyor_methods[h]
        
        try:
            if method == 'ctrl':
                sim.writeCustomTableData(h, '__ctrl__', {'vel': float(speed)})
            elif method == 'packFloat':
                sim.writeCustomDataBlock(h, 'conveyorVelocity', sim.packFloatTable([float(speed)]))
            elif method == 'legacy':
                sim.writeCustomDataBlock(h, 'conveyor_velocity', str(speed).encode('utf-8'))
                sim.writeCustomDataBlock(h, 'velocity', str(speed).encode('utf-8'))
        except Exception as e:
            # We catch explicit exceptions to prevent crashing the main loop, 
            # but we no longer swallow critical system exits (like Ctrl+C)
            print(f"[Actuators] Error writing speed to conveyor {h}: {e}")