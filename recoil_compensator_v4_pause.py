#!/usr/bin/env python3
"""
CS2 AK-47 Recoil Compensation POC v4 - COM PAUSE
=================================================

Versão com controle de PAUSE usando tecla F1.

CONTROLES:
- F1: Ativa/Desativa o compensador (TOGGLE)
- Clique Esquerdo: Dispara (quando ativado)
- Ctrl+C: Sair

Use F1 para pausar e copiar logs sem mexer o mouse!

AVISO: Este script é apenas para fins educacionais e de pesquisa.
O uso em jogos online pode violar os Termos de Serviço.
"""

import csv
import time
import threading
import sys
import platform
from pynput import mouse, keyboard
from pynput.mouse import Button
from pynput.keyboard import Key

# Importa ctypes para Windows API
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
    def __init__(self, pattern_file, sensitivity=1.0, resolution=(1920, 1080),
                 method='sendinput', scale_multiplier=1.0):
        self.pattern = self.load_pattern(pattern_file)
        self.sensitivity = sensitivity
        self.resolution = resolution
        self.method = method
        self.scale_multiplier = scale_multiplier

        self.is_windows = platform.system() == 'Windows'
        if not self.is_windows:
            print("⚠️  AVISO: Este script foi otimizado para Windows.")
            sys.exit(1)

        # Estado do disparo
        self.is_shooting = False
        self.current_bullet = 0
        self.shoot_thread = None
        self.running = True

        # NOVO: Estado de ativação (pausado por padrão)
        self.enabled = False

        # Tempo entre disparos da AK-47
        self.fire_rate = 0.1

        print(f"✓ Padrão de spray carregado: {len(self.pattern)} bullets")
        print(f"✓ Sensibilidade: {self.sensitivity}")
        print(f"✓ Resolução: {self.resolution[0]}x{self.resolution[1]}")
        print(f"✓ Método: {self.method.upper()}")
        print(f"✓ Scale Multiplier: {self.scale_multiplier}x")

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

    def move_mouse_sendinput(self, dx, dy):
        dx = int(dx)
        dy = int(dy)
        extra = c_ulong(0)
        ii_ = MOUSEINPUT(dx, dy, 0, MOUSEEVENTF_MOVE, 0, ctypes.pointer(extra))
        x = INPUT(INPUT_MOUSE, ii_)
        result = ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
        return result

    def move_mouse_event(self, dx, dy):
        dx = int(dx)
        dy = int(dy)
        ctypes.windll.user32.mouse_event(0x0001, dx, dy, 0, 0)

    def calculate_compensation(self, bullet_index):
        if bullet_index >= len(self.pattern):
            bullet_index = len(self.pattern) - 1

        x, y = self.pattern[bullet_index]

        base_scale = 2.0
        scale_factor = (base_scale * self.scale_multiplier) / self.sensitivity

        dx = -x * scale_factor
        dy = -y * scale_factor

        return (dx, dy)

    def compensate_recoil(self):
        self.current_bullet = 0
        last_shot_time = time.time()

        print(f"\n🔧 DEBUG: Método = {self.method}")
        print(f"🔧 DEBUG: Scale = {2.0 * self.scale_multiplier / self.sensitivity:.2f}")

        while self.is_shooting and self.running and self.enabled:
            current_time = time.time()

            if current_time - last_shot_time >= self.fire_rate:
                dx, dy = self.calculate_compensation(self.current_bullet)

                if self.method == 'sendinput':
                    result = self.move_mouse_sendinput(dx, dy)
                    print(f"Tiro {self.current_bullet + 1}/30: "
                          f"SendInput({dx:.1f}, {dy:.1f}) = {result}")
                elif self.method == 'mouse_event':
                    self.move_mouse_event(dx, dy)
                    print(f"Tiro {self.current_bullet + 1}/30: "
                          f"mouse_event({dx:.1f}, {dy:.1f})")

                self.current_bullet += 1
                last_shot_time = current_time

                if self.current_bullet >= len(self.pattern):
                    self.current_bullet = len(self.pattern) - 1

            time.sleep(0.001)

    def on_click(self, x, y, button, pressed):
        # Só responde se estiver ATIVADO
        if not self.enabled:
            return

        if button == Button.left:
            if pressed and not self.is_shooting:
                print("\n>>> INICIANDO SPRAY <<<")
                self.is_shooting = True
                self.current_bullet = 0

                self.shoot_thread = threading.Thread(target=self.compensate_recoil)
                self.shoot_thread.start()

            elif not pressed and self.is_shooting:
                print(">>> SPRAY FINALIZADO <<<\n")
                self.is_shooting = False

                if self.shoot_thread:
                    self.shoot_thread.join()

    def on_press(self, key):
        """Detecta tecla F1 para ativar/desativar"""
        try:
            # F1 para toggle
            if key == Key.f1:
                self.enabled = not self.enabled
                status = "🟢 ATIVADO" if self.enabled else "🔴 DESATIVADO"
                print(f"\n{'='*60}")
                print(f"Compensador: {status}")
                print(f"{'='*60}\n")
        except AttributeError:
            pass

    def start(self):
        print("\n" + "="*60)
        print("CS2 AK-47 RECOIL COMPENSATOR v4 - COM PAUSE")
        print("="*60)
        print(f"\n🎮 MODO DEBUG - Método: {self.method.upper()}")
        print("\n⌨️  CONTROLES:")
        print("   F1: Ativar/Desativar compensador (TOGGLE)")
        print("   Clique Esquerdo: Disparar (quando ativado)")
        print("   Ctrl+C: Sair")
        print("\n💡 DICA: Pressione F1 para pausar e copiar logs!")
        print("\nInstruções:")
        print("1. Execute como ADMINISTRADOR")
        print("2. Pressione F1 para ATIVAR")
        print("3. Entre no CS2 com AK-47")
        print("4. Atire e observe os logs")
        print("5. Pressione F1 para PAUSAR e copiar logs")
        print("\n⚠️  AVISO: Use apenas para fins educacionais!\n")
        print("🔴 Compensador DESATIVADO - Pressione F1 para ativar\n")

        try:
            # Inicia listeners de mouse E teclado
            mouse_listener = mouse.Listener(on_click=self.on_click)
            keyboard_listener = keyboard.Listener(on_press=self.on_press)

            mouse_listener.start()
            keyboard_listener.start()

            # Aguarda
            mouse_listener.join()
            keyboard_listener.join()

        except KeyboardInterrupt:
            print("\n\nEncerrando...")
            self.running = False


