"""
Compatibilidade legado.

O projeto utiliza apenas `crm_advocacia.settings` como fonte única de configuração.
Este módulo existe para evitar quebra de imports antigos.
"""

from crm_advocacia.settings import *  # noqa: F401,F403
