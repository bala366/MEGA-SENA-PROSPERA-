# -*- coding: utf-8 -*-
"""MEGA-SENA FALHAS V9 - estudo completo das 54 ausencias antes da busca."""
import re, itertools, time, math, sys
from pathlib import Path
from collections import Counter

BLOCKS=[tuple(h+r*10+c+d+1 for r in range(3) for d in (0,1)) for h in (0,30) for c in (0,2,4,6,8)]
ROWS=[tuple(range(r*10+1,r*10+11)) for r in range(6)]
BID={n:i for i,b in enumerate(BLOCKS) for n in b}
FULL=(1<<60)-1

def load(path):
    found={}; bad=[]
    for lineno,line in enumerate(Path(path).read_text(encoding='utf-8-sig',errors='replace').splitlines(),1):
        s=line.strip()
        if not s:continue
        # First number = contest, last 6 numbers = drawn balls. Dates in between tolerated.
        vals=[int(x) for x in re.findall(r'(?<!\d)\d{1,6}(?!\d)',s)]
        if len(vals)<7 or vals[0]<1 or len(set(vals[-6:]))!=6 or not all(1<=v<=60 for v in vals[-6:]):
            bad.append((lineno,s[:110]));continue
        found[vals[0]]=tuple(sorted(vals[-6:]))
    if len(found)<10:raise ValueError('Historico insuficiente: '+str(len(found))+' concursos validos; exemplos rejeitados: '+str(bad[:4]))
    return sorted(found.items()),bad

def mask(nums):
    v=0
    for x in nums:v|=1<<(x-1)
    return v

def streak(flags):
    k=0
    for v in reversed(flags):
        if not v:break
        k+=1
    return k

