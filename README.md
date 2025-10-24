<h1 align="center">
  <a href="https://github.com/confy-security/cli" target="_blank" rel="noopener noreferrer">
    <picture>
      <img width="80" src="https://github.com/user-attachments/assets/d95cfc93-8a78-4545-a9ba-ba6b9000795b">
    </picture>
  </a>
  <br>
  Confy CLI
</h1>

<p align="center">A command-line client for the Confy encrypted communication system.</p>

<div align="center">

[![Test](https://github.com/confy-security/cli/actions/workflows/test.yml/badge.svg)](https://github.com/confy-security/cli/actions/workflows/test.yml)
[![GitHub License](https://img.shields.io/github/license/confy-security/cli?color=blue)](/LICENSE)
[![Visitors](https://api.visitorbadge.io/api/visitors?path=confy-security%2Fcli&label=repository%20visits&countColor=%231182c3&style=flat)](https://github.com/confy-security/cli)
  
</div>

---

A secure command-line interface for peer-to-peer encrypted messaging using the Confy communication system. This CLI enables users to establish encrypted connections with other peers, exchange cryptographic keys, and communicate with end-to-end encryption using industry-standard algorithms.

Learn more about the project at [github.com/confy-security](https://github.com/confy-security)

Made with dedication by students from Brazil 🇧🇷.

## ⚡ Features

- **End-to-End Encryption** - Messages are encrypted using AES-256 in CFB mode
- **Digital Signatures** - Messages are signed using RSA with PSS padding for authenticity
- **Secure Key Exchange** - RSA-4096 key exchange with OAEP padding
- **Interactive Terminal** - User-friendly command-line interface using prompt-toolkit and Typer
- **Debug Mode** - Detailed logging for troubleshooting and development
- **Cross-Platform** - Works on Windows, macOS, and Linux
- **WebSocket Support** - Secure peer-to-peer communication over WebSocket (WSS)

## ⚙️ Requirements

- **Python:** 3.13 or higher
- **OS:** Windows, macOS, or Linux

## 📦 Installation

Install the CLI globally with your package manager of choice.

```shell
pipx install confy-cli
```

## 🚀 Quick Start

### Basic Usage

Start a secure conversation with another peer:

```bash
confy start your-user-id recipient-user-id
```

When prompted, enter the server address:

```txt
Server address: wss://secure-server.example.com
```

> [!TIP]
> To learn how to deploy your own self-hosted Confy server, see [github.com/confy-security/server](https://github.com/confy-security/server).

### Interactive Commands

Once connected, you can:

- **Send messages** - Type your message and press Enter
- **Receive messages** - Messages from peers appear in real-time
- **Exit** - Type `exit` to end the session

### Example Session

```bash
$ confy start alice bob
Server address: wss://secure-server.example.com
[SYSTEM] Waiting for recipient to connect...
[SYSTEM] The recipient is now connected.
> Hello Bob, this is Alice!
[RECEIVED] Hi Alice! I received your message.
> exit
```

## 🔒 Security Architecture

### Key Exchange Process

1. **RSA Key Generation** - Each client generates a 4096-bit RSA key pair
2. **Public Key Exchange** - Public keys are exchanged securely over WebSocket
3. **AES Key Generation** - A random 256-bit AES key is generated
4. **Encrypted Key Distribution** - AES key is encrypted with peer's RSA public key
5. **Secure Communication** - All messages are encrypted with the shared AES key and signed

### Encryption Details

- **Message Encryption** - AES-256 in CFB mode
- **Key Encryption** - RSA-4096 with OAEP padding
- **Signatures** - RSA-4096 with PSS padding and SHA-256
- **Cryptography Library** - Uses the `cryptography` library (actively maintained)

## 📚 Environment Variables

Configure the CLI using environment variables:

```bash
# Enable debug mode
export DEBUG=true

# Or set it in .env file
DEBUG=false
```

Create a `.env` file in your project directory:

```env
DEBUG=false
```

## 🔧 Configuration

### Server Address Format

The server address can be specified as:

- **Secure WebSocket** - `wss://example.com` (recommended)
- **WebSocket** - `ws://example.com` (use only for testing)
- **HTTPS** - `https://example.com` (automatically converts to WSS)
- **HTTP** - `http://example.com` (automatically converts to WS)

### Connection History

The CLI stores your connection history in:

```txt
~/.confy_address_history
```

This allows you to quickly access previously used server addresses using arrow keys.

## 🛠️ Troubleshooting

### Connection Issues

**"Error connecting to server"**

- Verify the server address is correct
- Ensure the server is running and accessible
- Check your network connectivity
- For WSS connections, verify the SSL certificate is valid

**"Connection refused"**

- Confirm the server is listening on the specified address and port
- Check if a firewall is blocking the connection

### Message Issues

**"AES key has not been established yet"**

- Wait a moment for the key exchange to complete
- Ensure both peers are connected
- Check if the server is properly relaying messages

**"Failed to encrypt/verify message"**

- This indicates an issue with the encryption layer
- Try reconnecting to the server
- Check if both peers are running compatible CLI versions

### Performance Issues

**Slow response times**

- Check your network latency to the server
- Consider using a server closer to your location
- Reduce the frequency of large messages

## 📖 Usage Guide

### Connecting to a Server

```bash
confy start alice bob
```

You'll be prompted to enter the server address. For the first time, you can enter:

```txt
Server address: wss://secure-server.example.com
```

### Sending Messages

Simply type your message and press Enter:

```txt
> Your encrypted message here
```

### Security Considerations

1. **Verify Recipients** - Ensure you're communicating with the intended person
2. **Secure Connections** - Always use WSS (WebSocket Secure) in production
3. **Key Management** - Store your user ID securely
4. **Session Management** - End sessions with `exit` when finished

### Advanced Usage

#### Debug Mode

Enable debug mode to see detailed information:

```bash
DEBUG=true confy start alice bob
```

This will display:

- Key exchange details
- Message encryption/decryption info
- Connection status changes
- Signature verification steps

#### Custom Server

Connect to a custom server:

```bash
confy start your-id recipient-id
Server address: wss://your-custom-server.com:8080
```

## 🤝 Dependencies

Confy CLI relies on:

- **[typer](https://typer.tiangolo.com/)** (>=0.15.4, <0.16.0) - CLI framework
- **[websockets](https://websockets.readthedocs.io/)** (>=15.0.1, <16.0.0) - WebSocket protocol support
- **[pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)** (>=2.11.0, <3.0.0) - Configuration management
- **[confy-addons](https://github.com/confy-security/confy-addons)** (>=1.1.0, <2.0.0) - Encryption primitives
- **[prompt-toolkit](https://python-prompt-toolkit.readthedocs.io/)** (>=3.0.52, <4.0.0) - Terminal interface

All dependencies are installed automatically with pip.

## 🐛 Bug Reports

If you encounter any issues, please report them:

1. Check if the issue already exists on [GitHub Issues](https://github.com/confy-security/cli/issues)
2. Provide clear reproduction steps
3. Include your Python version and OS
4. Attach relevant logs with `DEBUG=true`

See [CONTRIBUTING.md](CONTRIBUTING.md) for more information.

## 🔐 Security Policy

For security vulnerabilities, please follow responsible disclosure:

**DO NOT** open a public GitHub issue.

Instead, email: [confy@henriquesebastiao.com](mailto:confy@henriquesebastiao.com)

See [SECURITY.md](SECURITY.md) for detailed information.

## 📝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

- Setting up the development environment
- Code standards and style guidelines
- Testing requirements
- Pull request process

## 📄 License

Confy CLI is open source software licensed under the [GPL-3.0](https://github.com/confy-security/cli/blob/main/LICENSE) license.

## 📚 Additional Resources

- **Confy Security** - [github.com/confy-security](https://github.com/confy-security)
- **Contributing Guide** - [CONTRIBUTING.md](CONTRIBUTING.md)
- **Security Policy** - [SECURITY.md](SECURITY.md)
- **Code of Conduct** - [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

## 🙋 Support

For questions and support:

- Check existing issues and discussions on GitHub
- Review the [CONTRIBUTING.md](CONTRIBUTING.md) guide
- Contact the team at [confy@henriquesebastiao.com](mailto:confy@henriquesebastiao.com)

## Acknowledgments

This project was created with dedication by Brazilian students 🇧🇷 as part of the Confy Security initiative.

**Built with ❤️ by the Confy Security Team**