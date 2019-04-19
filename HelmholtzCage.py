import serial # Power Supply imports
import time
import smbus # Temperature & Magnotometer sensor imports
import MagneticFieldCurrentRelation as mfeq # Magnetic field equation import

# function to set voltage. 1st parameter is voltage, 2nd is PSU #
def setVolts(voltage, psu):
    setting = "Asu" + str(voltage * 100) + "\n"
    time.sleep(.1)
    if(psu == 1):
        ser1.write(setting)
    elif(psu == 2):
        ser2.write(setting)
    elif(psu == 3):
        ser3.write(setting)

# function to set amps. 1st parameter is amps, 2nd is PSU #
def setAmps(amps, psu):
    if amps < 0:
        amps = 0 - amps
        print "You need to change the polarity of PS" + str(psu)
    setting = "Asi" + str(amps * 1000) + "\n"
    time.sleep(.1)
    if(psu == 1):
        ser1.write(setting)
    elif(psu == 2):
        ser2.write(setting)
    elif(psu == 3):
        ser3.write(setting)

# function to turn on/off PSU. 1st param: 1 = on, 0 = off, 2nd param: PSU #
def setOutput(onoff, psu):
    setting = "Aso" + str(onoff) + "\n"
    time.sleep(.1)
    if(psu == 1):
        ser1.write(setting)
    elif(psu == 2):
        ser2.write(setting)
    elif(psu == 3):
        ser3.write(setting)

# function to switch all PSUs on or off
def turnAllOnOrOff(switch):
    setOutput(switch, 1)
    setOutput(switch, 2)
    setOutput(switch, 3)

# function to initialize serial port
def serialInit(initport):
    return serial.Serial(
        port=initport,
        baudrate=9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=1)

# Convert from beautiful Celsius to terrible Fahrenheit
def fahr(cels):
    return cels * 1.8 + 32

# data conversion processes for magnetometer and temperature
def checksize(measurement, maxval, offset):
    if measurement > maxval :
        return measurement - offset
    else:
        return measurement

# function to safety check temperatures
def safetycheck(temp, warning, shutoff):
    if temp > warning:
        print "Warning: It's getting hot in here!"
        if temp > shutoff:
            print "It's way too hot! I'm turning off the power supplies!"
            turnAllOnOrOff(0)
    return

# function to get magnetic field components from sensors
def magnotometer():
    # Get I2C bus
    bus = smbus.SMBus(1)

    # MAG3110 address, 0x0E(14)
    # Select Control register, 0x10(16)
    #        0x01(01)    Normal mode operation, Active mode
    bus.write_byte_data(0x0E, 0x10, 0x01)

    time.sleep(0.5)

    # MAG3110 address, 0x0E(14)
    # Read data back from 0x01(1), 6 bytes
    # X-Axis MSB, X-Axis LSB, Y-Axis MSB, Y-Axis LSB, Z-Axis MSB, Z-Axis LSB
    data = bus.read_i2c_block_data(0x0E, 0x01, 6)

    # Convert the data
    xMag = data[0] * 256 + data[1]
    xMag = checksize(xMag, 32767, 65536)

    yMag = data[2] * 256 + data[3]
    yMag = checksize(yMag, 32767, 65536)

    zMag = data[4] * 256 + data[5]
    zMag = checksize(zMag, 32767, 65536)

    # divide by 10 to convert bit counts to microteslas
    return xMag/10, yMag/10, zMag/10

