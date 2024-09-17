# uc_api.py
from packet import UcPacket, AddressPair, PV
from async_driver import AsyncUcDriver


class UcAPI:
    def __init__(self, driver: AsyncUcDriver):
        self.driver = driver

    async def set_mixer_bypass(self, bypass: bool):
        """
        Set the mixerBypass parameter to True or False.
        """
        await self.driver.send(PV(
            ap=AddressPair(a=0x68, b=0x6a),
            name="global/mixerBypass",
            val=1.0 if bypass else 0.0
        ))

    async def set_channel_mute(self, channel_number: int, mute: bool):
        """
        Mute or unmute the specified channel.

        Args:
            channel_number (int): The number of the channel to mute or unmute.
            mute (bool): True to mute the channel, False to unmute.
        """
        await self.driver.send(PV(
            ap=AddressPair(a=0x68, b=0x6a),
            name=f"line/ch{channel_number}/mute",
            val=1.0 if mute else 0.0
        ))

    # Add other methods for modifying mixer state as needed
    # For example, methods for muting channels or changing volume can be added here
