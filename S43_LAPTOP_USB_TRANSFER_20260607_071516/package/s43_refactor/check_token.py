import os
import ssl
import time
import socket
import http.client


API_HOST = "api.arzplus.net"
API_PATH = "/api/v1/wallet/balance/"
API_PORT = 443
TIMEOUT_SECONDS = 15
USER_AGENT = "Arzplus-Bot-Monitor/5.5"


token = os.getenv("ARZPLUS_TOKEN", "")
token = token.strip()

print("DIAG: endpoint=https://{}{}".format(API_HOST, API_PATH))

if not token:
    print("ERROR: ARZPLUS_TOKEN is not set")
    raise SystemExit(2)

print("DIAG: token_prefix={}... length={}".format(token[:8], len(token)))

headers = {
    "Authorization": "Token {}".format(token),
    "Accept": "application/json",
    "User-Agent": USER_AGENT,
}

connection = None
started_at = time.time()

try:
    context = ssl.create_default_context()

    print("DIAG: opening_https_connection=true")
    connection = http.client.HTTPSConnection(
        API_HOST,
        port=API_PORT,
        timeout=TIMEOUT_SECONDS,
        context=context,
    )

    print("DIAG: sending_request=true")
    connection.request("GET", API_PATH, headers=headers)

    response = connection.getresponse()
    elapsed = round(time.time() - started_at, 3)

    raw_body = response.read()
    try:
        body = raw_body.decode("utf-8", errors="replace")
    except Exception:
        body = repr(raw_body)

    print("STATUS: HTTP {}".format(response.status))
    print("REASON: {}".format(response.reason))
    print("LATENCY_SECONDS: {}".format(elapsed))
    print("BODY: {}".format(body))

    if response.status == 200:
        print("RESULT: API_ACCESS_OK")
        raise SystemExit(0)

    if response.status == 403:
        print("RESULT: API_ACCESS_FORBIDDEN")
        raise SystemExit(3)

    if response.status in (401,):
        print("RESULT: API_AUTH_REJECTED")
        raise SystemExit(4)

    print("RESULT: API_UNEXPECTED_STATUS")
    raise SystemExit(5)

except socket.timeout as exc:
    print("ERROR: type=SocketTimeout detail={}".format(str(exc)))
    print("RESULT: NETWORK_TIMEOUT")
    raise SystemExit(10)

except TimeoutError as exc:
    print("ERROR: type=TimeoutError detail={}".format(str(exc)))
    print("RESULT: NETWORK_TIMEOUT")
    raise SystemExit(10)

except ConnectionError as exc:
    print("ERROR: type=ConnectionError detail={}".format(str(exc)))
    print("RESULT: NETWORK_CONNECTION_ERROR")
    raise SystemExit(11)

except ssl.SSLError as exc:
    print("ERROR: type=SSLError detail={}".format(str(exc)))
    print("RESULT: TLS_ERROR")
    raise SystemExit(12)

except Exception as exc:
    print("ERROR: type={} detail={}".format(type(exc).__name__, str(exc)))
    print("RESULT: UNKNOWN_ERROR")
    raise SystemExit(20)

finally:
    if connection is not None:
        try:
            connection.close()
        except Exception:
            pass
