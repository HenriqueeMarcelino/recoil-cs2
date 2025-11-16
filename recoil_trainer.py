#!/usr/bin/env python3
"""
CS2 Recoil Trainer - Interface Gráfica Moderna
===============================================

Ferramenta profissional para treino de controle de recoil do CS2.

Autor: POC para estudo de padrões de recoil
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageDraw, ImageFont
import json
import csv
import time
import threading
import sys
import platform
from pathlib import Path
from datetime import datetime
from pynput import mouse
from pynput.mouse import Button

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


def create_weapon_image(weapon_name, size=(200, 100)):
    """Cria imagem placeholder da arma"""
    img = Image.new('RGBA', size, (30, 30, 30, 255))
    draw = ImageDraw.Draw(img)

    # Desenha retângulo com borda
    draw.rectangle([10, 10, size[0]-10, size[1]-10],
                   outline=(100, 100, 100), width=2)

    # Texto centralizado
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()

    text = weapon_name
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (size[0] - text_width) / 2
    y = (size[1] - text_height) / 2

    draw.text((x, y), text, fill=(255, 255, 255), font=font)

    return img


def create_spray_pattern_image(pattern_data, size=(300, 400)):
    """Cria visualização do spray pattern"""
    img = Image.new('RGBA', size, (20, 20, 20, 255))
    draw = ImageDraw.Draw(img)

    if not pattern_data:
        return img

    # Encontra limites do padrão
    xs = [p[0] for p in pattern_data]
    ys = [p[1] for p in pattern_data]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    # Escala para caber na imagem
    margin = 40
    scale_x = (size[0] - 2 * margin) / (max_x - min_x + 0.001)
    scale_y = (size[1] - 2 * margin) / (max_y - min_y + 0.001)
    scale = min(scale_x, scale_y) * 0.8

    # Centro da imagem
    center_x = size[0] / 2
    center_y = margin + 20

    # Desenha linhas conectando os pontos
    points = []
    for i, (x, y) in enumerate(pattern_data):
        px = center_x + x * scale
        py = center_y - y * scale  # Y invertido (tela vs coordenadas)
        points.append((px, py))

        # Desenha linha do ponto anterior
        if i > 0:
            color_value = 255 - int((i / len(pattern_data)) * 200)
            draw.line([points[i-1], points[i]],
                     fill=(color_value, 100, 100, 200), width=2)

    # Desenha pontos
    for i, (px, py) in enumerate(points):
        # Cor gradiente (vermelho -> azul)
        ratio = i / len(points)
        r = int(255 * (1 - ratio))
        b = int(255 * ratio)

        radius = 5 if i == 0 else 3
        draw.ellipse([px-radius, py-radius, px+radius, py+radius],
                    fill=(r, 100, b, 255))

        # Número do tiro a cada 5 tiros
        if i % 5 == 0 and i > 0:
            try:
                font = ImageFont.truetype("arial.ttf", 10)
            except:
                font = ImageFont.load_default()
            draw.text((px+8, py-5), str(i+1), fill=(200, 200, 200), font=font)

    # Título
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()
    draw.text((10, 10), "Spray Pattern", fill=(200, 200, 200), font=font)

    return img


class RecoilEngine:
    """Motor de compensação de recoil"""

    def __init__(self, weapon='AK-47', config=None):
        self.weapon = weapon
        self.config = config or {}
        self.pattern = []

        # Callbacks para GUI (ANTES de load_weapon_pattern)
        self.on_log = None
        self.on_status_change = None

        self.load_weapon_pattern(weapon)

        self.is_shooting = False
        self.enabled = False
        self.current_bullet = 0
        self.shoot_thread = None
        self.running = True

        # Reset de recoil (CS2 reseta após ~0.4s sem atirar)
        self.last_shot_time = 0
        self.recoil_reset_time = 0.4  # segundos

        # Fire rates por arma (RPM)
        self.fire_rates = {
            'AK-47': 0.1  # ~600 RPM
        }
        self.fire_rate = self.fire_rates.get(weapon, 0.1)

    def load_weapon_pattern(self, weapon):
        """Carrega padrão de spray baseado na arma"""
        pattern_files = {
            'AK-47': 'ak47_pattern.csv'
        }

        pattern_file = pattern_files.get(weapon)
        if not pattern_file or not Path(pattern_file).exists():
            self.log(f"⚠️ Padrão para {weapon} não encontrado")
            self.pattern = []
            return

        try:
            with open(pattern_file, 'r') as f:
                reader = csv.DictReader(f)
                self.pattern = []
                for row in reader:
                    x = float(row['x'])
                    y = float(row['y'])
                    self.pattern.append((x, y))
            self.log(f"✓ Padrão {weapon} carregado: {len(self.pattern)} tiros")
        except Exception as e:
            self.log(f"✗ Erro ao carregar padrão: {e}")
            self.pattern = []

    def calculate_scale(self):
        """Calcula scale baseado em DPI e sensibilidade"""
        dpi = self.config.get('dpi', 800)
        sens = self.config.get('sensitivity', 1.0)

        # Fórmula de conversão CS2
        dpi_factor = dpi / 800.0
        m_yaw = 0.022

        # Scale base empírico ajustado (AUMENTADO de 10.0 para 30.0)
        scale = 30.0 / (sens * dpi_factor)

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
        current_time = time.time()

        # Reset de recoil se passou muito tempo desde último tiro
        if current_time - self.last_shot_time > self.recoil_reset_time:
            self.current_bullet = 0
            self.log("Recoil resetado")

        last_shot_time = time.time()
        scale = self.calculate_scale()
        self.log(f"Spray iniciado - Scale: {scale:.4f}")

        while self.is_shooting and self.running and self.enabled:
            current_time = time.time()

            # Verifica se deve resetar (parou de atirar por >0.4s)
            if current_time - last_shot_time > self.recoil_reset_time:
                self.current_bullet = 0
                self.log("Recoil resetado (pausa detectada)")

            if current_time - last_shot_time >= self.fire_rate:
                dx, dy = self.calculate_compensation(self.current_bullet)
                self.move_mouse(dx, dy)

                self.log(f"Tiro {self.current_bullet + 1}/{len(self.pattern)}: ({dx:.1f}, {dy:.1f})")

                self.current_bullet += 1
                last_shot_time = current_time
                self.last_shot_time = current_time  # Atualiza tempo do último tiro

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
        self.root.geometry("850x600")
        self.root.resizable(True, True)  # Permite redimensionar

        # Configurações
        self.config_file = Path("config.json")
        self.config = self.load_config()

        # Engine de recoil
        self.engine = None
        self.setup_engine()

        # Listener de mouse
        self.mouse_listener = None

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
            'weapon': 'AK-47'
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
                    self.log(f"✓ Configurações carregadas de {self.config_file}")
            except Exception as e:
                self.log(f"⚠️ Erro ao carregar config: {e}")

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
            self.config['weapon'] = 'AK-47'  # Sempre AK-47 por enquanto

            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)

            self.log("✓ Configurações salvas em config.json")

            # Atualiza engine
            if self.engine:
                self.engine.config = self.config

        except Exception as e:
            self.log(f"✗ Erro ao salvar: {e}")

    def setup_engine(self):
        """Configura engine de recoil"""
        weapon = self.config.get('weapon', 'AK-47')
        self.engine = RecoilEngine(weapon=weapon, config=self.config)
        self.engine.on_log = self.log
        self.engine.on_status_change = self.update_status_indicator

    def create_ui(self):
        """Cria interface completa"""
        # Header
        header = ctk.CTkLabel(
            self.root,
            text="🎯 CS2 Recoil Trainer",
            font=("Segoe UI", 28, "bold")
        )
        header.pack(pady=15)

        # Container principal
        main_container = ctk.CTkFrame(self.root)
        main_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Coluna esquerda - Configurações + Arma
        left_frame = ctk.CTkFrame(main_container, width=450)
        left_frame.pack(side="left", fill="both", expand=False, padx=(0, 10))
        left_frame.pack_propagate(False)

        self.create_weapon_section(left_frame)
        self.create_config_section(left_frame)

        # Coluna direita - Status, Pattern e Logs
        right_frame = ctk.CTkFrame(main_container)
        right_frame.pack(side="right", fill="both", expand=True)

        self.create_status_section(right_frame)
        self.create_pattern_section(right_frame)
        self.create_log_section(right_frame)

        # Footer - Botões de ação
        self.create_action_buttons()

    def create_weapon_section(self, parent):
        """Seção de seleção de arma com imagem"""
        weapon_frame = ctk.CTkFrame(parent)
        weapon_frame.pack(fill="x", padx=10, pady=10)

        title = ctk.CTkLabel(weapon_frame, text="🔫 Arma", font=("Segoe UI", 16, "bold"))
        title.pack(pady=5)

        # Imagem da arma
        weapon_img = create_weapon_image("AK-47")
        self.weapon_photo = ctk.CTkImage(light_image=weapon_img, dark_image=weapon_img, size=(200, 100))

        self.weapon_img_label = ctk.CTkLabel(weapon_frame, image=self.weapon_photo, text="")
        self.weapon_img_label.pack(pady=10)

        # Nome da arma (fixo por enquanto)
        weapon_name = ctk.CTkLabel(weapon_frame, text="AK-47", font=("Segoe UI", 18, "bold"))
        weapon_name.pack(pady=5)

        info = ctk.CTkLabel(weapon_frame, text="Apenas AK-47 disponível no momento",
                           font=("Segoe UI", 10), text_color="gray")
        info.pack(pady=2)

    def create_pattern_section(self, parent):
        """Seção do spray pattern visual"""
        pattern_frame = ctk.CTkFrame(parent)
        pattern_frame.pack(fill="both", expand=True, padx=10, pady=10)

        title = ctk.CTkLabel(pattern_frame, text="📈 Spray Pattern", font=("Segoe UI", 14, "bold"))
        title.pack(pady=5)

        # Gera imagem do pattern
        if self.engine and self.engine.pattern:
            pattern_img = create_spray_pattern_image(self.engine.pattern)
            self.pattern_photo = ctk.CTkImage(light_image=pattern_img, dark_image=pattern_img,
                                             size=(280, 350))

            self.pattern_img_label = ctk.CTkLabel(pattern_frame, image=self.pattern_photo, text="")
            self.pattern_img_label.pack(pady=5)
        else:
            no_pattern = ctk.CTkLabel(pattern_frame, text="Nenhum padrão carregado",
                                     text_color="gray")
            no_pattern.pack(pady=20)

    def create_config_section(self, parent):
        """Seção de configurações"""
        config_frame = ctk.CTkFrame(parent)
        config_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Título
        title = ctk.CTkLabel(config_frame, text="⚙️ Configurações", font=("Segoe UI", 16, "bold"))
        title.pack(pady=10)

        # DPI
        dpi_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        dpi_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(dpi_frame, text="DPI do Mouse:", font=("Segoe UI", 12)).pack(side="left", padx=5)
        self.dpi_var = tk.StringVar(value=str(self.config.get('dpi', 800)))
        self.dpi_var.trace('w', self.on_config_change)
        dpi_entry = ctk.CTkEntry(dpi_frame, textvariable=self.dpi_var, width=100)
        dpi_entry.pack(side="right", padx=5)

        # Sensibilidade
        sens_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        sens_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(sens_frame, text="Sensibilidade CS2:", font=("Segoe UI", 12)).pack(side="left", padx=5)
        self.sens_var = tk.StringVar(value=str(self.config.get('sensitivity', 1.0)))
        self.sens_var.trace('w', self.on_config_change)
        sens_entry = ctk.CTkEntry(sens_frame, textvariable=self.sens_var, width=100)
        sens_entry.pack(side="right", padx=5)

        # Resolução
        res_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        res_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(res_frame, text="Resolução:", font=("Segoe UI", 12)).pack(side="left", padx=5)

        res_config = self.config.get('resolution', {'width': 1920, 'height': 1080})
        self.res_width_var = tk.StringVar(value=str(res_config['width']))
        self.res_height_var = tk.StringVar(value=str(res_config['height']))
        self.res_width_var.trace('w', self.on_config_change)
        self.res_height_var.trace('w', self.on_config_change)

        res_container = ctk.CTkFrame(res_frame, fg_color="transparent")
        res_container.pack(side="right", padx=5)

        res_width = ctk.CTkEntry(res_container, textvariable=self.res_width_var, width=70)
        res_width.pack(side="left", padx=2)
        ctk.CTkLabel(res_container, text="×", font=("Segoe UI", 12)).pack(side="left")
        res_height = ctk.CTkEntry(res_container, textvariable=self.res_height_var, width=70)
        res_height.pack(side="left", padx=2)

        auto_detect_btn = ctk.CTkButton(
            res_container,
            text="Auto",
            width=50,
            height=25,
            command=self.auto_detect_resolution
        )
        auto_detect_btn.pack(side="left", padx=5)

        # Scale Multiplier com botões +/-
        scale_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        scale_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(scale_frame, text="Scale Multiplier:", font=("Segoe UI", 12)).pack(side="left", padx=5)

        scale_controls = ctk.CTkFrame(scale_frame, fg_color="transparent")
        scale_controls.pack(side="right", padx=5)

        # Botão -
        btn_minus = ctk.CTkButton(
            scale_controls,
            text="-",
            width=30,
            height=25,
            command=self.decrease_scale
        )
        btn_minus.pack(side="left", padx=2)

        # Entry
        self.scale_var = tk.StringVar(value=str(self.config.get('scale_multiplier', 1.0)))
        self.scale_var.trace('w', self.on_config_change)
        scale_entry = ctk.CTkEntry(scale_controls, textvariable=self.scale_var, width=70)
        scale_entry.pack(side="left", padx=2)

        # Botão +
        btn_plus = ctk.CTkButton(
            scale_controls,
            text="+",
            width=30,
            height=25,
            command=self.increase_scale
        )
        btn_plus.pack(side="left", padx=2)

        # eDPI calculado
        edpi_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        edpi_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(edpi_frame, text="eDPI:", font=("Segoe UI", 12, "bold")).pack(side="left", padx=5)
        self.edpi_label = ctk.CTkLabel(edpi_frame, text="800", font=("Segoe UI", 12))
        self.edpi_label.pack(side="right", padx=5)

    def create_status_section(self, parent):
        """Seção de status"""
        status_frame = ctk.CTkFrame(parent)
        status_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(status_frame, text="📊 Status", font=("Segoe UI", 14, "bold")).pack(pady=5)

        # Indicador de status
        self.status_indicator = ctk.CTkLabel(
            status_frame,
            text="● DESATIVADO",
            font=("Segoe UI", 18, "bold"),
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
            width=35,
            height=8,
            bg="#2b2b2b",
            fg="#ffffff",
            font=("Consolas", 9),
            state='disabled'
        )
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

    def create_action_buttons(self):
        """Botões de ação"""
        button_frame = ctk.CTkFrame(self.root)
        button_frame.pack(fill="x", padx=20, pady=15)

        # Botão Start/Stop
        self.toggle_btn = ctk.CTkButton(
            button_frame,
            text="▶ INICIAR",
            font=("Segoe UI", 16, "bold"),
            height=50,
            fg_color="green",
            hover_color="darkgreen",
            command=self.toggle_compensator
        )
        self.toggle_btn.pack(side="left", fill="x", expand=True, padx=5)

        # Botão Salvar
        save_btn = ctk.CTkButton(
            button_frame,
            text="💾 SALVAR CONFIGURAÇÕES",
            font=("Segoe UI", 14, "bold"),
            height=50,
            fg_color="#1f6aa5",
            hover_color="#144870",
            command=self.save_config
        )
        save_btn.pack(side="left", fill="x", expand=True, padx=5)

    def on_config_change(self, *args):
        """Callback quando configuração muda - recalcula automaticamente"""
        self.recalculate_scale()

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
        except:
            pass

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
        """Inicia listener de mouse"""
        try:
            # Mouse listener
            self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click)
            self.mouse_listener.start()

            self.log("✓ Listener de mouse iniciado")
        except Exception as e:
            self.log(f"✗ Erro ao iniciar listener: {e}")

    def on_mouse_click(self, x, y, button, pressed):
        """Handler de clique do mouse"""
        if self.engine and button == Button.left:
            if pressed:
                self.engine.start_spray()
            else:
                self.engine.stop_spray()

    def increase_scale(self):
        """Aumenta scale em 10%"""
        try:
            current = float(self.scale_var.get())
            new_scale = current * 1.1
            self.scale_var.set(f"{new_scale:.2f}")
            self.log(f"⬆️ Scale aumentado: {new_scale:.2f}")
        except:
            pass

    def decrease_scale(self):
        """Diminui scale em 10%"""
        try:
            current = float(self.scale_var.get())
            new_scale = current * 0.9
            self.scale_var.set(f"{new_scale:.2f}")
            self.log(f"⬇️ Scale diminuído: {new_scale:.2f}")
        except:
            pass

    def on_closing(self):
        """Cleanup ao fechar"""
        # Salva automaticamente ao fechar
        self.save_config()

        if self.engine:
            self.engine.running = False

        if self.mouse_listener:
            self.mouse_listener.stop()

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
