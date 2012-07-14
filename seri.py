import serial
import struct
from time import sleep
import os

def C(val):
    return struct.pack('!H', val)

def sendCommand(port, code):
    port.flush()
    port.write(C(code))
    if code != 0xaabb:
        return port.read()
    return None

def humanRead(c):
    print responses[ord(c)]


base_path = '/dev'


responses = {
    0x00: 'No group recorded',
    0x01: 'Group 1 is recorded',
    0x02: 'Group 2 is recorded',
    0x03: 'Group 1 and 2 are recorded',
    0x04: 'Group 3 is recorded',
    0x05: 'Group 1 and 3 are recorded',
    0x06: 'Group 2 and 3 are recorded',
    0x07: 'All groups are recorded',
    0xcc: 'Successful',
    0xe0: 'Instruction error',
    0xe1: 'Importing voice group failed',
    0x40: 'Ready for recording',
    0x41: 'No voice detected',
    0x42: 'Speak again after START',
    0x43: 'Too loud',
    0x44: 'Second record is different from the first',
    0x45: 'Successfully recorded one voice',
    0x46: 'Finished recording group1',
    0x47: 'Finished recording group2',
    0x48: 'Finished recording group3',
}

commands = {
    0xaa00: "Enter waiting state",
    0xaa01: "Delete group 1",
    0xaa02: "Delete group 2",
    0xaa03: "Delete group 3",
    0xaa04: "Delete all groups",
    0xaa11: "Record group 1",
    0xaa12: "Record group 2",
    0xaa13: "Record group 3",
    0xaa21: "Import group 1",
    0xaa22: "Import group 2",
    0xaa23: "Import group 3",
    0xaa24: "Query the recorded groups",
    0xaa31: "Change speed to 2400bps",
    0xaa32: "Change speed to 4800bps",
    0xaa33: "Change speed to 9600bps",
    0xaa34: "Change speed to 19200bps",
    0xaa35: "Change speed to 38400bps",
    0xaa36: "Switch to common mode",
    0xaa37: "Switch to compact mode",
    0xaabb: "Query informations",
}

class StateMachine(object):
    def __init__(self, state):
        self.initial_state = state
        self.state = state

    def run(self):
        while type(self.state) != Closing:
            self.state.command(self)
        self.state.command(self)
        self.reset()

    def reset(self):
        self.state = self.initial_state

class State(object):
    pass

class Recording(State):
    def command(self, machine):

        while True:
            code = machine.port.read()
            print responses[ord(code)]
            if ord(code) in [0x46, 0x47, 0x48]:
                break

        code = machine.port.read()
        machine.state = Waiting()

class Listening(State):
    def command(self, machine):
        machine.state = Disconnecting()

class Waiting(State):
    def command(self, machine):
        print "Waiting for commands!"

        for i, message in enumerate(commands.values()):
            print "[%d]\t%s (%s)" % (i, message)

        index = raw_input("Select a command > ")
        if index.isdigit():
            code = commands.keys()[int(index)]
            response = sendCommand(machine.port, code)

            if response:
                print "%s (%s)" % (responses[ord(response)], hex(ord(response)))

            if response == '\xcc':
                if code in [0xaa21, 0xaa22, 0xaa23]:
                    machine.state = Listening()

            elif response == '\x40':
                machine.state = Recording()

        elif index == 'quit':
            machine.state = Disconnecting()

class Disconnecting(State):
    def command(self, machine):
        print "Closing connection to %s" % machine.port.name
        machine.port.close()
        machine.state = Closing()

class Closing(State):
    def command(self, machine):
        print "Bye!"

class NotConnected(State):
    def command(self, machine):
        global base_path
        ports = [port for port in os.listdir(base_path) if port.startswith('tty.')]

        for num, port in enumerate(ports):
            print "[%d] %s" % (num, port)

        number = raw_input("Select a number > ")

        if number.isdigit():
            try:
                file_path = os.path.join(base_path, ports[int(number)])
                machine.port = serial.Serial(port=file_path, baudrate=9800)
                machine.state = Waiting()
                sleep(2)
                machine.port.write(C(0xaa00))
                sleep(1)
                machine.port.write(C(0xaa37))
                sleep(1)
            except:
                print "Can't connect to this port"

            humanRead(machine.port.read())
            humanRead(machine.port.read())

        elif number == 'quit':
            machine.state = Closing()
        else:
            print "select one of the number or [quit]"

machine = StateMachine(NotConnected())
machine.run()
#  ser = serial.Serial(port='/dev/tty.PL2303-00002006', baudrate=9600)
#
#  sleep(2)
#
#  ser.write(C(0xaa00))
#
#  sleep(1)
#  ser.write(C(0xaa36))
#
#  sleep(1)
#  ser.write(C(0xaa11))
#
#  sleep(1)
#
#  while True:
#      print ser.readline()
#
#  ser.close()
