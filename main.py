import minimalmodbus
import argparse
from time import sleep

INVERTERS: int = 6
INIT_ADDRESS = 11
STRINGS = 12
OFFSET = 1
DELAY = 0.3


def set_instrument(address, debug=False):
    if not debug:
        instrument = minimalmodbus.Instrument('/dev/ttyAMA0', address)  # port name, slave address (in decimal)
    else:
        instrument = minimalmodbus.Instrument('/dev/pts/5', address)  # port name, slave address (in decimal)

    instrument.serial.baudrate = 9600  # Baud
    instrument.serial.bytesize = 8
    # instrument.serial.parity = PARITY_NONE
    instrument.serial.stopbits = 1
    instrument.serial.timeout = 0.5  # seconds
    instrument.mode = minimalmodbus.MODE_RTU  # rtu or ascii mode
    instrument.clear_buffers_before_each_transaction = True

    return instrument


def get_results(init_address, inverters, strings, debug=False):
    f = open('/tmp/iv_curves.csv', 'w')
    f.write('inverter;string;I;V\n')
    for inv in range(inverters):
        instrument = set_instrument(inv + init_address, debug=debug)

        for string in range(strings):
            instrument.write_register(3342-OFFSET, string, functioncode=6)
            sleep(DELAY)
            results = instrument.read_registers(registeraddress=3343-OFFSET, number_of_registers=120, functioncode=4)
            sleep(DELAY)
            print("Inversor {} - string {}:".format(inv+1, string+1))
            print(results)
            for i in range(0, 60):
                V = results[i] / 10
                I = results[i + 1] / 10
                f.write('{};{};{};{}\n'.format(inv + 1, string + 1, I, V))
    f.close()


def trigger_curves(init_address, inverters, strings):
    for inv in range(0, inverters):
        instrument = set_instrument(inv + init_address)
        instrument.write_register(3241-OFFSET, 850, 0)  # start voltage
        sleep(DELAY)
        instrument.write_register(3242-OFFSET, 10, 0)  # start voltage
        sleep(DELAY)
        instrument.write_register(3240-OFFSET, 1, 0)  # start


def test(init_address, inverters, debug=False):
    for inv in range(inverters):
        instrument = set_instrument(init_address+inv, debug=debug)
        try:
            print("Inverter {} - relogio {}".format(init_address+inv, instrument.read_registers(3073-OFFSET, number_of_registers=6, functioncode=4)))  # ano, mes, dia, hora, min, seg
            print("Inverter {} - param curvas {}".format(init_address + inv, instrument.read_registers(3241 - OFFSET, number_of_registers=2, functioncode=4)))  # ano, mes, dia, hora, min, seg
        except Exception as e:
            print("Inverter {} - No response".format(init_address+inv))


def cmd_line():
    cmd = argparse.ArgumentParser()
    cmd.add_argument("--action",
                     help="Action: trigger or get",
                     default='',
                     type=str)
    cmd.add_argument("--debug",
                     help="points to localhost TCP",
                     default=False,
                     type=bool)
    cmd.add_argument("--init_address",
                     help="First node",
                     default=1,
                     type=int)
    cmd.add_argument("--inverters",
                     help="number of inverters",
                     default=1,
                     type=int)
    cmd.add_argument("--strings",
                     help="number of strings per inverter",
                     default=1,
                     type=int)

    return cmd.parse_args()


def main():
    args = cmd_line()

    if args.debug:
        listOfGlobals = globals()
        listOfGlobals['INVERTERS'] = 1
        listOfGlobals['DELAY'] = 0

    if args.action == 'trigger':
        trigger_curves(args.init_address, args.inverters, args.strings)
    elif args.action == 'get':
        get_results(args.init_address, args.inverters, args.strings, args.debug)
    elif args.action == 'test':
        test(args.init_address, args.inverters, args.debug)
    else:
        print("No action")


if __name__ == '__main__':
    main()
