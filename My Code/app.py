# app.py
import asyncio
from async_driver import AsyncUcDriver
from uc_api import UcAPI


async def main():
    # Specify the IP address you want to connect to
    ip_address = '10.38.111.25'  # Replace with the desired IP address

    driver = await AsyncUcDriver.create(ip_address)
    print("Connected to the server!")
    await driver.subscribe()

    # Create an instance of UcAPI
    uc_api = UcAPI(driver)

    # Start the response reading task
    response_task = asyncio.create_task(driver.read_responses())
    try:
        # Initially set mixerBypass to False
        await uc_api.set_mixer_bypass(False)
        print("mixerBypass set to False")

        # Wait for a short period
        await asyncio.sleep(2)

        # Toggle mixerBypass to True
        await uc_api.set_mixer_bypass(True)
        print("mixerBypass set to True")

        # Wait for a short period
        await asyncio.sleep(2)

        # Toggle mixerBypass back to False
        await uc_api.set_mixer_bypass(False)
        print("mixerBypass set to False")

        await uc_api.set_channel_mute(1, True)
        print("set ch1 to mute")

        # Keep the program running to continue receiving responses
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("Shutting down...")
        # Cancel the response task and close connections
        response_task.cancel()
        await driver.close()

if __name__ == '__main__':
    asyncio.run(main())
