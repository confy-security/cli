import asyncio

import typer
import websockets
from decouple import config
from rich import print

app = typer.Typer()
running = True
host_address = config('SERVER_HOST', default='', cast=str)


async def receive_messages(websocket):
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
            print('> ', end='')
    except Exception as e:
        print(f'\nError receiving message: {e}')
        running = False


async def send_messages(websocket):
    global running
    while running:
        try:
            message = await asyncio.to_thread(input, '> ')

            if message.lower() == 'exit':
                running = False
                break

            await websocket.send(message)
        except Exception as e:
            print(f'Error sending message: {e}')
            running = False
            break


async def client(host: str, user_id: str, recipient_id: str):
    uri = f'ws://{host}/ws/{user_id}@{recipient_id}'
    async with websockets.connect(uri) as websocket:
        try:
            receive_task = asyncio.create_task(receive_messages(websocket))
            send_task = asyncio.create_task(send_messages(websocket))

            async def monitor_running():
                while True:
                    if not running:
                        receive_task.cancel()
                        send_task.cancel()
                        break
                    await asyncio.sleep(0.5)

            monitor_task = asyncio.create_task(monitor_running())

            try:
                await asyncio.gather(receive_task, send_task, monitor_task)
            except asyncio.CancelledError:
                pass
            finally:
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
    global host_address
    if not host_address:
        host_address = str(typer.prompt('Server address')).strip()

    asyncio.run(client(host_address, user_id, recipient_id))
