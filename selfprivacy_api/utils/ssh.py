from typing import Optional, Tuple
import base64

# https://www.openssh.org/specs.html
VALID_SSH_KEY_TYPES = [
    "ssh-ed25519",
    "ecdsa-sha2-nistp256",
    "ecdsa-sha2-nistp384",
    "ecdsa-sha2-nistp521",
    "sk-ssh-ed25519@openssh.com",
    # OpenSSH supports only P-256 for sk-ecdsa- keys.
    "sk-ecdsa-sha2-nistp256@openssh.com",
]


def _get_blob_keytype(b: bytes) -> Optional[Tuple[str, int]]:
    if len(b) <= 4:
        return None
    key_type_size = int.from_bytes(b[:4], "big", signed=False)
    if 4 + key_type_size > len(b):
        return None
    return (b[4 : 4 + key_type_size].decode("ascii"), 4 + key_type_size)


# returns RSA modulus bit-length from OpenSSH key blob. doesn't check if n is a prime or if e is sane.
def _rsa_modulus_from_blob(b: bytes) -> Optional[int]:
    e_len = int.from_bytes(b[:4], "big", signed=False)
    off = 4 + e_len

    n_len = int.from_bytes(b[off : off + 4], "big", signed=False)
    off += 4
    if off + n_len > len(b):
        return None
    n_bytes = b[off : off + n_len]

    if len(n_bytes) == 0:
        return None
    n_int = int.from_bytes(n_bytes, "big", signed=False)
    return n_int.bit_length()


def validate_ssh_public_key(key):
    """Validate SSH public key."""
    key = key.strip()

    if not key:
        return False

    try:
        key_type, b64blob = key.split()[:2]
        key_data = base64.b64decode(b64blob, validate=True)
        keytype_from_blob_result = _get_blob_keytype(key_data)
        if keytype_from_blob_result is None:
            return False
        # Blob should advertise same key type as string before the blob.
        if keytype_from_blob_result[0] != key_type:
            return False
        key_offset = keytype_from_blob_result[1]
        key_data = key_data[key_offset:]
    except Exception:
        return False

    if key_type == "ssh-rsa":
        try:
            bits = _rsa_modulus_from_blob(key_data)
            if bits is None:
                return False
            # https://crypto.stackexchange.com/questions/119164/benefits-and-drawbacks-of-ssh-rsa-long-key/119166#119166
            if bits < 2048 or bits > 16384:
                return False
            return True
        except Exception:
            return False

    if key_type in VALID_SSH_KEY_TYPES:
        return True

    return False
