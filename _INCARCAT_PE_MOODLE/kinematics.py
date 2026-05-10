import math

class KinematicsEngine:
    def __init__(self, d1, a2, a3, elbow_config=-1):
        self.d1 = d1
        self.a2 = a2
        self.a3 = a3
        self.elbow_config = elbow_config

    def forward(self, j2, j3):
        # Naturally allows negative reach (backward leaning arm)
        reach = self.a2 * math.sin(j2) + self.a3 * math.sin(j2 + j3)
        height = self.d1 + self.a2 * math.cos(j2) + self.a3 * math.cos(j2 + j3)
        return reach, height

    def inverse(self, reach, height, orient_sum):
        h = height - self.d1
        d_sq = reach**2 + h**2
        d = math.sqrt(d_sq)

        if d > (self.a2 + self.a3) or d < abs(self.a2 - self.a3):
            return None

        cos_j3 = (d_sq - self.a2**2 - self.a3**2) / (2 * self.a2 * self.a3)
        j3 = self.elbow_config * math.acos(max(-1.0, min(1.0, cos_j3)))

        # atan2 perfectly handles negative reach by returning negative angles
        alpha = math.atan2(reach, h)
        beta = math.atan2(self.a3 * math.sin(j3), self.a2 + self.a3 * math.cos(j3))
        j2 = alpha - beta
        
        j4 = orient_sum - (j2 + j3)
        return j2, j3, j4