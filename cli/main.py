import asyncio
import base64
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path

import typer
import websockets
from confy_addons import AESEncryption, RSAEncryption, RSAPublicEncryption, deserialize_public_key
from confy_addons.core.constants import RAW_PAYLOAD_LENGTH
from confy_addons.prefixes import AES_KEY_PREFIX, AES_PREFIX, KEY_EXCHANGE_PREFIX, SYSTEM_PREFIX
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from rich import print

from cli.settings import get_settings
from cli.utils import alert, debug, get_protocol, is_prefix, received, received_plaintext

app = typer.Typer()
running = True
settings = get_settings()

rsa = RSAEncryption()
peer_public_key = None
peer_aes_key = None
public_sent = False

# ids (atribua em client(): my_id = user_id; peer_id = recipient_id)
my_id = None
peer_id = None

# Executor de threads para rodar tarefas bloqueantes
# Usado para rodar prompts de entrada do usuário (prompt_toolkit) em paralelo
# ao loop assíncrono, evitando travar a comunicação WebSocket.
# max_workers=1 garante que apenas um prompt rode por vez.
executor = ThreadPoolExecutor(max_workers=1)


# Configurações do prompt de endereço do servidor
# Caminho do arquivo de histórico de endereço do servidor
history_path = Path('~/.confy_address_history').expanduser()

# Garantir que o diretório exista
history_path.parent.mkdir(parents=True, exist_ok=True)

# Garantir que o arquivo exista
if not history_path.exists():
    history_path.touch()

prompt_address_session = PromptSession(history=FileHistory(str(history_path)))
server_address_completer = WordCompleter(['http://', 'https://'])

# Configurações do prompt de mensagem
prompt_message_session = PromptSession()
message_completer = WordCompleter(['exit'])


