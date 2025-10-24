"""Confy encrypted messaging CLI client.

This module provides a command-line interface for establishing encrypted peer-to-peer
communication using the Confy secure messaging system. It handles WebSocket connections,
RSA key exchange, AES key encryption, and message encryption/decryption.
"""

import asyncio
import base64
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path

import typer
import websockets
from confy_addons import AESEncryption, RSAEncryption, RSAPublicEncryption, deserialize_public_key
from confy_addons.prefixes import AES_KEY_PREFIX, AES_PREFIX, KEY_EXCHANGE_PREFIX, SYSTEM_PREFIX
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from rich import print

from confy_cli.core.constants import RAW_PAYLOAD_LENGTH
from confy_cli.settings import get_settings
from confy_cli.utils import alert, debug, get_protocol, is_prefix, received, received_plaintext

app = typer.Typer()
running = True
settings = get_settings()

rsa = RSAEncryption()
peer_public_key: object | None = None
peer_aes_key: bytes | None = None
public_sent = False

my_id: str | None = None
peer_id: str | None = None

# Thread executor for running blocking tasks
# Used to run user input prompts (prompt_toolkit) in parallel
# to the asynchronous loop, avoiding blocking WebSocket communication.
# max_workers=1 ensures that only one prompt runs at a time.
executor = ThreadPoolExecutor(max_workers=1)


# Server Address Prompt Settings
# Server Address History File Path
history_path = Path('~/.confy_address_history').expanduser()

history_path.parent.mkdir(parents=True, exist_ok=True)

if not history_path.exists():
    history_path.touch()

prompt_address_session: PromptSession = PromptSession(history=FileHistory(str(history_path)))
server_address_completer = WordCompleter(['http://', 'https://'])

prompt_message_session: PromptSession = PromptSession()
message_completer = WordCompleter(['exit'])


