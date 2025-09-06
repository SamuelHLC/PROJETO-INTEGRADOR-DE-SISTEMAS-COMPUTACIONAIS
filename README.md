

## Guia para Testar o Projeto do Chat

Este guia descreve os passos necessários para configurar e executar o projeto do chat em um ambiente local, permitindo que você teste todas as suas funcionalidades.

### Pré-requisitos

Antes de começar, certifique-se de que você tem o seguinte instalado em seu computador:

  * **Python 3:** Recomendado ter a versão 3.6 ou superior.
  * **Git:** Para clonar o repositório do projeto.

### Passos para Executar o Projeto

1.  **Clonar o Repositório:**
    Abra o seu terminal ou prompt de comando e navegue até o local onde você deseja salvar o projeto. Em seguida, clone o repositório usando o seguinte comando:

    ```bash
    git clone [URL_DO_SEU_REPOSITORIO]
    ```

    *Substitua `[URL_DO_SEU_REPOSITORIO]` pela URL que você obteve do GitHub.*

2.  **Navegar até a Pasta do Projeto:**
    Após clonar o repositório, entre na pasta do projeto. Se a pasta principal se chama `atividade_2`, o comando seria:

    ```bash
    cd atividade_2
    ```

3.  **Instalar as Dependências:**
    O projeto utiliza algumas bibliotecas Python. Para instalá-las, você precisará criar um ambiente virtual (recomendado) e depois instalar as dependências.

      * **Criar um ambiente virtual (recomendado):**

        ```bash
        python -m venv venv
        ```

        *No Windows, ative-o com `venv\Scripts\activate`. No macOS/Linux, use `source venv/bin/activate`.*

      * **Instalar as bibliotecas:**
        Com o ambiente virtual ativado, instale as dependências com o Pip:

        ```bash
        pip install -r requirements.txt
        ```

        *Se você não criou um `requirements.txt` previamente, você precisará instalar manualmente as bibliotecas necessárias:*

        ```bash
        pip install Flask Flask-SocketIO python-dotenv # Adicione outras se houver
        ```

        *Nota: O seu código atual já inclui `Flask` e `Flask-SocketIO`. Se você não gerou um `requirements.txt`, pode instalar manualmente como mostrado acima.*

4.  **Executar o Servidor:**
    Agora, você pode iniciar o servidor Python. Certifique-se de estar na pasta raiz do projeto (onde está o arquivo `app.py`).

    ```bash
    python app.py
    ```

    O terminal exibirá uma mensagem indicando que o servidor está rodando, geralmente em `http://127.0.0.1:5000/` ou `http://0.0.0.0:5000/`.

5.  **Testar o Projeto:**
    Abra o seu navegador web e acesse o endereço fornecido pelo servidor (geralmente `http://127.0.0.1:5000/`). A partir daí, o professor poderá:

      * Clicar em **Registrar** para criar uma nova conta.
      * Fazer **Login** com a conta criada.
      * Visualizar a lista de **Salas** e criar novas salas.
      * Clicar em uma sala para **entrar no chat**.
      * Enviar **mensagens de texto**.
      * Enviar **imagens** clicando no ícone de imagem ao lado do campo de texto.
      * Testar a funcionalidade de **emojis**.

### Resolução de Problemas Comuns

  * **Erro `sqlite3.OperationalError: no such column: m.tipo`:** Este erro indica que o banco de dados não foi atualizado com a nova coluna `tipo` na tabela `mensagens`. Para resolver, delete o arquivo `chat_database.db` na pasta do projeto e execute `python app.py` novamente. O banco de dados será recriado com a estrutura correta.
  * **Erro ao enviar imagens:** Verifique se a pasta `static/uploads` foi criada corretamente dentro da estrutura do projeto. Se não, crie-a manualmente. Certifique-se também de que o arquivo `app.py` foi atualizado com as novas rotas e funcionalidades para upload.
  * **Erro de `ImportError`:** Certifique-se de ter instalado todas as dependências listadas no `requirements.txt` ou instaladas manualmente com `pip install`.

