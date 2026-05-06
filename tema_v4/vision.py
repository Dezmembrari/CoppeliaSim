def get_dominant_color(sim, sensor_handle):
    """Reads the camera and checks the center pixel for Red or Blue."""
    try:
        img, res = sim.getVisionSensorImg(sensor_handle)
        if not img or len(img) == 0:
            return "NONE"

        center_x = res[0] // 2
        center_y = res[1] // 2
        pixel_index = (center_y * res[0] + center_x) * 3

        r = img[pixel_index]
        g = img[pixel_index + 1]
        b = img[pixel_index + 2]

        if r > 150 and g < 100 and b < 100:
            return "RED"
        if b > 150 and r < 100 and g < 100:
            return "BLUE"
            
    except Exception:
        # Failsafe if the camera drops a frame
        pass
        
    return "NONE"