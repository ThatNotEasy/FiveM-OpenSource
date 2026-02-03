import os, time
from sys import stdout
from colorama import Fore, Style

# =========================================================================================================== #

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# =========================================================================================================== #

def banners():
    stdout.write("                                                                                         \n")
    stdout.write(""+Fore.LIGHTRED_EX +"███████╗███████╗██╗  ██╗     ██████╗        ██████╗ ██████╗ \n")
    stdout.write(""+Fore.LIGHTRED_EX +"██╔════╝██╔════╝╚██╗██╔╝     ╚════██╗      ██╔═══██╗██╔══██╗\n")
    stdout.write(""+Fore.LIGHTRED_EX +"█████╗  ███████╗ ╚███╔╝█████╗ █████╔╝█████╗██║   ██║██████╔╝\n")
    stdout.write(""+Fore.LIGHTRED_EX +"██╔══╝  ╚════██║ ██╔██╗╚════╝██╔═══╝ ╚════╝██║▄▄ ██║██╔══██╗\n")
    stdout.write(""+Fore.LIGHTRED_EX +"███████╗███████║██╔╝ ██╗     ███████╗      ╚██████╔╝██████╔╝\n")
    stdout.write(""+Fore.LIGHTRED_EX +"███████╗███████║██╔╝ ██╗     ███████╗      ╚██████╔╝██████╔╝\n")
    stdout.write(""+Fore.YELLOW +"═════════════╦═════════════════════════════════╦══════════════════════════════\n")
    stdout.write(""+Fore.YELLOW   +"╔════════════╩═════════════════════════════════╩═════════════════════════════╗\n")
    stdout.write(""+Fore.YELLOW   +"║ \x1b[38;2;255;20;147m• "+Fore.GREEN+"AUTHOR             "+Fore.RED+"    |"+Fore.LIGHTWHITE_EX+"   Ap0dexMe0                                    "+Fore.YELLOW+"║\n")
    stdout.write(""+Fore.YELLOW   +"╔════════════════════════════════════════════════════════════════════════════╝\n")
    stdout.write(""+Fore.YELLOW   +"║ \x1b[38;2;255;20;147m• "+Fore.GREEN+"GITHUB             "+Fore.RED+"    |"+Fore.LIGHTWHITE_EX+"   GITHUB.COM/THATNOTEASY                        "+Fore.YELLOW+"║\n")
    stdout.write(""+Fore.YELLOW   +"╚════════════════════════════════════════════════════════════════════════════╝\n") 
    print(f"{Fore.YELLOW}[ESX-2-QB] - {Fore.GREEN}A Python Code Conversion FiveM scripts between ESX and QB-Core frameworks. - {Fore.RED}[V0.1] \n{Fore.RESET}")

# =========================================================================================================== #

def clear_and_print():
    time.sleep(1)
    clear_screen()
    banners()