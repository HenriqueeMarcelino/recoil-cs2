#!/usr/bin/env python3
"""
CS2 AK-47 Recoil Compensation - CALIBRAÇÃO FINAL
=================================================

Versão com cálculo automático baseado em DPI + Sensibilidade.

Calcula o scale ideal usando a fórmula de conversão do CS2:
- Considera DPI do mouse
- Considera sensibilidade do jogo
- Usa m_yaw do CS2 (0.022)
- Permite ajuste fino manual

CONTROLES:
- F1: Ativar/Desativar compensador
- F2: Aumentar scale (+10%)
- F3: Diminuir scale (-10%)
- F4: Salvar configuração atual
- Ctrl+C: Sair

Autor: POC para estudo de padrões de recoil
"""

import csv
import time
import threading
import sys
import platform
import json
from pynput import mouse, keyboard
from pynput.mouse import Button
from pynput.keyboard import Key, KeyCode

if platform.system() == 'Windows':
    import ctypes
    from ctypes import windll, Structure, c_long, c_ulong, POINTER

    class MOUSEINPUT(Structure):
        _fields_ = [
            ('dx', c_long),
            ('dy', c_long),
            ('mouseData', c_ulong),
            ('dwFlags', c_ulong),
            ('time', c_ulong),
            ('dwExtraInfo', POINTER(c_ulong))
        ]

    class INPUT(Structure):
        _fields_ = [
            ('type', c_ulong),
            ('mi', MOUSEINPUT)
        ]

    INPUT_MOUSE = 0
    MOUSEEVENTF_MOVE = 0x0001


