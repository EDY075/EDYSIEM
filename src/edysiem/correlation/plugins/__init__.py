"""Plugins (regras) de correlacao do EDY SIEM.

Cada regra implementa ``CorrelationRule`` e informa via ``CorrelationMetadata``
o que precisa. Nenhuma regra hardcoded no engine.

Regras oficiais (sprints futuras):
- ``demo.py``: DEMO - mesmo IP gerou mais de N eventos em X minutos
- brute_force.py: multiplas falhas de autenticacao no mesmo host
- impossible_travel.py: login em locais geograficamente distantes
- beaconing.py: comunicacoes periodicas com C2
"""

from .demo import ThresholdByIpRule

__all__ = ["ThresholdByIpRule"]
