# 🎨 CS2 Recoil Trainer - Interface Gráfica

Interface gráfica moderna e profissional para treino de controle de recoil do Counter Strike 2.

![Interface](https://img.shields.io/badge/Interface-Modern_GUI-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![Platform](https://img.shields.io/badge/Platform-Windows-blue)

## ✨ Funcionalidades

### 🎯 Interface Moderna
- **Dark Mode** profissional
- Layout intuitivo e organizado
- Logs em tempo real
- Indicadores visuais de status

### ⚙️ Configurações Completas
- **DPI do Mouse**: Configure seu DPI exato
- **Sensibilidade CS2**: Sua sensibilidade in-game
- **Resolução**: Detecção automática ou manual
- **Scale Multiplier**: Ajuste fino da compensação
- **Seleção de Armas**: Escolha entre AK-47, M4A4, M4A1-S

### 💾 Sistema de Configuração
- **Auto-save**: Salva configurações em JSON
- **Auto-load**: Carrega automaticamente na inicialização
- **Portável**: Arquivo `config.json` simples

### ⌨️ Hotkeys
- **F1**: Liga/Desliga compensador
- **F2**: Aumenta scale (+10%)
- **F3**: Diminui scale (-10%)

### 📊 Cálculo Automático
- **eDPI**: Calcula automaticamente (DPI × Sensibilidade)
- **Scale**: Fórmula baseada no CS2 (considera m_yaw)
- **Conversão precisa**: De unidades do jogo para pixels

## 🚀 Instalação

### 1. Instale as dependências:

```bash
pip install -r requirements.txt
```

**Dependências:**
- `customtkinter` - Interface moderna
- `pynput` - Detecção de mouse/teclado
- `pillow` - Suporte a imagens
- `pywin32` - API do Windows (opcional)

### 2. Execute a interface:

```bash
python recoil_trainer.py
```

## 📖 Como Usar

### Primeira Configuração

1. **Abra o programa**
   ```bash
   python recoil_trainer.py
   ```

2. **Configure seus dados:**
   - **DPI**: Digite o DPI do seu mouse (ex: 3200)
   - **Sensibilidade**: Sua sens no CS2 (ex: 1.25)
   - **Resolução**: Clique em "Auto" ou digite manualmente

3. **Clique em "Recalcular Scale"**
   - O programa calcula automaticamente o scale ideal
   - Veja o eDPI calculado
   - Veja o Scale final

4. **Salve a configuração**
   - Clique em "💾 Salvar Config"
   - Cria arquivo `config.json`

### Durante o Treino

1. **Entre no CS2**
   - Abra um mapa de treino (ex: Recoil Master)
   - Selecione a AK-47

2. **Ative o compensador**
   - Pressione **F1** ou clique em "▶ INICIAR"
   - Status muda para "● ATIVADO" (verde)

3. **Teste o spray**
   - Segure clique esquerdo
   - Observe os logs
   - Veja a compensação em ação

4. **Ajuste fino**
   - Se compensar **pouco**: Pressione **F2** (aumenta)
   - Se compensar **muito**: Pressione **F3** (diminui)
   - Cada ajuste = ±10%

5. **Encontrou o valor ideal?**
   - Clique em "💾 Salvar Config"
   - Configuração salva permanentemente

## 🔧 Entendendo os Valores

### eDPI (Effective DPI)
```
eDPI = DPI × Sensibilidade
```

**Exemplos:**
- Pro players: 800-1200 eDPI
- Você (DPI 3200, Sens 1.25): **4000 eDPI** ← Muito alto!

### Scale
```
Scale = 10.0 / (Sensibilidade × DPI_Factor)
DPI_Factor = Seu_DPI / 800
```

**Para DPI 3200 e Sens 1.25:**
```
DPI_Factor = 3200 / 800 = 4.0
Scale = 10.0 / (1.25 × 4.0) = 2.0
```

### Scale Multiplier
- Ajuste fino manual
- Padrão: **1.0** (usa scale calculado)
- **>1.0**: Aumenta compensação
- **<1.0**: Diminui compensação

## 📁 Arquivos Criados

```
recoil-cs2/
├── recoil_trainer.py      # Interface gráfica (USE ESTE!)
├── config.json            # Configurações salvas (criado automaticamente)
├── ak47_pattern.csv       # Dados do padrão da AK-47
└── requirements.txt       # Dependências
```

### config.json (Exemplo)
```json
{
  "dpi": 3200,
  "sensitivity": 1.25,
  "resolution": {
    "width": 1920,
    "height": 1080
  },
  "scale_multiplier": 1.2,
  "weapon": "AK-47",
  "hotkeys": {
    "toggle": "f1",
    "increase_scale": "f2",
    "decrease_scale": "f3"
  }
}
```

## 🎮 Fluxo de Calibração

```
1. Configure DPI + Sens
          ↓
2. Programa calcula Scale teórico
          ↓
3. Teste no CS2
          ↓
4. Ajuste com F2/F3 até ficar perfeito
          ↓
5. Salve com "Salvar Config"
          ↓
6. Configuração carregada automaticamente na próxima vez!
```

## 🔍 Troubleshooting

### "Scale está muito alto/baixo"

**Verifique:**
1. DPI está correto?
2. Sensibilidade está correta?
3. Raw Input está **desabilitado** no CS2?

**Ajuste:**
- Use F2/F3 para ajuste fino
- Ou edite Scale Multiplier manualmente

### "Não está compensando no jogo"

**Possíveis causas:**
1. Raw Input **ligado** no CS2 → **DESLIGUE**
2. Não está como Administrador → Execute como Admin
3. VAC bloqueando → Use apenas offline

### "Interface não abre"

**Verifique:**
```bash
pip install --upgrade customtkinter pynput pillow
```

## 📊 Comparação de Setups

| DPI | Sens | eDPI | Scale Esperado |
|-----|------|------|----------------|
| 400 | 2.0 | 800 | ~10.0 |
| 800 | 1.0 | 800 | ~10.0 |
| 1600 | 1.0 | 1600 | ~5.0 |
| **3200** | **1.25** | **4000** | **~2.0** |

## ⚠️ Avisos Importantes

1. **Use apenas para fins educacionais**
2. **NÃO use em partidas competitivas**
3. **NÃO use em servidores VAC**
4. **Apenas para treino offline**

## 🎯 Próximos Passos (Futuro)

- [ ] Adicionar imagens das armas
- [ ] Suporte para M4A4, M4A1-S
- [ ] Gráfico visual do spray pattern
- [ ] Modo de análise pós-treino
- [ ] Exportar estatísticas
- [ ] Temas personalizáveis

## 📝 Licença

MIT License - Uso educacional apenas

---

**Desenvolvido como POC educacional para estudo de mecânicas do CS2**
