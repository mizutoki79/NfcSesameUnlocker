# -*- coding: utf-8 -*-
import requests
import json
import binascii
import nfc
import time
from threading import Thread, Timer
import os

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

# Suica接続リクエストのための準備
target_req_felica = nfc.clf.RemoteTarget("212F")
# NFC接続リクエストのための準備
target_req_nfc = nfc.clf.RemoteTarget("106A")

print "Waiting for NFC..."
i = 0
while True:
    i += 1
    print i
    # USBに接続されたNFCリーダに接続してインスタンス化
    clf = nfc.ContactlessFrontend("usb")
    # NFC待ち受け開始
    # clf.sense( [リモートターゲット], [検索回数], [検索の間隔] )
    target_res = clf.sense(target_req_nfc, target_req_felica, iterations=int(
        TIME_cycle//TIME_interval)+1, interval=TIME_interval)

    if target_res != None:
        print target_res
        tag = nfc.tag.activate(clf, target_res)
        print tag

        # Felica
        if tag.type == "Type3Tag":
            tag.sys = 3
            idm = binascii.hexlify(tag.idm)
            print "Felica detected. idm = {0}".format(idm)
            if idm in key_idms:
                response_unlock = control_sesame(device_id, "unlock")
                print (response_unlock.text)
        # NFC
        else:
            uid = binascii.hexlify(tag._nfcid)
            print uid
            if uid in key_uids:
                response_unlock = control_sesame(device_id, "unlock")
                print response_unlock.text
            break

        # 共通
        print "sleep{0}seconds".format(str(TIME_wait))
        time.sleep(TIME_wait)

    clf.close()


def control_sesame(device_id, command):
    url_control = "{0}/sesame/{1}".format(api_endpoint, device_id)
    head_control = {"Authorization": auth_token,
                    "Content-Type": "application/json"}
    payload_control = {"command": command}
    response_control = requests.post(
        url_control, headers=head_control, data=json.dumps(payload_control))
    return response_control
