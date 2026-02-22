import sys
from colorama import init, Fore, Style

# Initialize colorama for Windows support
init(autoreset=True)

def print_header(text):
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 40}\n {text.upper()}\n{'=' * 40}{Style.RESET_ALL}")

def print_sub_header(text):
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{text}{Style.RESET_ALL}")

def print_error(text):
    print(f"{Fore.RED}[!] {text}{Style.RESET_ALL}")

def print_warning(text):
    print(f"{Fore.YELLOW}[WARNING] {text}{Style.RESET_ALL}")

def print_success(text):
    print(f"{Fore.GREEN}[SUCCESS] {text}{Style.RESET_ALL}")

def print_result(text):
    print(f"{Fore.MAGENTA}{Style.BRIGHT}{text}{Style.RESET_ALL}")

def print_info(text):
    print(f"{Fore.WHITE}{text}{Style.RESET_ALL}")

def ask_user(prompt_text):
    """Prints prompt and returns the raw input string."""
    try:
        raw = input(f"{Fore.CYAN}{prompt_text}{Style.RESET_ALL}").strip()
        if raw.lower() == 'q':
            print_warning("Exiting interactive configuration.")
            sys.exit(0)
        return raw
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)
