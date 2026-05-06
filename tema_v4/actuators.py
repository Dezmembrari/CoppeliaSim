import time

def fire_pusher(sim, joint_handle, extend_distance=0.5, hold_time=1.0):
    """Extends the pusher, waits, and retracts it."""
    sim.setJointTargetPosition(joint_handle, extend_distance)
    time.sleep(hold_time)
    sim.setJointTargetPosition(joint_handle, 0.0)