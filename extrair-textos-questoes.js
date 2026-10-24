#!/usr/bin/env node
'use strict';

/**
 * gerar-tabela.js
 *
 * Lê um arquivo JSON de prova de concurso e gera uma tabela para cada texto
 * ("texto1", "texto2", ...), seguida da seção de questões ("questoes"):
 *   - Coluna 1: número da linha, exibido somente quando for múltiplo de 5
 *   - Coluna 2: conteúdo de cada linha ("texto")
 *
 * Uso:
 *   node gerar-tabela.js [entrada.json] [saida] [--formato=md|md-pipe|html]
 *
 * Formatos:
 *   md       (padrão) Markdown com tabelas em HTML puro. Renderiza no GitHub.
 *   md-pipe  Markdown com tabelas nativas "| a | b |". Renderiza no GitHub.
 *   html     Página HTML completa, com CSS (para abrir no navegador).
 *
 * Padrões: entrada = ./dados.json | saída = ./saida.md (ou saida.html)
 *
 * Observação sobre o GitHub: o renderizador remove <style>, class e style,
 * por isso o formato "md" usa apenas tags e atributos permitidos (align).
 */

const fs = require('fs');
const path = require('path');

// ---------------------------------------------------------------------------
// Utilitários
// ---------------------------------------------------------------------------

