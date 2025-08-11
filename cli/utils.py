from rich import print

from cli.settings import get_settings

settings = get_settings()


def keep():
    print('> ', end='')  # Mantém o prompt de entrada


def debug(text: str):
    if settings.DEBUG:
        print(f'[bold blue]DEBUG: {text}[/bold blue]')
        keep()


def get_protocol(url: str) -> tuple[str]:
    hostname = url.split('://')
    protocol = 'ws'

    if hostname[0] == 'https':
        protocol = 'wss'

    return protocol, hostname[1]
