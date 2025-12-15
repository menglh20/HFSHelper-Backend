import json
import logging

from django.http import JsonResponse
from wxcloudrun.models import Result, User

from wxcloudrun.settings import SECRET_KEY
import datetime
import requests

logger = logging.getLogger('log')


def register(request):
    if request.method == "POST":
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        logger.info(f"[register] Registering user body: {body}")
        name = body["name"]
        password = body["password"]
        logger.info(f"[register] Registering user: {name}")
        if User.objects.filter(name=name).exists():
            logger.info(f"[register] User already exists: {name}")
            return JsonResponse({
                "code": 400,
                "message": "User already exists"
            })
        User.objects.create(name=name, password=password)
        logger.info(f"[register] User created: {name}")
        return JsonResponse({
            "code": 200,
            "message": "User created"
        })
    else:
        return JsonResponse({
            "code": 400,
            "message": "Invalid request"
        })


def login(request):
    if request.method == "POST":
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        name = body["name"]
        password = body["password"]
        logger.info(f"[login] Logging in user: {name}")
        if not User.objects.filter(name=name).exists():
            logger.info(f"[login] User does not exist: {name}")
            return JsonResponse({
                "code": 400,
                "message": "Login failed"
            })
        user = User.objects.get(name=name)
        if user.password != password:
            logger.info(f"[login] Password does not match: {name}")
            return JsonResponse({
                "code": 401,
                "message": "Login failed"
            })
        logger.info(f"[login] Login success: {name}")
        return JsonResponse({
            "code": 200,
            "message": "Login successful"
        })
    else:
        return JsonResponse({
            "code": 402,
            "message": "Invalid request"
        })


def detect(request):
    if request.method == "POST":
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        user = body["user"]
        fileID = body["fileID"]
        logger.info(f"[detect] Detection result: {user}")
        if not User.objects.filter(user=user).exists():
            logger.info(f"[detect] User does not exist: {user}")
            return JsonResponse({
                "code": 400,
                "message": "User does not exist"
            })
        current_time = datetime.datetime.now()
        current_time = current_time.strftime("%Y.%m.%d %H:%M:%S")
        save_name = current_time.replace(".", "").replace(":", "")
        save_path = f"media/{user}_{save_name}/"
        record = Result(user=user, result=0, comment=0, time=current_time, save_path=save_path, fileId=str(fileID))
        record.save()
        try:
            data = {
                'user': user,
                'fileID': fileID
            }
            response = requests.post("http://123.56.218.127/api/detect/detect/", json=data)
            logger.info(f"[detect] recieve response from http://123.56.218.127/api/detect/detect: " + response.text)
            res = json.loads(response.text)
            result, detail = res["result"], res["detail"]
            record.result = result
            record.detail = detail
            record.save()
            logger.info(f"[detect] Detection success: {user} {result} {detail}")
            return JsonResponse({
                "code": 200,
                "id": record.id,
                "time": current_time,
                "result": result,
                "detail": detail,
            })
        except Exception as e:
            record.delete()
            logger.error(f"[detect] Detection failed: {user} {str(e)}")
            return JsonResponse({
                "code": 500,
                "message": str(e)
            })
    else:
        return JsonResponse({
            "code": 400,
            "message": "Invalid request"
        })


def history(request):
    if request.method == "POST":
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        name = body["name"]
        page = body["page"] if "page" in body else 1
        logger.info(f"[history] Requesting history for {name} page {page}")
        if not User.objects.filter(name=name).exists():
            logger.info(f"[history] User does not exist: {name}")
            return JsonResponse({
                "code": 400,
                "message": "User does not exist"
            })
        results = Result.objects.filter(name=name).order_by("-time")
        total = results.count()
        results = results[(page - 1) * 10:page * 10]
        return JsonResponse({
            "code": 200,
            "total": total,
            "page": page,
            "results": [{
                "id": result.id,
                "result": result.result,
                "time": result.time,
                "detail": result.detail,
                "comment": result.comment,
                "fileId": result.fileId
            } for result in results]
        })
    else:
        return JsonResponse({
            "code": 400,
            "message": "Invalid request"
        })


def comment(request):
    if request.method == "POST":
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        id = body["id"]
        comment = body["comment"]
        logger.info(f"[comment] Commenting on result {id}")
        if not Result.objects.filter(id=id).exists():
            logger.info(f"[comment] Result does not exist: {id}")
            return JsonResponse({
                "code": 400,
                "message": "Result does not exist"
            })
        record = Result.objects.filter(id=id).first()
        record.comment = comment
        record.save()
        logger.info(f"[comment] Comment success: {id}")
        return JsonResponse({
            "code": 200,
            "message": "Comment success"
        })
    else:
        return JsonResponse({
            "code": 400,
            "message": "Invalid request"
        })


# 内部接口
def clear(request):
    if request.method == "POST":
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        secret_key = body["secret_key"]
        logger.warning(f"[clear] Clearing all results with secret key {secret_key}")
        if secret_key != SECRET_KEY:
            return JsonResponse({
                "code": 400,
                "message": "Invalid secret key"
            })
        Result.objects.all().delete()
        logger.warning(f"[clear] Clear all results success")
    else:
        return JsonResponse({
            "code": 400,
            "message": "Invalid request"
        })


def get_all(request):
    if request.method == "POST":
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        secret_key = body["secret_key"]
        logger.warning(f"[get_all] Requesting all results with secret key {secret_key}")
        if secret_key != SECRET_KEY:
            return JsonResponse({
                "code": 400,
                "message": "Invalid secret key"
            })
        results = Result.objects.all().order_by("name")
        return JsonResponse({
            "code": 200,
            "results": [{
                "id": result.id,
                "name": result.name,
                "result": result.result,
                "time": result.time,
                "detail": result.detail,
                "comment": result.comment
            } for result in results]
        })
    else:
        return JsonResponse({
            "code": 400,
            "message": "Invalid request"
        })