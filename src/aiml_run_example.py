#!/usr/bin/env python3

import aiml


# Create the kernel and learn AIML files
kernel = aiml.Kernel()
kernel.verbose(False)
kernel.learn("../aiml/startup.xml")
#kernel.respond("load aiml b")

# Press CTRL-C to break this loop
while True:
    r = kernel.respond(input("> "))
    print(r)
