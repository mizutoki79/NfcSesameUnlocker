# -*- coding: utf-8 -*-
import requests
import json
import binascii
import nfc
import time
import os
from datetime import datetime

# Version 3 of CANDY HOUSE'S Sesame API
api_endpoint = "https://api.candyhouse.co/public"

key_idms = os.environ.get("SESAME_KEY_IDMS")
key_idms = key_idms.split(';') if key_idms != None else []
print key_idms
key_uids = os.environ.get("SESAME_KEY_UIDS")
key_uids = key_uids.split(';') if key_uids != None else []
print key_uids
device_id = os.environ.get("SESAME_DEVICE_ID")
auth_token = os.environ.get("SESAME_AUTH_TOKEN")

# 待ち受けの1サイクル秒
TIME_cycle = 1.0
# 待ち受けの反応インターバル秒
TIME_interval = 0.2
# タッチされてから次の待ち受けを開始するまで無効化する秒
TIME_wait = 3

def control_sesame(device_id, command):
    url_control = "{0}/sesame/{1}".format(api_endpoint, device_id)
    head_control = {"Authorization": auth_token,
                    "Content-Type": "application/json"}
    payload_control = {"command": command}
    response_control = requests.post(
        url_control, headers=head_control, data=json.dumps(payload_control))
    return response_control

def check_sesame_task(task_id):
    url_check = "{0}/action-result?task_id={1}".format(api_endpoint, task_id)
    head_check = {"Authorization": auth_token}
    response_check = requests.get(url_check, headers=head_check)
    return response_check

def unlock_sesame(device_id, card_id):
    response_control = control_sesame(device_id, "unlock")
    if response_control == None and not hasattr(response_control, "_content"):
        return False

    # print vars(response_control)
    response_control_content = json.loads(response_control._content)
    task_id = response_control_content["task_id"]
    print "task_id = {0}".format(task_id)

    # TODO: 時間を短くして繰り返し問い合わせる
    time.sleep(7.0)
    response_check = check_sesame_task(task_id)
    if response_check == None and not hasattr(response_check, "_content"):
        return False

    response_check_content = json.loads(response_check._content)
    # print response_check_content
    if response_check_content["status"] == "processing":
        # TODO: 数秒待ったり何度か問い合わせたりリクエスト投げたり、最悪 sync したり
        print "processing"
        pass

    if response_check_content["status"] == "terminated":
        result = response_check_content["successful"]
        print "[{0}] card_id: {1} device_id: {2} unlock: {3}".format(datetime.now().strftime("%Y/%m/%d %H:%M:%S"), card_id, device_id, "successful" if result else "failed")
        return

if __name__ == "__main__":
    # NFC接続リクエストのための準備
    target_req_nfc = nfc.clf.RemoteTarget("106A")
    # Suica接続リクエストのための準備
    target_req_felica = nfc.clf.RemoteTarget("212F")

    print "Waiting for NFC..."
    while True:
        # USBに接続されたNFCリーダに接続してインスタンス化
        clf = nfc.ContactlessFrontend("usb")
        # NFC待ち受け開始
        # clf.sense( [リモートターゲット], [検索回数], [検索の間隔] )
        target_res = clf.sense(target_req_nfc, target_req_felica, iterations=int(
            TIME_cycle//TIME_interval) + 1, interval=TIME_interval)

        if target_res != None:
            print target_res
            print vars(target_res)
            if not hasattr(target_res, "_brty_send"):
                continue

            brty = target_res._brty_send
            if brty == "106A":
                tag = nfc.tag.activate_tt2(clf, target_res)
            elif brty == "212F":
                tag = nfc.tag.activate_tt3(clf, target_res)
            else:
                continue

            print tag
            if tag != None:
                print vars(tag)
                print tag.type

                # Felica
                if hasattr(tag, "type") and tag.type == "Type3Tag":
                    tag.sys = 3
                    idm = binascii.hexlify(tag.idm)
                    print "Felica detected. idm = {0}".format(idm)
                    if idm in key_idms:
                        unlock_sesame(device_id, idm)

                # NFC
                else:
                    if not hasattr(tag, "_nfcid"):
                        print "Error: tag doesn't have nfcid"
                        continue

                    uid = binascii.hexlify(tag._nfcid)
                    print "NFC detected. uid = {0}".format(uid)
                    if uid in key_uids:
                        unlock_sesame(device_id, uid)

            # 共通
            print "sleep {0} seconds".format(str(TIME_wait))
            time.sleep(TIME_wait)
            # TODO: 自動ロック

        clf.close()

