#!/usr/bin/env node
'use strict';

/**
 * gerar-tabela.js
 *
 * Lê um arquivo JSON de prova de concurso e gera um HTML com uma tabela
 * para cada texto ("texto1", "texto2", ...).
 *
 * Tabela:
 *   - Coluna 1: número da linha, exibido somente quando for múltiplo de 5
 *   - Coluna 2: conteúdo de cada linha ("texto")
 *
 * Uso:
 *   node gerar-tabela.js [arquivo.json] [saida.html]
 *
 * Padrões:
 *   entrada = ./dados.json
 *   saída   = ./saida.html
 */

const fs = require('fs');
const path = require('path');

// ---------------------------------------------------------------------------
// Utilitários
// ---------------------------------------------------------------------------

/** Escapa caracteres especiais para evitar quebrar o HTML. */
function escapeHtml(valor) {
  return String(valor ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/** Lê e faz o parse do JSON, com mensagens de erro claras. */
function lerJson(caminho) {
  let conteudo;
  try {
    conteudo = fs.readFileSync(caminho, 'utf8');
  } catch (err) {
    throw new Error(`Não foi possível ler o arquivo "${caminho}": ${err.message}`, { cause: err });
  }

  // Remove BOM, se existir
  conteudo = conteudo.replace(/^\uFEFF/, '');

  try {
    return JSON.parse(conteudo);
  } catch (err) {
    throw new Error(`JSON inválido em "${caminho}": ${err.message}`, { cause: err });
  }
}

/** Retorna as chaves de texto (texto1, texto2, ...) em ordem numérica. */
function obterChavesDeTexto(dados) {
  return Object.keys(dados)
    .filter((chave) => /^texto\d+$/.test(chave))
    .sort((a, b) => parseInt(a.slice(5), 10) - parseInt(b.slice(5), 10));
}

// ---------------------------------------------------------------------------
// Geração do HTML
// ---------------------------------------------------------------------------

/** Gera o HTML (título + tabela) de um texto. */
function gerarTabelaDoTexto(chave, texto) {
  if (!texto || !Array.isArray(texto.linhas)) {
    throw new Error(`A chave "${chave}" não possui a estrutura esperada (titulo/linhas).`);
  }

  const linhasHtml = texto.linhas
    .map((item) => {
      const numero = Number(item.linha);
      const mostrarNumero = Number.isInteger(numero) && numero > 0 && numero % 5 === 0;

      const colNumero = mostrarNumero ? numero : '';
      // &nbsp; garante que linhas em branco mantenham a altura
      const colTexto = item.texto ? escapeHtml(item.texto) : '&nbsp;';

      return `        <tr>
          <td style="font-style: italic; padding-right: 15px; border: none !important;">${colNumero}</td>
          <td style="padding: 1px; border: none;">${colTexto}</td>
        </tr>`;
    })
    .join('\n');

  return `    <section id="${escapeHtml(chave)}">
      <h2>${escapeHtml(texto.titulo)}</h2>
      <p>${escapeHtml(texto.subtitulo)}</p>
      <table style="border: none; border-collapse: collapse;">
        <thead>
          <tr>
            <th></th>
            <th></th>
          </tr>
        </thead>
        <tbody>
${linhasHtml}
        </tbody>
      </table>
      <p>${escapeHtml(texto.autor)}</p>
      <p>${escapeHtml(texto.fonte)}</p>
    </section>`;
}

/** Gera o documento HTML completo. */
// eslint-disable-next-line no-unused-vars
function gerarHtml(dados) {
  const chaves = obterChavesDeTexto(dados);
''
  if (chaves.length === 0) {
    throw new Error('Nenhuma chave de texto ("texto1", "texto2", ...) encontrada no JSON.');
  }

  const secoes = chaves.map((chave) => gerarTabelaDoTexto(chave, dados[chave])).join('\n\n');

  return `<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Textos para leitura</title>
</head>
<body>
${secoes}
</body>
</html>
`;
}

// ---------------------------------------------------------------------------
// Execução
// ---------------------------------------------------------------------------

function main() {
  const entrada = path.resolve(process.argv[2] || './Transpetro 2018/Transpetro-2018-21.json');
  // eslint-disable-next-line no-unused-vars
  const saida = path.resolve(process.argv[3] || 'saida.html');

  try {
    // eslint-disable-next-line no-unused-vars
    const dados = lerJson(entrada);
    // eslint-disable-next-line no-unused-vars
    const html = gerarHtml(dados);
    fs.writeFileSync(saida, html, 'utf8');
    console.log(`HTML gerado com sucesso: ${saida}`);
  } catch (err) {
    console.error(`Erro: ${err.message}`);
    process.exit(1);
  }
}

main();
