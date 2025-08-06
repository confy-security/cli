import asyncio

import typer
import websockets
from decouple import config
from rich import print

app = typer.Typer()
running = True
host_address = config('SERVER_HOST', default='', cast=str)


async def receive_messages(websocket):
    """Lida com o recebimento de mensagens via WebSocket.

    Imprime as mensagens recebidas no terminal.
    Caso o outro usuário se desconecte, encerra a execução do cliente.

    Args:
        websocket: Conexão WebSocket que deve ser monitorada.
    """
    global running
    try:
        while running:
            message = await websocket.recv()

            if 'The other user has disconnected' in message:
                print(f'[bold yellow]WARNING:[/bold yellow] {message}')
                print('Press ENTER to exit.')
                running = False
                break

            print(f'[bold green]RECEIVED:[/bold green] {message}')
            print('> ', end='')  # Mantém o prompt de entrada
    except Exception as e:
        print(f'\nError receiving message: {e}')
        running = False


async def send_messages(websocket):
    """Lida com o envio de mensagens via WebSocket.

    Lê mensagens do usuário pelo terminal e as envia.
    Digitar 'exit' encerra a sessão.

    Args:
        websocket: Conexão WebSocket ativa.
    """
    global running
    while running:
        try:
            message = await asyncio.to_thread(
                input, '> '
            )  # Captura entrada sem bloquear o loop

            if message.lower() == 'exit':
                running = False
                break

            await websocket.send(message)
        except Exception as e:
            print(f'Error sending message: {e}')
            running = False
            break


async def client(host: str, user_id: str, recipient_id: str):
    """Inicia a conexão WebSocket e gerencia o envio e recebimento de mensagens.

    Cria e gerencia tarefas assíncronas para envio,
    recebimento e monitoramento da conexão.

    Args:
        host (str): Endereço do servidor WebSocket.
        user_id (str): ID do usuário cliente.
        recipient_id (str): ID do destinatário com quem será feita a comunicação.
    """
    uri = f'ws://{host}/ws/{user_id}@{recipient_id}'
    async with websockets.connect(uri) as websocket:
        try:
            # Tarefas para enviar e receber mensagens
            receive_task = asyncio.create_task(receive_messages(websocket))
            send_task = asyncio.create_task(send_messages(websocket))

            # Monitora a variável "running" para encerrar as tarefas quando necessário
            async def monitor_running():
                while True:
                    if not running:
                        receive_task.cancel()
                        send_task.cancel()
                        break
                    await asyncio.sleep(0.5)

            monitor_task = asyncio.create_task(monitor_running())

            try:
                # Aguarda até que todas as tarefas terminem
                await asyncio.gather(receive_task, send_task, monitor_task)
            except asyncio.CancelledError:
                pass
            finally:
                # Cancela tarefas que não terminaram
                await asyncio.gather(
                    *[
                        task
                        for task in [receive_task, send_task, monitor_task]
                        if not task.done()
                    ],
                    return_exceptions=True,
                )
        except websockets.ConnectionClosedOK:
            print('Connection closed by server.')
        except websockets.ConnectionClosedError:
            print('Connection closed abruptly.')
        except asyncio.CancelledError:
            print('All canceled')
            typer.Exit(1)
        except Exception as e:
            print(f'Error receiving messages: {e}')


@app.command()
def start(user_id: str, recipient_id: str):
    """Comando da CLI para iniciar o app.

    Se o endereço do servidor não estiver definido nas variáveis de ambiente,
    será solicitado ao usuário.

    Args:
        user_id (str): ID do usuário cliente.
        recipient_id (str): ID do destinatário para se comunicar.
    """
    global host_address
    if not host_address:
        host_address = str(typer.prompt('Server address')).strip()

    asyncio.run(client(host_address, user_id, recipient_id))