# function to get (and check) temperatures from sensors
# Sensors located at i2c addresses 0x18 and 0x1c
# Please update if changed
def temperature():
    # 1st sensor for wire temp
    # Distributed with a free-will license.
    # Use it any way you want, profit or free, provided it fits in the licenses of its associated works.
    # MCP9808
    # This code is designed to work with the MCP9808_I2CS I2C Mini Module available from ControlEverything.com.
    # https://www.controleverything.com/content/Temperature?sku=MCP9808_I2CS#tabs-0-product_tabset-2

    # Get I2C bus
    bus = smbus.SMBus(1)

    # MCP9808 address, 0x18(24)
    # Select configuration register, 0x01(1)
    #        0x0000(00)    Continuous conversion mode, Power-up default
    config = [0x00, 0x00]
    bus.write_i2c_block_data(0x18, 0x01, config)
    # MCP9808 address, 0x18(24)
    # Select resolution rgister, 0x08(8)
    #        0x03(03)    Resolution = +0.0625 / C
    bus.write_byte_data(0x18, 0x08, 0x03)

    time.sleep(0.5)

    # MCP9808 address, 0x18(24)
    # Read data back from 0x05(5), 2 bytes
    # Temp MSB, TEMP LSB
    data = bus.read_i2c_block_data(0x18, 0x05, 2)

    # Convert the data to 13-bits
    ctemp1 = ((data[0] & 0x1F) * 256) + data[1]
    ctemp1 = checksize(ctemp1, 4095, 8192)
    ctemp1 = ctemp1 * 0.0625

    # 2nd sensor for PSU temp
    #------------------------------------
    bus.write_i2c_block_data(0x1c, 0x01, config)
    bus.write_byte_data(0x1c, 0x08, 0x03)

    time.sleep(0.5)

    data = bus.read_i2c_block_data(0x1c, 0x05, 2)

    ctemp2 = ((data[0] & 0x1F) * 256) + data[1]
    ctemp2 = checksize(ctemp2, 4095, 8192)
    ctemp2 = ctemp2 * 0.0625

    # wire: 100 warn-120 danger, psu: 35 warn-40 danger
    safetycheck(ctemp1, 100, 120)
    safetycheck(ctemp2, 35, 40)
    return ctemp1, ctemp2

# function for controlling subfunctions, given their index
def controller(control):
    if control == 0:
        print("\nExiting...")
    elif control == 1:
        v1 = float(raw_input('Enter desired Voltage: '))
        p1 = int(raw_input('Select the power supply: '))
        setVolts(v1, p1)
        print("\nVoltage set to %s on PSU %d." % (v1, p1))
    elif control == 2:
        a1 = float(raw_input('Enter desired Amperage: '))
        p1 = int(raw_input('Select the power supply: '))
        setAmps(a1, p1)
        print("\nAmperage set to %s on PSU %d." % (a1, p1))
    elif control == 3:
        turnAllOnOrOff(1)
        print("Powering On...")
    elif control == 4:
        turnAllOnOrOff(0)
        print("Powering Off...")
    elif control == 5:
        print("Checking temperatures...")
        ctemp1, ctemp2 = temperature()
        # Output data to screen
        print "Sensor 1"
        print "Temperature in Celsius is    : %.2f C" % ctemp1
        print "Temperature in Fahrenheit is : %.2f F" % fahr(ctemp1)
        print "Sensor 2"
        print "Temperature in Celsius is    : %.2f C" % ctemp2
        print "Temperature in Fahrenheit is : %.2f F" % fahr(ctemp2)
    elif control == 6:
        print("Checking magnotometer, units in microTeslas")
        xMag, yMag, zMag = magnotometer()
        # Output data to screen
        print "Magnetic field in X-Axis : %d" % xMag
        print "Magnetic field in Y-Axis : %d" % yMag
        print "Magnetic field in Z-Axis : %d" % zMag
    elif control == 7:
        #ps3=x, ps2=y, ps1=z
        ps3, ps2, ps1 = mfeq.fieldToCurrent(x0, y0, z0)
        setAmps(ps1, 1)
        setAmps(ps2, 2)
        setAmps(ps3, 3)
        print("\nAmperage set to %s on PSU %d." % (ps1, 1))
        print("\nAmperage set to %s on PSU %d." % (ps2, 2))
        print("\nAmperage set to %s on PSU %d." % (ps3, 3))

# function for interacting with the user
def interface():
    control = 1
    while (control != 0):
        print("\nPlease enter a command.")
        print("0 to Exit program \n1 to set Voltage \n2 to set Amperage")
        print("3 to turn On PSU's \n4 to turn Off PSU's")
        print("5 to check temperature sensors \n6 to check magnetic fields\n")
        print("7 to set a uniform magnetic field\n")
        try:
            control = int(raw_input('Option selected: '))
            controller(control)
        except ValueError:
            print("\n***Invalid Entry***")

# Main program begins now. Should this go in a main function?

# Initialize serial ports
ser1 = serialInit('/dev/ttyUSB0')
print ser1.name
ser2 = serialInit('/dev/ttyUSB1')
print ser2.name
ser3 = serialInit('/dev/ttyUSB2')
print ser3.name

# initial magnetic field from environment
x0, y0, z0 = magnotometer()

# launch the text interface
interface()