def study(draws,out):
    n=len(draws); drawn=[mask(x) for _,x in draws]; absent=[FULL^x for x in drawn]
    # Overlap of two 54-element absence sets is always >=48 (88.89% of 54).
    # Compute all pairs, counts for 70/80/90% plus distribution of 0..6 repeated drawn numbers.
    overlaps=Counter(); bins=Counter(); nearest=[]
    total=n*(n-1)//2
    print('ETAPA 1/4: sobreposicao de TODAS as 54 falhas por pares de concursos',flush=True)
    for i,a in enumerate(drawn):
        best=(-1,-1)
        for j in range(i):
            shared=(a&drawn[j]).bit_count()
            overlaps[shared]+=1
            pct=(48+shared)/54*100
            if pct>=90:bins['90% ou mais']+=1
            elif pct>=80:bins['80% a 89,99%']+=1
            elif pct>=70:bins['70% a 79,99%']+=1
            if shared>best[0]:best=(shared,j)
        if best[1]>=0:nearest.append((best[0],i,best[1]))
        if (i+1)%500==0:print('  sobreposicoes:',i+1,'/',n,flush=True)
    print('ETAPA 2/4: falhas crescentes, duplas, linhas, blocos e repetidas',flush=True)
    windows=[w for w in (10,20,30,50,100,200) if w<=n]
    if n not in windows:windows.append(n)
    number=[]
    for v in range(1,61):
        f=[not (m>>(v-1)&1) for m in drawn]
        w=min(50,n//2); recent=sum(f[-w:])/w; prev=sum(f[-2*w:-w])/w
        number.append(dict(num=v,missing=sum(f),run=streak(f),recent=recent,growth=recent-prev))
    def group_study(groups):
        out=[]
        for idx,g in enumerate(groups,1):
            gm=mask(g); f=[(m&gm)==0 for m in drawn]
            w=min(50,n//2);a=sum(f[-w:])/w;b=sum(f[-2*w:-w])/w
            out.append(dict(id=idx,total=sum(f),run=streak(f),recent=a,growth=a-b,values=g))
        return out
    blocks=group_study(BLOCKS);rows=group_study(ROWS)
    pair_groups=[BLOCKS[i]+BLOCKS[j] for i,j in itertools.combinations(range(10),2)]
    pairs=group_study(pair_groups)
    reps=Counter((drawn[i]&drawn[i-1]).bit_count() for i in range(1,n))
    gapshape=Counter(tuple(b-a for a,b in zip(balls,balls[1:])) for _,balls in draws)
    blockshape=Counter(tuple(sorted(Counter(BID[x] for x in balls).values(),reverse=True)) for _,balls in draws)
    rowshape=Counter(tuple(sorted(Counter((x-1)//10 for x in balls).values(),reverse=True)) for _,balls in draws)
    odd=Counter(sum(x%2 for x in balls) for _,balls in draws)
    sums=Counter((sum(balls)//20)*20 for _,balls in draws)
    spans=Counter(((balls[-1]-balls[0])//10)*10 for _,balls in draws)
    last=draws[-1][1]; lastset=set(last)
    # Prioritize dominant absence masks and growth, but use relative baseline.
    def rank(g):return (g['growth']*4+g['recent']+min(g['run'],20)*.015)
    # For candidate games: expected 'missing blocks' by mask is learned from historical distribution.
    blockmask=Counter()
    for m in drawn:
        bm=0
        for i,b in enumerate(BLOCKS):
            if m&mask(b):bm|=1<<i
        blockmask[bm]+=1
    # Report BEFORE enumerating candidate games.
    report=out/'AUDITORIA_ANTES_DO_JOGO_V9.txt'
    with report.open('w',encoding='utf-8') as f:
        def p(*a):print(*a,file=f)
        p('MEGA-SENA V9 - AUDITORIA HISTORICA ANTES DO JOGO')
        p('Concursos:',n,'Primeiro:',draws[0][0],'Ultimo:',draws[-1][0]);p('Ultimas seis dezenas:',last)
        missing_contests=sorted(set(range(draws[0][0],draws[-1][0]+1))-set(c for c,_ in draws))
        p('Concursos ausentes:',len(missing_contests),'Exemplos:',missing_contests[:30])
        p('\nSOBREPOSICAO DAS 54 FALHAS - TODAS AS DUPLAS:',total)
        p('IMPORTANTE: duas listas de 54 ausentes em universo de 60 SEMPRE compartilham no minimo 48 ausencias = 88,89%.')
        p('Assim, 70% e 80% nao distinguem concursos; 90% exige ao menos 1 dezena sorteada repetida entre os dois concursos.')
        p('Faixas:',dict(bins),'Repeticoes das seis dezenas entre pares:',dict(sorted(overlaps.items())))
        p('20 pares de concursos com maior sobreposicao (empates por proximidade temporal):')
        for shared,i,j in sorted(nearest,key=lambda x:(x[0],x[1]-x[2]),reverse=True)[:20]:
            p('Concursos',draws[j][0],draws[i][0],'sobreposicao',48+shared,'/54 =',round(100*(48+shared)/54,2),'%')
        p('\nREPETIDAS ENTRE CONCURSOS CONSECUTIVOS:',dict(sorted(reps.items())))
        p('Exigencia do usuario para o proximo jogo: EXATAMENTE 1 dezena repetida do ultimo concurso.')
        p('\nJANELAS DE AUSENCIAS:')
        for w in windows:
            rates=[(sum((m>>(x-1)&1)==0 for m in drawn[-w:])/w,x) for x in range(1,61)]
            p('Janela',w,'dezenas com maior frequencia de falha:',sorted(rates,reverse=True)[:12])
        p('\n60 DEZENAS - TOTAL AUSENCIAS / SEQUENCIA ATUAL / ULTIMOS 50 / CRESCIMENTO:')
        for x in number:p(x)
        p('\n10 BLOCOS:')
        for x in blocks:p(x)
        p('\n6 LINHAS:')
        for x in rows:p(x)
        p('\n45 DUPLAS DE BLOCOS (ordem B1+B2, B1+B3...):')
        for x in pairs:p(x)
        p('\nPADROES HISTORICOS:')
        p('Distribuicao dezenas por bloco:',blockshape.most_common(15))
        p('Distribuicao dezenas por linha:',rowshape.most_common(15))
        p('Impares:',odd.most_common());p('Faixas soma de 20:',sums.most_common(15));p('Amplitude:',spans.most_common(10))
        p('Intervalos exatos mais frequentes:',gapshape.most_common(15))
        p('Mascaras de blocos ocupados:',blockmask.most_common(15))
        p('\nREGISTRO CONCURSO A CONCURSO:')
        for (c,balls),am in zip(draws,absent):
            p('CONCURSO',c,'SORTEADAS',' '.join('%02d'%x for x in balls),'54 FALHAS',' '.join('%02d'%x for x in range(1,61) if am>>(x-1)&1))
    return dict(number=number,blocks=blocks,rows=rows,pairs=pairs,reps=reps,blockshape=blockshape,rowshape=rowshape,odd=odd,sums=sums,spans=spans,blockmask=blockmask,last=last,lastset=lastset,n=n,report=report)

def search(stats,out,limit=None):
    print('ETAPA 3/4: TODAS as 50.063.860 combinacoes (uma repetida obrigatoria)',flush=True)
    n=stats['n']; last=stats['lastset']; lastmask=mask(last)
    # Growth of absence reduces a candidate's score, but not a deterministic prediction.
    weights=[0]+[int(250*(1-d['recent'])-170*d['growth']-min(d['run'],50)*2) for d in stats['number']]
    shape=stats['blockshape'];rowshape=stats['rowshape'];odd=stats['odd'];sums=stats['sums'];spans=stats['spans'];bmask=stats['blockmask']
    # Smooth empirical frequencies; no zero-probability penalty for unseen patterns.
    def sc(counter,key):return int(65*math.log1p(counter[key]))
    score_shape={k:sc(shape,k) for k in shape};score_row={k:sc(rowshape,k) for k in rowshape}
    score_odd={k:sc(odd,k) for k in odd};score_sum={k:sc(sums,k) for k in sums};score_span={k:sc(spans,k) for k in spans}
    score_bmask={k:sc(bmask,k) for k in bmask}
    best=(-10**12,None,None); examined=0; eligible=0; t=time.monotonic()
    for c in itertools.combinations(range(1,61),6):
        examined+=1
        # Exhaustive enumeration, with fast exact-one-repeat filter.
        repeated=sum(x in last for x in c)
        if repeated==1:
            eligible+=1
            cnt=Counter(BID[x] for x in c)
            sh=tuple(sorted(cnt.values(),reverse=True))
            rows=Counter((x-1)//10 for x in c)
            rh=tuple(sorted(rows.values(),reverse=True))
            bm=sum(1<<b for b in cnt)
            sm=sum(c)
            val=sum(weights[x] for x in c)+score_shape.get(sh,0)+score_row.get(rh,0)+score_odd.get(sum(x%2 for x in c),0)+score_sum.get((sm//20)*20,0)+score_span.get(((c[-1]-c[0])//10)*10,0)+score_bmask.get(bm,0)
            if val>best[0]:best=(val,c,dict(blockshape=sh,rowshape=rh,blockmask=bm,sum=sm,repeated=tuple(set(c)&last),gaps=tuple(b-a for a,b in zip(c,c[1:]))))
        if examined%250000==0:
            print(f'  {examined:,}/50.063.860 | {examined/50063860:.1%} | elegiveis {eligible:,} | {time.monotonic()-t:.1f}s | melhor {best[1]}',flush=True)
        if limit and examined>=limit:break
    return best,examined,eligible

def pdf(path,draws,stats,best,examined):
    """Apenas apresentacao: volante laranja/azul com marcacoes verdes."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor
    c=canvas.Canvas(str(path),pagesize=A4)
    W,H=A4
    orange=HexColor('#E9913E'); blue=HexColor('#328AC0')
    green=HexColor('#18864A'); ink=HexColor('#463F36')
    c.setFillColor(HexColor('#FFFFFF'));c.rect(0,0,W,H,fill=1,stroke=0)
    # Cabecalho laranja da referencia, sem alterar dados do jogo.
    c.setFillColor(orange);c.roundRect(37,H-112,W-74,70,11,fill=1,stroke=0)
    c.setFillColor(HexColor('#FFFFFF'));c.setFont('Helvetica-Bold',25)
    c.drawCentredString(W/2,H-85,'MEGA-SENA')
    c.setFillColor(ink);c.setFont('Helvetica-Bold',13)
    c.drawCentredString(W/2,H-145,'VOLANTE DIVIDIDO EM 10 BLOCOS')
    c.setFont('Helvetica',10)
    c.drawCentredString(W/2,H-164,'5 blocos superiores + 5 inferiores | 6 dezenas por bloco')
    score,game,meta=best
    chosen=set(game)
    left=40;right=W-40;total_w=right-left;bw=total_w/5
    top=H-194;header=29;cell_h=47;grid_h=header+cell_h*3;gap=22
    for band in range(2):
        yy=top-band*(grid_h+gap)
        for col in range(5):
            idx=band*5+col
            x0=left+col*bw
            c.setFillColor(HexColor('#FCFBF5'))
            c.setStrokeColor(blue);c.setLineWidth(1.6)
            c.rect(x0,yy-grid_h,bw,grid_h,fill=1,stroke=1)
            c.setFillColor(blue);c.rect(x0,yy-header,bw,header,fill=1,stroke=0)
            c.setFillColor(HexColor('#FFFFFF'));c.setFont('Helvetica-Bold',10)
            c.drawCentredString(x0+bw/2,yy-19,f'BLOCO {idx+1}')
            for j,num in enumerate(BLOCKS[idx]):
                row=j//2;column=j%2
                cx=x0+bw*(.29 if column==0 else .71)
                cy=yy-header-cell_h*(row+.5)
                c.setStrokeColor(HexColor('#D6D9D1'));c.setLineWidth(.65)
                c.circle(cx,cy,16,stroke=1,fill=0)
                if num in chosen:
                    c.setFillColor(HexColor('#E2F3E8'));c.circle(cx,cy,16,stroke=0,fill=1)
                    c.setStrokeColor(green);c.setLineWidth(2.7)
                    c.circle(cx,cy,16,stroke=1,fill=0)
                c.setFillColor(green if num in chosen else ink)
                c.setFont('Helvetica-Bold' if num in chosen else 'Helvetica',12)
                c.drawCentredString(cx,cy-4,f'{num:02d}')
    bottom=top-2*grid_h-gap
    c.setFillColor(ink);c.setFont('Helvetica-Bold',11)
    c.drawCentredString(W/2,bottom-28,'JOGO CLASSIFICADO PELO ESTUDO DAS FALHAS')
    c.setFont('Helvetica-Bold',15);c.setFillColor(green)
    c.drawCentredString(W/2,bottom-50,'  -  '.join(f'{n:02d}' for n in game))
    c.setFillColor(ink);c.setFont('Helvetica',9)
    c.drawCentredString(W/2,bottom-70,f'Concursos estudados: {len(draws)} | Ultimo: {draws[-1][0]} | Combinacoes examinadas: {examined:,}')
    c.drawCentredString(W/2,bottom-84,f'Pontuacao: {score} | Repetida: {" ".join(str(x) for x in meta["repeated"])}')
    c.setFont('Helvetica',8);c.setFillColor(HexColor('#666666'))
    c.drawCentredString(W/2,49,'Estudo estatistico de resultados passados; nao aumenta a probabilidade matematica.')
    c.drawCentredString(W/2,36,'Analise e regras identicas a V8. V9 altera somente a apresentacao do PDF.')
    c.save()

def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--arquivo');p.add_argument('--limite-teste',type=int,default=None);a=p.parse_args()
    if a.arquivo:path=a.arquivo
    else:
        try:
            import tkinter as tk
            from tkinter import filedialog
            root=tk.Tk();root.withdraw();path=filedialog.askopenfilename(title='SELECIONE O HISTORICO MEGA-SENA',filetypes=[('Historico TXT/CSV','*.txt *.csv'),('Todos','*.*')]);root.destroy()
        except Exception:path=input('Caminho do arquivo TXT/CSV: ').strip(' "')
    if not path:print('Nenhum arquivo selecionado.');return
    out=Path(__file__).resolve().parent/'RESULTADOS_MEGA_FALHAS_V9';out.mkdir(exist_ok=True)
    draws,bad=load(path);print('Concursos validos:',len(draws),'| linhas rejeitadas:',len(bad),flush=True)
    (out/'LINHAS_REJEITADAS.txt').write_text('\n'.join(f'{i}: {s}' for i,s in bad),encoding='utf-8')
    stats=study(draws,out)
    print('Auditoria gravada:',stats['report'],flush=True)
    best,examined,eligible=search(stats,out,a.limite_teste)
    print('ETAPA 4/4: PDF e resultado',flush=True)
    if best[1] is None:raise RuntimeError('Nenhum jogo elegivel encontrado no intervalo testado.')
    pdf(out/'VOLANTE_MEGA_FALHAS_V9.pdf',draws,stats,best,examined)
    (out/'RESULTADO_V9.txt').write_text('Jogo: '+' '.join(f'{x:02d}' for x in best[1])+'\nScore: '+str(best[0])+'\nCandidatos elegiveis: '+str(eligible)+'\nTotal examinados: '+str(examined)+'\n',encoding='utf-8')
    print('CONCLUIDO:',best[1],'| pasta:',out,flush=True)

if __name__=='__main__':
    try:main()
    except Exception as e:
        import traceback
        traceback.print_exc();sys.exit(1)
