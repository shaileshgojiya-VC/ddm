"""
Service for importing products from JSON file and listing them.
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.products.models.methods import CategoryRepository, ProductRepository
from apps.v1.api.products.models.model import Categories, Products
from apps.v1.api.products.serializer import ProductSerializer
from core.utils.pagination import Page

logger = logging.getLogger(__name__)


class ProductImportService:
    """Service for product import and listing operations."""

    def __init__(self, file_path: Optional[str] = None):
        if file_path:
            self.file_path = Path(file_path)
        else:
            # Default to all_products_readable.json in the project root
            self.file_path = (
                Path(__file__).resolve().parents[5]
                / "all_products_readable_formatted.json"
            )

    async def import_and_list(
        self,
        db: AsyncSession,
        params,
        name_filter: Optional[str] = None,
        min_price_filter: Optional[float] = None,
        max_price_filter: Optional[float] = None,
        certificate_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
        **_: Any,
    ) -> Page[dict]:
        """Import products if needed and return paginated list."""
        filters = ProductRepository.parse_filter(
            name_filter,
            min_price_filter,
            max_price_filter,
            certificate_filter,
            category_filter,
        )

        await self._import_if_needed(db)

        total = await ProductRepository.count_products(db, filters)
        offset, size = ProductRepository.resolve_params(params)
        if getattr(params, "size", None) is None:
            params.size = size

        items = await ProductRepository.fetch_product_page(db, offset, size, filters)
        data = ProductSerializer().dump(items, many=True)

        # Add category path information to each product using denormalized fields
        for i, product in enumerate(items):
            category_path = {
                "main_category": None,
                "sub_category": None,
                "sub_sub_category": None,
                "main_category_uuid": None,
                "sub_category_uuid": None,
                "sub_sub_category_uuid": None,
            }

            # Use denormalized fields for fast access
            if product.parent_category_uuid:
                parent_cat = await CategoryRepository.fetch_category_by_uuid(
                    db, product.parent_category_uuid
                )
                if parent_cat:
                    category_path["main_category"] = parent_cat.name
                    category_path["main_category_uuid"] = parent_cat.uuid

            if product.sub_category_uuid:
                sub_cat = await CategoryRepository.fetch_category_by_uuid(
                    db, product.sub_category_uuid
                )
                if sub_cat:
                    category_path["sub_category"] = sub_cat.name
                    category_path["sub_category_uuid"] = sub_cat.uuid

            # Get current category (sub-sub level) via section_id
            if product.section_id:
                current_cat = await db.execute(
                    select(Categories).where(Categories.bitrix_id == product.section_id)
                )
                current_cat = current_cat.scalar_one_or_none()
                if current_cat:
                    category_path["sub_sub_category"] = current_cat.name
                    category_path["sub_sub_category_uuid"] = current_cat.uuid

            data[i]["category_path"] = category_path

        return Page.create(items=data, total=total, params=params)

    async def get_product_by_id(self, db: AsyncSession, product_id: str) -> dict:
        """Get a single product by xml_id."""
        product = await ProductRepository.fetch_product_by_xml_id(db, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        serializer = ProductSerializer()
        return serializer.dump(product)

    async def _import_if_needed(self, db: AsyncSession) -> None:
        """Import products from JSON file if table is empty."""
        if await ProductRepository.count_products(db, None) > 0:
            return

        if not self.file_path.exists():
            logger.warning(
                f"Product file not found at {self.file_path}; skipping import"
            )
            return

        try:
            # Convert Path to string for load_json_file
            raw_data = ProductRepository.load_json_file(str(self.file_path))
            if not raw_data:
                logger.warning(
                    f"Product file {self.file_path} is empty or contains no data"
                )
                return
            logger.info(
                f"Loaded {len(raw_data) if isinstance(raw_data, list) else 1} products from {self.file_path}"
            )
        except FileNotFoundError as e:
            logger.error(f"Product file not found: {e}")
            return
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in product file {self.file_path}: {e}")
            return
        except Exception as e:
            logger.error(
                f"Error loading product file {self.file_path}: {e}", exc_info=True
            )
            return

        try:
            normalized = ProductSerializer().load(raw_data, many=True)
            if not normalized:
                logger.warning("No products were normalized from the JSON data")
                return
            logger.info(f"Normalized {len(normalized)} products for import")
        except Exception as e:
            logger.error(f"Error serializing product data: {e}", exc_info=True)
            return

        allowed_fields = {col.name for col in Products.__table__.columns}
        # Exclude 'id' field to ensure it remains autoincrement
        allowed_fields.discard("id")

        # Verify new columns are in allowed_fields
        logger.info(
            f"STEP 0: Allowed fields include category_uuid: {'category_uuid' in allowed_fields}"
        )
        logger.info(
            f"STEP 0: Allowed fields include parent_category_uuid: {'parent_category_uuid' in allowed_fields}"
        )
        logger.info(
            f"STEP 0: Allowed fields include sub_category_uuid: {'sub_category_uuid' in allowed_fields}"
        )
        if (
            "category_uuid" not in allowed_fields
            or "parent_category_uuid" not in allowed_fields
            or "sub_category_uuid" not in allowed_fields
        ):
            logger.warning(
                "WARNING: category_uuid, parent_category_uuid or sub_category_uuid not found in model columns. "
                "Database table may need migration."
            )

        # First pass: clean records and prepare for category lookup
        clean_records = []
        section_ids_to_resolve = set()

        for rec in normalized:
            clean_rec = {
                k: json.dumps(v) if isinstance(v, (dict, list)) else v
                for k, v in rec.items()
                if k in allowed_fields
            }
            clean_records.append(clean_rec)

            # Collect section_ids that need category references
            section_id = clean_rec.get("section_id")
            if section_id:
                try:
                    section_ids_to_resolve.add(int(section_id))
                except (ValueError, TypeError):
                    pass

        # Get category references for all unique section_ids
        logger.info(
            f"STEP 1: Resolving category references for {len(section_ids_to_resolve)} unique section IDs"
        )
        category_references = {}
        resolved_count = 0

        for section_id in section_ids_to_resolve:
            try:
                refs = await CategoryRepository.get_category_references_by_bitrix_id(
                    db, section_id
                )
                category_references[section_id] = refs
                if (
                    refs.get("category_uuid")
                    or refs.get("parent_category_uuid")
                    or refs.get("sub_category_uuid")
                ):
                    resolved_count += 1
            except Exception as e:
                logger.warning(
                    f"Failed to get category references for section_id {section_id}: {e}"
                )
                category_references[section_id] = {
                    "category_uuid": None,
                    "parent_category_uuid": None,
                    "sub_category_uuid": None,
                }

        logger.info(
            f"STEP 2: Resolved category references for {resolved_count}/{len(section_ids_to_resolve)} section IDs"
        )

        # Populate category references in records
        logger.info(
            "STEP 3: Populating category_uuid, parent_category_uuid and sub_category_uuid in product records"
        )
        populated_count = 0

        for rec in clean_records:
            section_id = rec.get("section_id")
            if section_id:
                try:
                    section_id_int = int(section_id)
                    refs = category_references.get(
                        section_id_int,
                        {
                            "category_uuid": None,
                            "parent_category_uuid": None,
                            "sub_category_uuid": None,
                        },
                    )
                    rec["category_uuid"] = refs.get("category_uuid")
                    rec["parent_category_uuid"] = refs.get("parent_category_uuid")
                    rec["sub_category_uuid"] = refs.get("sub_category_uuid")

                    # Add detailed logging for first few records
                    if populated_count < 3:
                        logger.info(
                            f"Sample record {populated_count + 1}: section_id={section_id_int}, "
                            f"category_uuid={rec.get('category_uuid')}, "
                            f"parent_uuid={rec.get('parent_category_uuid')}, "
                            f"sub_uuid={rec.get('sub_category_uuid')}"
                        )

                    if (
                        rec["category_uuid"]
                        or rec["parent_category_uuid"]
                        or rec["sub_category_uuid"]
                    ):
                        populated_count += 1
                except (ValueError, TypeError):
                    rec["category_uuid"] = None
                    rec["parent_category_uuid"] = None
                    rec["sub_category_uuid"] = None
            else:
                rec["category_uuid"] = None
                rec["parent_category_uuid"] = None
                rec["sub_category_uuid"] = None

        logger.info(
            f"STEP 4: Populated category references for {populated_count}/{len(clean_records)} products"
        )

        # Bulk insert in chunks (DB ignores duplicates via IGNORE)
        chunk_size = 200
        total_chunks = (len(clean_records) + chunk_size - 1) // chunk_size
        logger.info(
            f"Starting import of {len(clean_records)} products in {total_chunks} chunks"
        )

        successful_chunks = 0
        failed_chunks = 0

        for i in range(0, len(clean_records), chunk_size):
            chunk = clean_records[i : i + chunk_size]
            chunk_num = (i // chunk_size) + 1

            # Verify first chunk has the fields
            if chunk_num == 1 and chunk:
                sample = chunk[0]
                logger.info(
                    f"Sample record before insert - has category_uuid: {'category_uuid' in sample}, "
                    f"value: {sample.get('category_uuid')}"
                )
                logger.info(
                    f"Sample record before insert - has parent_category_uuid: {'parent_category_uuid' in sample}, "
                    f"value: {sample.get('parent_category_uuid')}"
                )
                logger.info(
                    f"Sample record before insert - has sub_category_uuid: {'sub_category_uuid' in sample}, "
                    f"value: {sample.get('sub_category_uuid')}"
                )

            try:
                await db.execute(
                    mysql_insert(Products).prefix_with("IGNORE").values(chunk)
                )
                await db.commit()
                successful_chunks += 1
                logger.info(
                    f"Imported chunk {chunk_num}/{total_chunks} ({len(chunk)} products)"
                )
            except OperationalError as exc:
                failed_chunks += 1
                logger.error(
                    f"Import chunk {chunk_num}/{total_chunks} ({i}-{i + len(chunk)}) failed: {exc}"
                )
                # Log the actual SQL error details
                logger.error(f"Error details: {str(exc)}")
                await db.rollback()
            except Exception as exc:
                failed_chunks += 1
                logger.error(
                    f"Unexpected error in chunk {chunk_num}/{total_chunks}: {exc}"
                )
                logger.error(f"Error type: {type(exc).__name__}, Details: {str(exc)}")
                await db.rollback()

        logger.info(
            f"Import completed: {successful_chunks} successful chunks, {failed_chunks} failed chunks"
        )
