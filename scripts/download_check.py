import requests
BASE='http://127.0.0.1:5000'
doc_id='ebebcdfe-f269-4868-b13d-423c9626cc29'
try:
    r = requests.get(f"{BASE}/api/v1/download/{doc_id}?type=corrected", timeout=20)
    print('download status', r.status_code)
    if r.status_code==200:
        open('outputs/manual_download_corrected.pptx','wb').write(r.content)
        print('Saved outputs/manual_download_corrected.pptx')
    else:
        print(r.text)
except Exception as e:
    print('download error', e)