async def read_input(prompt: str) -> str:
    """Lê a entrada do usuário no terminal de forma assíncrona.

    Essa função executa a chamada bloqueante `input()` em um executor
    de threads para evitar travar o loop de eventos, permitindo que
    outras tarefas assíncronas continuem rodando enquanto o usuário digita.

    Args:
        prompt (str): Texto exibido como solicitação no terminal.

    Returns:
        str: Texto digitado pelo usuário.

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
    """Gerencia o recebimento e processamento de mensagens via WebSocket.

    Esta função é responsável por:
    - Ler mensagens recebidas do servidor ou do peer.
    - Processar mensagens de controle do sistema (prefixo SYSTEM_PREFIX).
    - Executar o handshake inicial de troca de chaves públicas RSA
      (prefixo KEY_EXCHANGE_PREFIX).
    - Receber e descriptografar chaves AES enviadas pelo peer
      (prefixo AES_KEY_PREFIX).
    - Receber, descriptografar e exibir mensagens criptografadas com AES
      (prefixo AES_PREFIX).
    - Exibir mensagens em texto puro quando não possuem prefixo conhecido.

    Caso a conexão seja encerrada pelo servidor ou pelo peer, a função
    encerra o loop de execução e sinaliza o encerramento do cliente.

    Args:
        websocket (websockets.WebSocketClientProtocol):
            Conexão WebSocket ativa a ser monitorada para recebimento de mensagens.

    Side Effects:
        - Pode alterar variáveis globais relacionadas à sessão
          (`peer_public_key`, `peer_aes_key`, `public_sent`, `running`).
        - Pode enviar mensagens de volta ao peer como parte do handshake.

    Raises:
        Exception: Para erros inesperados durante o processamento
        ou descriptografia das mensagens.

    """
    global running, peer_public_key, peer_aes_key, public_sent
    try:
        while running:
            try:
                message = await websocket.recv()
            except websockets.ConnectionClosed:
                running = False
                alert('Conexão fechada pelo servidor ou pelo destinatário.')
                try:
                    executor.shutdown(wait=False, cancel_futures=True)
                    prompt_message_session.app.exit()  # encerra o prompt imediatamente
                except Exception:
                    pass
                break

            # Mensagens do servidor (não criptografadas)
            if is_prefix(message, SYSTEM_PREFIX):
                if message == f'{SYSTEM_PREFIX} O usuário destinatário agora está conectado.':
                    # Envia a chave pública automaticamente apenas uma vez
                    if not public_sent:
                        await websocket.send(f'{KEY_EXCHANGE_PREFIX}{rsa.base64_public_key}')

                        public_sent = True
                        debug('Enviou a chave pública para o peer.')

                        # Não enviamos a mensagem do usuário agora — garantimos handshake primeiro.
                        alert(message)
                        continue
                alert(message)
                continue

            # Recebe chave pública do peer
            elif is_prefix(message, KEY_EXCHANGE_PREFIX):
                debug(message)
                b64_key = message[len(KEY_EXCHANGE_PREFIX) :]
                try:
                    peer_public_key = deserialize_public_key(b64_key)
                    debug('Chave pública recebida do peer.')
                except Exception as e:
                    print(f'[ERROR] Chave pública de peer inválida: {e}')
                    continue

                if not public_sent:
                    try:
                        await websocket.send(f'{KEY_EXCHANGE_PREFIX}{rsa.base64_public_key}')
                        public_sent = True
                        debug('Enviou a chave pública de volta para o peer.')
                    except Exception as e:
                        print(f'[ERROR] Falha ao enviar minha chave pública: {e}')
                        continue

                if peer_aes_key is None and public_sent:
                    should_generate = str(my_id) > str(peer_id)
                    if should_generate:
                        aes = AESEncryption()
                        encrypted_key = RSAPublicEncryption(peer_public_key).encrypt(aes.key)
                        b64_encrypted_key = base64.b64encode(encrypted_key).decode()
                        await websocket.send(f'{AES_KEY_PREFIX}{b64_encrypted_key}')
                        peer_aes_key = aes.key
                        debug('Chave AES gerada e enviada.')

            # Recebe chave AES cifrada (o outro lado foi o gerador)
            elif is_prefix(message, AES_KEY_PREFIX):
                b64_enc = message[len(AES_KEY_PREFIX) :]
                try:
                    encrypted_key = base64.b64decode(b64_enc)
                    aes_key = rsa.decrypt(encrypted_key)
                    peer_aes_key = AESEncryption(key=aes_key).key
                    debug('Chave AES recebida e descriptografada com sucesso.')
                except Exception as e:
                    print(f'[ERROR] Falha ao descriptografar a chave AES: {e}')
                continue

            # Mensagem criptografada com AES (nosso prefixo AES_PREFIX)
            elif is_prefix(message, AES_PREFIX):
                if peer_aes_key is None:
                    print(
                        '[WARN] Mensagem criptografada recebida, '
                        'mas a chave AES não está definida. Ignorando.'
                    )
                    continue

                # <--- INÍCIO DA LÓGICA DE VERIFICAÇÃO DE ASSINATURA (MODIFICADO) --->
                try:
                    # 1. Extrai o payload bruto (contém msg + assinatura)
                    raw_payload_with_sig = message[len(AES_PREFIX) :]

                    # 2. Separa o payload da assinatura (usando '::' como separador)
                    parts = raw_payload_with_sig.split('::')
                    if len(parts) != RAW_PAYLOAD_LENGTH:
                        print('[ERROR] Payload de mensagem malformado recebido. Descartando.')
                        continue

                    b64_payload = parts[0]
                    b64_signature = parts[1]

                    # 3. Descriptografa a mensagem
                    # <--- MODIFICADO: Usa a classe AESEncryption
                    decrypted_message = AESEncryption(peer_aes_key).decrypt(b64_payload)

                    # 4. Prepara dados para verificação
                    decrypted_bytes = decrypted_message.encode('utf-8')
                    signature_bytes = base64.b64decode(b64_signature)

                    # 5. VERIFICA a assinatura com a chave pública do peer
                    #    Criamos uma instância RSAPublicEncryption temporária para isso
                    # <--- MODIFICADO: Usa a classe RSAPublicEncryption
                    RSAPublicEncryption(peer_public_key).verify(decrypted_bytes, signature_bytes)

                    # 6. SUCESSO: Se a verificação não lançou exceção, a msg é válida
                    debug(f'payload (b64) -> {b64_payload}')
                    received(decrypted_message)

                except Exception as e:
                    # Falha na verificação! Mensagem pode ter sido adulterada ou corrompida.
                    print(f'[CRITICAL] ASSINATURA INVÁLIDA! Mensagem descartada. ({e})')
                    continue  # Descarta a mensagem

                except Exception as e:
                    # Erro na descriptografia, decodificação base64, etc.
                    print(f'[ERROR] Falha ao descriptografar/verificar a mensagem: {e}')
                    continue
                # <--- FIM DA LÓGICA DE VERIFICAÇÃO DE ASSINATURA --->
            else:
                # Fallback: mensagem em plaintext (sem prefixo conhecido)
                received_plaintext(message)
    except Exception as e:
        print(f'\nErro ao receber mensagem: {e}')
        running = False


async def send_messages(websocket):
    """Gerencia o envio de mensagens pelo WebSocket.

    Esta função lê mensagens digitadas no terminal pelo usuário e as envia
    para o peer conectado via WebSocket. Caso uma chave AES já tenha sido
    estabelecida, a mensagem será criptografada com AES antes do envio.
    Digitar "exit" encerra a sessão de envio.

    Fluxo de execução:
        1. Aguarda o input do usuário.
        2. Se a mensagem for "exit", encerra o loop e finaliza a função.
        3. Se existir `peer_aes_key`, criptografa a mensagem com AES e envia.
        4. Caso contrário, exibe um aviso informando que a chave ainda não foi estabelecida.

    Args:
        websocket: Objeto WebSocket conectado que será usado para enviar mensagens.

    Exceptions:
        Exception: Captura e exibe qualquer erro ocorrido durante o envio
        ou criptografia da mensagem, encerrando o loop de execução.

    Observação:
        O estado global `running` é usado para controlar o loop de envio.

    """
    global running
    while running:
        try:
            message = await read_input('> ')

            if message.lower() == 'exit':
                running = False
                break

            # Se já temos a chave AES, criptografa E ASSINA a mensagem
            if peer_aes_key:
                try:
                    # <--- INÍCIO DA LÓGICA DE ASSINATURA (MODIFICADO) --->

                    # 1. Criptografa a mensagem com AES
                    #    (A classe AESEncryption já retorna base64 string)
                    # <--- MODIFICADO: Usa a classe AESEncryption
                    encrypted_payload = AESEncryption(peer_aes_key).encrypt(message)

                    # 2. Assina a mensagem ORIGINAL (em bytes) com nossa chave privada
                    #    Usamos a instância global 'rsa'
                    message_bytes = message.encode('utf-8')
                    # <--- MODIFICADO: Usa o método da instância 'rsa'
                    signature = rsa.sign(message_bytes)

                    # 3. Codifica a assinatura em base64
                    b64_signature = base64.b64encode(signature).decode('utf-8')

                    # 4. Envia payload e assinatura (separados por '::')
                    final_payload = f'{AES_PREFIX}{encrypted_payload}::{b64_signature}'
                    await websocket.send(final_payload)

                    # <--- FIM DA LÓGICA DE ASSINATURA --->
                except Exception as e:
                    print(f'[ERROR] Falha ao criptografar/assinar/enviar mensagem: {e}')
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


async def client(server_address: str, user_id: str, recipient_id: str):
    """Abre uma conexão WebSocket com o servidor e gerencia a comunicação entre dois usuários.

    A função cria e mantém três tarefas assíncronas:
      - Envio de mensagens para o servidor.
      - Recebimento de mensagens do servidor.
      - Monitoramento do estado global `running` para encerrar a comunicação.

    Args:
        server_address (str): Endereço do servidor WebSocket (sem protocolo).
        user_id (str): ID do usuário cliente.
        recipient_id (str): ID do destinatário para a comunicação.

    Raises:
        websockets.ConnectionClosedOK: Quando a conexão é encerrada normalmente pelo servidor.
        websockets.ConnectionClosedError: Quando a conexão é encerrada de forma abrupta.
        asyncio.CancelledError: Quando as tarefas são canceladas manualmente.
        Exception: Para outros erros durante a conexão ou execução.

    Side Effects:
        - Atualiza as variáveis globais `my_id` e `peer_id`.
        - Exibe mensagens no terminal sobre o status da conexão.

    """
    protocol, host = get_protocol(server_address)
    uri = f'{protocol}://{host}/ws/{user_id}@{recipient_id}'

    global my_id, peer_id

    my_id = user_id
    peer_id = recipient_id

    try:
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
                        await asyncio.sleep(0.5)  # NÃO EXCLUA ESSA LINHA. Ass.: @henriquesebastiao

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
                print('Conexão fechada pelo servidor.')
            except websockets.ConnectionClosedError:
                print('Conexão fechada abruptamente.')
            except asyncio.CancelledError:
                print('Tudo cancelado')
                typer.Exit(1)
            except Exception as e:
                print(f'Erro ao receber mensagens: {e}')
    except Exception:
        print('Erro ao conectar ao servidor, verifique o endereço fornecido.')


@app.command()
def start(user_id: str, recipient_id: str):
    """Comando da CLI para iniciar o cliente de mensagens.

    Ao ser executado, solicita (se necessário) o endereço do servidor e
    inicia a conexão WebSocket com o servidor, permitindo a troca de mensagens
    entre o usuário e o destinatário especificado.

    Args:
        user_id (str): ID único do usuário cliente.
        recipient_id (str): ID único do destinatário para comunicação.

    Behavior:
        - Se a variável de ambiente `SERVER_HOST` não estiver definida,
          o endereço será solicitado via prompt interativo.
        - A função é executada de forma síncrona, mas inicia o cliente assíncrono
          usando `asyncio.run()`.

    Raises:
        Exception: Propaga erros de conexão ou execução ocorridos no cliente.

    """
    host_address = str(
        prompt_address_session.prompt(
            'Endereço do servidor: ',
            completer=server_address_completer,
            auto_suggest=AutoSuggestFromHistory(),
        )
    ).strip()
    asyncio.run(client(host_address, user_id, recipient_id))
