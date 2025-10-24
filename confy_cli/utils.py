"""Módulo utilitário do cliente CLI de mensagens Confy.

Este módulo contém funções auxiliares para:
    - Exibir mensagens no terminal com cores e formatação usando Rich.
    - Manter o prompt de entrada visível após exibir mensagens.
    - Exibir mensagens de depuração, alertas e mensagens recebidas
      (criptografadas ou em texto puro).
    - Verificar se mensagens possuem um prefixo específico.
    - Determinar o protocolo WebSocket adequado ('ws' ou 'wss') com base
      no protocolo HTTP informado.

Variáveis:
    settings: Objeto de configuração retornado por `get_settings()`,
              utilizado para controlar o comportamento de depuração.

Dependências:
    - rich.print: para exibir texto colorido e formatado no terminal.
    - cli.settings.get_settings: para obter configurações da aplicação.

Funções:
    keep(): Mantém o prompt de entrada no terminal.
    debug(text): Exibe mensagens de depuração se o modo DEBUG estiver ativo.
    alert(text): Exibe mensagens de alerta em amarelo.
    received(text): Exibe mensagens recebidas criptografadas em verde.
    received_plaintext(text): Exibe mensagens recebidas em texto puro em vermelho.
    is_prefix(message, prefix): Verifica se uma mensagem começa com um prefixo específico.
    get_protocol(url): Determina o protocolo WebSocket adequado a partir de uma URL.
"""

from rich import print

from confy_cli.settings import get_settings

settings = get_settings()


def keep():
    """Exibe um prompt de entrada (`> `) no terminal sem quebrar a linha.

    Usado para manter o indicador de entrada visível após exibir mensagens no terminal.
    """
    print('> ', end='')  # Mantém o prompt de entrada


def debug(text: str):
    """Exibe uma mensagem de depuração no terminal, se o modo DEBUG estiver ativado.

    A mensagem é formatada em azul e o prompt de entrada é mantido após a exibição.

    Args:
        text (str): Texto da mensagem de depuração.

    """
    if settings.DEBUG:
        print(f'[bold blue]DEBUG: {text}[/bold blue]')
        keep()


def alert(text: str):
    """Exibe uma mensagem de alerta no terminal em amarelo.

    Args:
        text (str): Texto da mensagem de alerta.

    """
    print(f'[bold yellow]{text}[/bold yellow]')


def received(text: str):
    """Exibe uma mensagem recebida (criptografada) no terminal.

    Args:
        text (str): Texto da mensagem recebida.

    """
    print(f'[bold green]RECEIVED:[/bold green] {text}')
    keep()


def received_plaintext(text: str):
    """Exibe uma mensagem recebida em texto puro (não criptografada) no terminal.

    Args:
        text (str): Texto da mensagem recebida em texto puro.

    """
    print(f'[bold red]RECEIVED (plaintext):[/bold red] {text}')
    keep()


def is_prefix(message, prefix: str) -> bool:
    """Verifica se uma mensagem é uma string que começa com o prefixo fornecido.

    Args:
        message (Any): Mensagem a ser verificada.
        prefix (str): Prefixo esperado.

    Returns:
        bool: True se a mensagem for uma string e começar com o prefixo,
              False caso contrário.

    """
    if isinstance(message, str) and message.startswith(prefix):
        return True
    return False


def get_protocol(url: str) -> tuple[str, str]:
    """Determina o protocolo WebSocket apropriado (ws ou wss) com base no esquema da URL.

    Args:
        url (str): URL completa, incluindo o protocolo (http:// ou https://).

    Returns:
        tuple[str]: Uma tupla contendo:
            - O protocolo WebSocket correspondente ('ws' ou 'wss').
            - O hostname extraído da URL.

    """
    hostname = url.split('://')
    protocol = 'ws'

    if hostname[0] == 'https':
        protocol = 'wss'

    return protocol, hostname[1]
