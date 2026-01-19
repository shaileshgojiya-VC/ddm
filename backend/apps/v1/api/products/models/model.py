from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from core.db import Base
from core.db.mixins.timestamp_mixin import TimestampMixin
from core.utils import constant_variable as constant


class Products(Base, TimestampMixin):
    __tablename__ = "products"

    id = Column(
        Integer,
        primary_key=constant.STATUS_TRUE,
        autoincrement=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
    )
    bitrix_id = Column(Integer, nullable=constant.STATUS_FALSE)
    sku_id = Column(String(255), nullable=constant.STATUS_TRUE, comment="SKU ID")
    category_type = Column(String(255), nullable=constant.STATUS_TRUE, comment="Category type")
    name = Column(String(255), nullable=constant.STATUS_TRUE, comment="Product name")
    supplier_id = Column(
        Integer, nullable=constant.STATUS_TRUE, comment="Supplier unique identifier"
    )
    supplier_name = Column(
        String(255), nullable=constant.STATUS_TRUE, comment="Supplier company name"
    )
    has_supplier = Column(
        Boolean,
        nullable=constant.STATUS_TRUE,
        default=constant.STATUS_FALSE,
        comment="Whether product has a supplier (Yes/No)",
    )
    code = Column(String(255), nullable=constant.STATUS_TRUE, comment="Product code")
    active = Column(
        Boolean,
        nullable=constant.STATUS_TRUE,
        default=constant.STATUS_TRUE,
        comment="Whether product is active (Yes/No)",
    )
    preview_picture = Column(Text, nullable=constant.STATUS_TRUE, comment="Preview picture")
    detail_picture = Column(Text, nullable=constant.STATUS_TRUE, comment="Detail picture")
    sort = Column(Integer, nullable=constant.STATUS_TRUE, default=0, comment="Sort order")
    xml_id = Column(String(255), nullable=constant.STATUS_TRUE, comment="XML identifier")
    timestamp_x = Column(
        DateTime, nullable=constant.STATUS_TRUE, comment="Last modification timestamp"
    )
    date_create = Column(DateTime, nullable=constant.STATUS_TRUE, comment="Creation date")
    modified_by = Column(
        String(255), nullable=constant.STATUS_TRUE, comment="User who last modified"
    )
    created_by = Column(String(255), nullable=constant.STATUS_TRUE, comment="User who created")
    catalog_id = Column(Integer, nullable=constant.STATUS_TRUE, comment="Catalog identifier")
    section_id = Column(Integer, nullable=constant.STATUS_TRUE, comment="Section identifier")
    description = Column(String(255), nullable=constant.STATUS_TRUE, comment="Product description")
    description_type = Column(
        String(255), nullable=constant.STATUS_TRUE, comment="Description format type"
    )
    price = Column(Float, nullable=constant.STATUS_TRUE, comment="Price of product")
    currency_id = Column(String(36), nullable=constant.STATUS_TRUE, comment="Currency code")
    vat_id = Column(Integer, nullable=constant.STATUS_TRUE, comment="VAT identifier")
    vat_included = Column(Boolean, nullable=constant.STATUS_TRUE, comment="Whether VAT is included")
    measure = Column(Integer, nullable=constant.STATUS_TRUE, comment="Unit of measure")
    barcode = Column(String(255), nullable=constant.STATUS_TRUE, comment="Product barcode")
    carton_barcode = Column(String(255), nullable=constant.STATUS_TRUE, comment="Carton barcode")
    bestseller = Column(Boolean, nullable=constant.STATUS_TRUE, comment="Bestseller flag")
    special_offer = Column(Boolean, nullable=constant.STATUS_TRUE, comment="Special offer flag")
    product = Column(String(255), nullable=constant.STATUS_TRUE, comment="Product name variant")
    product_label = Column(String(255), nullable=constant.STATUS_TRUE, comment="Product label")
    art_number = Column(String(255), nullable=constant.STATUS_TRUE, comment="Article number")
    factory_logo = Column(Text, nullable=constant.STATUS_TRUE, comment="Factory logo file URL")
    specifications = Column(Text, nullable=constant.STATUS_TRUE, comment="Product specifications")
    product_artwork = Column(
        Text, nullable=constant.STATUS_TRUE, comment="Product artwork file URL"
    )
    factory = Column(String(255), nullable=constant.STATUS_TRUE, comment="Factory/Supplier ID")
    factory_raw = Column(String(255), nullable=constant.STATUS_TRUE, comment="Factory raw data")
    country_of_origin = Column(
        String(255), nullable=constant.STATUS_TRUE, comment="Country of origin code"
    )
    hs_code = Column(
        String(255),
        nullable=constant.STATUS_TRUE,
        comment="Harmonized System tariff code",
    )
    package_material = Column(
        String(255), nullable=constant.STATUS_TRUE, comment="Packaging material code"
    )
    net_content = Column(Float, nullable=constant.STATUS_TRUE, comment="Net content/weight")
    background_image = Column(
        String(255), nullable=constant.STATUS_TRUE, comment="Background image file URL"
    )
    shelf_life = Column(Integer, nullable=constant.STATUS_TRUE, comment="Product shelf life")
    units_per_carton = Column(Integer, nullable=constant.STATUS_TRUE, comment="Units per carton")
    loading_quantities = Column(
        String(255), nullable=constant.STATUS_TRUE, comment="Loading quantities"
    )
    product_category = Column(
        String(255), nullable=constant.STATUS_TRUE, comment="Product category code"
    )
    product_short_name = Column(
        String(255), nullable=constant.STATUS_TRUE, comment="Short product name"
    )
    link_to_artwork_files = Column(
        Text, nullable=constant.STATUS_TRUE, comment="Link to artwork files"
    )
    sku_package = Column(String(255), nullable=constant.STATUS_TRUE, comment="SKU package units")
    cartons_per_pallet = Column(
        Integer, nullable=constant.STATUS_TRUE, comment="Number of cartons per pallet"
    )
    carton_artwork = Column(Text, nullable=constant.STATUS_TRUE, comment="Carton artwork file URL")
    photo_of_primary_packing = Column(
        Text, nullable=constant.STATUS_TRUE, comment="Photo of primary packing"
    )
    photo_of_secondary_packing = Column(
        Text,
        nullable=constant.STATUS_TRUE,
        comment="Photo of secondary packing",
    )
    technical_data_sheet = Column(
        Text,
        nullable=constant.STATUS_TRUE,
        comment="Technical data sheet file URL",
    )
    primary_packing_artwork = Column(
        Text,
        nullable=constant.STATUS_TRUE,
        comment="Primary packing artwork file URL",
    )
    secondary_packing_artwork = Column(
        Text,
        nullable=constant.STATUS_TRUE,
        comment="Secondary packing artwork file URL",
    )
    transport_conditions_temperature = Column(
        String(255),
        nullable=constant.STATUS_TRUE,
        comment="Transport conditions temperature conditions",
    )
    storage_conditions_temperature = Column(
        String(255),
        nullable=constant.STATUS_TRUE,
        comment="Storage conditions temperature",
    )
    carton_dimensions = Column(
        String(255), nullable=constant.STATUS_TRUE, comment="Carton dimensions"
    )
    pallet_dimensions = Column(
        String(255), nullable=constant.STATUS_TRUE, comment="Pallet dimensions"
    )
    lead_time_to_print_packing_material = Column(
        String(100),
        nullable=constant.STATUS_TRUE,
        comment="Lead time to print packing material",
    )
    lead_time_to_reorder_packing_material = Column(
        String(100),
        nullable=constant.STATUS_TRUE,
        comment="Lead time to reorder packing material",
    )
    lead_time_to_production = Column(
        String(100), nullable=constant.STATUS_TRUE, comment="Lead time to production"
    )
    art_works_approved_by_fda_of_country_of_destination = Column(
        Boolean,
        nullable=constant.STATUS_TRUE,
        comment="Art works approved by FDA of country of destination",
    )
    loading_address = Column(String(255), nullable=constant.STATUS_TRUE, comment="Loading address")
    unit_pack_size = Column(Integer, nullable=constant.STATUS_TRUE, comment="Unit pack size")
    packing = Column(String(255), nullable=constant.STATUS_TRUE, comment="Packing type")
    carton = Column(String(255), nullable=constant.STATUS_TRUE, comment="Carton specification")
    term_of_delivery = Column(
        Integer, nullable=constant.STATUS_TRUE, comment="Delivery terms (Incoterms)"
    )
    quantity = Column(Integer, nullable=constant.STATUS_TRUE, comment="Quantity")
    origin = Column(String(255), nullable=constant.STATUS_TRUE, comment="Origin")
    product_keylines = Column(
        Text, nullable=constant.STATUS_TRUE, comment="Product keylines file URL"
    )
    documents_from_factory = Column(
        Text,
        nullable=constant.STATUS_TRUE,
        comment="Documents from factory (COO, HC, FSC)",
    )
    moq_packaging_matereal = Column(
        Integer,
        nullable=constant.STATUS_TRUE,
        comment="Minimum order quantity for packaging material",
    )
    moq_production = Column(
        Integer,
        nullable=constant.STATUS_TRUE,
        comment="Minimum order quantity for production",
    )
    category_id = Column(Integer, nullable=constant.STATUS_TRUE, comment="Category ID (FK)")
    parent_product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=constant.STATUS_TRUE,
        comment="Parent Product ID (FK) - On delete cascade",
    )
    parent_category_id = Column(
        Integer, nullable=constant.STATUS_TRUE, comment="Parent Category ID (FK)"
    )
    sub_category_id = Column(Integer, nullable=constant.STATUS_TRUE, comment="Sub Category ID (FK)")
    date_active_from = Column(
        DateTime, nullable=constant.STATUS_TRUE, comment="Product active from date"
    )
    date_active_to = Column(
        DateTime, nullable=constant.STATUS_TRUE, comment="Product active to date"
    )
    updated_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="User ID who last updated the product (mapped from modified_by Bitrix ID)",
    )
    generated_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="User ID who created the product (mapped from created_by Bitrix ID)",
    )

    # Relationships
    category = relationship(
        "Categories",
        primaryjoin="Products.category_id == Categories.id",
        foreign_keys=[category_id],
        uselist=False,
        lazy="select",
    )
    parent_category = relationship(
        "Categories",
        primaryjoin="Products.parent_category_id == Categories.id",
        foreign_keys=[parent_category_id],
        uselist=False,
        lazy="select",
    )
    sub_category = relationship(
        "Categories",
        primaryjoin="Products.sub_category_id == Categories.id",
        foreign_keys=[sub_category_id],
        uselist=False,
        lazy="select",
    )
    product_suppliers = relationship(
        "ProductSupplierMapping",
        foreign_keys="ProductSupplierMapping.product_id",
        back_populates="product",
        lazy="selectin",
    )
    updated_by_user = relationship(
        "Users",
        foreign_keys=[updated_by],
        uselist=False,
        lazy="select",
    )
    generated_by_user = relationship(
        "Users",
        foreign_keys=[generated_by],
        uselist=False,
        lazy="select",
    )


class Categories(Base, TimestampMixin):
    __tablename__ = "categories"

    id = Column(
        Integer,
        primary_key=constant.STATUS_TRUE,
        autoincrement=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
    )
    bitrix_id = Column(Integer, nullable=constant.STATUS_TRUE, comment="Bitrix category ID")
    parent_category_id = Column(
        Integer, nullable=constant.STATUS_TRUE, comment="Parent category ID"
    )
    sub_category_id = Column(
        Integer,
        nullable=constant.STATUS_TRUE,
        comment="Sub category UUID",
    )
    catelog_id = Column(Integer, nullable=constant.STATUS_TRUE, comment="Category ID")
    section_id = Column(Integer, nullable=constant.STATUS_TRUE, comment="Section ID")
    name = Column(String(100), nullable=constant.STATUS_TRUE, comment="Category name")
    code = Column(String(100), nullable=constant.STATUS_TRUE, comment="Category code")
