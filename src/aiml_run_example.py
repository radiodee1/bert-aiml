#!/usr/bin/env python3

import aiml
import argparse

parser = argparse.ArgumentParser(description="Bert Aiml", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--generated', action='store_true', help='use generated aiml.')
parser.add_argument('--startup', action='store_true', help='use startup xml.')

args = parser.parse_args()
# Create the kernel and learn AIML files
kernel = aiml.Kernel()
kernel.verbose(True)
if args.generated:
    kernel.learn("../maze/generated.aiml")
if args.startup:
    kernel.learn("../aiml/startup.xml")
#kernel.respond("load aiml b")

# Press CTRL-C to break this loop
while True:
    r = kernel.respond(input("> "))
    print(r)
