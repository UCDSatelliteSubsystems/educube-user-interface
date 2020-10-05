# educube-user-interface


Python client for the EduCube educational satellite


## Features

Provides a Web UI for interacting with the EduCube
Provides a CLI for interacting with the EduCube

## Installation

You can install the educube user interface directly from this repo using pip.

It is recommended (though not essential) to run the interface in a virtual
environment. 


To install the client:
```
pip install git+https://github/com/UCDSatelliteSubsystems/educube-user-interface
```

To test the client, open a command prompt and type:
```
$ educube
```
You should see some help information

## Usage

1. Connect to EduCube using a USB to the basestation or to the individual
boards
1. Open a command prompt and type:  `educube start`

You will be asked for the serial port name and the baud rate. The baud rate is
115200 if directly connected to a board, or 9600 if using the basestation.


## Contribute


## Support

If you are having issues, please let us know.


