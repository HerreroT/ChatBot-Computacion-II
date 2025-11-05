"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tabla tenants
    op.create_table(
        'tenants',
        sa.Column('id', sa.String(50), primary_key=True, comment='ID único del tenant'),
        sa.Column('name', sa.String(200), nullable=False, comment='Nombre del tenant'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    
    # Insertar tenant demo
    op.execute(
        "INSERT INTO tenants (id, name) VALUES ('barberia-01', 'Barbería Demo')"
    )
    
    # Tabla reservations
    op.create_table(
        'reservations',
        sa.Column('id', sa.String(36), primary_key=True, comment='UUID de la reserva'),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True, comment='ID del tenant'),
        sa.Column('message_id', sa.String(100), nullable=False, comment='ID del mensaje WhatsApp'),
        sa.Column('phone', sa.String(20), nullable=False, index=True, comment='Teléfono del cliente'),
        sa.Column('service', sa.String(50), nullable=False, comment='Servicio solicitado'),
        sa.Column('start_at', sa.DateTime(), nullable=False, index=True, comment='Fecha y hora en UTC'),
        sa.Column('status', sa.String(20), nullable=False, server_default='CONFIRMED', comment='Estado de la reserva'),
        sa.Column('source', sa.String(20), nullable=False, server_default='whatsapp', comment='Origen de la reserva'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
    )
    
    # Índices
    op.create_index('idx_tenant_message', 'reservations', ['tenant_id', 'message_id'], unique=True)
    op.create_index('idx_tenant_slot', 'reservations', ['tenant_id', 'start_at', 'status'])


def downgrade() -> None:
    op.drop_index('idx_tenant_slot', table_name='reservations')
    op.drop_index('idx_tenant_message', table_name='reservations')
    op.drop_table('reservations')
    op.drop_table('tenants')





