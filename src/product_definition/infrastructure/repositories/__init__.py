"""
Repository implementations for product definition domain.
"""

from src.product_definition.infrastructure.repositories.mongodb_product_requirement_repository import MongoDBProductRequirementRepository
from src.product_definition.infrastructure.repositories.file_product_requirement_repository import FileProductRequirementRepository

__all__ = [
    "MongoDBProductRequirementRepository",
    "FileProductRequirementRepository"
] 