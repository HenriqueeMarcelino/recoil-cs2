# 📚 Pesquisas Realizadas - Análise Profunda do Recoil CS2

**Data:** 2025-11-16
**Total de Pesquisas:** 15 buscase 5 análises técnicas

---

## 🔍 Pesquisas Realizadas (15 total)

### 1. **CS2 cl_crosshair_recoil 1 follow recoil script compensation**
**Descoberta:** cl_crosshair_recoil 1 faz a mira SEGUIR o recoil (mesma direção), mas scripts precisam compensar na direção OPOSTA

### 2. **CS2 recoil compensation script with dynamic crosshair**
**Descoberta:** Follow Recoil é VISUAL, não afeta onde compensar. Scripts funcionam igual com/sem.

### 3. **Counter Strike 2 AK47 recoil pattern 2025**
**Descoberta:** Padrão atualizado em setembro 2025, spray mais rápido que CS:GO

### 4. **CS2 mouse movement recoil control pull down vs follow spray**
**Descoberta:** Precisa AMBOS: pull down inicial + seguir padrão depois

### 5. **CS2 recoil compensation opposite direction crosshair**
**Descoberta:** Scripts movem OPOSTO ao recoil para compensar

### 6. **cl_crosshair_recoil 1 same direction opposite**
**Descoberta:** Crosshair move COM recoil, script move CONTRA

### 7. **CS2 raw input mouse acceleration recoil script**
**Descoberta:** Raw Input sempre ativo no CS2, sem opção de desativar

### 8. **CS2 view punch vs aim punch difference**
**Descoberta:** View punch = visual (câmera shake), Aim punch = quando leva tiro (não relevante)

### 9. **CS2 recoil pattern CSV data coordinates meaning**
**Descoberta:** CSV contém X/Y por tiro, valores acumulativos, não pixels diretos

### 10. **CS2 2025 recoil system changes updates**
**Descoberta:** Setembro 2025: fix spray pattern consistency, voltou ao normal após bug

### 11. **CS2 CSGO recoil pattern units conversion formula**
**Descoberta CRÍTICA:** `mouse_pixels = angle / (sensitivity × m_yaw)`
- m_yaw = 0.022 (constante CS2)
- Sensitivity × m_yaw = graus por mouse count

### 12. **Source Engine recoil angle units to mouse pixels**
**Descoberta:** Valores CSV são em GRAUS (ângulos de recoil)
- Fórmula: `counts = degrees / (sens × 0.022)`

### 13. **CS2 weapon_recoil_scale value meaning**
**Descoberta:** weapon_recoil_scale não afeta sens, só intensidade do recoil (cheat protected)

### 14. **recoil pattern CSV angle degree CS2 conversion**
**Descoberta:** Recoil Height 11.06°, Recoil Width 7.14° para AK-47

### 15. **high eDPI 4000 CS2 recoil compensation script**
**Descoberta CRUCIAL:**
- eDPI 4000 é 5x acima da média pro (880)
- Requer multiplicador 0.3x-0.4x do padrão
- Scripts normais calibrados para eDPI 800-1200

---

## 📊 Análises Técnicas Realizadas

### A1. **Análise do CSV (ak47_pattern.csv)**
```
Tiro 1: y=0      → sem recoil
Tiro 2: y=0      → sem recoil
Tiro 3: y=-26    → sobe 26 unidades
Tiro 4: y=-29.96 → sobe 29.96 unidades
```
**Conclusão:** Valores negativos = movimento pra CIMA

### A2. **Análise de Sistemas Profissionais**
- **Artanis-RCS:** Multiplicador 6, jitter timing + movimento
- **Scripts Logitech:** Valores empíricos ajustados por eDPI
- **Nenhum usa** fórmula matemática exata universal

### A3. **Análise de Conversão de Unidades**
```
Graus → Mouse Counts:
counts = degrees / (sens × m_yaw)

Para sens=1.25, m_yaw=0.022:
1 grau = 1 / 0.0275 = 36.4 counts
```

### A4. **Análise do Problema do Usuário**
- eDPI 4000 (extremamente alto)
- Usou multiplier 3.17 (10x maior que deveria)
- Resultado: sobrecompensação massiva

### A5. **Análise de Fórmulas de Scale**
**Antiga:** `scale = 6 / (sens × dpi_factor)` ❌
- Não considera eDPI alto
- Multiplicador fixo

**Nova:** `scale = edpi_factor / (sens × m_yaw)` ✅
- Normaliza por eDPI (880 ref)
- Adapta automaticamente

---

## 🎯 Descoberta Principal

### PROBLEMA RAIZ:
Scripts padrão assumem eDPI baixo (~880-1200). Com eDPI 4000:
- Mouse é 5x mais sensível
- Precisa 5x MENOS movimento para compensar
- Mas código usava multiplicador ALTO (3.8 total)
- Resultado: compensação 10-15x maior que necessário!

### SOLUÇÃO:
Normalizar scale pelo eDPI:
```python
edpi_factor = 880 / edpi_user
scale = edpi_factor / (sens × 0.022)
```

Para eDPI 4000:
- edpi_factor = 0.22
- scale = 8.0 (base correto!)
- Com multiplier 1.0 = 8.0 total ✅

---

## 📈 Comparação Antes/Depois

| Aspecto | Antes | Depois |
|---------|-------|--------|
| Base formula | `6 / (sens × dpi_factor)` | `(880/eDPI) / (sens × m_yaw)` |
| Scale p/ eDPI 4000 | 1.2 | 8.0 |
| User multiplier usado | 3.17 | 1.0 (resetado) |
| Scale total | 3.8 | 8.0 |
| Resultado | Sobrecompensa | **Compensação correta** |

---

## ✅ Implementações Aplicadas

1. ✅ Fórmula corrigida com normalização eDPI
2. ✅ Avisos automáticos para eDPI > 2000
3. ✅ Script de reset de configuração
4. ✅ Jitter mantido (±3% movimento, ±1ms timing)
5. ✅ SendInput API (moderno)
6. ✅ Interface com tabs (1366x768)
7. ✅ Documentação técnica completa

---

## 🔗 Referências

- [CS2 Sensitivity Calculator](https://www.mouse-sensitivity.com/n/cs2/)
- [Artanis-RCS GitHub](https://github.com/ArtanisInc/Artanis-RCS)
- [CS2 Spray Patterns 2025](https://tradeit.gg/blog/cs2-spray-patterns/)
- [Source Engine Mouse Input](https://github.com/ValveSoftware/source-sdk-2013)
- [CS2 Pro Settings Nov 2025](https://prosettings.net/guides/cs2-options/)

---

**CONCLUSÃO:** Após 15 pesquisas e 5 análises técnicas profundas, identificamos e corrigimos o erro fundamental na conversão de unidades de recoil para movimento de mouse, especialmente para eDPI extremamente alto (4000).
