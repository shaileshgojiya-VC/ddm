"""
Service to import suppliers from a JSON dump and provide paginated results.
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy import Integer
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.suppliers.models.methods import (
    bulk_insert_suppliers,
    count_suppliers,
    fetch_supplier_page,
    load_json_file,
    parse_filter,
    resolve_params,
)
from apps.v1.api.suppliers.models.methods import (
    get_supplier_by_id as fetch_supplier_by_id,
)
from apps.v1.api.suppliers.models.model import Suppliers
from apps.v1.api.suppliers.schema import SupplierFullSchema
from apps.v1.api.suppliers.serializer import SupplierSerializer
from core.utils.pagination import Page, Params


class SupplierImportService:
    """Import suppliers from the bundled JSON file and list them."""

    def __init__(self) -> None:
        # Find the JSON file at project root
        current_file = Path(__file__).resolve()
        project_root = current_file
        for _ in range(6):  # Go up 6 levels to reach project root
            project_root = project_root.parent
            if (project_root / "all_supplier_data_details_formatted.json").exists():
                break
        self.file_path = project_root / "all_supplier_data_details_formatted.json"

    async def import_and_list(
        self,
        db: AsyncSession,
        params: Params,
        auto_import: bool = True,
        filter_raw: Optional[str] = None,
        name_filter: Optional[str] = None,
        country_filter: Optional[str] = None,
    ) -> Page[SupplierFullSchema]:
        """Ensure suppliers are imported and return a paginated list."""
        resolved_params = resolve_params(params)
        filter_data = parse_filter(
            filter_raw=filter_raw,
            name_filter=name_filter,
            country_filter=country_filter,
        )

        if auto_import:
            await self._import_if_needed(db=db)

        total = await count_suppliers(db, filters=filter_data)
        items = await fetch_supplier_page(
            db=db, params=resolved_params, filters=filter_data
        )

        serializer = SupplierSerializer()
        serialized_items = serializer.dump(items, many=True)

        # Serializer now handles id and bitrix_id correctly, no manual mapping needed

        return Page.create(
            items=serialized_items,
            total=total,
            params=resolved_params,
        )

    async def _import_if_needed(self, db: AsyncSession) -> None:
        """Load JSON file and bulk-insert suppliers if the table is empty."""
        existing_total = await count_suppliers(db)
        if existing_total > 0:
            return

        if not self.file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supplier source file not found at {self.file_path}",
            )

        raw_data = await asyncio.to_thread(load_json_file, self.file_path)
        normalized = SupplierSerializer().load(raw_data, many=True)

        records = normalized

        if not records:
            return

        allowed_fields = {col.name for col in Suppliers.__table__.columns}
        # Exclude 'id' field to ensure it remains autoincrement
        allowed_fields.discard("id")
        clean_records = [
            self._clean_record_for_database(
                {k: v for k, v in record.items() if k in allowed_fields}
            )
            for record in records
        ]

        await bulk_insert_suppliers(db=db, records=clean_records)

    @staticmethod
    def _clean_integer_value(value: Any) -> Optional[int]:
        """
        Clean and convert integer values, converting empty strings to None.
        """
        if value is None or value == "":
            return None

        if isinstance(value, int):
            return value

        if isinstance(value, str):
            value = value.strip()
            if value == "" or value.lower() in ["null", "none", "n/a"]:
                return None
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return None

        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _clean_record_for_database(record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean record data types to match database schema.
        Handles empty strings for integer fields, dict/list serialization, and type conversions.
        """
        safe_record = {}
        column_types = {col.name: type(col.type) for col in Suppliers.__table__.columns}

        for k, v in record.items():
            if k not in column_types:
                safe_record[k] = v
                continue

            col_type = column_types[k]
            col = Suppliers.__table__.columns[k]

            # Handle integer fields - convert empty strings to None
            if col_type == Integer:
                safe_record[k] = SupplierImportService._clean_integer_value(v)
            # Handle dict/list - convert to JSON string
            elif isinstance(v, (dict, list)):
                try:
                    safe_record[k] = json.dumps(v)
                except Exception:
                    safe_record[k] = None
            # Handle empty strings for nullable string/text fields
            elif isinstance(v, str) and col.nullable and v.strip() == "":
                safe_record[k] = None
            else:
                safe_record[k] = v

        return safe_record

    async def get_supplier_by_id(
        self, db: AsyncSession, supplier_id: str
    ) -> Dict[str, Any]:
        """Fetch a single supplier by database id only."""
        try:
            db_id = int(supplier_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supplier ID must be a valid integer",
            )

        supplier = await fetch_supplier_by_id(db=db, supplier_id=db_id)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found"
            )
        return SupplierSerializer().dump(supplier)
