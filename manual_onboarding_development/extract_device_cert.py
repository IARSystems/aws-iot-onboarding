""""
Extract device certificate from production record file.

This script reads a production record file (PRD file) containing a JWS object,
extracts the device certificate from the JWS object, and converts it to PEM
format. The extracted certificate is then printed to the console.

Usage:
    python extract_device_cert.py <path_to_prd_file>

Arguments:
    prdfile : The path to the production record file.
"""

import argparse
import os
import sys
from pathlib import Path

from jwcrypto import jws


def parse_args():
    """Parse command line aguments."""
    parser = argparse.ArgumentParser(
        description="Extract device certificate from production record file."
    )
    parser.add_argument("prdfile", type=Path)
    return parser.parse_args()


def read_prd_cert_body(prdfile: Path) -> str:
    """
    Read the production record file provided as an argument and return the
    device certificate as a base64 encoded string.

    Args:
        prdfile (Path): The path to the production record file.

    Returns:
        str: The device certificate as a base64 encoded string.
    """
    jws_obj = jws.JWS()
    jws_obj.deserialize(prdfile.read_text())

    return jws_obj.jose_header.get("dev")["deviceCert"]


def convert_to_pem_certificate(raw_string: str) -> str:
    """
    Convert a given string to PEM certificate format. Note that it will not
    check to see if the string represents a valid certificate.

    Args:
        raw_string (str): The raw string to convert.

    Returns:
        str: The converted PEM certificate string.
    """
    return os.linesep.join(
        (
            "-----BEGIN CERTIFICATE-----",
            *(raw_string[i : i + 64] for i in range(0, len(raw_string), 64)),
            f"-----END CERTIFICATE-----{os.linesep}",
        )
    )


def main():
    """Entry point."""
    args = parse_args()
    certificate_body = read_prd_cert_body(args.prdfile)
    print(convert_to_pem_certificate(certificate_body), end="")


if __name__ == "__main__":
    sys.exit(main())
