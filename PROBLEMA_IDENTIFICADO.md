# 🔴 PROBLEMA CRÍTICO IDENTIFICADO

## Análise do CSV da AK-47

```csv
Tiro 1: x=0,      y=0         (sem recoil)
Tiro 2: x=0,      y=0         (quase sem recoil)
Tiro 3: x=0.10,   y=-26.00    (recoil começa)
Tiro 4: x=-2.49,  y=-29.96    (recoil aumenta)
Tiro 5: x=-1.05,  y=-31.90
Tiro 6: x=12.32,  y=-33.12    (máximo vertical)
```

## ⚠️ PROBLEMAS ENCONTRADOS

### 1. **Valores Y Negativos = Recoil pra CIMA**

- Y negativo no CSV significa bala vai PRA CIMA na tela
- Nosso código faz: `dy = -y * scale = -(-26) * 1.2 = +31.2`
- Move mouse PRA BAIXO (correto!)
- **MAS**: Com eDPI 4000, scale = 1.2 é MUITO FRACO!

### 2. **Fórmula de Scale ERRADA para eDPI Alto**

**Cálculo atual:**
```python
scale = 6.0 / (sens × dpi_factor)
scale = 6.0 / (1.25 × 4.0) = 1.2
```

**Problema:**
- eDPI 4000 é **5x mais sensível** que pro players (eDPI 800)
- Mouse sensível precisa de **movimentos menores**
- MAS os valores do CSV são em **unidades de ângulo CS2**, não pixels!
- Precisa converter: **unidades CS2 → graus → pixels de mouse**

### 3. **Conversão Incorreta de Unidades**

**Fórmula correta CS2:**
```
Movimento em pixels = (ângulo × DPI) / (360 × sens × m_yaw)

Onde:
- ângulo: valor do CSV (ex: -26)
- DPI: 3200
- sens: 1.25
- m_yaw: 0.022 (constante CS2)
```

**Cálculo exemplo (tiro 3, y=-26):**
```
pixels = (26 × 3200) / (360 × 1.25 × 0.022)
pixels = 83200 / 9.9
pixels = 8404 pixels !!! 😱
```

Isso é ABSURDO! Significa que a fórmula está errada.

### 4. **Unidades do CSV são RELATIVAS, não Absolutas**

Os valores do CSV (-26, -29, -31) **NÃO são ângulos diretos**, mas sim:
- **Incrmentos acumulativos** de recoil por tiro
- OU **unidades internas do CS2** que precisam de conversão especial

## 🔬 Investigação: Como Sistemas Profissionais Fazem

**Artanis-RCS:**
- Multiplicador: **6** para rifles
- Fórmula: `movimento = (pattern_value × 6) / sensitivity_factor`
- `sensitivity_factor = ?` (não documentado claramente)

**Scripts Logitech:**
- Usam valores **empíricos** ajustados manualmente
- Não há fórmula matemática exata
- Cada DPI/sens tem tabela própria

## 💡 SOLUÇÃO PROPOSTA

### Opção A: Usar Multiplicador Empírico Alto

Para eDPI 4000, testar:
```python
# Base multiplier MUITO maior
base_mult = 50.0  # ou 100.0, ajustar empiricamente

scale = base_mult / (sens × dpi_factor)
# scale = 50 / 5 = 10 (para eDPI 4000)
```

### Opção B: Fórmula Reversa (multiplicar ao invés de dividir)

```python
# Para eDPI alto, precisa MENOS movimento
# MAS valores CSV grandes precisam de escala grande

scale = base_mult / ((sens × m_yaw) * (dpi / 800))
# scale = 6 / ((1.25 × 0.022) × 4)
# scale = 6 / 0.11 = 54.5
```

### Opção C: Normalizar pelo eDPI de Referência

```python
edpi_reference = 800  # Pro players
edpi_user = dpi × sens  # 4000

scale = base_mult × (edpi_reference / edpi_user)
# scale = 6 × (800 / 4000) = 1.2

# Depois multiplicar pelo valor CSV
movimento = pattern_value × scale × ajuste_empirico
```

## 🎯 POR QUE "PRIMEIRAS BALAS SOBEM E OUTRAS DESCEM"?

1. **Scale muito baixo (1.2)**: Não compensa suficiente o recoil inicial
2. **Valores CSV grandes** (y=-26 a -33): Multiplicados por 1.2 = 31-40 pixels
3. **eDPI 4000**: Cada pixel tem MENOS impacto que eDPI 800
4. **Resultado**: Compensação fraca no início, depois fica desbalanceada

## 📋 PRÓXIMOS PASSOS

1. ✅ Analisar CSV (feito)
2. ⏳ Testar fórmulas com valores empíricos
3. ⏳ Adicionar sistema de calibração automática
4. ⏳ Comparar com gameplay real

---

**Data:** 2025-11-16
**eDPI Usuário:** 4000 (DPI 3200 × Sens 1.25)
**Scale Atual:** 1.2 (MUITO FRACO!)
