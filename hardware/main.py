import network
from time import sleep, ticks_ms, ticks_diff
from picozero import pico_led
import machine
import rp2
import sys
import dht
import urequests


##################

# -- Kill Switch Variables
click_count = 0
button_pressed = False
last_click_time = 0

def check_kill_switch():
    """Checks if the BOOTSEL button was triple-clicked."""
    global click_count, button_pressed, last_click_time
    state = rp2.bootsel_button()
    
    # Reset count if more than 2 seconds since the last click
    if click_count > 0 and ticks_diff(ticks_ms(), last_click_time) > 2000:
        click_count = 0
        
    # Detect button press down
    if state == 1 and not button_pressed:
        click_count += 1
        button_pressed = True
        last_click_time = ticks_ms()
        print(f"Kill switch: {click_count}/3")
        
        if click_count >= 3:
            print("\n !!! KILL SWITCH ACTIVATED! Terminating program. !!!")
            pico_led.off()  # Turn off LED
            sys.exit()      # Stop script 
            
    # Detect button release
    elif state == 0:
        button_pressed = False

def smart_sleep(seconds):
    """Sleeps for X seconds while continuously checking the kill switch."""
    iterations = int(seconds / 0.05)
    for _ in range(iterations):
        check_kill_switch()
        sleep(0.05)
        
################
#
#
sensor = dht.DHT22(machine.Pin(22))
#
#
####################################

# -- Network Variables
        
ssid = "wifi_name"         #Network Name
password = 'wifi_password' #Network Password
SERVER_URL = "http://192.168.1.97:5000/data" #IPv4 changes based on connected network

# 192.168.1.97
# --

def connect():
    # -- Initialize and start the connection
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    wlan.config(pm=0) #battery fix?
    
    wlan.connect(ssid, password)
    
    pico_led.on()
    print('Waiting for connection...')
    
    # 2. Just wait
    while wlan.isconnected() == False:
        print("Not connected.. retrying")
        smart_sleep(5)
     
    #When connected -> print
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    
    # Flash 3 times fast to show successful connection, then stay off
    pico_led.blink(0.1, 0.1, 3) 
    sleep(1) # Wait for the quick blinks to finish
    pico_led.off()
    
    return ip

#######################################




#===== Main Loop



print("Booting up... You have 5 seconds to press STOP!")
sleep(5)



try:
    ip = connect()
    
    sleep(5)
    
    #Start Confirmation
    print(f"Starting sensor readings --- Sending to {SERVER_URL}\n")
    
    #	Get sensor readings
    #	Make a data Package
    #	Send to Flask Server
    #	Close Connection
    while True:
        try:
            # -- Get Sensor Reading
            sensor.measure()
            temp_c = sensor.temperature()
            humidity = sensor.humidity()
            
            print(f"Temp: {temp_c} °C | Humidity: {humidity} %  -  Collected ")
            
            # -- Package the data
            payload = {
                "node_id": "pico_prototype_1_dht11",
                "temperature_c": temp_c,
                "humidity_rh": humidity
            }
            
            # -- Send the POST request to the Flask server
            print("Sending to server...")
           
            pico_led.on() # Turn LED on before sending
            
            response = urequests.post(SERVER_URL, json=payload)
            print(f"Server replied: {response.text}")
            response.close()
            
            pico_led.off() # Turn LED OFF as soon as it finishes
            # -- Always close the response
            response.close()
            
        except OSError as e:
            
            print(f"Failed to read sensor or network Failure: {e}")
            
        # DHT22 sensors need at least 2 seconds between readings
        smart_sleep(4)

except KeyboardInterrupt:
    print("\nProgram stopped.")
    machine.reset()

