from . import utils
from . import xml_to_dict
import xml.etree.ElementTree as ET

from urllib.parse import urlencode

from django.conf import settings
from django.http import JsonResponse

import requests
from .models import *



# settings.pyから設定を読み込む
base_url = settings.BBB_SERVER_URL
shared_secret = settings.BBB_SHARED_SECRET
logoutURL = settings.BBB_LOGOUT_URL



# 会議を作成
def create_meeting(mtg_id, mtg_name, is_guest_join, participant_emails, attendee_pw, moderator_pw, is_record, is_recurrence, recurrence_days):
    # URLのクエリを作成
    action = "create"

    welcome = "会議へようこそ！！"
    notifyRecordIsOn = "true"
    guestPolicy = "ALWAYS_ACCEPT"
    params = {
        "name": mtg_name,
        "meetingID": mtg_id,
        "attendeePW": attendee_pw,
        "moderatorPW": moderator_pw,
        "welcome": welcome,
        "record": is_record,
        "guestPolicy": guestPolicy,
        "notifyRecordIsOn": notifyRecordIsOn,
        "logoutURL": logoutURL,
        "meetingExpireIfNoUserJoinedInMinutes": 43200,  # 30日
    }
    query_str = urlencode(params)


    # チェックサムを生成
    checksum_str = f"{action}{query_str}{shared_secret}"
    checksum = utils.generate_sha1(checksum_str)

    # リクエストURLを作成
    full_url = f"{base_url}{action}?{query_str}&checksum={checksum}"
    # リクエストを送信
    response = requests.get(full_url)
    response_dict = xml_to_dict.xml_to_dict(response.text)

    # レスポンスを辞書に格納
    response_data = {
        "status_code": response.status_code,
        "meeting_url": full_url,
        "meeting_id": mtg_id,
        "meeting_name": mtg_name,
        "moderator_pw": moderator_pw,
        "attendee_pw": attendee_pw,
        "welcome": welcome,
        "record": is_record,
        "guestPolicy": guestPolicy,
        "notifyRecordIsOn": notifyRecordIsOn,
        "logoutURL": logoutURL,
        "createTime" : response_dict['createTime'],
    }

    # レスポンスのエラーハンドリング
    if response.status_code == 200:
        # return response.text
        return response_data
    else:
        response.raise_for_status()



# 会議に参加
def join_meeting_api(meeting_id, full_name, pw, createTime, guest_flag):
    # URLのクエリを作成
    action = "join"
    if guest_flag:
        params = {
            "fullName": full_name,
            "meetingID": meeting_id,
            "password": pw,
            "guest": True,
            "createTime": createTime,
        }
    else:
        params = {
            "fullName": full_name,
            "meetingID": meeting_id,
            "password": pw,
            "createTime": createTime,
        }
    query_str = urlencode(params)

    # チェックサムを生成
    checksum_str = f"{action}{query_str}{shared_secret}"
    checksum = utils.generate_sha1(checksum_str)

    # リクエストURLを作成
    full_url = f"{base_url}{action}?{query_str}&checksum={checksum}"
    # リクエストを送信
    response = requests.get(full_url)

    # レスポンスを辞書に格納
    response_data = {
        "status_code": response.status_code,
        "meeting_url": full_url,  # 参加URL
        "meeting_id": meeting_id,
        "full_name": full_name,
        "create_time": createTime,
    }

    # レスポンスのエラーハンドリング
    if response.status_code == 200:
        return response_data
    else:
        response.raise_for_status()



# 会議の詳細情報を取得するビュー
def get_meeting_info(meeting_id):
    # URLのクエリを作成
    action = "getMeetingInfo"
    query_str = f"meetingID={meeting_id}"

    # チェックサムを生成
    checksum_str = f"{action}{query_str}{shared_secret}"
    checksum = utils.generate_sha1(checksum_str)

    # リクエストURLを作成
    full_url = f"{base_url}{action}?{query_str}&checksum={checksum}"
    # リクエストを送信
    response = requests.get(full_url)
    response_dict = xml_to_dict.xml_to_dict(response.text)

    # レスポンスを辞書に格納
    response_data = {
        "status_code": response.status_code,
        "returncode": response_dict['returncode'],
        "meeting_url": full_url,  # 参加URL
        "meeting_id": meeting_id,
    }

    # レスポンスのエラーハンドリング
    if response.status_code == 200:
        return response_data
    else:
        response.raise_for_status()