class RecoilCompensator:
    def __init__(self, pattern_file, sensitivity=1.0, dpi=800, resolution=(1920, 1080)):
        self.pattern = self.load_pattern(pattern_file)
        self.sensitivity = sensitivity
        self.dpi = dpi
        self.resolution = resolution

        self.is_windows = platform.system() == 'Windows'
        if not self.is_windows:
            print("⚠️  AVISO: Este script foi otimizado para Windows.")
            sys.exit(1)

        # Calcula eDPI e scale base
        self.edpi = self.dpi * self.sensitivity
        self.m_yaw = 0.022  # Valor padrão do CS2

        # Calcula scale teórico baseado na fórmula do CS2
        # Formula: scale = base_conversion / (sensitivity × m_yaw × dpi_factor)
        dpi_factor = self.dpi / 800.0  # Normaliza para 800 DPI base
        self.scale_base = 10.0 / (self.sensitivity * dpi_factor)  # Valor empírico ajustado

        # Multiplier ajustável em tempo real
        self.scale_multiplier = 1.0

        # Estado
        self.is_shooting = False
        self.current_bullet = 0
        self.shoot_thread = None
        self.running = True
        self.enabled = False
        self.fire_rate = 0.1

        print(f"✓ Padrão carregado: {len(self.pattern)} bullets")
        print(f"✓ DPI: {self.dpi}")
        print(f"✓ Sensibilidade: {self.sensitivity}")
        print(f"✓ eDPI: {self.edpi}")
        print(f"✓ Resolução: {self.resolution[0]}x{self.resolution[1]}")
        print(f"✓ Scale Base (calculado): {self.scale_base:.4f}")
        print(f"✓ Scale Final: {self.get_current_scale():.4f}")

    def get_current_scale(self):
        """Retorna o scale atual (base × multiplier)"""
        return self.scale_base * self.scale_multiplier

    def load_pattern(self, pattern_file):
        pattern = []
        try:
            with open(pattern_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    x = float(row['x'])
                    y = float(row['y'])
                    pattern.append((x, y))
            print(f"✓ Carregado padrão com {len(pattern)} pontos")
            return pattern
        except Exception as e:
            print(f"✗ Erro ao carregar padrão: {e}")
            sys.exit(1)

    def move_mouse_event(self, dx, dy):
        dx = int(dx)
        dy = int(dy)
        ctypes.windll.user32.mouse_event(0x0001, dx, dy, 0, 0)

    def calculate_compensation(self, bullet_index):
        if bullet_index >= len(self.pattern):
            bullet_index = len(self.pattern) - 1

        x, y = self.pattern[bullet_index]

        # Aplica scale atual
        current_scale = self.get_current_scale()

        dx = -x * current_scale
        dy = -y * current_scale

        return (dx, dy)

    def compensate_recoil(self):
        self.current_bullet = 0
        last_shot_time = time.time()

        print(f"\n🎯 Spray iniciado - Scale: {self.get_current_scale():.4f}")

        while self.is_shooting and self.running and self.enabled:
            current_time = time.time()

            if current_time - last_shot_time >= self.fire_rate:
                dx, dy = self.calculate_compensation(self.current_bullet)
                self.move_mouse_event(dx, dy)

                print(f"Tiro {self.current_bullet + 1}/30: ({dx:.1f}, {dy:.1f})")

                self.current_bullet += 1
                last_shot_time = current_time

                if self.current_bullet >= len(self.pattern):
                    self.current_bullet = len(self.pattern) - 1

            time.sleep(0.001)

    def on_click(self, x, y, button, pressed):
        if not self.enabled:
            return

        if button == Button.left:
            if pressed and not self.is_shooting:
                self.is_shooting = True
                self.current_bullet = 0
                self.shoot_thread = threading.Thread(target=self.compensate_recoil)
                self.shoot_thread.start()

            elif not pressed and self.is_shooting:
                print("✓ Spray finalizado\n")
                self.is_shooting = False
                if self.shoot_thread:
                    self.shoot_thread.join()

    def on_press(self, key):
        try:
            # F1: Toggle ativação
            if key == Key.f1:
                self.enabled = not self.enabled
                status = "🟢 ATIVADO" if self.enabled else "🔴 DESATIVADO"
                print(f"\n{'='*60}")
                print(f"Compensador: {status}")
                print(f"Scale atual: {self.get_current_scale():.4f}")
                print(f"{'='*60}\n")

            # F2: Aumentar scale
            elif key == Key.f2:
                self.scale_multiplier *= 1.1  # +10%
                print(f"\n⬆️  Scale aumentado: {self.get_current_scale():.4f} "
                      f"(multiplier: {self.scale_multiplier:.2f}x)\n")

            # F3: Diminuir scale
            elif key == Key.f3:
                self.scale_multiplier *= 0.9  # -10%
                print(f"\n⬇️  Scale diminuído: {self.get_current_scale():.4f} "
                      f"(multiplier: {self.scale_multiplier:.2f}x)\n")

            # F4: Salvar configuração
            elif key == Key.f4:
                self.save_config()

        except AttributeError:
            pass

    def save_config(self):
        """Salva a configuração atual em arquivo JSON"""
        config = {
            'dpi': self.dpi,
            'sensitivity': self.sensitivity,
            'edpi': self.edpi,
            'scale_base': self.scale_base,
            'scale_multiplier': self.scale_multiplier,
            'scale_final': self.get_current_scale()
        }

        try:
            with open('config_ideal.json', 'w') as f:
                json.dump(config, f, indent=2)
            print(f"\n💾 Configuração salva em 'config_ideal.json'!")
            print(f"   Scale final: {self.get_current_scale():.4f}")
            print(f"   Multiplier: {self.scale_multiplier:.2f}x\n")
        except Exception as e:
            print(f"\n✗ Erro ao salvar: {e}\n")

    def start(self):
        print("\n" + "="*60)
        print("CS2 AK-47 RECOIL COMPENSATOR - CALIBRAÇÃO FINAL")
        print("="*60)
        print(f"\n📊 Configuração:")
        print(f"   DPI: {self.dpi}")
        print(f"   Sensibilidade: {self.sensitivity}")
        print(f"   eDPI: {self.edpi}")
        print(f"   Scale calculado: {self.scale_base:.4f}")
        print("\n⌨️  CONTROLES:")
        print("   F1: Ativar/Desativar compensador")
        print("   F2: Aumentar scale (+10%)")
        print("   F3: Diminuir scale (-10%)")
        print("   F4: Salvar configuração ideal")
        print("   Clique Esquerdo: Disparar")
        print("   Ctrl+C: Sair")
        print("\n💡 CALIBRAÇÃO:")
        print("   1. Pressione F1 para ativar")
        print("   2. Entre no CS2 e teste")
        print("   3. Use F2/F3 para ajustar até ficar perfeito")
        print("   4. Pressione F4 para salvar")
        print("\n⚠️  AVISO: Use apenas para fins educacionais!\n")
        print("🔴 Compensador DESATIVADO - Pressione F1 para ativar\n")

        try:
            mouse_listener = mouse.Listener(on_click=self.on_click)
            keyboard_listener = keyboard.Listener(on_press=self.on_press)

            mouse_listener.start()
            keyboard_listener.start()

            mouse_listener.join()
            keyboard_listener.join()

        except KeyboardInterrupt:
            print("\n\nEncerrando...")
            self.running = False


def main():
    print("CS2 AK-47 Recoil Compensator - CALIBRAÇÃO FINAL\n")

    if platform.system() == 'Windows':
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                print("⚠️  AVISO: Não está executando como Administrador!")
                print("   Execute como Admin para melhores resultados.\n")
        except:
            pass

    try:
        # DPI do mouse
        print("🖱️  Qual é o DPI do seu mouse?")
        print("   (Geralmente: 400, 800, 1600, 3200)")
        dpi_input = input("DPI: ").strip()
        dpi = int(dpi_input) if dpi_input else 800

        # Sensibilidade
        sensitivity_input = input("Sensibilidade no CS2 (padrão 1.0): ").strip()
        sensitivity = float(sensitivity_input) if sensitivity_input else 1.0

        # Resolução
        print("\nResolução:")
        print("1. 1920x1080 (Full HD)")
        print("2. 2560x1440 (2K)")
        print("3. 3840x2160 (4K)")
        res_choice = input("Escolha (1-3, padrão 1): ").strip()

        resolutions = {'1': (1920, 1080), '2': (2560, 1440), '3': (3840, 2160)}
        resolution = resolutions.get(res_choice, (1920, 1080))

        print(f"\n✓ Configuração:")
        print(f"  DPI: {dpi}")
        print(f"  Sensibilidade: {sensitivity}")
        print(f"  eDPI: {dpi * sensitivity}")
        print(f"  Resolução: {resolution[0]}x{resolution[1]}\n")

        # Cria compensador
        compensator = RecoilCompensator(
            pattern_file='ak47_pattern.csv',
            sensitivity=sensitivity,
            dpi=dpi,
            resolution=resolution
        )

        compensator.start()

    except KeyboardInterrupt:
        print("\n\nPrograma encerrado pelo usuário.")
    except Exception as e:
        print(f"\n✗ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
