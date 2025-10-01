  const form = document.getElementById("uploadForm");
  const responseBox = document.getElementById("responseContent");

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      responseBox.innerHTML = "Enviando...";

      const fileInput = document.getElementById("fileInput");
      if (!fileInput.files.length) { responseBox.innerText = "Selecione um arquivo."; return; }
      const formData = new FormData();
      formData.append("file", fileInput.files[0]);

      try {
        const res = await fetch("/upload", { method: "POST", body: formData });
        const data = await res.json();

        document.getElementById("processingMode").textContent = data.mode;


        if (data.error) {
          responseBox.innerHTML = `<strong>Erro:</strong> ${data.error}`;
          return;
        }

        responseBox.innerHTML = ""; // limpa
        data.emails.forEach((email, idx) => {
          const box = document.createElement("div");
          box.className = "email-box " + (email.css_class || "indefinido");
          box.innerHTML = `
            <h3>Email ${idx + 1}</h3>
            <p><strong>Assunto:</strong> ${email.assunto || "(sem assunto)"}</p>
            <p><strong>Mensagem:</strong> <pre style="white-space:pre-wrap">${email.mensagem || "(vazia)"}</pre></p>
            <p><strong>Classificação:</strong> ${email.classificacao}</p>
            <p><strong>Resposta:</strong> ${email.resposta}</p>
          `;
          responseBox.appendChild(box);
        });

      } catch (err) {
        console.error(err);
        responseBox.innerHTML = "Erro ao conectar com o servidor.";
      }

      
    });

  const fileInput = document.getElementById('fileInput');
  const fileNameDisplay = document.getElementById('fileNameDisplay');

  fileInput.addEventListener('change', function() {
    if (this.files && this.files.length > 0) {
        fileNameDisplay.textContent = this.files[0].name; // Mostra o nome do arquivo selecionado
    } else {
        fileNameDisplay.textContent = 'Nenhum arquivo escolhido'; // Volta ao texto padrão se nada for selecionado
    }
  });