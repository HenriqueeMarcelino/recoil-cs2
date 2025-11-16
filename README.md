# CS2 AK-47 Recoil Compensator - POC

**Prova de Conceito (POC)** para entender a matemática e lógica por trás do sistema de recoil da AK-47 no Counter Strike 2.

## 🎯 Objetivo do Projeto

Este projeto foi criado com fins educacionais e de pesquisa para:

1. **Entender a matemática do recoil**: Como funciona o padrão de spray da AK-47
2. **Analisar se é determinístico ou aleatório**: Descobrir se há um padrão fixo ou variação
3. **Criar base para ferramenta de treino**: Fundação para futura plataforma de treinamento de spray

## ⚠️ AVISO IMPORTANTE

**Este script é APENAS para fins educacionais e de pesquisa.**

- ❌ NÃO use em partidas competitivas
- ❌ NÃO use em servidores oficiais da Valve
- ❌ Uso em jogos online pode violar Termos de Serviço
- ✅ Use apenas para entender a mecânica do jogo
- ✅ Use em servidores offline/locais para testes

## 📊 Descobertas sobre o Recoil da AK-47

### Padrão de Spray Observado

Através de testes manuais e análise de dados, descobrimos:

#### Primeiros 3 Tiros
- **Tiro 1**: Perfeito, vai exatamente onde você mirou
- **Tiro 2**: Praticamente no mesmo lugar, sobe levemente para cima e direita
- **Tiro 3**: Movimento vertical para cima, fácil de compensar com movimento do mouse para baixo

#### Tiros 4-10
- Continuam subindo (movimento vertical predominante)
- Começam a desviar para os lados (principalmente direita)
- **Y negativo** nos dados = tiro sobe (recoil para cima)

#### Tiros 11-20
- Movimento se inverte para a **esquerda**
- Grande deslocamento horizontal
- Ainda mantém algum movimento vertical

#### Tiros 21-30
- Padrão em zigue-zague (esquerda-direita-esquerda)
- Mais caótico e difícil de controlar
- Requer precisão e ritmo

### O Padrão é Fixo ou Aleatório?

**Resposta: FIXO com pequena variação aleatória**

- O padrão base é **determinístico** - sempre segue a mesma forma geral
- Existe uma pequena variação aleatória (spread) em cada tiro
- Os dados no arquivo `ak47_pattern.csv` representam o padrão médio/base

## 🔧 Como Funciona

### Dados do Padrão

O arquivo `ak47_pattern.csv` contém 30 coordenadas (X, Y) que representam:

```csv
x,y,z
0,0,30          # Tiro 1: sem recoil
0,0,99          # Tiro 2: sem recoil
0.10497,-26.00426,99  # Tiro 3: sobe muito (Y negativo)
-2.49497,-29.9552,99  # Tiro 4: sobe mais, leve esquerda
...
```

- **X**: Movimento horizontal (negativo = esquerda, positivo = direita)
- **Y**: Movimento vertical (negativo = para cima, positivo = para baixo)
- **Z**: Valor de confiança/referência (99 ou 109)

### Compensação

Para compensar o recoil, movemos o mouse na **direção oposta**:

```python
# Se o recoil vai para CIMA (Y negativo)
# Movemos o mouse para BAIXO (Y positivo)

# Se o recoil vai para ESQUERDA (X negativo)
# Movemos o mouse para DIREITA (X positivo)

dx = -x * scale_factor  # Inverte X
dy = -y * scale_factor  # Inverte Y
```

### Fatores de Ajuste

O movimento do mouse depende de:

1. **Resolução do jogo**: Mais pixels = mais movimento necessário
2. **Sensibilidade**: Maior sensibilidade = menos movimento necessário
3. **DPI do mouse**: Influencia a escala de movimento

Fórmula básica:
```python
scale_factor = base_scale / sensibilidade
movimento_final = coordenada_recoil * scale_factor
```

## 🚀 Como Usar

### Requisitos

- Python 3.7+
- Sistema operacional: Windows, Linux ou macOS
- CS2 instalado (para testes)

### Instalação

