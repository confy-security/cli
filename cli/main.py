import asyncio
import base64

import typer
import websockets
from confy_addons.encryption import (
    aes_decrypt,
    aes_encrypt,
    deserialize_public_key,
    generate_aes_key,
    generate_rsa_keypair,
    rsa_decrypt,
    rsa_encrypt,
    serialize_public_key,
)
from confy_addons.prefixes import AES_KEY_PREFIX, AES_PREFIX, KEY_EXCHANGE_PREFIX, SYSTEM_PREFIX
from rich import print

from cli.settings import get_settings
from cli.utils import debug, keep

app = typer.Typer()
running = True
settings = get_settings()
host_address = settings.SERVER_HOST

private_key, public_key = generate_rsa_keypair()
peer_public_key = None
peer_aes_key = None
public_sent = False

# ids (atribua em client(): my_id = user_id; peer_id = recipient_id)
my_id = None
peer_id = None


async def receive_messages(websocket):
    """Lida com o recebimento de mensagens via WebSocket.

    Imprime as mensagens recebidas no terminal.
    Caso o outro usuário se desconecte, encerra a execução do cliente.

    Args:
        websocket: Conexão WebSocket que deve ser monitorada.
    """
    global running, peer_public_key, peer_aes_key, public_sent
    try:
        while running:
            try:
                message = await websocket.recv()
            except websockets.ConnectionClosed:
                print(
                    '[bold yellow]Conexão fechada pelo servidor '
                    'ou pelo destinatário.[/bold yellow]'
                )
                print('Pressione ENTER para sair.')
                running = False
                break

            # Mensagens do servidor (não criptografadas)
            if isinstance(message, str) and message.startswith(SYSTEM_PREFIX):
                if message == f'{SYSTEM_PREFIX} O usuário destinatário agora está conectado.':
                    # Envia a chave pública automaticamente apenas uma vez
                    if not public_sent:
                        pub_b64 = serialize_public_key(public_key)

                        await websocket.send(f'{KEY_EXCHANGE_PREFIX}{pub_b64}')

                        public_sent = True
                        debug('Enviou a chave pública para o peer.')

                        # Não enviamos a mensagem do usuário agora — garantimos handshake primeiro.
                        print(f'[bold yellow]{message}[/bold yellow]')
                        keep()
                        continue
                print(f'[bold yellow]{message}[/bold yellow]')
                keep()
                continue

            # Recebe chave pública do peer
            elif isinstance(message, str) and message.startswith(KEY_EXCHANGE_PREFIX):
                b64_key = message[len(KEY_EXCHANGE_PREFIX) :]
                try:
                    peer_public_key = deserialize_public_key(b64_key)
                    debug('Chave pública recebida do peer.')
                except Exception as e:
                    print(f'[ERROR] Chave pública de peer inválida: {e}')
                    continue

                # Determinar quem deve gerar a AES (regra determinística)
                # Apenas um dos lados deve gerar e enviar a chave AES.
                # Exemplo: o lado com my_id > peer_id gera a chave.
                should_generate = False
                if peer_aes_key is None:
                    if my_id is None or peer_id is None:
                        # fallback: gera se não souber ids (menos ideal)
                        should_generate = True
                    else:
                        should_generate = str(my_id) > str(peer_id)

                if should_generate:
                    try:
                        aes_key = generate_aes_key()
                        encrypted_key = rsa_encrypt(peer_public_key, aes_key)
                        b64_encrypted_key = base64.b64encode(encrypted_key).decode()

                        await websocket.send(f'{AES_KEY_PREFIX}{b64_encrypted_key}')

                        debug(f'encrypted AES key: {b64_encrypted_key}')
                        debug(f'plain-text AES key: {aes_key}')

                        peer_aes_key = aes_key
                        debug('Chave AES gerada e enviada ao peer.')
                    except Exception as e:
                        print(f'[ERROR] Falha ao gerar/enviar chave AES: {e}')
                continue

            # Recebe chave AES cifrada (o outro lado foi o gerador)
            elif isinstance(message, str) and message.startswith(AES_KEY_PREFIX):
                b64_enc = message[len(AES_KEY_PREFIX) :]
                try:
                    encrypted_key = base64.b64decode(b64_enc)
                    aes_key = rsa_decrypt(private_key, encrypted_key)
                    peer_aes_key = aes_key
                    debug('Chave AES recebida e descriptografada com sucesso.')
                except Exception as e:
                    print(f'[ERROR] Falha ao descriptografar a chave AES: {e}')
                continue

            # Mensagem criptografada com AES (nosso prefixo AES_PREFIX)
            elif isinstance(message, str) and message.startswith(AES_PREFIX):
                if peer_aes_key is None:
                    print(
                        '[WARN] Mensagem criptografada recebida, '
                        'mas a chave AES não está definida. Ignorando.'
                    )
                    continue

                b64_payload = message[len(AES_PREFIX) :]
                try:
                    decrypted = aes_decrypt(peer_aes_key, b64_payload)
                    # opcional: mostrar payload para debug
                    debug(f'payload (b64) -> {b64_payload}')

                    print(f'[bold green]RECEIVED:[/bold green] {decrypted}')
                    keep()
                except Exception as e:
                    # Descriptografia falhou -> mostra aviso e payload bruto para debug
                    print(f'[ERROR] Falha ao descriptografar a mensagem: {e}')
                continue

            # Fallback: mensagem em plaintext (sem prefixo conhecido)
            print(f'[bold green]RECEIVED (plaintext):[/bold green] {message}')
            keep()

    except Exception as e:
        print(f'\nErro ao receber mensagem: {e}')
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
            message = await asyncio.to_thread(input, '> ')

            if message.lower() == 'exit':
                running = False
                break

            # Se já temos a chave AES, criptografa a mensagem e envia com o prefixo AES_PREFIX
            if peer_aes_key:
                try:
                    encrypted_payload = aes_encrypt(peer_aes_key, message)  # retorna base64 string

                    await websocket.send(f'{AES_PREFIX}{encrypted_payload}')
                except Exception as e:
                    print(f'[ERROR] Falha ao criptografar/enviar mensagem: {e}')
            else:
                # Ainda não há AES; recomendamos não enviar texto puro para evitar confusão
                print(
                    '[WARN] A chave AES ainda não foi estabelecida. '
                    'Aguarde um momento (handshake).'
                )

        except Exception as e:
            print(f'Erro ao enviar mensagem: {e}')
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

    global my_id, peer_id

    my_id = user_id
    peer_id = recipient_id

    async with websockets.connect(uri) as websocket:
        try:
            # Tarefas para enviar e receber mensagens
            send_task = asyncio.create_task(send_messages(websocket))
            receive_task = asyncio.create_task(receive_messages(websocket))

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
                    *[task for task in [receive_task, send_task, monitor_task] if not task.done()],
                    return_exceptions=True,
                )
        except websockets.ConnectionClosedOK:
            print('Conexão fechada pelo servidor.')
        except websockets.ConnectionClosedError:
            print('Conexão fechada abruptamente.')
        except asyncio.CancelledError:
            print('Tudo cancelado')
            typer.Exit(1)
        except Exception as e:
            print(f'Erro ao receber mensagens: {e}')


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
        host_address = str(typer.prompt('Endereço do servidor')).strip()

    asyncio.run(client(host_address, user_id, recipient_id))
