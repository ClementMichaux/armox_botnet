# Armox Botnet

A simple piece of malware developped in Python with some functionalities like a botnet, a keylogger and a http ddos.

## Getting started
These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Note
This software isn't designed to work on Linux except for the server side. So i would recommend you to install it on Windows and on a virtual machine because the software is going to create register keys for the persistance.

For a better explanation, you can read the report present on the repository (in french) or take a look at the UML.

### Prerequisites
- Installing [pip3](https://vgkits.org/blog/pip3-windows-howto/)
- Installing the externals libraries
	```bash
	pip3 install pynput
	pip3 install requests
	pip3 install pyinstaller
	```
- Installing a text editor of your choice (we're using pyCharm)

## Server Deployement (WINDOWS or LINUX)
Server is using argparse, like that you can choose on which ip address and on which port you would like to start it.

### Launch on Linux
```bash
python3 server.py -a server_ip_address -p server_port
```

### Launch on Windows
```batch
py server.py -a server_ip_address -p server_port
```

### Compilation
If you want, you can compile the server with pyinstaller
```bash
pyinstaller --onefile server.py
```
In the dist directory you can find your executable client.

## Client Deployement (ONLY on WINDOWS)
You need to start the server first otherwise your client won't be able to connect.

Open client.py and edit these lines :
```python3
self.ip = "server_ip_address"
self.port = server_port
```

### Launch
```batch
py client.py
```

### Compilation
```python3
pyinstaller --onefile client.py
```
In the dist directory, you will find your .exe client.

## Built with
* [Python](https://www.python.org/) - Main programing language of the malware
* [pyCharm](https://www.jetbrains.com/fr-fr/pycharm/) - Main text editor
* [pynput](https://pypi.org/project/pynput/) - External library used for the keylogger
* [requests](https://requests.readthedocs.io/en/master/) - External library used for the ddos

## Authors
* **Michaux Clément** - *Initial work* - [Personnal website](https://www.clement-michaux.be)
* **Laenen Maximilien** - *Initial work* - [Personnal website](https://www.maximilien-laenen.be)

## License
This project is licensed under the MIT License - see the [LICENSE.md](https://github.com/MaxBresil/armox_botnet/blob/master/LICENSE.md) file for details.

## Disclaimer
We decline all responsibility for any malicious use of this software.
