/* Sign-in for the temporary review gate. The password is checked on the server;
 * this page only sends it once over HTTPS and never stores it. */
"use strict";

const form = document.getElementById("login");
const input = document.getElementById("password");
const error = document.getElementById("login-error");
const button = document.getElementById("submit");
input.focus();

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!input.value) { error.textContent = "Enter the password."; input.focus(); return; }
  button.disabled = true;
  error.textContent = "";
  let res = null;
  let data = null;
  try {
    res = await fetch("/api/login", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: input.value }), credentials: "same-origin" });
    data = await res.json();
  } catch (err) {
    data = { error: "The server could not be reached." };
  }
  if (res && res.ok) { location.replace("/"); return; }
  input.value = "";
  button.disabled = false;
  error.textContent = (data && data.error) || "Sign-in failed.";
  input.focus();
});
