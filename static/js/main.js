// Menu mobile — abre/fecha a navegação em telas pequenas.
document.addEventListener("DOMContentLoaded", function () {
  var botao = document.getElementById("navToggle");
  var nav = document.getElementById("navPrincipal");

  if (!botao || !nav) return;

  botao.addEventListener("click", function () {
    var aberto = nav.classList.toggle("aberto");
    botao.setAttribute("aria-expanded", aberto ? "true" : "false");
  });

  nav.querySelectorAll("a").forEach(function (link) {
    link.addEventListener("click", function () {
      nav.classList.remove("aberto");
      botao.setAttribute("aria-expanded", "false");
    });
  });
});
