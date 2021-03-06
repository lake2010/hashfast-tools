#! /usr/bin/env python3

# Copyright (c) 2014, HashFast Technologies LLC
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#   1.  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#   2.  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#   3.  Neither the name of HashFast Technologies LLC nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL HASHFAST TECHNOLOGIES LLC BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import argparse

def parse_args():
  parser = argparse.ArgumentParser(description='Update HashFast modules. By default loads the latest release firmware.')
  parser.add_argument('-l', '--list',       dest='list',       action='store_true', help='list firmware')
  parser.add_argument('-r', '--release',    dest='release',    type=str, help='specific release to load')
  parser.add_argument('-t', '--bootloader', dest='bootloader', action='store_true', help='installs the latest bootloader')
  # debug
  parser.add_argument('-d', '--debug',      dest='debug',      action='store_true', help='load debug firmware')
  parser.add_argument('-b', '--build',      dest='build',      type=str, help='specific build to load')
  return parser.parse_args()

if __name__ == '__main__':
  # parse args before other imports
  args = parse_args()

import sys
from hf.usb             import usbctrl
from hf.usb             import util
from hf.firmware.update import HF_Updater

def printme(msg):
  print(msg)

def main(args):
  if args.debug:
    print("WARNING - Debug builds are experimental!")
    print("HashFast is not responsible for damage resulting from debug builds.")

  updater = HF_Updater()

  ####################
  # BOOTLOADER       #
  ####################
  if args.bootloader:
    # doing a load, wait for a valid HashFast device
    dev = util.poll_hf_device()
    if dev is util.USB_DEV_DFU:
      # found a device that needs a bootloader
      print("Bootloader not detected.")
      for flash_size in [512, 128]:
        try:
          dfu = updater.fetch_release_bootloader(flash=flash_size)
          updater.load_firmware_dfu(dfu, flash=flash_size)
          break
        except:
          pass
      # wait for device to reboot
      util.poll_hf_device()
      return

    elif dev is util.USB_DEV_HF:
      # found device in application mode
      updater.dev = usbctrl.poll_hf_ctrl_device(printer=printme)
      #updater.enumerate_modules()
      updater.enter_loader()

    # load firmware
    updater.dev_loader = usbctrl.poll_hf_ctrl_device_loader(printer=printme)
    updater.enumerate_modules_loader()
    # get flash size
    loader_version = updater.read_version_loader().version
    if loader_version >= 4:
      flash_size = int(updater.read_flash_size_loader().flash_size / 1024)
    else:
      flash_size = 512
    print("Using flash_size of: {}k".format(flash_size))
    # fetch file
    hfu = updater.fetch_release_bootloader_update(flash=flash_size)
    updater.load_firmware_hfu(hfu, force=False)
    updater.enter_app()


  ####################
  # LIST             #
  ####################
  elif args.list:
    # list releases/builds
    if args.debug:
      updater.list_debug_builds()
    else:
      updater.list_release_firmwares()


  ####################
  # FIRMWARE         #
  ####################
  else:
    # doing a load, wait for a valid HashFast device
    dev = util.poll_hf_device()
    if dev is util.USB_DEV_DFU:
      # found a device that needs a bootloader
      print("Bootloader not detected.")
      for flash_size in [512, 128]:
        try:
          # if no release specified, then latest will be loaded
          dfu = updater.fetch_release_bootloader(args.release, flash=flash_size)
          updater.load_firmware_dfu(dfu, flash=flash_size)
          break
        except:
          pass
      # wait for device to reboot
      util.poll_hf_device()

    elif dev is util.USB_DEV_HF:
      # found device in application mode
      updater.dev = usbctrl.poll_hf_ctrl_device(printer=printme)
      #updater.enumerate_modules()
      updater.enter_loader()

    # load firmware
    if args.debug or args.build:
      if args.build:
        updater.dev_loader = usbctrl.poll_hf_ctrl_device_loader(printer=printme)
        updater.enumerate_modules_loader()
        # get flash size
        loader_version = updater.read_version_loader().version
        if loader_version >= 4:
          flash_size = int(updater.read_flash_size_loader().flash_size / 1024)
        else:
          flash_size = 512
        print("Using flash_size of: {}k".format(flash_size))
        # fetch file
        hfu = updater.fetch_debug_build(args.build, flash=flash_size)
        updater.load_firmware_hfu(hfu)
        updater.enter_app()
      else:
        raise HF_UpdateError("You must specify a debug build with --build BUILD")

    else:
      # if no release specified, then latest will be loaded
      updater.dev_loader = usbctrl.poll_hf_ctrl_device_loader(printer=printme)
      updater.enumerate_modules_loader()
      # get flash size
      loader_version = updater.read_version_loader().version
      if loader_version >= 4:
        flash_size = int(updater.read_flash_size_loader().flash_size / 1024)
      else:
        flash_size = 512
      print("Using flash_size of: {}k".format(flash_size))
      # fetch file
      # if no release specified, then latest will be loaded
      hfu = updater.fetch_release_firmware(args.release, flash=flash_size)
      updater.load_firmware_hfu(hfu)
      updater.enter_app()

if __name__ == "__main__":
   main(args)
