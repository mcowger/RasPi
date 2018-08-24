
#!/usr/bin/python
from sense_hat import SenseHat
import datetime, time, subprocess, re, os
#account for temp that the SenseHat has next to motherboard: https://github.com/initialstate/wunderground-sensehat/wiki/Part-3.-Sense-HAT-Temperature-Correction



while True:
#get date time
    datetimestamp = datetime.datetime.now()

#get cpu temp to offset the Pi SenseHat and get closer to real temp:
    tFile = open('/sys/class/thermal/thermal_zone0/temp')
    cpuTemp = float(tFile.read())
    cpuTempC = cpuTemp/1000
    cpuTempC = round(cpuTempC, 3)
    cpuTempF = ((cpuTempC/5)*9)+32
    cpuTempF = round(cpuTempF, 3)
    print("RasPi_cpuTempC: %s C" % cpuTempC)
    print("RasPi_cpuTempF: %s F" % cpuTempF)


#get SenseHat CPU reading 
    ap = SenseHat()
    SHtempC = ap.get_temperature()
    SHtempC = round(SHtempC, 3)
    SHtempF = ((SHtempC/5)*9)+32
    SHtempF = round(SHtempF, 3)
    Humidity = ap.get_humidity()
    Humidity = round(Humidity, 3)
    print("SenseHat_TempC: %s C" % SHtempC)
    print("SenseHat_TempF: %s F" % SHtempF) # Show temp on console
    print("Humidity: %s" % Humidity)
    ap.set_rotation(180) # Set LED matrix to scroll from right to left w/power plugin up top

#get serial number:
    serial = subprocess.check_output("sed -n 's/^Serial\s*: 0*//p' /proc/cpuinfo", shell=True)
    serial = serial.decode()
    serial.replace("\n","")
    print("Serial# is: %s" % serial)
    
#get hardware number:
    hardware = subprocess.check_output("sed -n 's/^Hardware\s*: 0*//p' /proc/cpuinfo", shell=True)
    hardware = hardware.decode()
    hardware.replace("\n","")
    
#get linux version
    linux_ver = subprocess.check_output("cat /proc/version|cut -d' ' -f 3", shell=True)
    linux_ver = linux_ver.decode()
    linux_ver.replace("\n","")
    print("Linux is: %s" % linux_ver)
    
#get MemFree 
    memfree = subprocess.check_output("cat /proc/meminfo | grep MemFree|cut -d' ' -f 2-", shell=True)
    memfree = memfree.decode()
    memfree.replace("\n","")
    memfree.replace("\t","")
    
    print("memfree is: %s" % memfree)
    
#get uptime 
    uptime = subprocess.check_output("uptime -s", shell=True)
    uptime = uptime.decode()
    uptime.replace("\n","") 
    print("uptime is: %s" % uptime)
    
    
#get air pressure
    pressure = ap.get_pressure()
    pressure = round(pressure, 3)
    print("Air Pressure: %s" % pressure)
    
#get accelerometer and gyroscope info

    orientation = ap.get_orientation ()
    pitch = orientation['pitch']
    roll = orientation['roll']
    yaw = orientation['yaw']

    pitch = round(pitch,3)
    roll = round(roll,3)
    yaw = round(yaw,3)
    
    acceleration = ap.get_accelerometer_raw()
    x = acceleration ['x']
    y = acceleration ['y']
    z = acceleration ['z']

    x=round(x,3)
    y=round(y,3)
    z=round(z,3)

#mash the 2 cpu readings together to get close to room temp
#via: https://mwho.co/cpuMinusSense or https://www.raspberrypi.org/forums/viewtopic.php?p=939588#p939588
    #added humidity from the 2nd link above, seems close to barometer on desk...
    calcHumidity=Humidity*(2.5-0.029*SHtempC)
    calcHumidity = round(calcHumidity,3)
    
#this algo is based on this data: https://docs.google.com/spreadsheets/d/1H4cc0u-jJHFnKwah2uEkLJA8ZqwJ1TP-FYRa-eHq0V0/edit#gid=0
    ######
####IMPORTANT#########You'll need to change these numbers to meet your fridge/oven/environment!
    ######
    heatPercentDiff = SHtempF / cpuTempF
    #likely in a freezer
    if 0 < heatPercentDiff < 0.273:
        tempDiff = -4.2264
    elif heatPercentDiff > 0.2731 and heatPercentDiff < 0.5861:
        tempDiff = 11.78845
    #lower end of a fridge, start range of motherboardCPU affecting
    elif heatPercentDiff > 0.58611 and heatPercentDiff < 0.64:
        tempDiff = 12.46085
    #mid range fridge, and CPU from Motherboard affecting now
    elif heatPercentDiff > 0.641 and heatPercentDiff < 0.72:
        tempDiff = 21.7334
    #cpu heat diff kinda peaks around here
    elif heatPercentDiff > 0.721 and heatPercentDiff < 0.75:
        tempDiff = 23.7334
    #seems to have hit peak right before here and starts back the other way
    elif heatPercentDiff > 0.751 and heatPercentDiff < 0.79:
        tempDiff = 24.364
    elif heatPercentDiff > 0.791 and heatPercentDiff < 0.85:
        tempDiff = 22.07   
    else:
    #just a general overall diff (0.80 to 0.84ish) of it sitting on my desk
        tempDiff = 21.5103
        
    print("heatDiff: %s" % heatPercentDiff)
    
    calibratedTempF = SHtempF - tempDiff
    calibratedTempF = round(calibratedTempF, 3)
    calibratedTempC = (calibratedTempF -32)*5/9
    calibratedTempC = round(calibratedTempC, 3) 
    
    print("Algo is: %s" % tempDiff)
    print("Calibrated_TempC: %s C" % calibratedTempC)
    print("Calibrated_TempF: %s F" % calibratedTempF)


#use Boomi/Dell colors to show on RasPi
    ap.show_message("%.1fC /" % calibratedTempC, scroll_speed=0.05, text_colour=[0, 133, 195])
    ap.show_message("%.1fF /" % calibratedTempF, scroll_speed=0.05, text_colour=[170, 170, 170])
    ap.show_message("%.1frH" % calcHumidity, scroll_speed=0.05, text_colour=[0, 133, 195])


#save it to the file that Atomsphere will consume
    #NOTE 8/21/18 -->adding a new text line use a REPLACE at the end of the file.write statement to remove the carriage return and comma.
    with open('/home/pi/Boomi_AtomSphere/Atom/Atom_raspberrypi/bin/boomiConsume/pi_stats.txt', 'a') as file:
        file.write('{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19},{20}\n'.format(datetimestamp, calcHumidity, cpuTempC, cpuTempF, SHtempF, SHtempC, calibratedTempF, calibratedTempC, pressure, z, y, x, pitch, roll, yaw, serial, hardware, tempDiff, linux_ver, memfree, uptime).replace("\n,",","))

#use HTTP POST something

#wait for 3 seconds and do it again 
time.sleep(3)