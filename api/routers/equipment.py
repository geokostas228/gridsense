from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict

from db.mongo import equipment_collection


router = APIRouter(
    prefix="/equipment",
    tags=["Equipment"]
)


class EquipmentCreate(BaseModel):
    asset_id: str
    equipment_type: str
    metadata: Dict[str, Any]


class EquipmentPatch(BaseModel):
    updates: Dict[str, Any]


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


@router.get("/{asset_id}")
def get_equipment(asset_id: str):
    doc = equipment_collection.find_one({
        "$or": [
            {"asset_id": asset_id},
            {"equipment_id": asset_id}
        ]
    })

    if not doc:
        raise HTTPException(status_code=404, detail="Equipment not found")

    return serialize_document(doc)


@router.post("")
def create_equipment(equipment: EquipmentCreate):
    doc = {
        "asset_id": equipment.asset_id,
        "equipment_type": equipment.equipment_type,
        **equipment.metadata
    }

    equipment_collection.replace_one(
        {"asset_id": equipment.asset_id},
        doc,
        upsert=True
    )

    saved = equipment_collection.find_one({"asset_id": equipment.asset_id})

    return {
        "created_or_updated": True,
        "equipment": serialize_document(saved)
    }


@router.patch("/{asset_id}")
def patch_equipment(asset_id: str, patch: EquipmentPatch):
    result = equipment_collection.update_one(
        {
            "$or": [
                {"asset_id": asset_id},
                {"equipment_id": asset_id}
            ]
        },
        {"$set": patch.updates}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Equipment not found")

    doc = equipment_collection.find_one({
        "$or": [
            {"asset_id": asset_id},
            {"equipment_id": asset_id}
        ]
    })

    return {
        "updated": True,
        "equipment": serialize_document(doc)
    }