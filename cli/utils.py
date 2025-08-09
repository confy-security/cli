from rich import print

from cli.settings import get_settings

settings = get_settings()


def keep():
    print('> ', end='')  # Mantém o prompt de entrada


def debug(text: str):
    if settings.DEBUG:
        print(f'[bold blue]DEBUG: {text}[/bold blue]')
        keep()
