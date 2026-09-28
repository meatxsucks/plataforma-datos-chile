import json
import os
import subprocess
import sys

ENTORNO = {
    **os.environ,
    "AWS_ACCESS_KEY_ID": "test",
    "AWS_SECRET_ACCESS_KEY": "test",
    "AWS_REGION": "us-east-1",
    "AWS_ENDPOINT_URL": "http://localhost:4566",
    "READ_OPERATIONS_ONLY": "true",
}


# Mensaje JSON-RPC al servidor MCP
def enviar(proc, mensaje):
    """Escribe un mensaje JSON-RPC en la entrada del servidor."""
    proc.stdin.write(json.dumps(mensaje) + "\n")
    proc.stdin.flush()


# Respuesta con un id dado
def leer(proc, id_):
    """Lee líneas del servidor hasta encontrar la respuesta con el id indicado."""
    for linea in proc.stdout:
        datos = json.loads(linea)
        if datos.get("id") == id_:
            return datos
    raise RuntimeError("El servidor terminó sin responder")


# Prueba de punta a punta del MCP de AWS contra floci
def main():
    """Levanta aws-api-mcp-server, lista sus herramientas y ejecuta un comando contra floci."""
    comando = sys.argv[1] if len(sys.argv) > 1 else "aws s3 ls"
    proc = subprocess.Popen(
        ["uvx", "awslabs.aws-api-mcp-server@latest"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, env=ENTORNO,
    )
    enviar(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "prueba", "version": "0"}}})
    leer(proc, 1)
    enviar(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
    enviar(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    print("herramientas:", [t["name"] for t in leer(proc, 2)["result"]["tools"]])
    enviar(proc, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                  "params": {"name": "call_aws", "arguments": {"cli_command": comando}}})
    print(json.dumps(leer(proc, 3).get("result", {}), ensure_ascii=False)[:1500])
    proc.terminate()


if __name__ == "__main__":
    main()
