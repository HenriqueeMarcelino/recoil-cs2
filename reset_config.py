#!/usr/bin/env python3
"""
Reset de Configuração - CS2 Recoil Trainer
===========================================

IMPORTANTE: Execute este script ANTES de usar o recoil_trainer.py
após a atualização da fórmula de scale!

Isso vai resetar o scale_multiplier para 1.0 (valor seguro).
"""

import json
from pathlib import Path

def reset_config():
    """Reseta configurações para valores seguros"""
    config_file = Path("config.json")

    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)

        # Reseta scale_multiplier
        old_mult = config.get('scale_multiplier', 1.0)
        config['scale_multiplier'] = 1.0

        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        print("✅ Configuração resetada!")
        print(f"   Scale Multiplier: {old_mult} → 1.0")
        print(f"   DPI: {config.get('dpi', 800)}")
        print(f"   Sens: {config.get('sensitivity', 1.0)}")
        print(f"   eDPI: {config.get('dpi', 800) * config.get('sensitivity', 1.0)}")
        print()
        print("💡 NOVA FÓRMULA implementada:")
        print("   - Normalizada por eDPI")
        print("   - Começa com multiplier 1.0")
        print("   - Ajuste com +/- botões se necessário")
        print()
        print("🎯 Agora execute: python recoil_trainer.py")
    else:
        print("⚠️ Arquivo config.json não encontrado")
        print("   Não há problema, será criado automaticamente")

if __name__ == "__main__":
    reset_config()
