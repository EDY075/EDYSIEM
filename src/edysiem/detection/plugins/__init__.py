"""Plugins (regras) de deteccao do EDY SIEM.

Cada regra implementa ``DetectionRule`` e informa via ``RuleMetadata``
o que precisa. Nenhuma regra hardcoded no engine.

Regras oficiais (sprints futuras):
- ``demo.py``: DEMO - mais de 5 falhas de login em 5 minutos
- brute_force.py: ataques de forca bruta por host
- malware_detection.py: assinaturas de malware
- exfiltration.py: grande volume de dados para IP externo
"""

from .demo import LoginFailuresRule

__all__ = ["LoginFailuresRule"]