def main():
    print("CS2 AK-47 Recoil Compensator v4 - COM PAUSE\n")

    if platform.system() == 'Windows':
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                print("⚠️  AVISO: Não está executando como Administrador!")
                print("   Execute como Admin para melhores resultados.\n")
        except:
            pass

    try:
        # Resolução
        print("Configuração de Resolução:")
        print("1. 1920x1080 (Full HD)")
        print("2. 2560x1440 (2K)")
        print("3. 3840x2160 (4K)")
        print("4. Customizado")

        res_choice = input("Escolha a resolução (1-4): ").strip()

        resolutions = {
            '1': (1920, 1080),
            '2': (2560, 1440),
            '3': (3840, 2160)
        }

        if res_choice in resolutions:
            resolution = resolutions[res_choice]
        elif res_choice == '4':
            width = int(input("Largura: "))
            height = int(input("Altura: "))
            resolution = (width, height)
        else:
            print("Opção inválida, usando 1920x1080")
            resolution = (1920, 1080)

        # Sensibilidade
        print(f"\nResolução selecionada: {resolution[0]}x{resolution[1]}")
        sensitivity_input = input("Digite sua sensibilidade no CS2 (padrão 1.0): ").strip()

        if sensitivity_input:
            sensitivity = float(sensitivity_input)
        else:
            sensitivity = 1.0

        # Método
        print("\n🔧 Escolha o método de movimento:")
        print("1. SendInput (API moderna)")
        print("2. mouse_event (API antiga)")

        method_choice = input("Escolha o método (1-2, padrão 2): ").strip()
        method = 'mouse_event' if method_choice == '2' or method_choice == '' else 'sendinput'

        # Scale multiplier
        print("\n🔧 Scale Multiplier:")
        print("1. Fraco (0.5x)")
        print("2. Normal (1x)")
        print("3. Dobro (2x)")
        print("4. Forte (5x)")
        print("5. Extremo (10x)")

        scale_choice = input("Escolha (1-5, padrão 2): ").strip()
        scale_map = {'1': 0.5, '2': 1.0, '3': 2.0, '4': 5.0, '5': 10.0}
        scale_multiplier = scale_map.get(scale_choice, 1.0)

        print(f"\nSensibilidade: {sensitivity}")
        print(f"Método: {method}")
        print(f"Scale Multiplier: {scale_multiplier}x\n")

        # Cria e inicia compensador
        compensator = RecoilCompensator(
            pattern_file='ak47_pattern.csv',
            sensitivity=sensitivity,
            resolution=resolution,
            method=method,
            scale_multiplier=scale_multiplier
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
