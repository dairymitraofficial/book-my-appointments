function showTab(id) {
  document.querySelectorAll('.tab-content')
    .forEach(el => el.style.display = 'none');

  document.getElementById(id).style.display = 'grid';

  document.querySelectorAll('.tab')
    .forEach(t => t.classList.remove('active'));

  event.target.classList.add('active');
}
