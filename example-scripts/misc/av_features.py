import errno
import subprocess
import sys
import os
from termcolor import colored

# todo add command line switch for this
# also look into gst-vaapi state of the system
gst = True
# also look into v4l2 devices
v4l2 = True
if v4l2:
    import v4l2ctl

# debian/ubuntu is currently supported, feel free to add your distribution
# "debian" should be used also for ubuntu based distributions
distribution = "debian"
if distribution == "debian":
    import apt

root = False
if os.geteuid() == 0:
    root = True


def get_cards():
    cards = {}
    if not root:
        print("running as user, can't detect cards")
    else:
        devices = int(len(os.listdir("/sys/kernel/debug/dri/")) / 2)
        i = 0
        while i < devices:
            name = open("/sys/kernel/debug/dri/" + str(i) + "/name", "r")
            properties = name.read().split(" ")
            cards["/dev/dri/card" + str(i)] = properties[0]
            i += 1
    return cards


def get_drivers():
    drivers = {}
    if distribution == "debian":
        drivers = {"i965-va-driver-shaders": False,
                   "i965-va-driver": False,
                   "intel-media-va-driver-non-free": False,
                   "intel-media-va-driver": False,
                   "mesa-va-drivers": False}
        for driver in drivers.keys():
            cache = apt.Cache()
            if cache[driver].is_installed:
                drivers[driver] = True

    # check if we are on the iHD driver and therefore want to load the firmware
    if drivers["intel-media-va-driver"] or drivers["intel-media-va-driver-non-free"]:
        if root:
            guc = subprocess.check_output(["cat", "/sys/kernel/debug/dri/0/gt/uc/guc_info"]).decode()
            if "status: RUNNING" in guc:
                print(colored("+ GUC firmware loaded and running", "green"))
            else:
                print(colored("+ GUC firmware not loaded", "red"))
            huc = subprocess.check_output(["cat", "/sys/kernel/debug/dri/0/gt/uc/huc_info"]).decode()
            if "status: RUNNING" in huc:
                print(colored("+ HUC firmware loaded and running", "green"))
            else:
                print(colored("+ HUC firmware not loaded", "red"))
        else:
            print(colored("running as user: skipping firmware check for iHD driver"))
    return drivers


def get_gst(drivers: {}):
    # todo collect results in data structure and return it
    # debian specific stuff
    cache = apt.Cache()
    if cache["gstreamer1.0-vaapi"].is_installed:
        print(colored("+ " + "gstreamer1.0-vaapi installed", "green"))
    else:
        print(colored("+ " + "gstreamer1.0-vaapi not installed", "red"))
    try:
        subprocess.check_output(["gst-inspect-1.0"])
    except OSError as e:
        if e.errno == errno.ENOENT:
            print(colored("gst-inspect-1.0 seems not to be present, can't run gst tests.", "red"))
            sys.exit(-1)
        else:
            print(colored("Something strange happened while looking for gst-inspect-1.0"), "red")
            sys.exit(-1)

    bl = subprocess.check_output(["gst-inspect-1.0", "-b"]).decode()
    if "Total count: 0" in bl:
        print(colored("+ GST Blacklist ist empty on your system.", "green"))
    else:
        print(colored("+ GST Blacklist is not empty, checkout gst-inspect-1.0 -b to learn more"), "red")
        # todo parse the blacklist and print it

    if len(drivers) > 0:
        for driver in drivers.items():
            if "i965" in driver[0] and driver[1]:
                parse_gst_inspect("i965")
            elif "intel-media" in driver[0] and driver[1]:
                parse_gst_inspect("iHD")
            elif "mesa-va-driver" in driver[0] and driver[1]:
                parse_gst_inspect("radeonsi")

    return True


