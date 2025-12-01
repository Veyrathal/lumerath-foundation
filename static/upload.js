(function () {
  const dz = document.getElementById("dropzone");
  const form = document.getElementById("uploadForm");
  const codexInput = document.getElementById("codexFile");
  const imgInput = document.getElementById("imageFile");
  const log = document.getElementById("uploadLog");

  function logLine(msg, ok=true){
    const li = document.createElement("li");
    li.textContent = msg;
    li.style.color = ok ? "inherit" : "crimson";
    log.prepend(li);
  }

  async function sendPair(codexFile, imageFile){
    const fd = new FormData();
    if (codexFile) fd.append("codex", codexFile);
    if (imageFile) fd.append("image", imageFile);

    const r = await fetch("/upload", { method: "POST", body: fd });
    const j = await r.json();
    if (!r.ok) throw new Error(j.error || "Upload failed");
    logLine(`✔ ${j.message} — ${JSON.stringify(j.saved)}`);
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await sendPair(codexInput.files[0] || null, imgInput.files[0] || null);
      codexInput.value = ""; imgInput.value = "";
      setTimeout(() => location.reload(), 400); // refresh list
    } catch (err) {
      logLine(`✖ ${err.message}`, false);
    }
  });

  ;["dragenter","dragover"].forEach(ev =>
    dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.add("is-over"); })
  );
  ;["dragleave","drop"].forEach(ev =>
    dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.remove("is-over"); })
  );

  dz.addEventListener("drop", async (e) => {
    const files = [...e.dataTransfer.files];
    // pick a .json and an image if present
    const codex = files.find(f => f.name.toLowerCase().endsWith(".json")) || null;
    const image = files.find(f => /\.(png|jpg|jpeg|webp)$/i.test(f.name)) || null;
    if (!codex && !image) return logLine("No valid files in drop.", false);

    try {
      await sendPair(codex, image);
      setTimeout(() => location.reload(), 400);
    } catch (err) {
      logLine(`✖ ${err.message}`, false);
    }
  });
})();
