"""Adapter Android: calls the original V9 study and search, without changing their scoring."""
import contextlib
from pathlib import Path
import mega_falhas_v9 as v9

class Progress:
    def __init__(self, path): self.path = Path(path)
    def write(self, s):
        if s.strip():
            with self.path.open('a', encoding='utf-8') as f: f.write(s)
    def flush(self): pass

def run(history_file, output_dir):
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    log = out / 'ANDAMENTO.txt'
    log.write_text('Iniciando leitura do historico...\n', encoding='utf-8')
    with contextlib.redirect_stdout(Progress(log)):
        draws, bad = v9.load(history_file)
        print('Concursos validos:', len(draws), '| linhas rejeitadas:', len(bad), flush=True)
        (out/'LINHAS_REJEITADAS.txt').write_text('\n'.join(f'{i}: {s}' for i,s in bad), encoding='utf-8')
        stats = v9.study(draws, out)
        print('Auditoria concluida. Iniciando combinacoes...', flush=True)
        best, examined, eligible = v9.search(stats, out)
        if best[1] is None: raise ValueError('Nenhum jogo elegivel encontrado')
        (out/'RESULTADO_V9.txt').write_text(
            'Jogo: ' + ' '.join(f'{x:02d}' for x in best[1]) + '\n'
            + 'Score: ' + str(best[0]) + '\n'
            + 'Candidatos elegiveis: ' + str(eligible) + '\n'
            + 'Total examinados: ' + str(examined) + '\n', encoding='utf-8')
        print('Concluido! Jogo:', best[1], flush=True)
        return ','.join(str(x) for x in best[1]) + '|' + str(len(draws)) + '|' + str(draws[-1][0]) + '|' + str(examined) + '|' + str(best[0])
