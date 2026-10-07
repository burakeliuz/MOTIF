/* "Download brief (PDF)": fetches the PDF the server renders from this session's result
 * (GET /api/sessions/<id>/brief.pdf, behind the review gate; no Qloo or LLM request) and
 * saves it as a real .pdf file. Shows a short busy state and a plain error when it fails. */
"use strict";

const MotifDownload = (() => {
  const LABEL = "Download brief (PDF)";

  function fileName(response, fallback) {
    const m = /filename="([^"]+)"/.exec(response.headers.get("Content-Disposition") || "");
    return m ? m[1] : fallback;
  }

  async function brief(id, button, status) {
    if (button.disabled) return;
    button.disabled = true;
    button.setAttribute("aria-busy", "true");
    button.textContent = "Preparing PDF…";
    status.textContent = "";
    status.className = "dlstatus";
    try {
      const response = await fetch("/api/sessions/" + encodeURIComponent(id) + "/brief.pdf", { credentials: "same-origin" });
      if (!response.ok) {
        let message = "The PDF could not be prepared. Please try again.";
        if (response.status === 401) message = "Your sign-in has expired. Sign in again, then download the brief.";
        else {
          try { const body = await response.json(); if (body && body.error) message = body.error; } catch (_) { /* keep the default */ }
        }
        throw new Error(message);
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = fileName(response, "MOTIF-Brief.pdf");
      document.body.append(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 10000);
      status.textContent = "Downloaded " + link.download + ".";
    } catch (err) {
      status.className = "dlstatus error";
      status.setAttribute("role", "alert");
      status.textContent = err instanceof TypeError ? "The PDF could not be downloaded: the connection failed. Please try again." : err.message;
    } finally {
      button.disabled = false;
      button.removeAttribute("aria-busy");
      button.textContent = LABEL;
    }
  }

  return { brief, LABEL };
})();
