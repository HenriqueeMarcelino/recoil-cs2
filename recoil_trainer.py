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
import random
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
    """Cria imagem estilizada da arma AK-47"""
    img = Image.new('RGBA', size, (25, 25, 35, 255))
    draw = ImageDraw.Draw(img)

    if weapon_name == "AK-47":
        # Cores
        weapon_color = (80, 70, 60)  # Marrom escuro (madeira)
        metal_color = (120, 120, 130)  # Metal
        highlight = (150, 140, 120)

        # Corpo principal (receiver)
        draw.rectangle([40, 35, 170, 55], fill=metal_color, outline=(90, 90, 95), width=2)

        # Cano
        draw.rectangle([120, 42, 180, 48], fill=metal_color, outline=(70, 70, 75), width=1)

        # Coronha (stock) - madeira
        draw.polygon([(35, 38), (55, 38), (55, 52), (35, 52)], fill=weapon_color, outline=(60, 50, 40))

        # Grip (empunhadura) - madeira
        draw.polygon([(75, 55), (85, 55), (90, 70), (70, 70)], fill=weapon_color, outline=(60, 50, 40))

        # Carregador (magazine)
        draw.rectangle([80, 60, 95, 85], fill=(60, 55, 50), outline=(40, 35, 30), width=1)
        draw.rectangle([82, 62, 93, 83], fill=(50, 45, 40))

        # Guarda-mão (handguard) - madeira
        draw.rectangle([100, 40, 140, 56], fill=weapon_color, outline=(60, 50, 40), width=1)

        # Detalhes metálicos
        draw.line([130, 43, 175, 43], fill=(90, 90, 95), width=1)
        draw.line([130, 47, 175, 47], fill=(90, 90, 95), width=1)

        # Mira frontal
        draw.rectangle([175, 38, 178, 42], fill=(150, 150, 160))

        # Highlights
        draw.line([42, 37, 168, 37], fill=highlight, width=1)

    # Nome da arma
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()

    text = weapon_name
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]

    x = (size[0] - text_width) / 2
    y = 8

    # Sombra do texto
    draw.text((x+1, y+1), text, fill=(0, 0, 0, 180), font=font)
    # Texto principal
    draw.text((x, y), text, fill=(255, 200, 100), font=font)

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
        """Calcula scale com FÓRMULA MATEMÁTICA EXATA - CS2 Raw Input"""
        sens = self.config.get('sensitivity', 1.0)

        # Constante CS2 (m_yaw)
        m_yaw = 0.022

        # FÓRMULA EXATA: mouse_counts = degrees / (sensitivity × m_yaw)
        # CSV contém valores em GRAUS
        # SendInput usa mouse counts (mickeys), não pixels
        #
        # Derivação:
        # - Recoil no jogo: X graus
        # - Movimento necessário: X / (sens × m_yaw) counts
        # - Exemplo: 26° com sens 1.25 = 26 / 0.0275 = 945 counts
        #
        # Portanto, scale = 1 / (sens × m_yaw)

        scale = 1.0 / (sens * m_yaw)

        # User adjustment OPCIONAL (deveria ser ~1.0 sempre)
        # Mantido apenas para ajuste fino se necessário
        user_multiplier = self.config.get('scale_multiplier', 1.0)

        return scale * user_multiplier

    def move_mouse(self, dx, dy):
        """Move mouse usando SendInput (Windows API moderna)"""
        if platform.system() != 'Windows':
            return

        dx = int(dx)
        dy = int(dy)

        try:
            # Usa SendInput ao invés de mouse_event (mais preciso e moderno)
            input_obj = INPUT()
            input_obj.type = INPUT_MOUSE
            input_obj.mi.dx = dx
            input_obj.mi.dy = dy
            input_obj.mi.mouseData = 0
            input_obj.mi.dwFlags = MOUSEEVENTF_MOVE
            input_obj.mi.time = 0
            input_obj.mi.dwExtraInfo = None

            ctypes.windll.user32.SendInput(1, ctypes.byref(input_obj), ctypes.sizeof(INPUT))
        except Exception as e:
            # Fallback para mouse_event se SendInput falhar
            try:
                ctypes.windll.user32.mouse_event(0x0001, dx, dy, 0, 0)
            except:
                pass

    def calculate_compensation(self, bullet_index):
        """Calcula compensação para o tiro atual (com jitter)"""
        if bullet_index >= len(self.pattern):
            bullet_index = len(self.pattern) - 1

        x, y = self.pattern[bullet_index]
        scale = self.calculate_scale()

        # Calcula movimento base
        dx = -x * scale
        dy = -y * scale

        # CORREÇÃO: Adiciona jitter (variação aleatória) para movimento natural
        # Jitter de ±3% no movimento (sistemas profissionais usam ±5%)
        jitter_factor = random.uniform(0.97, 1.03)
        dx *= jitter_factor
        dy *= jitter_factor

        return (dx, dy)

    def compensate_recoil(self):
        """Thread de compensação (otimizada)"""
        current_time = time.time()

        # Reset de recoil se passou muito tempo desde último tiro
        if current_time - self.last_shot_time > self.recoil_reset_time:
            self.current_bullet = 0
            self.log("Recoil resetado")

        last_shot_time = time.time()
        scale = self.calculate_scale()
        dpi = self.config.get('dpi', 800)
        sens = self.config.get('sensitivity', 1.0)
        edpi = dpi * sens

        # Aviso sobre eDPI extremo
        if edpi > 2000:
            self.log(f"⚠️ eDPI {edpi} é MUITO alto! (Pro: ~880)")
        self.log(f"Spray iniciado - Scale: {scale:.4f} | eDPI: {edpi}")

        while self.is_shooting and self.running and self.enabled:
            current_time = time.time()

            # Verifica se deve resetar (parou de atirar por >0.4s)
            if current_time - last_shot_time > self.recoil_reset_time:
                self.current_bullet = 0
                self.log("Recoil resetado (pausa detectada)")

            # CORREÇÃO: Adiciona jitter no timing (±1ms)
            jitter_timing = random.uniform(-0.001, 0.001)
            effective_fire_rate = self.fire_rate + jitter_timing

            if current_time - last_shot_time >= effective_fire_rate:
                dx, dy = self.calculate_compensation(self.current_bullet)
                self.move_mouse(dx, dy)

                # Log mais detalhado
                if self.current_bullet % 3 == 0:  # Log a cada 3 tiros para não poluir
                    self.log(f"Tiro {self.current_bullet + 1}: dx={dx:.1f}, dy={dy:.1f}")

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

        # Janela principal (otimizada para 1366x768)
        self.root = ctk.CTk()
        self.root.title("CS2 Recoil Trainer")
        self.root.geometry("1280x680")
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
                    print(f"✓ Configurações carregadas de {self.config_file}")
            except Exception as e:
                print(f"⚠️ Erro ao carregar config: {e}")

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
        """Cria interface completa com tabs"""
        # Header compacto
        header = ctk.CTkLabel(
            self.root,
            text="🎯 CS2 Recoil Trainer",
            font=("Segoe UI", 20, "bold")
        )
        header.pack(pady=10)

        # Status compacto no topo
        self.create_status_section(self.root)

        # Sistema de tabs
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=10)

        # Cria as tabs
        tab1 = self.tabview.add("⚙️ Configurações")
        tab2 = self.tabview.add("🔫 Arma & Pattern")
        tab3 = self.tabview.add("📝 Logs")

        # Preenche cada tab
        self.create_config_section(tab1)
        self.create_weapon_and_pattern_section(tab2)
        self.create_log_section(tab3)

        # Footer - Botões de ação (SEMPRE VISÍVEIS)
        self.create_action_buttons()

    def create_weapon_and_pattern_section(self, parent):
        """Tab combinada: Arma + Spray Pattern"""
        # Container com duas colunas
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # Coluna esquerda - Arma
        left_col = ctk.CTkFrame(container)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 5))

        title_weapon = ctk.CTkLabel(left_col, text="🔫 Arma Selecionada", font=("Segoe UI", 14, "bold"))
        title_weapon.pack(pady=10)

        # Tenta carregar imagem real, senão usa placeholder
        weapon_img_path = Path("ak47.png")
        if weapon_img_path.exists():
            try:
                weapon_img = Image.open(weapon_img_path)
                weapon_img.thumbnail((200, 100), Image.Resampling.LANCZOS)
            except:
                weapon_img = create_weapon_image("AK-47")
        else:
            weapon_img = create_weapon_image("AK-47")

        self.weapon_photo = ctk.CTkImage(light_image=weapon_img, dark_image=weapon_img, size=(200, 100))
        self.weapon_img_label = ctk.CTkLabel(left_col, image=self.weapon_photo, text="")
        self.weapon_img_label.pack(pady=10)

        weapon_name = ctk.CTkLabel(left_col, text="AK-47", font=("Segoe UI", 16, "bold"))
        weapon_name.pack(pady=5)

        info = ctk.CTkLabel(left_col, text="Padrão de 30 tiros\n600 RPM (~0.1s entre tiros)",
                           font=("Segoe UI", 10), text_color="gray")
        info.pack(pady=5)

        # Coluna direita - Pattern
        right_col = ctk.CTkFrame(container)
        right_col.pack(side="right", fill="both", expand=True, padx=(5, 0))

        title_pattern = ctk.CTkLabel(right_col, text="📈 Spray Pattern", font=("Segoe UI", 14, "bold"))
        title_pattern.pack(pady=10)

        if self.engine and self.engine.pattern:
            pattern_img = create_spray_pattern_image(self.engine.pattern, size=(250, 320))
            self.pattern_photo = ctk.CTkImage(light_image=pattern_img, dark_image=pattern_img,
                                             size=(250, 320))
            self.pattern_img_label = ctk.CTkLabel(right_col, image=self.pattern_photo, text="")
            self.pattern_img_label.pack(pady=5)
        else:
            no_pattern = ctk.CTkLabel(right_col, text="Nenhum padrão carregado", text_color="gray")
            no_pattern.pack(pady=20)

    def create_config_section(self, parent):
        """Seção de configurações - Tab dedicada"""
        config_frame = ctk.CTkFrame(parent, fg_color="transparent")
        config_frame.pack(fill="both", expand=True, padx=10, pady=10)

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

        # Aviso sobre eDPI
        edpi_info_frame = ctk.CTkFrame(config_frame, fg_color="#2b2b2b")
        edpi_info_frame.pack(fill="x", padx=10, pady=15)

        ctk.CTkLabel(edpi_info_frame, text="💡 Informação Importante",
                    font=("Segoe UI", 12, "bold")).pack(pady=5)

        info_text = ("Pro players CS2 usam eDPI ~880\n"
                    "eDPI alto (>2000) requer multiplicador BAIXO (0.5-1.5)\n"
                    "Comece com multiplier 1.0 e ajuste aos poucos")

        ctk.CTkLabel(edpi_info_frame, text=info_text,
                    font=("Segoe UI", 9), text_color="gray", justify="left").pack(pady=5)

    def create_status_section(self, parent):
        """Banner de status compacto"""
        status_frame = ctk.CTkFrame(parent, height=40)
        status_frame.pack(fill="x", padx=20, pady=5)

        # Layout horizontal
        # Status à esquerda
        self.status_indicator = ctk.CTkLabel(
            status_frame,
            text="● DESATIVADO",
            font=("Segoe UI", 14, "bold"),
            text_color="red"
        )
        self.status_indicator.pack(side="left", padx=15, pady=5)

        # eDPI no centro
        self.edpi_label = ctk.CTkLabel(
            status_frame,
            text="eDPI: 800",
            font=("Segoe UI", 12)
        )
        self.edpi_label.pack(side="left", padx=15, pady=5)

        # Scale à direita
        self.scale_label = ctk.CTkLabel(
            status_frame,
            text="Scale: 0.0000",
            font=("Segoe UI", 12)
        )
        self.scale_label.pack(side="right", padx=15, pady=5)

    def create_log_section(self, parent):
        """Seção de logs - Tab dedicada"""
        log_frame = ctk.CTkFrame(parent, fg_color="transparent")
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Área de texto com scroll (maior na tab)
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            width=80,
            height=20,
            bg="#2b2b2b",
            fg="#ffffff",
            font=("Consolas", 10),
            state='disabled'
        )
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

    def create_action_buttons(self):
        """Botões de ação - sempre visíveis no rodapé"""
        button_frame = ctk.CTkFrame(self.root)
        button_frame.pack(fill="x", padx=20, pady=10)

        # Botão Start/Stop
        self.toggle_btn = ctk.CTkButton(
            button_frame,
            text="▶ INICIAR",
            font=("Segoe UI", 16, "bold"),
            height=45,
            fg_color="green",
            hover_color="darkgreen",
            command=self.toggle_compensator
        )
        self.toggle_btn.pack(side="left", fill="x", expand=True, padx=5)

        # Botão Salvar
        save_btn = ctk.CTkButton(
            button_frame,
            text="💾 SALVAR",
            font=("Segoe UI", 14, "bold"),
            height=45,
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

        # Informa se config foi carregado
        if self.config_file.exists():
            self.log(f"✓ Configurações carregadas de {self.config_file.name}")
        else:
            self.log("ℹ️ Usando configurações padrão")

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
