from enum import Enum


class RequestStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    DELETED = "deleted"
    COMPLETED = "completed"
    NEW_UNCLEAR = "new_unclear"


class StageStatus(Enum):
    NEW_UNCLEAR = "new_unclear"
    NEW_CLEAR = "new_clear"
    LOST = "lost"
    CONTINUE = "continue"
    REJECT = "reject"
    ACCEPT = "accept"
    APPROVED = "approved"


class RequestPhase(Enum):
    INQUIRY = "inquiry"
    LEAD = "lead"
    REGISTRATION = "registration"
    DEAL = "deal"


class RegistrationStep(Enum):
    JOIN_WITH_BUYER_TEAM = "join_with_buyer_team"
    IDENTIFY_EXACT_PRODUCT = "identify_exact_product"
    OBTAIN_LIST_OF_DOCUMENTS = "obtain_list_of_documents"
    EXECUTION_PLAN = "execution_plan"
    ART_WORK_PREPARATION = "art_work_preparation"
    DOCS_PREPARATION = "docs_preparation"
    DOCS_SUBMITTED = "docs_submitted"
    DISPATCH_APPROVED_DOCUMENTS = "dispatch_approved_documents"
    REGISTER_APPROVAL = "register_approval"
    MOVE_TO_DEAL = "move_to_deal"


class DealOutcome(Enum):
    ON_HOLD = "on_hold"
    SOURCING_PRICING = "sourcing_pricing"
    PROPOSAL_QUOTATION = "proposal_quotation"
    CUSTOMER_REVIEW_FEEDBACK = "customer_review_feedback"
    NEGOTIATION = "negotiation"
    AGREEMENT = "agreement"
    ORDER_PLACEMENT = "order_placement"
    PROFORMA = "proforma"
    GO_TO_OPERATION = "go_to_operation"
    GO_TO_REGISTRATION = "go_to_registration"


class Source(Enum):
    BITRIX = "bitrix"
    ONEDRIVE = "onedrive"
    SHEET = "sheet"
    OUTLOOK = "outlook"


class ProjectGroup(Enum):
    Y = "Y"  # Important Project
    Z = "Z"  # Agreed Finished
    EX = "EX"  # Existing Customers


class LeadGroup(Enum):
    GROUP_A = "GROUP_A"  # Danalac Infant Formula
    GROUP_B = "GROUP_B"  # Dana Consumer Pack Dairy Product
    GROUP_C = "GROUP_C"  # Food Service Dairy Product
    GROUP_D = "GROUP_D"  # Dairy Ingredients to Manufacturers
    GROUP_E = "GROUP_E"  # Infant Formula in 25KG
    GROUP_F = "GROUP_F"  # Baby Food Private Label
    GROUP_G = "GROUP_G"  # Infant Formula Dubai/Korea
    GROUP_H = "GROUP_H"  # Baby Cereal 25KG
    GROUP_I = "GROUP_I"  # Dairy Product Private Label


class DealActionStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"
    CANCELLED = "cancelled"


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class StagePhase(Enum):
    LEAD = "lead"
    REGISTRATION = "registration"
    DEAL = "deal"