/** Escapa caracteres especiais de HTML. */
function escapeHtml(valor) {
  return String(valor ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/** Escapa caracteres com significado especial em Markdown (modo pipe). */
function escapeMarkdown(valor) {
  return escapeHtml(valor).replace(/([\\`*_[\]|#~])/g, '\\$1');
}

/**
 * Preserva recuos: converte espaços/tabs iniciais em &nbsp;
 * (o GitHub não aplica white-space: pre-wrap).
 */
function preservarRecuo(texto) {
  return texto
    .replace(/\t/g, '    ')
    .replace(/^ +/, (espacos) => '&nbsp;'.repeat(espacos.length));
}

/** Indica se o número da linha deve ser exibido (múltiplos de 5). */
function numeroVisivel(item) {
  const numero = Number(item.linha);
  return Number.isInteger(numero) && numero > 0 && numero % 5 === 0 ? numero : '';
}

/** Lê e faz o parse do JSON, com mensagens de erro claras. */
function lerJson(caminho) {
  let conteudo;
  try {
    conteudo = fs.readFileSync(caminho, 'utf8');
  } catch (err) {
    throw new Error(`Não foi possível ler o arquivo "${caminho}": ${err.message}`, { cause: err });
  }

  conteudo = conteudo.replace(/^\uFEFF/, ''); // remove BOM

  try {
    return JSON.parse(conteudo);
  } catch (err) {
    throw new Error(`JSON inválido em "${caminho}": ${err.message}`, { cause: err });
  }
}

/** Retorna as chaves de texto (texto1, texto2, ...) em ordem numérica. */
function obterTextos(dados) {
  const chaves = Object.keys(dados)
    .filter((chave) => /^texto\d+$/.test(chave))
    .sort((a, b) => parseInt(a.slice(5), 10) - parseInt(b.slice(5), 10));

  if (chaves.length === 0) {
    throw new Error('Nenhuma chave de texto ("texto1", "texto2", ...) encontrada no JSON.');
  }

  return chaves.map((chave) => {
    const texto = dados[chave];
    if (!texto || !Array.isArray(texto.linhas)) {
      throw new Error(`A chave "${chave}" não possui a estrutura esperada (titulo/linhas).`);
    }
    return { chave, titulo: String(texto.titulo ?? chave), linhas: texto.linhas };
  });
}

/**
 * Lê a chave "questoes" (ou "questões") e normaliza cada questão:
 *   { numero, texto, alternativas: [[letra, texto], ...] }  (letras em ordem A-Z)
 * Se a chave não existir, avisa e segue apenas com os textos.
 */
function obterQuestoes(dados) {
  const lista = dados.questoes ?? dados['questões'];

  if (lista === undefined) {
    console.warn('Aviso: chave "questoes" não encontrada; gerando apenas os textos.');
    return [];
  }
  if (!Array.isArray(lista)) {
    throw new Error('A chave "questoes" deve ser uma lista (array).');
  }

  return lista.map((q, i) => {
    const posicao = i + 1;
    if (!q || typeof q.alternativas !== 'object' || q.alternativas === null) {
      throw new Error(`A questão na posição ${posicao} não possui o objeto "alternativas".`);
    }
    return {
      numero: q.numero ?? posicao,
      texto: String(q.texto ?? ''),
      alternativas: Object.entries(q.alternativas).sort(([a], [b]) => a.localeCompare(b)),
    };
  });
}

// ---------------------------------------------------------------------------
// Seção de questões
// ---------------------------------------------------------------------------

/** Questões em Markdown (usado nos formatos "md" e "md-pipe"). */
function secaoQuestoesMarkdown(questoes) {
  if (questoes.length === 0) return '';

  const blocos = questoes.map((q) => {
    const alternativas = q.alternativas
      .map(([letra, texto]) => `(${escapeMarkdown(letra)})  &nbsp; ${escapeMarkdown(texto)}`)
      .join('  \n');
    return `--- \n  \n###  ${escapeMarkdown(q.numero)}\n\n${escapeMarkdown(q.texto)}\n\n${alternativas}`;
  });

  return `\n## Questões\n\n${blocos.join('\n\n')}\n`;
}

/** Questões em HTML (usado na página completa). */
function secaoQuestoesHtml(questoes) {
  if (questoes.length === 0) return '';

  const blocos = questoes
    .map((q) => {
      const alternativas = q.alternativas
        .map(([letra, texto]) => `          <li><strong>${escapeHtml(letra)})</strong> ${escapeHtml(texto)}</li>`)
        .join('\n');
      return `      <article class="questao">
        <h3>Questão ${escapeHtml(q.numero)}</h3>
        <p>${escapeHtml(q.texto)}</p>
        <ul>
${alternativas}
        </ul>
      </article>`;
    })
    .join('\n');

  return `\n\n    <section id="questoes">\n      <h2>Questões</h2>\n${blocos}\n    </section>`;
}

/** Textos (tabela HTML) + questões, em Markdown. */
function gerarMarkdownHtml(textos, questoes) {
  return gerarMarkdownHtmlTextos(textos) + secaoQuestoesMarkdown(questoes);
}

/** Textos (tabela pipe) + questões, em Markdown. */
function gerarMarkdownPipe(textos, questoes) {
  return gerarMarkdownPipeTextos(textos) + secaoQuestoesMarkdown(questoes);
}

// ---------------------------------------------------------------------------
// Formato 1: Markdown com tabela HTML (compatível com GitHub)
// ---------------------------------------------------------------------------

function tabelaHtmlGithub(linhas) {
  // IMPORTANTE: não pode haver linhas em branco dentro do bloco HTML,
  // senão o Markdown encerra o bloco e a tabela quebra.
  const corpo = linhas
    .map((item) => {
      const texto = item.texto ? preservarRecuo(escapeHtml(item.texto)) : '&nbsp;';
      return [
        '  <tr>',
        `    <td align="right">${numeroVisivel(item)}</td>`,
        `    <td>${texto}</td>`,
        '  </tr>',
      ].join('\n');
    })
    .join('\n');

  return [
    '<table>',
    '  <thead>',
    '    <tr>',
    '      <th align="right">Linha</th>',
    '      <th align="left">Texto</th>',
    '    </tr>',
    '  </thead>',
    '  <tbody>',
    corpo,
    '  </tbody>',
    '</table>',
  ].join('\n');
}

function gerarMarkdownHtmlTextos(textos) {
  return (
    textos
      .map((t) => `**${t.titulo.replace(/\s+/g, ' ')}**\n\n${tabelaHtmlGithub(t.linhas)}`)
      .join('\n\n') + '\n'
  );
}

// ---------------------------------------------------------------------------
// Formato 2: Markdown com tabela nativa (pipe)
// ---------------------------------------------------------------------------

function tabelaPipe(linhas) {
  const cabecalho = ['| Linha | Texto |', '| ---: | :--- |'];
  const corpo = linhas.map((item) => {
    const texto = item.texto ? preservarRecuo(escapeMarkdown(item.texto)) : '&nbsp;';
    return `| ${numeroVisivel(item)} | ${texto} |`;
  });
  return [...cabecalho, ...corpo].join('\n');
}

function gerarMarkdownPipeTextos(textos) {
  return (
    textos
      .map((t) => `## ${t.titulo.replace(/\s+/g, ' ')}\n\n${tabelaPipe(t.linhas)}`)
      .join('\n\n') + '\n'
  );
}

// ---------------------------------------------------------------------------
// Formato 3: página HTML completa (navegador)
// ---------------------------------------------------------------------------

function gerarPaginaHtml(textos, questoes = []) {
  const secoes = textos
    .map((t) => {
      const corpo = t.linhas
        .map(
          (item) =>
            `        <tr><td class="num">${numeroVisivel(item)}</td>` +
            `<td class="txt">${item.texto ? escapeHtml(item.texto) : '&nbsp;'}</td></tr>`
        )
        .join('\n');

      return `    <section id="${escapeHtml(t.chave)}">
      <h2>${escapeHtml(t.titulo)}</h2>
      <table>
        <thead><tr><th class="num">Linha</th><th class="txt">Texto</th></tr></thead>
        <tbody>
${corpo}
        </tbody>
      </table>
    </section>`;
    })
    .join('\n\n');

  return `<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Textos para leitura</title>
  <style>
    body { font-family: Georgia, 'Times New Roman', serif; max-width: 820px; margin: 2rem auto; padding: 0 1rem; color: #1a1a1a; line-height: 1.5; }
    h2 { margin: 2.5rem 0 1rem; font-size: 1.3rem; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 2px 8px; vertical-align: top; }
    thead th { border-bottom: 2px solid #333; font-size: .85rem; text-transform: uppercase; letter-spacing: .05em; }
    td.num, th.num { width: 4rem; text-align: right; color: #666; font-family: 'Courier New', monospace; border-right: 1px solid #ccc; }
    td.txt, th.txt { text-align: left; white-space: pre-wrap; }
    .questao { margin: 1.5rem 0; }
    .questao h3 { margin: 0 0 .4rem; font-size: 1.05rem; }
    .questao p { margin: 0 0 .5rem; }
    .questao ul { list-style: none; margin: 0; padding-left: 1rem; }
  </style>
</head>
<body>
${secoes}${secaoQuestoesHtml(questoes)}
</body>
</html>
`;
}

// ---------------------------------------------------------------------------
// Execução
// ---------------------------------------------------------------------------

const GERADORES = {
  md: { gerar: gerarMarkdownHtml, extensao: 'md' },
  'md-pipe': { gerar: gerarMarkdownPipe, extensao: 'md' },
  html: { gerar: gerarPaginaHtml, extensao: 'html' },
};

function main() {
  const args = process.argv.slice(2);
  const opcaoFormato = args.find((a) => a.startsWith('--formato='));
  const posicionais = args.filter((a) => !a.startsWith('--'));

  const formato = opcaoFormato ? opcaoFormato.split('=')[1] : 'md';

  try {
    if (!GERADORES[formato]) {
      throw new Error(`Formato "${formato}" inválido. Use: ${Object.keys(GERADORES).join(', ')}.`);
    }

    const { gerar, extensao } = GERADORES[formato];
    const entrada = path.resolve(posicionais[0] || 'dados.json');
    const saida = path.resolve(posicionais[1] || `saida.${extensao}`);

    const dados = lerJson(entrada);
    const textos = obterTextos(dados);
    const questoes = obterQuestoes(dados);
    fs.writeFileSync(saida, gerar(textos, questoes), 'utf8');

    console.log(`Arquivo gerado (${formato}): ${saida}`);
    console.log(`  ${textos.length} texto(s) e ${questoes.length} questão(ões).`);
  } catch (err) {
    console.error(`Erro: ${err.message}`);
    process.exit(1);
  }
}

main();
