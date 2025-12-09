from . import utils

from django.conf import settings

import xml.etree.ElementTree as ET

def xml_to_dict(response):
    # XML文字列を解析してElementTreeオブジェクトを生成
    root = ET.fromstring(response)

    # データを動的に辞書に格納
    response_data = {child.tag: child.text for child in root}
    return response_data
