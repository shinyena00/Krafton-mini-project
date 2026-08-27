from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, jsonify

from db import users_collection, errands_collection
from routes.auth import get_current_user


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
            }
        },
        {
            "$set": {
                "status": "WAITING_CONFIRM",
                "worker_id": user["_id"]
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

    completed_errand = errands_collection.find_one_and_update(
        {
            "_id": object_id,
            "status": "WAITING_CONFIRM",
            "requester_id": user["_id"],
            "worker_id": {
                "$ne": None
            }
        },
        {
            "$set": {
                "status": "COMPLETED"
            }
        }
    )

    if completed_errand:
        users_collection.update_one(
            {"_id": completed_errand["worker_id"]},
            {"$inc": {"point": completed_errand["reward"]}}
        )

        return jsonify({
            "success": True,
            "message": "심부름 완료를 확정했습니다."
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
            "message": "심부름 작성자만 완료를 확정할 수 있습니다."
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

    if not errand.get("worker_id"):
        return jsonify({
            "success": False,
            "message": "심부름 수락자 정보가 없습니다."
        })

    return jsonify({
        "success": False,
        "message": "심부름 완료를 확정할 수 없습니다."
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
            "status": "OPEN",
            "worker_id": None
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

    if errand.get("status") != "OPEN":
        return jsonify({
            "success": False,
            "message": "이미 처리된 심부름은 취소할 수 없습니다."
        })

    return jsonify({
        "success": False,
        "message": "심부름을 취소할 수 없습니다."
    })