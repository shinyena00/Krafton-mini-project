from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, jsonify

from db import users_collection, errands_collection
from routes.auth import get_current_user
from routes.errands import not_expired_conditions, is_expired


status = Blueprint("status", __name__)


@status.route(
    "/api/errands/<errand_id>/accept",
    methods=["POST"]
)
def accept_errand(errand_id):
    user = get_current_user()

    if not user:
        return jsonify({
            "success": False,
            "message": "로그인이 필요합니다."
        })

    try:
        object_id = ObjectId(errand_id)
    except InvalidId:
        return jsonify({
            "success": False,
            "message": "잘못된 심부름 ID입니다."
        })

    result = errands_collection.update_one(
        {
            "_id": object_id,
            "status": "OPEN",
            "worker_id": None,
            "requester_id": {
                "$ne": user["_id"]
            },
            "$or": not_expired_conditions()
        },
        {
            "$set": {
                "status": "WAITING_CONFIRM",
                "worker_id": user["_id"],
                "requester_confirmed": False,
                "worker_confirmed": False
            }
        }
    )

    if result.modified_count == 1:
        return jsonify({
            "success": True,
            "message": "심부름을 수락했습니다."
        })


    errand = errands_collection.find_one({
        "_id": object_id
    })

    if not errand:
        return jsonify({
            "success": False,
            "message": "존재하지 않는 심부름입니다."
        })

    if errand.get("requester_id") == user["_id"]:
        return jsonify({
            "success": False,
            "message": "자신이 등록한 심부름은 수락할 수 없습니다."
        })

    if errand.get("status") != "OPEN":
        return jsonify({
            "success": False,
            "message": "이미 다른 사용자가 수락했거나 처리된 심부름입니다."
        })

    if is_expired(errand):
        return jsonify({
            "success": False,
            "message": "기한이 지난 심부름은 수락할 수 없습니다."
        })

    return jsonify({
        "success": False,
        "message": "심부름을 수락할 수 없습니다."
    })


@status.route(
    "/api/errands/<errand_id>/complete",
    methods=["POST"]
)
def complete_errand(errand_id):
    user = get_current_user()

    if not user:
        return jsonify({
            "success": False,
            "message": "로그인이 필요합니다."
        })

    try:
        object_id = ObjectId(errand_id)
    except InvalidId:
        return jsonify({
            "success": False,
            "message": "잘못된 심부름 ID입니다."
        })

    errand = errands_collection.find_one({
        "_id": object_id
    })

    if not errand:
        return jsonify({
            "success": False,
            "message": "존재하지 않는 심부름입니다."
        })

    if user["_id"] == errand.get("requester_id"):
        my_field = "requester_confirmed"
        other_field = "worker_confirmed"
    elif errand.get("worker_id") and user["_id"] == errand.get("worker_id"):
        my_field = "worker_confirmed"
        other_field = "requester_confirmed"
    else:
        return jsonify({
            "success": False,
            "message": "심부름 요청자 또는 수락자만 완료를 확인할 수 있습니다."
        })

    if errand.get("status") == "COMPLETED":
        return jsonify({
            "success": False,
            "message": "이미 완료된 심부름입니다."
        })

    if errand.get("status") != "WAITING_CONFIRM":
        return jsonify({
            "success": False,
            "message": "완료 확인을 기다리는 심부름이 아닙니다."
        })

    errands_collection.update_one(
        {
            "_id": object_id,
            "status": "WAITING_CONFIRM",
            my_field: False
        },
        {
            "$set": {
                my_field: True
            }
        }
    )

    finalized_errand = errands_collection.find_one_and_update(
        {
            "_id": object_id,
            "status": "WAITING_CONFIRM",
            "requester_confirmed": True,
            "worker_confirmed": True
        },
        {
            "$set": {
                "status": "COMPLETED"
            }
        }
    )

    if finalized_errand:
        users_collection.update_one(
            {"_id": finalized_errand["worker_id"]},
            {"$inc": {"point": finalized_errand["reward"]}}
        )

        return jsonify({
            "success": True,
            "message": "양쪽 모두 확인되어 심부름이 완료 처리되었습니다.",
            "completed": True
        })

    return jsonify({
        "success": True,
        "message": "완료를 확인했습니다. 상대방의 확인을 기다려주세요.",
        "completed": False
    })


@status.route(
    "/api/errands/<errand_id>/cancel",
    methods=["POST"]
)
def cancel_errand(errand_id):
    user = get_current_user()

    if not user:
        return jsonify({
            "success": False,
            "message": "로그인이 필요합니다."
        })

    try:
        object_id = ObjectId(errand_id)
    except InvalidId:
        return jsonify({
            "success": False,
            "message": "잘못된 심부름 ID입니다."
        })

    canceled_errand = errands_collection.find_one_and_update(
        {
            "_id": object_id,
            "requester_id": user["_id"],
            "status": {
                "$in": ["OPEN", "WAITING_CONFIRM"]
            },
            "worker_confirmed": {
                "$ne": True
            }
        },
        {
            "$set": {
                "status": "CANCELED"
            }
        }
    )

    if canceled_errand:
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$inc": {"point": canceled_errand["reward"]}}
        )

        return jsonify({
            "success": True,
            "message": "심부름을 취소했습니다."
        })

    errand = errands_collection.find_one({
        "_id": object_id
    })

    if not errand:
        return jsonify({
            "success": False,
            "message": "존재하지 않는 심부름입니다."
        })

    if errand.get("requester_id") != user["_id"]:
        return jsonify({
            "success": False,
            "message": "심부름 작성자만 취소할 수 있습니다."
        })

    if errand.get("worker_confirmed"):
        return jsonify({
            "success": False,
            "message": "수락자가 완료를 확인한 심부름은 취소할 수 없습니다."
        })

    if errand.get("status") not in ["OPEN", "WAITING_CONFIRM"]:
        return jsonify({
            "success": False,
            "message": "이미 처리된 심부름은 취소할 수 없습니다."
        })

    return jsonify({
        "success": False,
        "message": "심부름을 취소할 수 없습니다."
    })