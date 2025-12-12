// JS para mejorar el inline de jugadores en el admin:
// - Cambia el checkbox de DELETE por un botón Eliminar / Cancelar
// - Marca la fila en rojo cuando está marcada para eliminar

document.addEventListener("DOMContentLoaded", function () {
  // Cambiar encabezado "Eliminar?" por "Eliminar"
  document.querySelectorAll(".inline-group th.delete").forEach(function (th) {
    th.textContent = "Eliminar";
  });

  // Para cada checkbox de DELETE creamos un botón
  document.querySelectorAll(".inline-group td.delete").forEach(function (td) {
    const checkbox = td.querySelector('input[type="checkbox"]');
    if (!checkbox) return;

    // Ocultamos el checkbox
    checkbox.style.display = "none";

    // Creamos el botón
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "button-delete-inline";
    btn.textContent = "Eliminar";
    td.appendChild(btn);

    const row = td.closest("tr");

    function sync() {
      if (!row) return;
      if (checkbox.checked) {
        row.classList.add("row-marked-delete");
        btn.textContent = "Cancelar";
      } else {
        row.classList.remove("row-marked-delete");
        btn.textContent = "Eliminar";
      }
    }

    btn.addEventListener("click", function (e) {
      e.preventDefault();
      checkbox.checked = !checkbox.checked;
      sync();
    });

    // Estado inicial (por si viene marcado después de un POST con errores)
    sync();
  });
});