1. Clone o repositório:
```bash
git clone <repo-url>
cd recoil-cs2
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

### Execução

1. Execute o script:
```bash
python recoil_compensator.py
```

2. Configure suas opções:
   - Escolha sua resolução de jogo
   - Digite sua sensibilidade no CS2

3. Entre no CS2 (modo offline ou servidor de treino)

4. Selecione a AK-47

5. Segure o botão esquerdo do mouse para disparar
   - O script detectará automaticamente
   - Compensação será aplicada em tempo real

6. Pressione `Ctrl+C` para sair

### Exemplo de Uso

```
$ python recoil_compensator.py

CS2 AK-47 Recoil Compensator POC

Configuração de Resolução:
1. 1920x1080 (Full HD)
2. 2560x1440 (2K)
3. 3840x2160 (4K)
4. Customizado
Escolha a resolução (1-4): 1

Resolução selecionada: 1920x1080
Digite sua sensibilidade no CS2 (padrão 1.0): 1.5

✓ Carregado padrão com 30 pontos
✓ Padrão de spray carregado: 30 bullets
✓ Sensibilidade: 1.5
✓ Resolução: 1920x1080

============================================================
CS2 AK-47 RECOIL COMPENSATOR - POC
============================================================

Instruções:
1. Entre no CS2 e selecione a AK-47
2. Segure o botão esquerdo do mouse para disparar
3. O script compensará o recoil automaticamente
4. Pressione Ctrl+C para sair

⚠️  AVISO: Use apenas para fins educacionais!

Aguardando cliques...
```

## 📁 Estrutura do Projeto

```
recoil-cs2/
├── ak47_pattern.csv          # Dados do padrão de spray (30 pontos)
├── recoil_compensator.py     # Script principal
├── requirements.txt          # Dependências Python
└── README.md                 # Este arquivo
```

## 🔍 Análise Técnica

### Cadência de Tiro

- **AK-47 RPM**: ~600 rounds per minute
- **Tempo entre tiros**: ~0.1 segundos
- O script simula essa cadência para sincronizar a compensação

### Movimentos do Mouse

O script usa `pynput` para:
- **Detectar** quando o botão esquerdo está pressionado
- **Mover** o mouse automaticamente baseado no padrão
- **Sincronizar** com a cadência de tiro da arma

### Thread de Compensação

```python
while shooting:
    1. Calcula tempo desde último tiro
    2. Se >= 0.1s, aplica próxima compensação
    3. Move mouse (dx, dy)
    4. Incrementa contador de tiros
    5. Repete até soltar botão
```

## 🎓 Próximos Passos

Esta POC é a base para:

1. **Ferramenta de Análise**
   - Visualizar padrão de spray em tempo real
   - Comparar seu spray vs padrão perfeito
   - Gerar estatísticas de precisão

2. **Plataforma de Treino**
   - Exercícios progressivos de spray control
   - Feedback visual em tempo real
   - Ranking e progressão
   - Modos de treino para diferentes armas

3. **Comercialização**
   - Software de treino para times profissionais
   - Análise de performance de jogadores
   - Tutoriais interativos

## 📚 Fontes de Dados

Os dados do padrão de spray foram obtidos de:
- Comunidade chinesa de CS2
- Repositórios GitHub com dados extraídos do jogo
- Testes e validações manuais

Referências:
- [Artanis-RCS](https://github.com/ArtanisInc/Artanis-RCS)
- CS2 Community spray pattern databases

## 📝 Licença

MIT License - Uso educacional apenas

## 🤝 Contribuindo

Este é um projeto de pesquisa. Contribuições são bem-vindas para:
- Melhorar precisão da compensação
- Adicionar suporte para outras armas
- Criar visualizações do padrão
- Documentar descobertas

## ❓ FAQ

### Por que os valores Y são negativos?

No sistema de coordenadas do jogo, Y negativo significa que o tiro foi **para cima** em relação ao ponto de mira. Por isso invertemos: movemos o mouse para baixo (positivo) para compensar.

### O script funciona em qualquer resolução?

Sim, mas pode precisar de ajustes no `scale_factor`. Começamos com valores conservadores que funcionam na maioria dos casos.

### Posso usar para outras armas?

Sim! Cada arma tem seu próprio padrão. Você precisaria dos dados CSV específicos da arma.

### É preciso ajustar o scale_factor?

Provavelmente sim. O valor padrão (0.15) é conservador. Teste e ajuste conforme necessário no código.

### Como treinar sem o script?

Use os mapas de treino do Workshop:
- Recoil Master
- aim_botz
- Training Center

---

**Desenvolvido como POC educacional para entender mecânicas de CS2**
