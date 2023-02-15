from typing import Optional, AnyStr, Callable
from .rfc7515 import JWSAlgorithm
from .rfc7515.compact import (
    CompactData,
    extract_compact,
)
from .rfc7515.json import (
    JSONData,
    extract_json,
)
from .rfc7515.types import Header, check_header
from .rfc7518.jws_algs import JWS_ALGORITHMS
from .rfc8812 import ES256K
from .errors import BadSignatureError
from .jwk import Key, KeyFlexible, guess_key
from .util import to_bytes

__all__ = [
    'CompactData',
    'serialize_compact',
    'extract_compact',
    'deserialize_compact',
    'validate_compact',
    'JSONData',
    'extract_json',
    'JWSAlgorithm',
    'JWS_REGISTRY',
]

# supported algs
JWS_REGISTRY = {alg.name: alg for alg in JWS_ALGORITHMS}
JWS_REGISTRY[ES256K.name] = ES256K

#: Recommended "alg" (Algorithm) Header Parameter Values for JWS
#: by `RFC7618 Section 3.1`_
#: .. `RFC7618 Section 3.1`_: https://www.rfc-editor.org/rfc/rfc7518#section-3.1
RECOMMENDED_ALGORITHMS = [
    'HS256',  # Required
    'RS256',  # Recommended
    'ES256',  # Recommended+
]


def serialize_compact(
    header: Header,
    payload: bytes,
    key: KeyFlexible,
    allowed_algorithms: Optional[list[str]]=None) -> bytes:
    """Generate a JWS Compact Serialization. The JWS Compact Serialization
    represents digitally signed or MACed content as a compact, URL-safe
    string, per Section 7.1.

    .. code-block:: text

        BASE64URL(UTF8(JWS Protected Header)) || '.' ||
        BASE64URL(JWS Payload) || '.' ||
        BASE64URL(JWS Signature)

    :param header: protected header part of the JWS, in dict
    :param payload: payload data of the JWS, in bytes
    :param key: a flexible private key to sign the signature
    :param allowed_algorithms: allowed algorithms to use, default to HS256, RS256, ES256
    :return: JWS in bytes

    .. note:: The returned value is in bytes
    """

    check_header(header, ['alg'])

    if allowed_algorithms is None:
        allowed_algorithms = RECOMMENDED_ALGORITHMS

    alg = header['alg']
    if alg not in allowed_algorithms:
        raise ValueError(f'Algorithm "{alg}" is not allowed in {allowed_algorithms}')

    obj = CompactData(header, payload)
    key: Key = guess_key(key, obj, 'sign')
    # if key is designed for the "use"
    key.check_use('sig')

    algorithm = JWS_REGISTRY[alg]
    return obj.sign(algorithm, key)


def validate_compact(
    obj: CompactData,
    key: KeyFlexible,
    allowed_algorithms: Optional[list[str]]=None):
    """Validate the JWS Compact Serialization with the given key.
    This method is usually used together with ``extract_compact``.

    :param obj: object of the JWS Compact Serialization
    :param key: a flexible public key to verify the signature
    :param allowed_algorithms: allowed algorithms to use, default to HS256, RS256, ES256
    :raise: ValueError or BadSignatureError
    """

    if allowed_algorithms is None:
        allowed_algorithms = RECOMMENDED_ALGORITHMS

    alg = obj.header['alg']
    if alg not in allowed_algorithms:
        raise ValueError(f'Algorithm "{alg}" is not allowed in {allowed_algorithms}')

    key: Key = guess_key(key, obj, 'verify')
    # if key is designed for the "use"
    key.check_use('sig')

    algorithm = JWS_REGISTRY[alg]
    if not obj.verify(algorithm, key):
        raise BadSignatureError()


def deserialize_compact(
    value: AnyStr,
    key: KeyFlexible,
    allowed_algorithms: Optional[list[str]]=None) -> CompactData:
    """Extract and validate the JWS (in string) with the given key.

    :param value: a string (or bytes) of the JWS
    :param key: a flexible public key to verify the signature
    :param allowed_algorithms: allowed algorithms to use, default to HS256, RS256, ES256
    :return: object of the JWS Compact Serialization
    """

    obj = extract_compact(to_bytes(value))
    validate_compact(obj, key, allowed_algorithms)
    return obj
