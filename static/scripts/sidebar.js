// sidebar toggle
console.log('clikkkkk******************')
const btnToggle = document.querySelector('.toggle-btn');
console.log('clikkkkk')
btnToggle.addEventListener('click', function () {
  console.log('clik')
  document.getElementById('sidebar').classList.toggle('active');
  console.log(document.getElementById('sidebar'))
});
