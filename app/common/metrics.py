"""Módulo de métricas de Prometheus."""
from prometheus_client import Counter


# Métricas personalizadas
reservations_created_total = Counter(
    'reservations_created_total',
    'Total de reservas creadas',
    ['tenant_id', 'service']
)

reservations_rejected_total = Counter(
    'reservations_rejected_total',
    'Total de reservas rechazadas',
    ['tenant_id', 'reason']
)


class Metrics:
    """Clase helper para métricas."""
    
    @staticmethod
    def inc_created(tenant_id: str, service: str):
        """Incrementa contador de reservas creadas."""
        reservations_created_total.labels(
            tenant_id=tenant_id,
            service=service
        ).inc()
    
    @staticmethod
    def inc_rejected(tenant_id: str, reason: str):
        """Incrementa contador de reservas rechazadas."""
        reservations_rejected_total.labels(
            tenant_id=tenant_id,
            reason=reason
        ).inc()


metrics = Metrics()





