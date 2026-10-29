import random


def get_readings(self):
        
        # Simulate reading update
        self.current_temp += random(-1.5, 1.5)
        self.current_humidity += random(-1.5, 1.5)
        
        #
        #
        # DHT11 read goes here
        #
        #
        
        # Make sure humidity stays within physical 0-100% limits
        
        if(self.current_humidity < 0.00 or self.current_humidity > 100.00):
            self.current_humidity = 20.00
        

class MockSensorNode:


    def __init__(self, 
                 
                 node_id: str = "pico_prototype_1",
                 zone: str = "zone1", 
                 area: str = "upper_plants"
                 
                 ):

        
        self.node_id          = node_id
        self.zone             = zone
        self.area             = area
        
        self.current_temp     = 22.0   # °C
        self.current_humidity = 60.0   # %

    def get_readings(self) -> dict:
        # Small random drift each reading — feels like a real sensor
        self.current_temp     += random.uniform(-0.5, 0.5)
        self.current_humidity += random.uniform(-1.0, 1.0)

        # Keep values in physically plausible ranges
        self.current_temp     = max(10.0, min(40.0, self.current_temp))
        self.current_humidity = max(20.0, min(95.0, self.current_humidity))

        return {
            "node_id":       self.node_id,
            "zone":          self.zone,
            "area":          self.area,
            "temperature_c": round(self.current_temp, 2),
            "humidity_rh":   round(self.current_humidity, 2),
            "status":        "ok_simulated",
        }