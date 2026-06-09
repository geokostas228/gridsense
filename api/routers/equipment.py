from fastapi import APIRouter
from bson import ObjectId

from db.mongo import equipment_collection

router = APIRouter(
    prefix="/equipment",
    tags=["Equipment"]
)


def serialize_document(doc):
    doc["_id"] = str(doc["_id"])
    return doc


@router.get("/")
def list_equipment():

    docs = equipment_collection.find()

    return {
        "equipment": [
            serialize_document(doc)
            for doc in docs
        ]
    }


@router.get("/{equipment_id}")
def get_equipment(equipment_id: str):

    doc = equipment_collection.find_one(
        {"equipment_id": equipment_id}
    )

    if not doc:
        return {
            "error": "Equipment not found"
        }

    return serialize_document(doc)