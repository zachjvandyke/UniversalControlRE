# UC Control Python Package

This package provides a Python-based interface for controlling Presonus' Universal Control (UC) software, specifically designed for the new Quantum HD 8. It allows you to connect to the UC device over TCP/IP, subscribe to its services, and modify mixer settings such as muting channels and toggling the mixer bypass.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Connecting to the Device](#connecting-to-the-device)
  - [Muting a Channel](#muting-a-channel)
  - [Toggling Mixer Bypass](#toggling-mixer-bypass)
- [Files Overview](#files-overview)
- [Contributing](#contributing)
- [License](#license)

## Features

- Connect to a UC device over TCP/IP.
- Subscribe to the device's services and receive updates.
- Mute or unmute specific channels.
- Toggle the mixer bypass setting.
- Asynchronous communication using `asyncio`.

## Requirements

- Python 3.7 or higher
- An accessible Universal Control device on the network
- Required Python packages:
  - `asyncio`
  - `dataclasses` (for Python 3.7, built-in for 3.7+)
  - `typing`
  - `zlib`
  - `json`

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/zachjvandyke/UniversalControlRE.git
   cd UniversalControlRE
   ```

2. **Install Dependencies**

   Ensure you have Python 3.7 or higher installed. If necessary, create a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate
   ```

   Install any required packages (most are part of the standard library):

   ```bash
   pip install -r requirements.txt  # If you have a requirements file
   ```

   *Note:* Since most dependencies are part of the standard library, you may not need to install additional packages.

## Usage

### Connecting to the Device

Update the `ip_address` variable in `app.py` with the IP address of your UC device:

```python
ip_address = '10.0.0.1'  # Replace with your device's IP address
```

Run the `app.py` script:

```bash
python app.py
```

### Muting a Channel

The `UcAPI` class provides a method to mute or unmute a specific channel. In `app.py`, you can use:

```python
# Mute channel 1
await uc_api.set_channel_mute(channel_number=1, mute=True)

# Unmute channel 1
await uc_api.set_channel_mute(channel_number=1, mute=False)
```

### Toggling Mixer Bypass

To toggle the mixer bypass setting:

```python
# Enable mixer bypass
await uc_api.set_mixer_bypass(True)

# Disable mixer bypass
await uc_api.set_mixer_bypass(False)
```

### Full Example in `app.py`

```python
import asyncio
from async_driver import AsyncUcDriver
from uc_api import UcAPI

async def main():
    ip_address = '10.38.111.25'  # Replace with your device's IP address

    driver = await AsyncUcDriver.create(ip_address)
    print("Connected to the server!")
    await driver.subscribe()

    uc_api = UcAPI(driver)

    response_task = asyncio.create_task(driver.read_responses())
    try:
        # Mute channel 1
        await uc_api.set_channel_mute(channel_number=1, mute=True)
        print("Channel 1 muted")

        await asyncio.sleep(2)

        # Unmute channel 1
        await uc_api.set_channel_mute(channel_number=1, mute=False)
        print("Channel 1 unmuted")

        await asyncio.sleep(2)

        # Toggle mixer bypass
        await uc_api.set_mixer_bypass(True)
        print("Mixer bypass enabled")

        await asyncio.sleep(2)

        await uc_api.set_mixer_bypass(False)
        print("Mixer bypass disabled")

        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("Shutting down...")
        response_task.cancel()
        await driver.close()

if __name__ == '__main__':
    asyncio.run(main())
```

## Files Overview

- `app.py`: The main application script where you establish a connection and control the UC device using `UcAPI`.
- `async_driver.py`: Handles asynchronous communication with the UC device, including connection management and packet transmission.
- `async_packet.py`: Provides the `PacketCodec` class for encoding and decoding packets asynchronously.
- `packet.py`: Defines the packet structures and serialization/deserialization methods for communication with the UC device.
- `uc_api.py`: Contains the `UcAPI` class with high-level methods for controlling the mixer state, such as muting channels and toggling mixer bypass.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Make your changes and commit them with clear messages.
4. Push your changes to your fork.
5. Submit a pull request to the main repository.

Please ensure your code follows PEP 8 style guidelines and includes docstrings for public methods.

## Thanks

bananu7 and his [ultimate-control repo](https://github.com/bananu7/ultimate_control/tree/main) was a huge resource to me in the create of this package.
## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---


*Note:* This package is intended for educational and testing purposes. Ensure you have permission to connect to and control the UC device on your network. The authors are not responsible for any misuse of this software.
