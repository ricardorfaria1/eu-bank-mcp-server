# Notas de conformidade

[English](COMPLIANCE.md)

Como o desenho do servidor se relaciona com três regulamentos europeus. É um projeto de portfólio com dados sintéticos; não é aconselhamento jurídico nem uma avaliação de conformidade.

## RGPD (Regulamento (UE) 2016/679)

| Artigo | Exigência | Neste servidor |
|---|---|---|
| 5.º, n.º 1, alínea c) | Minimização dos dados | Cada perfil recebe só os campos de que precisa (ver a tabela no README). NIF e IBAN vão sempre mascarados; o analista recebe a idade em vez da data de nascimento e o país em vez da morada. |
| 25.º | Proteção de dados desde a conceção e por defeito | As restrições estão no servidor, não no prompt. As ferramentas que um perfil não pode usar não são registadas, e o modelo nem sabe que existem. A base de dados é aberta só de leitura. |
| 15.º | Direito de acesso | O registo de auditoria guarda que operador viu que cliente, quando e que campos. O encarregado de proteção de dados consegue responder a "quem acedeu aos meus dados?". |
| 30.º | Registos das atividades de tratamento | O registo de auditoria alimenta o registo das atividades de tratamento, não o substitui. |

O registo de auditoria nunca guarda valores de campos nem termos de pesquisa. Caso contrário, passaria a ser uma segunda cópia dos dados pessoais que devia proteger.

## Branqueamento de capitais (Regulamento (UE) 2024/1624, AMLR)

O artigo 73.º proíbe as entidades obrigadas e os seus funcionários de revelar ao cliente, ou a terceiros, que há informação sobre ele a ser analisada ou comunicada como suspeita ("tipping off"). O AMLR aplica-se a partir de 10 de julho de 2027; até lá, a mesma proibição vem da lei nacional que transpõe a Diretiva (UE) 2015/849.

Neste servidor:

- O atendente, que fala com o cliente, nunca recebe o indicador de PEP, o estado de KYC nem nada ligado a AML, por isso não o pode revelar por engano.
- Os alertas de AML existem na base de dados e nenhuma ferramenta os devolve, a nenhum perfil. Os alertas pertencem aos sistemas da equipa de compliance.
- A pesquisa é limitada (NIF completo ou 3 ou mais letras do nome, no máximo 5 resultados, no máximo 20 clientes por sessão), para o modelo não servir para varrer a base.

## Regulamento da IA (Regulamento (UE) 2024/1689)

O Anexo III, ponto 5, alínea b), classifica como de risco elevado os sistemas de IA destinados a avaliar a capacidade de endividamento de pessoas singulares ou a estabelecer a sua classificação de crédito, exceto os usados para detetar fraude financeira.

Este servidor obtém dados e não decide nada. Não classifica ninguém: o score que devolve vem dos sistemas do banco, e quem decide é uma pessoa. Sozinho, é um componente de acesso a dados.

Se fosse ligado a um sistema que avalia a capacidade de endividamento, esse sistema seria de risco elevado e o servidor faria parte dele. O desenho já suporta duas das obrigações que daí decorrem:

- Manutenção de registos (artigo 12.º): cada chamada fica registada com operador, perfil, clientes e campos.
- Supervisão humana (artigo 14.º): o modelo só obtém e resume; nenhuma ferramenta aprova, recusa ou altera nada.

Ficariam ainda a faltar, entre outros: sistema de gestão de riscos (artigo 9.º), governação dos dados do modelo de scoring (artigo 10.º), documentação técnica (artigo 11.º), testes de exatidão e robustez do próprio modelo (artigo 15.º) e avaliação da conformidade.

O Regulamento (UE) 2026/1744 ("Digital Omnibus" sobre IA) adiou a aplicação das obrigações de risco elevado do Anexo III de 2 de agosto de 2026 para 2 de dezembro de 2027. Confirme as datas em vigor no Jornal Oficial.

## Fora do âmbito

Autenticação (o perfil vem da configuração do servidor), cifragem em repouso, prazo de conservação do registo de auditoria e avaliação de impacto sobre a proteção de dados. Uma versão de produção precisaria de todos.

## Fontes

- RGPD: <https://eur-lex.europa.eu/eli/reg/2016/679/oj>
- AMLR: <https://eur-lex.europa.eu/eli/reg/2024/1624/oj>, artigo 73.º também em <https://www.springlex.eu/pt/packages/aml/amlr-regulation/article-73/>
- Regulamento da IA: <https://eur-lex.europa.eu/eli/reg/2024/1689/oj>
- Digital Omnibus sobre IA: <https://www.regulation-ai.eu/en/omnibus/>, <https://cdp.cooley.com/digital-ai-omnibus-delays-key-deadlines-introduces-new-rules/>
