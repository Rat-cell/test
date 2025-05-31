# Adapters package - external system interfaces

from .email_adapter import EmailAdapterInterface, create_email_adapter
# Database adapter removed
# from .database_adapter import DatabaseAdapterInterface, create_database_adapter
from .audit_adapter import AuditAdapterInterface, MockAuditAdapter

__all__ = [
    'EmailAdapterInterface',
    # 'DatabaseAdapterInterface', # Removed
    'AuditAdapterInterface',
    'MockAuditAdapter',
    'create_email_adapter',
    # 'create_database_adapter', # Removed
] 