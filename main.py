# Copyright (C) 2022 NG:ITL
from platform_output_writer.main import PlatformWriter

if __name__ == "__main__":
    print("initializing Platform Socket")
    platform_writer = PlatformWriter()
    print("Starting Loop")
    while True:
        platform_writer.run()