def parse_gst_inspect(driver: str):
    # see https://github.com/GStreamer/gstreamer-vaapi for documentation
    env_vars = {"GST_VAAPI_ALL_DRIVERS": "1", "LIBVA_DRIVER_NAME": driver}
    os.environ.update(env_vars)
    gstinfo = subprocess.check_output("gst-inspect-1.0", stderr=subprocess.DEVNULL).decode().split("\n")
    print("En/Decoder for driver: " + driver)
    features = []
    for line in gstinfo:
        items = line.split(":")
        if "vaapi" in items[0]:
            features.append(items[1])
            print(colored("+ " + items[1].strip(), "green"))
    return features


def parse_vainfo(driver: str, device: str):
    env_vars = {"LIBVA_DRIVER_NAME": driver}
    os.environ.update(env_vars)
    vainfo = subprocess.check_output(["vainfo", "--display", "drm", "--device", device],
                                     stderr=subprocess.DEVNULL).decode().split("\n")
    features = []
    for line in vainfo:
        if line.strip().startswith("VA"):
            features.append(line.strip())
    return features


def get_v4l2_devices():
    devs = os.listdir("/dev/")
    v4l2_devs = []
    for dev in devs:
        if "video" in dev:
            v4l2_devs.append(v4l2ctl.V4l2Device("/dev/" + dev))
    return v4l2_devs


def main():
    global gst
    print("c3voc av-features")
    print("OS type: " + distribution + ", Gstreamer check: " + str(gst))
    if root:
        print("Running with root privileges this will print all information but is also dangerous ... whohoo")
    else:
        print("Running without root, not all features will work....most likely")

    print("Looking for render devices:")
    cards = get_cards()
    for card in cards.items():
        print(colored("+ device:  " + card[0] + "  driver: " + card[1], "green"))

    print("Checking installed va drivers")
    drivers = get_drivers()
    for driver in drivers.items():
        if driver[1]:
            print(colored("+ " + driver[0] + " is installed", "green"))
        else:
            print(colored("+ " + driver[0] + " is not installed", "red"))

    # print some warnings regarding driver / card combinations

    if "i915" in cards.values():
        intel_va = False
        for driver in drivers.items():
            if "i965" in driver[0] or "intel-media" in driver[0]:
                intel_va = True
        if intel_va:
            print(colored("+ Intel iGPU and intel va driver found", "green"))
        else:
            print(colored("+ Intel iGPU detected but no suitable vaapi driver found"), "red")

    if "i965-va-driver-shaders" not in drivers.keys() and "intel-media-va-driver-non-free" not in drivers.keys():
        print(colored("+ only free intel va drivers installed, encoding will most likely not work!", "red"))

    if "amdgpu" in cards.values():
        amd_va = False
        for driver in drivers.items():
            if "mesa-va-drivers" in driver[0]:
                amd_va = True
        if amd_va:
            print(colored("+ AMD GPU/iGPU and mesa va driver found", "green"))
        else:
            print(colored("+ AMD GPU/iGPU detected but no suitable vaapi driver found"), "red")

    # check what vainfo things about the device and driver
    cards_features = []
    for card in cards.items():
        if "i915" in card[1]:
            for driver in drivers.items():
                if "i965-va-driver" in driver[0] and driver[1]:
                    cards_features.append(parse_vainfo("i965", card[0]))
                elif "intel-media-va-driver" in driver[0] and driver[1]:
                    cards_features.append(parse_vainfo("iHD", card[0]))
        elif "amdgpu" in card[1]:
            for driver in drivers.items():
                if "mesa-va-driver" in driver[0] and driver[1]:
                    cards_features.append(parse_vainfo("radeonsi", card[0]))

    for i, card in enumerate(cards_features):
        print("Card " + str(i) + " vainfo:")
        for feature in card:
            print(colored("+ " + feature, "green"))

    if gst:
        print("GStreamer tests")
        gst = get_gst(drivers)

    if v4l2:
        print("v4l2 devices")
        v4ldevs = get_v4l2_devices()
        for dev in v4ldevs:
            print(colored("+ " + dev.device + " " + dev.name, 'green'))
            print(colored("+ " + str(dev.physical_capabilities), "green"))


if __name__ == "__main__":
    # execute only if run as a script
    main()
