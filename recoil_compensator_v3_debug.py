#!/usr/bin/env python3
"""
CS2 AK-47 Recoil Compensation POC v3 - DEBUG MODE
==================================================

Versão de DEBUG para testar diferentes métodos de movimento do mouse
e descobrir qual funciona dentro do CS2.

TESTA:
- SendInput (API moderna)
- mouse_event (API antiga)
- Scale factors diferentes
- Logging detalhado

AVISO: Este script é apenas para fins educacionais e de pesquisa.
O uso em jogos online pode violar os Termos de Serviço.

Autor: POC para estudo de padrões de recoil
"""

import csv
import time
import threading
import sys
import platform
from pynput import mouse
from pynput.mouse import Button

# Importa ctypes para Windows API
if platform.system() == 'Windows':
    import ctypes
    from ctypes import windll, Structure, c_long, c_ulong, POINTER, sizeof, byref

    # Estruturas do Windows para SendInput
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

    # Constantes do Windows
    INPUT_MOUSE = 0
    MOUSEEVENTF_MOVE = 0x0001


class RecoilCompensator:
    def __init__(self, pattern_file, sensitivity=1.0, resolution=(1920, 1080),
                 method='sendinput', scale_multiplier=1.0):
        """
        Inicializa o compensador de recoil.

        Args:
            pattern_file: Caminho para o arquivo CSV com o padrão de spray
            sensitivity: Sensibilidade do mouse no jogo (padrão 1.0)
            resolution: Resolução do jogo (largura, altura)
            method: 'sendinput' ou 'mouse_event'
            scale_multiplier: Multiplicador extra para scale_factor (1.0 = normal)
        """
        self.pattern = self.load_pattern(pattern_file)
        self.sensitivity = sensitivity
        self.resolution = resolution
        self.method = method
        self.scale_multiplier = scale_multiplier

        # Verifica se está no Windows
        self.is_windows = platform.system() == 'Windows'
        if not self.is_windows:
            print("⚠️  AVISO: Este script foi otimizado para Windows.")
            sys.exit(1)

        # Estado do disparo
        self.is_shooting = False
        self.current_bullet = 0
        self.shoot_thread = None
        self.running = True

        # Tempo entre disparos da AK-47 (RPM: ~600, ~0.1s entre tiros)
        self.fire_rate = 0.1

        print(f"✓ Padrão de spray carregado: {len(self.pattern)} bullets")
        print(f"✓ Sensibilidade: {self.sensitivity}")
        print(f"✓ Resolução: {self.resolution[0]}x{self.resolution[1]}")
        print(f"✓ Método: {self.method.upper()}")
        print(f"✓ Scale Multiplier: {self.scale_multiplier}x")

    def load_pattern(self, pattern_file):
        """Carrega o padrão de spray do arquivo CSV."""
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
        """Move o mouse usando Windows SendInput API."""
        dx = int(dx)
        dy = int(dy)

        extra = c_ulong(0)
        ii_ = MOUSEINPUT(dx, dy, 0, MOUSEEVENTF_MOVE, 0, ctypes.pointer(extra))
        x = INPUT(INPUT_MOUSE, ii_)

        result = ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
        return result

    def move_mouse_event(self, dx, dy):
        """Move o mouse usando Windows mouse_event API (API antiga)."""
        dx = int(dx)
        dy = int(dy)

        # MOUSEEVENTF_MOVE = 0x0001
        ctypes.windll.user32.mouse_event(0x0001, dx, dy, 0, 0)

    def calculate_compensation(self, bullet_index):
        """
        Calcula o movimento necessário para compensar o recoil.

        Args:
            bullet_index: Índice do tiro atual (0-29 para AK-47)

        Returns:
            Tupla (dx, dy) com o movimento do mouse em pixels
        """
        if bullet_index >= len(self.pattern):
            bullet_index = len(self.pattern) - 1

        x, y = self.pattern[bullet_index]

        # Fator de escala BASE - AUMENTADO para ser MUITO visível
        base_scale = 2.0  # Aumentado de 0.5 para 2.0

        # Aplica multiplicador extra
        scale_factor = (base_scale * self.scale_multiplier) / self.sensitivity

        # Inverte direções
        dx = -x * scale_factor
        dy = -y * scale_factor

        return (dx, dy)

    def compensate_recoil(self):
        """Thread que compensa o recoil enquanto o mouse está pressionado."""
        self.current_bullet = 0
        last_shot_time = time.time()

        print(f"\n🔧 DEBUG: Método = {self.method}")
        print(f"🔧 DEBUG: Scale = {2.0 * self.scale_multiplier / self.sensitivity:.2f}")

        while self.is_shooting and self.running:
            current_time = time.time()

            # Simula a cadência de tiro da AK-47
            if current_time - last_shot_time >= self.fire_rate:
                # Calcula compensação
                dx, dy = self.calculate_compensation(self.current_bullet)

                # Move o mouse usando o método escolhido
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

                # Se passou do último tiro, mantém no último padrão
                if self.current_bullet >= len(self.pattern):
                    self.current_bullet = len(self.pattern) - 1

            time.sleep(0.001)

    def on_click(self, x, y, button, pressed):
        """Callback chamado quando um botão do mouse é pressionado/solto."""
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

    def start(self):
        """Inicia o listener do mouse."""
        print("\n" + "="*60)
        print("CS2 AK-47 RECOIL COMPENSATOR v3 - DEBUG MODE")
        print("="*60)
        print(f"\n🔍 MODO DEBUG - Método: {self.method.upper()}")
        print("\nInstruções:")
        print("1. Execute como ADMINISTRADOR")
        print("2. Entre no CS2 com AK-47")
        print("3. Atire e observe os logs")
        print("4. Pressione Ctrl+C para sair")
        print("\n⚠️  AVISO: Use apenas para fins educacionais!\n")
        print("Aguardando cliques...\n")

        try:
            with mouse.Listener(on_click=self.on_click) as listener:
                listener.join()
        except KeyboardInterrupt:
            print("\n\nEncerrando...")
            self.running = False


def main():
    """Função principal - configura e inicia o compensador."""
    print("CS2 AK-47 Recoil Compensator v3 - DEBUG MODE\n")

    # Verifica Admin
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
        print("\n🔧 MODO DEBUG - Escolha o método de movimento:")
        print("1. SendInput (API moderna) - Padrão")
        print("2. mouse_event (API antiga) - Pode funcionar melhor em jogos")

        method_choice = input("Escolha o método (1-2, padrão 1): ").strip()
        method = 'mouse_event' if method_choice == '2' else 'sendinput'

        # Scale multiplier
        print("\n🔧 Scale Multiplier (quanto mais alto, mais movimento):")
        print("1. Normal (1x)")
        print("2. Dobro (2x)")
        print("3. Triplo (3x)")
        print("4. 5x (muito forte)")
        print("5. 10x (extremo - para teste)")

        scale_choice = input("Escolha (1-5, padrão 2): ").strip()
        scale_map = {'1': 1.0, '2': 2.0, '3': 3.0, '4': 5.0, '5': 10.0}
        scale_multiplier = scale_map.get(scale_choice, 2.0)

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
