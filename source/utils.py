from django.conf import settings

import hashlib
import requests

def generate_sha1(input_str: str) -> str:
    """
    引数の文字列をSHA-1ハッシュに変換する関数。

    Args:
        input_str (str): ハッシュ化する文字列。

    Returns:
        str: SHA-1ハッシュ値(16進数表記)。
    """
    # 文字列をバイトに変換
    input_bytes = input_str.encode('utf-8')
    
    # SHA-1ハッシュを計算
    sha1_hash = hashlib.sha1(input_bytes)
    
    # ハッシュ値を16進数文字列で返す
    return sha1_hash.hexdigest()

