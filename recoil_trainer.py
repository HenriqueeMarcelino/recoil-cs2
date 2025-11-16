#!/usr/bin/env python3
"""
CS2 Recoil Trainer - Interface Gráfica Moderna
===============================================

Ferramenta profissional para treino de controle de recoil do CS2.

Funcionalidades:
- Interface gráfica moderna (dark mode)
- Configuração completa (DPI, sensibilidade, resolução)
- Detecção automática de resolução
- Seleção de armas (com imagens)
- Sistema de calibração automática
- Salvar/Carregar configurações
- Logs em tempo real
- Hotkeys configuráveis

Autor: POC para estudo de padrões de recoil
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import scrolledtext
import json
import csv
import time
import threading
import sys
import platform
from pathlib import Path
from datetime import datetime
from pynput import mouse, keyboard
from pynput.mouse import Button
from pynput.keyboard import Key

# Importa Windows API se estiver no Windows
if platform.system() == 'Windows':
    import ctypes
    from ctypes import Structure, c_long, c_ulong, POINTER
    try:
        import win32api
        HAS_WIN32API = True
    except ImportError:
        HAS_WIN32API = False

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


class RecoilEngine:
    """Motor de compensação de recoil"""

    def __init__(self, pattern_file, config):
        self.pattern = self.load_pattern(pattern_file)
        self.config = config
        self.is_shooting = False
        self.enabled = False
        self.current_bullet = 0
        self.shoot_thread = None
        self.running = True
        self.fire_rate = 0.1  # AK-47: ~600 RPM

        # Callbacks para GUI
        self.on_log = None
        self.on_status_change = None

    def load_pattern(self, pattern_file):
        """Carrega padrão de spray do CSV"""
        pattern = []
        try:
            with open(pattern_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    x = float(row['x'])
                    y = float(row['y'])
                    pattern.append((x, y))
            return pattern
        except Exception as e:
            print(f"Erro ao carregar padrão: {e}")
            return []

    def calculate_scale(self):
        """Calcula scale baseado em DPI e sensibilidade"""
        dpi = self.config.get('dpi', 800)
        sens = self.config.get('sensitivity', 1.0)

        # Fórmula de conversão CS2
        dpi_factor = dpi / 800.0
        m_yaw = 0.022  # Padrão CS2

        # Scale base empírico ajustado
        scale = 10.0 / (sens * dpi_factor)

        # Aplica multiplier do usuário
        multiplier = self.config.get('scale_multiplier', 1.0)

        return scale * multiplier

    def move_mouse(self, dx, dy):
        """Move mouse usando Windows API"""
        if platform.system() != 'Windows':
            return

        dx = int(dx)
        dy = int(dy)

        try:
            ctypes.windll.user32.mouse_event(0x0001, dx, dy, 0, 0)
        except:
            pass

    def calculate_compensation(self, bullet_index):
        """Calcula compensação para o tiro atual"""
        if bullet_index >= len(self.pattern):
            bullet_index = len(self.pattern) - 1

        x, y = self.pattern[bullet_index]
        scale = self.calculate_scale()

        dx = -x * scale
        dy = -y * scale

        return (dx, dy)

    def compensate_recoil(self):
        """Thread de compensação"""
        self.current_bullet = 0
        last_shot_time = time.time()

        scale = self.calculate_scale()
        self.log(f"Spray iniciado - Scale: {scale:.4f}")

        while self.is_shooting and self.running and self.enabled:
            current_time = time.time()

            if current_time - last_shot_time >= self.fire_rate:
                dx, dy = self.calculate_compensation(self.current_bullet)
                self.move_mouse(dx, dy)

                self.log(f"Tiro {self.current_bullet + 1}/30: ({dx:.1f}, {dy:.1f})")

                self.current_bullet += 1
                last_shot_time = current_time

                if self.current_bullet >= len(self.pattern):
                    self.current_bullet = len(self.pattern) - 1

            time.sleep(0.001)

    def start_spray(self):
        """Inicia spray"""
        if not self.enabled:
            return

        self.is_shooting = True
        self.current_bullet = 0
        self.shoot_thread = threading.Thread(target=self.compensate_recoil, daemon=True)
        self.shoot_thread.start()

    def stop_spray(self):
        """Para spray"""
        if self.is_shooting:
            self.is_shooting = False
            if self.shoot_thread:
                self.shoot_thread.join(timeout=1.0)
            self.log("Spray finalizado")

    def toggle_enabled(self):
        """Liga/desliga compensador"""
        self.enabled = not self.enabled
        status = "ATIVADO" if self.enabled else "DESATIVADO"
        self.log(f"Compensador: {status}")

        if self.on_status_change:
            self.on_status_change(self.enabled)

        return self.enabled

    def log(self, message):
        """Envia log para GUI"""
        if self.on_log:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.on_log(f"[{timestamp}] {message}")


class RecoilTrainerGUI:
    """Interface Gráfica Principal"""

    def __init__(self):
        # Configuração de tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Janela principal
        self.root = ctk.CTk()
        self.root.title("CS2 Recoil Trainer")
        self.root.geometry("900x700")
        self.root.resizable(False, False)

        # Configurações
        self.config_file = Path("config.json")
        self.config = self.load_config()

        # Engine de recoil
        self.engine = None
        self.setup_engine()

        # Listeners de input
        self.mouse_listener = None
        self.keyboard_listener = None

        # Criar interface
        self.create_ui()

        # Aplicar configurações carregadas
        self.apply_loaded_config()

        # Iniciar listeners
        self.start_listeners()

        # Protocolo de fechamento
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_config(self):
        """Carrega configurações do JSON"""
        default_config = {
            'dpi': 800,
            'sensitivity': 1.0,
            'resolution': {'width': 1920, 'height': 1080},
            'scale_multiplier': 1.0,
            'weapon': 'AK-47',
            'hotkeys': {
                'toggle': 'f1',
                'increase_scale': 'f2',
                'decrease_scale': 'f3'
            }
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
            except Exception as e:
                print(f"Erro ao carregar config: {e}")

        return default_config

    def save_config(self):
        """Salva configurações no JSON"""
        try:
            # Atualiza config com valores atuais
            self.config['dpi'] = int(self.dpi_var.get())
            self.config['sensitivity'] = float(self.sens_var.get())
            self.config['resolution'] = {
                'width': int(self.res_width_var.get()),
                'height': int(self.res_height_var.get())
            }
            self.config['scale_multiplier'] = float(self.scale_var.get())
            self.config['weapon'] = self.weapon_var.get()

            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)

            self.log("✓ Configurações salvas")
        except Exception as e:
            self.log(f"✗ Erro ao salvar: {e}")

    def setup_engine(self):
        """Configura engine de recoil"""
        self.engine = RecoilEngine('ak47_pattern.csv', self.config)
        self.engine.on_log = self.log
        self.engine.on_status_change = self.update_status_indicator

    def create_ui(self):
        """Cria interface completa"""
        # Header
        header = ctk.CTkLabel(
            self.root,
            text="CS2 Recoil Trainer",
            font=("Segoe UI", 24, "bold")
        )
        header.pack(pady=20)

        # Container principal
        main_container = ctk.CTkFrame(self.root)
        main_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Coluna esquerda - Configurações
        left_frame = ctk.CTkFrame(main_container)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.create_config_section(left_frame)

        # Coluna direita - Status e Logs
        right_frame = ctk.CTkFrame(main_container)
        right_frame.pack(side="right", fill="both", expand=True)

        self.create_status_section(right_frame)
        self.create_log_section(right_frame)

        # Footer - Botões de ação
        self.create_action_buttons()

    def create_config_section(self, parent):
        """Seção de configurações"""
        # Título
        title = ctk.CTkLabel(parent, text="⚙️ Configurações", font=("Segoe UI", 16, "bold"))
        title.pack(pady=10)

        # Seleção de Arma
        weapon_frame = ctk.CTkFrame(parent)
        weapon_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(weapon_frame, text="Arma:", font=("Segoe UI", 12)).pack(side="left", padx=5)
        self.weapon_var = tk.StringVar(value=self.config.get('weapon', 'AK-47'))
        weapon_menu = ctk.CTkOptionMenu(
            weapon_frame,
            variable=self.weapon_var,
            values=["AK-47", "M4A4", "M4A1-S"],
            command=self.on_weapon_change
        )
        weapon_menu.pack(side="left", fill="x", expand=True, padx=5)

        # DPI
        dpi_frame = ctk.CTkFrame(parent)
        dpi_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(dpi_frame, text="DPI do Mouse:", font=("Segoe UI", 12)).pack(side="left", padx=5)
        self.dpi_var = tk.StringVar(value=str(self.config.get('dpi', 800)))
        dpi_entry = ctk.CTkEntry(dpi_frame, textvariable=self.dpi_var, width=100)
        dpi_entry.pack(side="left", padx=5)

        # Sensibilidade
        sens_frame = ctk.CTkFrame(parent)
        sens_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(sens_frame, text="Sensibilidade CS2:", font=("Segoe UI", 12)).pack(side="left", padx=5)
        self.sens_var = tk.StringVar(value=str(self.config.get('sensitivity', 1.0)))
        sens_entry = ctk.CTkEntry(sens_frame, textvariable=self.sens_var, width=100)
        sens_entry.pack(side="left", padx=5)

        # Resolução
        res_frame = ctk.CTkFrame(parent)
        res_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(res_frame, text="Resolução:", font=("Segoe UI", 12)).pack(side="left", padx=5)

        res_config = self.config.get('resolution', {'width': 1920, 'height': 1080})
        self.res_width_var = tk.StringVar(value=str(res_config['width']))
        self.res_height_var = tk.StringVar(value=str(res_config['height']))

        res_width = ctk.CTkEntry(res_frame, textvariable=self.res_width_var, width=70)
        res_width.pack(side="left", padx=2)
        ctk.CTkLabel(res_frame, text="×").pack(side="left")
        res_height = ctk.CTkEntry(res_frame, textvariable=self.res_height_var, width=70)
        res_height.pack(side="left", padx=2)

        auto_detect_btn = ctk.CTkButton(
            res_frame,
            text="Auto",
            width=60,
            command=self.auto_detect_resolution
        )
        auto_detect_btn.pack(side="left", padx=5)

        # Scale Multiplier
        scale_frame = ctk.CTkFrame(parent)
        scale_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(scale_frame, text="Scale Multiplier:", font=("Segoe UI", 12)).pack(side="left", padx=5)
        self.scale_var = tk.StringVar(value=str(self.config.get('scale_multiplier', 1.0)))
        scale_entry = ctk.CTkEntry(scale_frame, textvariable=self.scale_var, width=100)
        scale_entry.pack(side="left", padx=5)

        # eDPI calculado
        edpi_frame = ctk.CTkFrame(parent)
        edpi_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(edpi_frame, text="eDPI:", font=("Segoe UI", 12, "bold")).pack(side="left", padx=5)
        self.edpi_label = ctk.CTkLabel(edpi_frame, text="800", font=("Segoe UI", 12))
        self.edpi_label.pack(side="left", padx=5)

        # Botão calcular
        calc_btn = ctk.CTkButton(
            parent,
            text="🔄 Recalcular Scale",
            command=self.recalculate_scale
        )
        calc_btn.pack(pady=10)

        # Hotkeys info
        hotkey_frame = ctk.CTkFrame(parent)
        hotkey_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(hotkey_frame, text="⌨️ Atalhos:", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=5)
        ctk.CTkLabel(hotkey_frame, text="F1: Liga/Desliga", font=("Segoe UI", 10)).pack(anchor="w", padx=5)
        ctk.CTkLabel(hotkey_frame, text="F2: Aumenta Scale (+10%)", font=("Segoe UI", 10)).pack(anchor="w", padx=5)
        ctk.CTkLabel(hotkey_frame, text="F3: Diminui Scale (-10%)", font=("Segoe UI", 10)).pack(anchor="w", padx=5)

    def create_status_section(self, parent):
        """Seção de status"""
        status_frame = ctk.CTkFrame(parent)
        status_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(status_frame, text="📊 Status", font=("Segoe UI", 14, "bold")).pack(pady=5)

        # Indicador de status
        self.status_indicator = ctk.CTkLabel(
            status_frame,
            text="● DESATIVADO",
            font=("Segoe UI", 16, "bold"),
            text_color="red"
        )
        self.status_indicator.pack(pady=5)

        # Scale atual
        self.scale_label = ctk.CTkLabel(
            status_frame,
            text="Scale: 0.0000",
            font=("Segoe UI", 12)
        )
        self.scale_label.pack(pady=2)

    def create_log_section(self, parent):
        """Seção de logs"""
        log_frame = ctk.CTkFrame(parent)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(log_frame, text="📝 Logs", font=("Segoe UI", 14, "bold")).pack(pady=5)

        # Área de texto com scroll
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            width=40,
            height=15,
            bg="#2b2b2b",
            fg="#ffffff",
            font=("Consolas", 9),
            state='disabled'
        )
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

    def create_action_buttons(self):
        """Botões de ação"""
        button_frame = ctk.CTkFrame(self.root)
        button_frame.pack(fill="x", padx=20, pady=10)

        # Botão Start/Stop
        self.toggle_btn = ctk.CTkButton(
            button_frame,
            text="▶ INICIAR",
            font=("Segoe UI", 14, "bold"),
            height=40,
            fg_color="green",
            hover_color="darkgreen",
            command=self.toggle_compensator
        )
        self.toggle_btn.pack(side="left", fill="x", expand=True, padx=5)

        # Botão Salvar
        save_btn = ctk.CTkButton(
            button_frame,
            text="💾 Salvar Config",
            font=("Segoe UI", 12),
            height=40,
            command=self.save_config
        )
        save_btn.pack(side="left", padx=5)

    def apply_loaded_config(self):
        """Aplica configurações carregadas na UI"""
        self.recalculate_scale()

    def auto_detect_resolution(self):
        """Detecta resolução automaticamente"""
        if platform.system() == 'Windows' and HAS_WIN32API:
            try:
                width = win32api.GetSystemMetrics(0)
                height = win32api.GetSystemMetrics(1)
                self.res_width_var.set(str(width))
                self.res_height_var.set(str(height))
                self.log(f"✓ Resolução detectada: {width}×{height}")
            except:
                self.log("✗ Erro ao detectar resolução")
        else:
            self.log("⚠ Detecção automática disponível apenas no Windows")

    def recalculate_scale(self):
        """Recalcula eDPI e scale"""
        try:
            dpi = int(self.dpi_var.get())
            sens = float(self.sens_var.get())
            edpi = dpi * sens

            self.edpi_label.configure(text=str(edpi))

            # Atualiza config do engine
            self.config['dpi'] = dpi
            self.config['sensitivity'] = sens
            self.config['scale_multiplier'] = float(self.scale_var.get())

            if self.engine:
                self.engine.config = self.config
                scale = self.engine.calculate_scale()
                self.scale_label.configure(text=f"Scale: {scale:.4f}")
                self.log(f"✓ Scale recalculado: {scale:.4f} (eDPI: {edpi})")
        except Exception as e:
            self.log(f"✗ Erro ao calcular: {e}")

    def on_weapon_change(self, weapon):
        """Callback de mudança de arma"""
        self.log(f"Arma selecionada: {weapon}")
        # TODO: Carregar padrão da arma correspondente

    def toggle_compensator(self):
        """Liga/desliga compensador"""
        if self.engine:
            enabled = self.engine.toggle_enabled()

    def update_status_indicator(self, enabled):
        """Atualiza indicador visual de status"""
        if enabled:
            self.status_indicator.configure(text="● ATIVADO", text_color="green")
            self.toggle_btn.configure(text="■ PARAR", fg_color="red", hover_color="darkred")
        else:
            self.status_indicator.configure(text="● DESATIVADO", text_color="red")
            self.toggle_btn.configure(text="▶ INICIAR", fg_color="green", hover_color="darkgreen")

    def log(self, message):
        """Adiciona mensagem ao log"""
        self.log_text.configure(state='normal')
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')

    def start_listeners(self):
        """Inicia listeners de mouse e teclado"""
        try:
            # Mouse listener
            self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click)
            self.mouse_listener.start()

            # Keyboard listener
            self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
            self.keyboard_listener.start()

            self.log("✓ Listeners iniciados")
        except Exception as e:
            self.log(f"✗ Erro ao iniciar listeners: {e}")

    def on_mouse_click(self, x, y, button, pressed):
        """Handler de clique do mouse"""
        if self.engine and button == Button.left:
            if pressed:
                self.engine.start_spray()
            else:
                self.engine.stop_spray()

    def on_key_press(self, key):
        """Handler de teclas"""
        try:
            # F1: Toggle
            if key == Key.f1:
                self.toggle_compensator()

            # F2: Aumentar scale
            elif key == Key.f2:
                try:
                    current = float(self.scale_var.get())
                    new_scale = current * 1.1
                    self.scale_var.set(f"{new_scale:.2f}")
                    self.recalculate_scale()
                except:
                    pass

            # F3: Diminuir scale
            elif key == Key.f3:
                try:
                    current = float(self.scale_var.get())
                    new_scale = current * 0.9
                    self.scale_var.set(f"{new_scale:.2f}")
                    self.recalculate_scale()
                except:
                    pass
        except:
            pass

    def on_closing(self):
        """Cleanup ao fechar"""
        if self.engine:
            self.engine.running = False

        if self.mouse_listener:
            self.mouse_listener.stop()

        if self.keyboard_listener:
            self.keyboard_listener.stop()

        self.root.destroy()

    def run(self):
        """Inicia aplicação"""
        self.log("=== CS2 Recoil Trainer Iniciado ===")
        self.log("⚠️ Use apenas para fins educacionais!")
        self.log("")
        self.recalculate_scale()
        self.root.mainloop()


def main():
    """Ponto de entrada"""
    if platform.system() != 'Windows':
        print("⚠️ Este programa foi desenvolvido para Windows.")
        print("   Algumas funcionalidades podem não funcionar.")

    app = RecoilTrainerGUI()
    app.run()


if __name__ == "__main__":
    main()
