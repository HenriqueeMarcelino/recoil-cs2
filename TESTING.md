# 🔧 Guia de Testes - Versão DEBUG

## Por que a v2 não funcionou no CS2?

O CS2 pode estar **bloqueando** movimentos automáticos de mouse por causa do:
- **VAC (Valve Anti-Cheat)**: Detecta e bloqueia automação
- **Raw Input**: Captura mouse direto do driver
- **Trusted Mode**: Modo de segurança do CS2

## 🧪 Versão v3 - DEBUG MODE

Criei a v3 para **testar diferentes métodos** e descobrir qual funciona:

### O que a v3 testa:

1. **SendInput** (API moderna do Windows)
2. **mouse_event** (API antiga - pode ter mais sucesso)
3. **Scale factors diferentes** (1x até 10x)
4. **Logging detalhado** para debug

## 🚀 Como Testar

### 1. Execute a versão DEBUG:

```bash
# Como Administrador
cd C:\PJ\recoil-cs2
python recoil_compensator_v3_debug.py
```

### 2. Configure para testes:

Quando pedir para escolher método, teste AMBOS:

**Teste 1: mouse_event com scale 5x**
- Método: `2` (mouse_event)
- Scale: `4` (5x)

**Teste 2: SendInput com scale 10x**
- Método: `1` (SendInput)
- Scale: `5` (10x)

### 3. Entre no CS2 e teste:

1. Abra mapa de treino de spray
2. Mire na parede
3. Segure clique esquerdo
4. Observe se a mira se move para baixo

### 4. Analise os logs:

```
>>> INICIANDO SPRAY <<<
🔧 DEBUG: Método = mouse_event
🔧 DEBUG: Scale = 8.00
Tiro 1/30: mouse_event(0.0, 0.0)
Tiro 2/30: mouse_event(0.0, 0.0)
Tiro 3/30: mouse_event(-0.8, 208.0)  ← Deveria mover mouse para BAIXO (208 pixels)
Tiro 4/30: mouse_event(19.9, 239.6)  ← Deveria mover mouse para BAIXO (239 pixels)
```

## 📊 O que cada número significa:

```python
mouse_event(x, y)
# x: negativo = esquerda, positivo = direita
# y: positivo = PARA BAIXO (compensa o recoil que vai para cima)
```

Se você vê números grandes (tipo 200+) mas a mira não se move no jogo:
- ✅ O script está funcionando corretamente
- ❌ **O CS2 está bloqueando** os movimentos

## ⚠️ Possíveis Limitações

### 1. VAC pode estar bloqueando

O VAC (Valve Anti-Cheat) pode detectar:
- Automação de mouse
- Movimentos "perfeitos" demais
- Padrões repetitivos

**Solução**: Pode não haver solução sem modificar o jogo (banível)

### 2. Trusted Mode

CS2 tem "Trusted Mode" que bloqueia:
- DLLs não autorizadas
- Hooks de API
- Automação de input

**Teste**:
```
No CS2, abra console e digite:
sv_cheats 1
sv_allow_wait_command 1
```

Tente em servidor offline/local.

### 3. Raw Input no CS2

Desabilite Raw Input nas configurações do CS2:
```
Opções → Teclado/Mouse → Raw Input → DESABILITADO
```

Isso pode permitir que o script funcione.

## 🎯 Ordem de Testes

### Teste 1: Fora do jogo
```bash
python recoil_compensator_v3_debug.py
```
- Use método 2 (mouse_event)
- Scale 2x
- Teste no desktop/bloco de notas
- **Deve funcionar**: ✅

### Teste 2: No menu do CS2
- Deixe script rodando
- Abra CS2 (no menu principal)
- Teste clicando
- **Deve funcionar**: ✅ (provavelmente)

### Teste 3: Servidor offline
- Entre em partida offline (bots)
- Desabilite Raw Input no CS2
- Teste com AK-47
- **Pode funcionar**: ⚠️

### Teste 4: Mapa de treino
- Workshop → Recoil Master
- Teste com diferentes scales
- **Pode não funcionar**: ❌ (VAC ativo)

## 📝 Resultados Esperados

| Local | v1 | v2 | v3 (mouse_event) | v3 (SendInput) |
|-------|----|----|------------------|----------------|
| Desktop | ✅ | ✅ | ✅ | ✅ |
| Menu CS2 | ❌ | ❌ | ⚠️ | ⚠️ |
| Jogo Offline | ❌ | ❌ | ⚠️ | ❌ |
| Jogo Online | ❌ | ❌ | ❌ | ❌ |

## 🔍 Se NADA funcionar no jogo

Isso significa que o CS2 está **bloqueando ativamente** qualquer automação de mouse.

### Alternativas:

1. **Treino Manual**: Use os dados do padrão para treinar manualmente
2. **Overlay Visual**: Criar overlay que mostra onde mover o mouse
3. **Análise de Replay**: Ferramenta que analisa seus sprays após o jogo
4. **Plataforma Web**: Site de treino com simulação do spray

Todas essas alternativas são **legais** e não violam ToS.

## 💡 Próximos Passos (se bloquear)

Se descobrirmos que o CS2 bloqueia tudo, vou criar:

1. **Overlay de Treino**:
   - Mostra o padrão na tela
   - Você move o mouse manualmente
   - Feedback visual em tempo real

2. **Analisador de Performance**:
   - Grava seus sprays
   - Compara com padrão perfeito
   - Dá nota e sugestões

3. **Simulador Web**:
   - Jogo simples de navegador
   - Treina spray control
   - Sem violar ToS do CS2

## 🚨 IMPORTANTE

**NÃO use em competitivo/online!**

Mesmo que funcione:
- Pode resultar em ban VAC
- Viola Termos de Serviço
- É considerado cheating

Use **APENAS** para:
- ✅ Entender a mecânica
- ✅ Estudar padrões
- ✅ Treino offline
- ✅ Análise educacional

---

**Teste a v3 e me avise os resultados!** 🔬
