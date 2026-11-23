import io
import zipfile
import pandas as pd
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from PIL import Image, ImageDraw, ImageFont
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'uma_chave_secreta_muito_segura'  # Necessário para mensagens flash

# ===== Configurações de posição (ajuste conforme seu template) =====
POSICAO_NOME = 550
POSICAO_CURSO = 680
POSICAO_CARGA = 740
POSICAO_DATA = 800
TAMANHO_FONTE_NOME = 80
TAMANHO_FONTE_TEXTO = 40
COR_TEXTO = (30, 30, 30)
# =================================================================

def gerar_certificados(planilha_file, template_file, fonte_file):
    """Gera PDFs em memória e retorna um buffer ZIP."""
    df = pd.read_excel(planilha_file)
    template_img = Image.open(template_file).convert("RGB")
    
    # Salva a fonte temporariamente para o Pillow poder usá-la
    fonte_bytes = fonte_file.read()
    fonte_path = "/tmp/fonte_web.ttf"
    with open(fonte_path, "wb") as f:
        f.write(fonte_bytes)
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for _, linha in df.iterrows():
            img = template_img.copy()
            draw = ImageDraw.Draw(img)
            fn = ImageFont.truetype(fonte_path, TAMANHO_FONTE_NOME)
            ft = ImageFont.truetype(fonte_path, TAMANHO_FONTE_TEXTO)
            w = img.size[0]

            def centro(txt, y, fonte):
                b = draw.textbbox((0, 0), str(txt), font=fonte)
                draw.text(((w - (b[2] - b[0])) // 2, y), str(txt), font=fonte, fill=COR_TEXTO)

            centro(linha["Nome"], POSICAO_NOME, fn)
            centro(f'Curso: {linha["Curso"]}', POSICAO_CURSO, ft)
            centro(f'Carga Horária: {linha["Carga Horaria"]}', POSICAO_CARGA, ft)
            centro(f'Data: {linha["Data"]}', POSICAO_DATA, ft)

            # Salva o PDF em memória e adiciona ao ZIP
            pdf_bytes = io.BytesIO()
            img.save(pdf_bytes, "PDF", resolution=150.0)
            
            nome_arquivo = secure_filename(str(linha["Nome"])) + ".pdf"
            zf.writestr(nome_arquivo, pdf_bytes.getvalue())
    
    zip_buffer.seek(0)
    return zip_buffer

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Verifica se todos os arquivos foram enviados
        if 'planilha' not in request.files or 'template' not in request.files or 'fonte' not in request.files:
            flash('Por favor, envie todos os três arquivos.')
            return redirect(request.url)
        
        planilha = request.files['planilha']
        template = request.files['template']
        fonte = request.files['fonte']
        
        if planilha.filename == '' or template.filename == '' or fonte.filename == '':
            flash('Nenhum arquivo selecionado.')
            return redirect(request.url)
        
        try:
            zip_buffer = gerar_certificados(planilha, template, fonte)
            return send_file(
                zip_buffer,
                mimetype='application/zip',
                as_attachment=True,
                download_name='certificados.zip'
            )
        except Exception as e:
            flash(f'Erro ao gerar certificados: {e}')
            return redirect(request.url)
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)