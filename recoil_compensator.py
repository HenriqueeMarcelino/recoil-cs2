#!/usr/bin/env python3
"""
CS2 AK-47 Recoil Compensation POC
==================================

Este script é uma Prova de Conceito (POC) para entender e compensar
automaticamente o padrão de recoil da AK-47 no Counter Strike 2.

AVISO: Este script é apenas para fins educacionais e de pesquisa.
O uso em jogos online pode violar os Termos de Serviço.

Autor: POC para estudo de padrões de recoil
"""

import csv
import time
import threading
from pynput import mouse
from pynput.mouse import Controller, Button
import sys


class RecoilCompensator:
    def __init__(self, pattern_file, sensitivity=1.0, resolution=(1920, 1080)):
        """
        Inicializa o compensador de recoil.

        Args:
            pattern_file: Caminho para o arquivo CSV com o padrão de spray
            sensitivity: Sensibilidade do mouse no jogo (padrão 1.0)
            resolution: Resolução do jogo (largura, altura)
        """
        self.pattern = self.load_pattern(pattern_file)
        self.sensitivity = sensitivity
        self.resolution = resolution
        self.mouse_controller = Controller()

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

    def load_pattern(self, pattern_file):
        """
        Carrega o padrão de spray do arquivo CSV.

        Returns:
            Lista de tuplas (x, y) representando o movimento do recoil
        """
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

        # O padrão mostra onde o tiro vai (recoil)
        # Precisamos mover o mouse na direção OPOSTA para compensar
        # Y negativo no padrão = tiro sobe, então movemos mouse para baixo (positivo)
        # X negativo no padrão = tiro vai esquerda, movemos mouse para direita (positivo)

        # Fator de escala baseado na resolução e sensibilidade
        # Valores ajustáveis - começamos conservador
        scale_factor = 0.15 / self.sensitivity

        dx = -x * scale_factor  # Inverte X
        dy = -y * scale_factor  # Inverte Y

        return (dx, dy)

    def compensate_recoil(self):
        """
        Thread que compensa o recoil enquanto o mouse está pressionado.
        """
        self.current_bullet = 0
        last_shot_time = time.time()

        while self.is_shooting and self.running:
            current_time = time.time()

            # Simula a cadência de tiro da AK-47
            if current_time - last_shot_time >= self.fire_rate:
                # Calcula e aplica compensação
                dx, dy = self.calculate_compensation(self.current_bullet)

                # Move o mouse
                self.mouse_controller.move(dx, dy)

                # Debug: mostra o tiro atual e movimento
                print(f"Tiro {self.current_bullet + 1}/{len(self.pattern)}: "
                      f"Movimento ({dx:.2f}, {dy:.2f})")

                self.current_bullet += 1
                last_shot_time = current_time

                # Se passou do último tiro, mantém no último padrão
                if self.current_bullet >= len(self.pattern):
                    self.current_bullet = len(self.pattern) - 1

            time.sleep(0.001)  # Pequeno delay para não sobrecarregar CPU

    def on_click(self, x, y, button, pressed):
        """
        Callback chamado quando um botão do mouse é pressionado/solto.
        """
        # Apenas responde ao botão esquerdo
        if button == Button.left:
            if pressed and not self.is_shooting:
                # Iniciou o disparo
                print("\n>>> INICIANDO SPRAY <<<")
                self.is_shooting = True
                self.current_bullet = 0

                # Inicia thread de compensação
                self.shoot_thread = threading.Thread(target=self.compensate_recoil)
                self.shoot_thread.start()

            elif not pressed and self.is_shooting:
                # Parou de disparar
                print(">>> SPRAY FINALIZADO <<<\n")
                self.is_shooting = False

                # Espera thread terminar
                if self.shoot_thread:
                    self.shoot_thread.join()

    def start(self):
        """
        Inicia o listener do mouse.
        """
        print("\n" + "="*60)
        print("CS2 AK-47 RECOIL COMPENSATOR - POC")
        print("="*60)
        print("\nInstruções:")
        print("1. Entre no CS2 e selecione a AK-47")
        print("2. Segure o botão esquerdo do mouse para disparar")
        print("3. O script compensará o recoil automaticamente")
        print("4. Pressione Ctrl+C para sair")
        print("\n⚠️  AVISO: Use apenas para fins educacionais!\n")
        print("Aguardando cliques...\n")

        try:
            # Cria listener de mouse
            with mouse.Listener(on_click=self.on_click) as listener:
                listener.join()
        except KeyboardInterrupt:
            print("\n\nEncerrando...")
            self.running = False


def main():
    """
    Função principal - configura e inicia o compensador.
    """
    print("CS2 AK-47 Recoil Compensator POC\n")

    # Solicita configurações do usuário
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

        print(f"Sensibilidade: {sensitivity}\n")

        # Cria e inicia compensador
        compensator = RecoilCompensator(
            pattern_file='ak47_pattern.csv',
            sensitivity=sensitivity,
            resolution=resolution
        )

        compensator.start()

    except KeyboardInterrupt:
        print("\n\nPrograma encerrado pelo usuário.")
    except Exception as e:
        print(f"\n✗ Erro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