# 会議リストを取得するビュー
def get_meetings(request):
    # URLのクエリを作成
    action = "getMeetings"
    url = f"{action}{shared_secret}"
    # チェックサムを生成
    checksum = utils.generate_sha1(url)
    full_url = f"{base_url}{action}?&checksum={checksum}"
    # リクエストを送信
    response = requests.get(full_url)
    # XMLを解析
    root = ET.fromstring(response.text)
    # 返却コードを取得
    return_code = root.find("returncode").text
    # ミーティング情報を格納するリスト
    meetings = []
    # 各ミーティングのデータを取得
    for meeting in root.findall(".//meeting"):
        meeting_data = {
            "meetingName": meeting.find("meetingName").text,
            "meetingID": meeting.find("meetingID").text,
            "internalMeetingID": meeting.find("internalMeetingID").text,
            "createTime": int(meeting.find("createTime").text),
            "createDate": meeting.find("createDate").text,
            "attendeePW": meeting.find("attendeePW").text,
            "moderatorPW": meeting.find("moderatorPW").text,
            "running": meeting.find("running").text == "true",
            "participantCount": int(meeting.find("participantCount").text),
            "moderatorCount": int(meeting.find("moderatorCount").text),
            "isBreakout": meeting.find("isBreakout").text == "true"
        }
        meetings.append(meeting_data)

    # 取得結果を表示
    if response.status_code == 200:
        return meetings
    else:
        response.raise_for_status()



# 使用していないAPI -----------------------------------------------------------------------------------------------



# 特定の会議が開催中か取得する
def is_meeting_running(request):
    """
    会議の開催状況を取得するビュー

    /isMeetingRunning?meetingID=1&checksum=2

    """

    action = "isMeetingRunning"
    meeting_id = "random-1730297"

    url = f"meetingID={meeting_id}"
    checksum_str = f"{action}{url}{shared_secret}"
    checksum = utils.generate_sha1(checksum_str)
    full_url = f"{base_url}{action}?{url}&checksum={checksum}"
    response = requests.get(full_url)

    if response.status_code == 200:
        return response.text
    else:
        response.raise_for_status()
    
    return JsonResponse({"response": response})



# 録画はオプションとして、基本的にはフロント実装しない。
def get_recordings(request):
    """
    特定の会議の録画リストを取得するビュー

    /getRecordings?meetingID=1&checksum=2

    """
    action = "getRecordings"
    meeting_id = "random-1730297"

    url = f"meetingID={meeting_id}"
    checksum_str = f"{action}{url}{shared_secret}"
    checksum = utils.generate_sha1(checksum_str)
    full_url = f"{base_url}{action}?{url}&checksum={checksum}"
    response = requests.get(full_url)

    if response.status_code == 200:
        return response.text
    else:
        response.raise_for_status()
    
    return JsonResponse({"response": response})



def publish_recordings(request):
    """
    特定の会議の録画リストの公開範囲を変更するビュー

    /publishRecordings?recordID=1&publish=2&checksum=3
    """

    action = "publishRecordings"
    record_id = "12345"
    publish = "true"

    record_id_str = f"recordID={record_id}"
    publish_str = f"publish={publish}"
    url = f"{record_id_str}&{publish_str}"
    checksum_str = f"{action}{url}{shared_secret}"
    checksum = utils.generate_sha1(checksum_str)
    full_url = f"{base_url}{action}?{url}&checksum={checksum}"
    response = requests.get(full_url)

    if response.status_code == 200:
        return response.text
    else:
        response.raise_for_status()
    
    return JsonResponse({"response": response})



def unpublish_recordings(request):
    """
    特定の会議の録画リストの公開範囲を変更するビュー

    /publishRecordings?recordID=1&publish=2&checksum=3
    """

    action = "publishRecordings"
    record_id = "12345"
    publish = "false"

    record_id_str = f"recordID={record_id}"
    publish_str = f"publish={publish}"
    url = f"{record_id_str}&{publish_str}"
    checksum_str = f"{action}{url}{shared_secret}"
    checksum = utils.generate_sha1(checksum_str)
    full_url = f"{base_url}{action}?{url}&checksum={checksum}"
    response = requests.get(full_url)

    if response.status_code == 200:
        return response.text
    else:
        response.raise_for_status()
    
    return JsonResponse({"response": response})



def delete_recordings(request):
    """
    特定の会議の録画リストを削除するビュー

    /deleteRecordings?recordID=1&checksum=2
    """

    action = "deleteRecordings"
    record_id = "12345"
    publish = "false"

    record_id_str = f"recordID={record_id}"
    publish_str = f"publish={publish}"
    url = f"{record_id_str}&{publish_str}"
    checksum_str = f"{action}{url}{shared_secret}"
    checksum = utils.generate_sha1(checksum_str)
    full_url = f"{base_url}{action}?{url}&checksum={checksum}"
    response = requests.get(full_url)

    if response.status_code == 200:
        return response.text
    else:
        response.raise_for_status()
    
    return JsonResponse({"response": response})