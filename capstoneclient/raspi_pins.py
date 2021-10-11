# DW 2021-10-03-13:54 it appears the RPi library, or board library forces us to use BCM gpio values... bah!

RASPI_PIN = {
    "zone1":7,
    "valve1_enable":19,
    "valve2_enable":26,
    "valve3_enable":18,
    "valve4_enable":23,
    "valve5_enable":24,
    "valve6_enable":25,
    "polarity":5,
    "shutdown":6,
    "ps_shutoff":13,
    "stat1":27,
    "stat2":22,
        }

# DW 2021-10-03-14:19 everything below here was set up for GPIO.BOARD mode and is no longer valid
#RASPI_PIN_NAMES = ["3v3",
#"5v_1",
#"sda",
#"5v_2",
#"scl",
#"gnd_1",
#"noConn_1",
#"debug_tx",
#"gnd_2",
#"debug_rx",
#"noconn_2",
#"valve3_enable",
#"stat1",
#"gnd_3",
#"stat2",
#"valve4_enable",
#"3v3_2",
#"valve5_enable",
#"zone6",
#"gnd_4",
#"rdy1",
#"valve6_enable",
#"rdy2",
#"emergency",
#"gnd_5",
#"zone1",
#"rdy3",
#"rdy4",
#"polarity",
#"gnd_8",
#"shutdown",
#"zone2",
#"ps_shutoff",
#"gnd_6",
#"valve1_enable",
#"zone3",
#"valve2_enable",
#"zone4",
#"gnd_7",
#"zone5"
#]
## DW 2021-10-03-10:53 the file line number corresponds to the 
##   pin number of the pin_name above. ex: "SCL" occurrs on line 3 of
##   this file which means it's pin#3 on the raspi's 40 pin connector.
##   That's also why the list elements are hugged against the left side of file,
##   just puts the names right next to the editors line numbers display
## DW 2021-10-03-11:14 go all lowercase just to avoid upper/lower confusion
#RASPI_PIN_NAMES = list(map(lambda s: s.lower(), RASPI_PIN_NAMES))
#RASPI_PIN_NUMS = list(range(1, len(RASPI_PIN_NAMES)+1))
#RASPI_PIN = {}
#for pin_num in RASPI_PIN_NUMS:
#    RASPI_PIN[RASPI_PIN_NAMES[pin_num-1]] = pin_num
#    RASPI_PIN[pin_num] = RASPI_PIN_NAMES[pin_num-1]
#
#DW 2021-10-03-10:56 the dictionary is built to be bi-directional
#   What I mean by this is you can use the pin number to get the pin name
#   Or vice-versa use the pin name to get the 40-pin pin number
# example, If I have a variable that is the pin number, I can use that to look up
# which semantic pin this is on the board like so, return value is after the =>
#   RASPI_PIN[5] => "scl"
#
# To go the other way, let's say I want to get which pin number "SCL" is, I'd do it like so:
#   RASPI_PIN["scl"] => 5
    
if __name__ == "__main__":
#    print(f"Pin name count is: {len(RASPI_PIN_NAMES)}")
#    print(f"Pin num count is: {len(RASPI_PIN_NUMS)}")
#    print(f"Pin bidirectional count is: {len(RASPI_PIN)}")
#    for pin in RASPI_PIN_NAMES:
#        print(f"{RASPI_PIN[pin]:02d} : {pin}")
#    print("We'll print now in a view that's easy to compare to the schematic, so all odds first, then all evens")
#    print("ODDS (LEFT SIDE)")
#    for pinnum in range(1,len(RASPI_PIN_NUMS)+1,2):
#        print(f"{pinnum:02d} : {RASPI_PIN[pinnum]}")
#    print("EVENS (RIGHT SIDE)")
#    for pinnum in range(2,len(RASPI_PIN_NUMS)+1,2):
#        print(f"{pinnum:02d} : {RASPI_PIN[pinnum]}")
    pass
