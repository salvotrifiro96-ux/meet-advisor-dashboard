// popup.js — minimal status display in the extension popup.

(async function init() {
  const dot = document.getElementById("dot");
  const label = document.getElementById("label");

  try {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    const tab = tabs[0];
    const isMeet = tab?.url?.startsWith("https://meet.google.com/");

    if (!isMeet) {
      label.textContent = "Apri un link Meet per attivare il tracking";
      return;
    }

    const url = new URL(tab.url);
    const code = url.pathname.replace(/^\//, "").split("/")[0];
    if (!/^[a-z]{3}-[a-z]{4}-[a-z]{3}$/.test(code)) {
      label.textContent = "Pagina Meet non valida";
      return;
    }

    label.textContent = `Tab aperta su: ${code}`;
    dot.classList.add("live");
  } catch (err) {
    label.textContent = "Errore nel leggere lo stato";
    console.error(err);
  }
})();
