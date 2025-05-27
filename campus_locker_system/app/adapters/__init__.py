# Adapters package - external system interfaces

from .email_adapter import EmailAdapterInterface, create_email_adapter
from .database_adapter import DatabaseAdapterInterface, create_database_adapter
from .audit_adapter import AuditAdapterInterface, create_audit_adapter

__all__ = [
    'EmailAdapterInterface',
    'DatabaseAdapterInterface', 
    'AuditAdapterInterface',
    'create_email_adapter',
    'create_database_adapter',
    'create_audit_adapter'
] 