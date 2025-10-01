# Entrar na pasta do projeto
cd "D:\Atividades Concluidas\ProjetoAlexandre\projeto_fitness"

# Criar o ambiente virtual
python -m venv venv

# Ativar o venv no PowerShell
.\venv\Scripts\Activate.ps1

# Permitir execução de scripts caso dê erro (uma única vez)
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# Instalar todas as dependências de uma vez
pip install Flask Flask-SQLAlchemy Flask-WTF Flask-Login Flask-Bcrypt email_validator

# Rodar o app
python app.py
