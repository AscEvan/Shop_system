import sys, os

def clear():
    if sys.platform == 'win32':os.system('cls')
    else: os.system('clear')
    
def pause():
    try:
        input('Enter to continue..')
    except(EOFError, KeyboardInterrupt):return