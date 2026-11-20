// Инициализация всех тултипов на странице
document.addEventListener('DOMContentLoaded', function () {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Для роута скачивания документов
// Если искомых документов нет, возвращаем сообщение о необходимости сгенерировать их
document.getElementById('download-btn').addEventListener('click', async (e) => {
  e.preventDefault();                       // приказывает остаться на той же странице

  const btn = e.currentTarget;
  const errBox = document.getElementById('download-error');
  errBox.classList.add('d-none');

  btn.disabled = true;
  try {
    const resp = await fetch(btn.href, { credentials: 'same-origin' });

    if (!resp.ok) {
      // 404/403/500 — показываем detail из JSON
      let msg = `Ошибка ${resp.status}`;
      try {
        const data = await resp.json();
        if (data.detail) msg = data.detail;
      } catch {}
      errBox.textContent = msg;
      errBox.classList.remove('d-none');
      return;                               // ← остаёмся на странице
    }

    // Успех — превращаем ответ в файл и запускаем скачивание
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;

    // имя файла из Content-Disposition
    const cd = resp.headers.get('Content-Disposition') || '';
    const m = cd.match(/filename\*=UTF-8''([^;]+)/)
           || cd.match(/filename="?([^";]+)"?/);
    a.download = m ? decodeURIComponent(m[1]) : 'documents.zip';

    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } catch (err) {
    errBox.textContent = 'Ошибка сети: ' + err.message;
    errBox.classList.remove('d-none');
  } finally {
    btn.disabled = false;
  }
});