async def read_input(prompt: str) -> str:
    """Read user input from terminal asynchronously.

    This function executes the blocking `input()` call in a thread executor
    to prevent blocking the event loop, allowing other async tasks to continue
    running while the user types.

    Args:
        prompt: Display text shown as input solicitation in terminal.

    Returns:
        str: The text typed by the user.

    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        executor,
        partial(
            prompt_message_session.prompt,
            prompt,
            completer=message_completer,
            auto_suggest=AutoSuggestFromHistory(),
        ),
    )


async def receive_messages(websocket):
    """Manage receiving and processing messages via WebSocket.

    This function is responsible for:
    - Reading messages received from the server or peer.
    - Processing system control messages (SYSTEM_PREFIX prefix).
    - Executing the initial RSA public key exchange handshake
      (KEY_EXCHANGE_PREFIX prefix).
    - Receiving and decrypting AES keys sent by peer
      (AES_KEY_PREFIX prefix).
    - Receiving, decrypting and displaying AES-encrypted messages
      (AES_PREFIX prefix).
    - Displaying plaintext messages when no known prefix is present.

    If the connection is closed by server or peer, the function
    terminates the execution loop and signals client shutdown.

    Args:
        websocket: Active WebSocket connection to monitor for incoming messages.

    Side Effects:
        - May modify global session-related variables
          (`peer_public_key`, `peer_aes_key`, `public_sent`, `running`).
        - May send messages back to peer as part of handshake.

    Raises:
        Exception: For unexpected errors during message processing
            or decryption.

    """
    global running, peer_public_key, peer_aes_key, public_sent
    try:
        while running:
            try:
                message = await websocket.recv()
            except websockets.ConnectionClosed:
                running = False
                alert('Connection closed by server or recipient.')
                try:
                    executor.shutdown(wait=False, cancel_futures=True)
                    prompt_message_session.app.exit()
                except Exception:
                    pass  # nosec
                break

            # Server messages (unencrypted)
            if is_prefix(message, SYSTEM_PREFIX):
                # NÃO TRADUZIR A STRING ABAIXO ENQUANTO NÃO FOR ALTERADA NO SERVIDOR
                if message == f'{SYSTEM_PREFIX} O usuário destinatário agora está conectado.':
                    if not public_sent:
                        await websocket.send(f'{KEY_EXCHANGE_PREFIX}{rsa.base64_public_key}')

                        public_sent = True
                        debug('Public key sent to peer.')

                        # We don't send the user's message now — we guarantee handshake first
                        alert(message)
                        continue
                alert(message)
                continue

            # Receives public key from peer
            elif is_prefix(message, KEY_EXCHANGE_PREFIX):
                debug(message)
                b64_key = message[len(KEY_EXCHANGE_PREFIX) :]
                try:
                    peer_public_key = deserialize_public_key(b64_key)
                    debug('Public key received from peer.')
                except Exception as e:
                    print(f'[ERROR] Invalid peer public key: {e}')
                    continue

                if not public_sent:
                    try:
                        await websocket.send(f'{KEY_EXCHANGE_PREFIX}{rsa.base64_public_key}')
                        public_sent = True
                        debug('Public key sent back to peer.')
                    except Exception as e:
                        print(f'[ERROR] Failed to send public key: {e}')
                        continue

                if peer_aes_key is None and public_sent:
                    should_generate = str(my_id) > str(peer_id)
                    if should_generate:
                        aes = AESEncryption()
                        encrypted_key = RSAPublicEncryption(peer_public_key).encrypt(aes.key)
                        b64_encrypted_key = base64.b64encode(encrypted_key).decode()
                        await websocket.send(f'{AES_KEY_PREFIX}{b64_encrypted_key}')
                        peer_aes_key = aes.key
                        debug('AES key generated and sent.')

            # Receives encrypted AES key (the other side was the generator)
            elif is_prefix(message, AES_KEY_PREFIX):
                b64_enc = message[len(AES_KEY_PREFIX) :]
                try:
                    encrypted_key = base64.b64decode(b64_enc)
                    aes_key = rsa.decrypt(encrypted_key)
                    peer_aes_key = AESEncryption(key=aes_key).key
                    debug('AES key received and decrypted successfully.')
                except Exception as e:
                    print(f'[ERROR] Failed to decrypt AES key: {e}')
                continue

            # Message encrypted with AES (our prefix AES_PREFIX)
            elif is_prefix(message, AES_PREFIX):
                if peer_aes_key is None:
                    print('[WARN] Encrypted message received, but AES key is not set. Ignoring.')
                    continue

                # START OF SIGNATURE VERIFICATION
                try:
                    # Extracts the raw payload (contains msg + signature)
                    raw_payload_with_sig = message[len(AES_PREFIX) :]

                    # Separates the payload from the signature (using '::' as separator)
                    parts = raw_payload_with_sig.split('::')
                    if len(parts) != RAW_PAYLOAD_LENGTH:
                        print('[ERROR] Malformed message payload received. Discarding.')
                        continue

                    b64_payload = parts[0]
                    b64_signature = parts[1]

                    # Decrypt the message
                    decrypted_message = AESEncryption(peer_aes_key).decrypt(b64_payload)

                    # Prepare data for verification
                    decrypted_bytes = decrypted_message.encode('utf-8')
                    signature_bytes = base64.b64decode(b64_signature)

                    # VERIFIES the signature with the peer's public key
                    RSAPublicEncryption(peer_public_key).verify(decrypted_bytes, signature_bytes)

                    # SUCCESS: If the check did not throw an exception, the msg is valid
                    debug(f'payload (b64) -> {b64_payload}')
                    received(decrypted_message)

                except Exception as e:
                    # Error in decryption, base64 decoding, etc.
                    print(f'[ERROR] Failed to decrypt/verify message: {e}')
                    continue
                # END OF SIGNATURE VERIFICATION
            else:
                # Fallback: plaintext message (no known prefix)
                received_plaintext(message)
    except Exception as e:
        print(f'\nError receiving message: {e}')
        running = False


async def send_messages(websocket):
    """Manage sending messages via WebSocket.

    This function reads messages typed in the terminal by the user and sends them
    to the connected peer via WebSocket. If an AES key has already been
    established, the message will be encrypted with AES before transmission.
    Typing "exit" terminates the sending session.

    Execution flow:
        1. Awaits user input.
        2. If message is "exit", terminates loop and finalizes function.
        3. If `peer_aes_key` exists, encrypts message with AES and sends.
        4. Otherwise, displays warning that key has not been established yet.

    Args:
        websocket: Connected WebSocket object used to send messages.

    Exceptions:
        Exception: Captures and displays any error during message sending
            or encryption, terminating the execution loop.

    Note:
        The global `running` state is used to control the send loop.

    """
    global running
    while running:
        try:
            message = await read_input('> ')

            if message.lower() == 'exit':
                running = False
                break

            # If we already have the AES key, encrypt AND SIGN the message
            if peer_aes_key:
                try:
                    # START OF SIGNATURE

                    # Encrypt the message with AES
                    encrypted_payload = AESEncryption(peer_aes_key).encrypt(message)

                    # Sign the ORIGINAL message (in bytes) with our private key
                    # We use the global instance 'rsa'
                    message_bytes = message.encode('utf-8')
                    signature = rsa.sign(message_bytes)

                    # Encodes the signature in base64
                    b64_signature = base64.b64encode(signature).decode('utf-8')

                    # Sends payload and signature (separated by '::')
                    final_payload = f'{AES_PREFIX}{encrypted_payload}::{b64_signature}'
                    await websocket.send(final_payload)

                    # END OF SIGNATURE
                except Exception as e:
                    print(f'[ERROR] Failed to encrypt/send message: {e}')
            else:
                # There is no AES yet; we recommend not sending plain text to avoid confusion.
                print(
                    '[WARN] AES key has not been established yet. '
                    'Please wait a moment (handshake in progress).'
                )

        except Exception as e:
            print(f'Error sending message: {e}')
            running = False
            break


async def client(server_address: str, user_id: str, recipient_id: str) -> None:
    """Open WebSocket connection and manage peer-to-peer communication.

    This function creates and maintains three async tasks:
      - Send messages to server.
      - Receive messages from server.
      - Monitor global `running` state to terminate communication.

    Args:
        server_address: Server address without protocol scheme.
        user_id: ID of the client user.
        recipient_id: ID of the recipient for communication.

    Raises:
        websockets.ConnectionClosedOK: When connection is normally closed by server.
        websockets.ConnectionClosedError: When connection closes abruptly.
        asyncio.CancelledError: When tasks are manually cancelled.
        Exception: For other errors during connection or execution.

    Side Effects:
        - Updates global variables `my_id` and `peer_id`.
        - Displays messages on terminal about connection status.

    """
    protocol, host = get_protocol(server_address)
    uri = f'{protocol}://{host}/ws/{user_id}@{recipient_id}'

    global my_id, peer_id

    my_id = user_id
    peer_id = recipient_id

    try:
        async with websockets.connect(uri) as websocket:
            try:
                # Tasks for sending and receiving messages
                send_task = asyncio.create_task(send_messages(websocket))
                receive_task = asyncio.create_task(receive_messages(websocket))

                async def monitor_running() -> None:
                    """Monitor the running flag and cancel tasks when needed."""
                    while True:
                        if not running:
                            receive_task.cancel()
                            send_task.cancel()
                            break
                        await asyncio.sleep(0.5)

                monitor_task = asyncio.create_task(monitor_running())

                try:
                    # Waits until all tasks are finished
                    await asyncio.gather(receive_task, send_task, monitor_task)
                except asyncio.CancelledError:
                    pass
                finally:
                    # Cancel tasks that have not finished
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
                print('All tasks cancelled.')
                typer.Exit(1)
            except Exception as e:
                print(f'Error receiving messages: {e}')
    except Exception:
        print('Error connecting to server. Please verify the address provided.')


@app.command()
def start(user_id: str, recipient_id: str) -> None:
    """Start the encrypted messaging CLI client.

    When executed, this command requests the server address (if necessary)
    and initiates the WebSocket connection with the server, enabling message
    exchange between the user and specified recipient.

    Args:
        user_id: Unique identifier of the client user.
        recipient_id: Unique identifier of the recipient for communication.

    Behavior:
        - If `SERVER_HOST` environment variable is not set,
          the address will be requested via interactive prompt.
        - The function executes synchronously but starts the async client
          using `asyncio.run()`.

    Raises:
        Exception: Propagates connection or execution errors from client.

    """
    host_address = str(
        prompt_address_session.prompt(
            'Server address: ',
            completer=server_address_completer,
            auto_suggest=AutoSuggestFromHistory(),
        )
    ).strip()
    asyncio.run(client(host_address, user_id, recipient_id))
