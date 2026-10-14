"""Bundle de certificados = certifi + raíces de confianza del sistema Windows.

En redes corporativas con inspección TLS, Python y Node (Prisma) no conocen la CA
de la empresa que Windows sí tiene instalada. Este bundle las incluye sin
desactivar la verificación.
"""
import os
import ssl
import sys
from pathlib import Path

import certifi

BUNDLE = Path(__file__).resolve().parent.parent / ".data" / "ca-bundle.pem"


def build_bundle() -> Path:
    BUNDLE.parent.mkdir(parents=True, exist_ok=True)
    pems = [Path(certifi.where()).read_text(encoding="utf-8")]
    if sys.platform == "win32":
        for store in ("ROOT", "CA"):
            for cert, encoding, _trust in ssl.enum_certificates(store):
                if encoding == "x509_asn":
                    pems.append(ssl.DER_cert_to_PEM_cert(cert))
    BUNDLE.write_text("\n".join(pems), encoding="utf-8")
    return BUNDLE


def apply_to_env() -> None:
    bundle = str(build_bundle())
    for var in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "NODE_EXTRA_CA_CERTS"):
        os.environ.setdefault(var, bundle)
