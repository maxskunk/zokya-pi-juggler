import pigpio  # http://abyz.co.uk/rpi/pigpio/python.html
import time
import argparse

remoteCommands = {
    "off": "0x300ffe01f",
    "green": "0x300ff906f",
    "red": "0x300ff10ef",
    "magenta": "0x300ff30cf"
}

p = argparse.ArgumentParser()
p.add_argument("-c", "--command", help="command", type=str, default='off')
args = p.parse_args()

COMMAND = args.command

pi = pigpio.pi()


def commandToBinary(my_hexdata):
    scale = 16
    num_of_bits = 8
    return bin(int(my_hexdata, scale))[2:].zfill(num_of_bits)

# Square Wave Generator


def carrier(gpio, frequency, micros):
    wf = []
    cycle = 1000.0 / frequency
    cycles = int(round(micros / cycle))
    on = int(round(cycle / 2.0))
    sofar = 0
    for c in range(cycles):
        target = int(round((c + 1) * cycle))
        sofar += on
        off = target - sofar
        sofar += off
        wf.append(pigpio.pulse(1 << gpio, 0, on))
        wf.append(pigpio.pulse(0, 1 << gpio, off))
    return wf


def sendBinary(hex):
    command = commandToBinary(hex)[2:]
    emit_time = time.time()
    active_waves = []
    # Create Wave
    wave = []

    # 9108
    wf = carrier(18, 38, 9108)
    pi.wave_add_generic(wf)
    lead_pulse = pi.wave_create()
    wave.append(lead_pulse)
    active_waves.append(lead_pulse)

    # 4423
    pi.wave_add_generic([pigpio.pulse(0, 0, 4423)])
    lead_space = pi.wave_create()
    wave.append(lead_space)
    active_waves.append(lead_space)

    wf = carrier(18, 38, 562)
    pi.wave_add_generic(wf)
    pulse = pi.wave_create()
    active_waves.append(pulse)

    pi.wave_add_generic([pigpio.pulse(0, 0, 562)])
    std_space = pi.wave_create()
    active_waves.append(std_space)

    pi.wave_add_generic([pigpio.pulse(0, 0, 1688)])
    one_space = pi.wave_create()
    active_waves.append(one_space)

    for i in command:
        # add pulse
        wave.append(pulse)
        if(i == '1'):
            wave.append(one_space)
        else:
            wave.append(std_space)

    delay = emit_time - time.time()
    if delay > 0.0:
        time.sleep(delay)
    pi.wave_chain(wave)

    while pi.wave_tx_busy():
        time.sleep(0.002)

    for i in active_waves:
        pi.wave_delete(i)


if(COMMAND in remoteCommands):
    print("Sending Command: ", COMMAND)
    sendBinary(remoteCommands[COMMAND])
else:
    print("Command Not Found: ", COMMAND)

pi.stop()
