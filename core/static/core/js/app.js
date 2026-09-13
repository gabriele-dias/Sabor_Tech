document.addEventListener('DOMContentLoaded', function(){
  const loginBtn = document.getElementById('loginBtn')
  const modal = document.getElementById('loginModal')
  const close = document.getElementById('closeModal')
  const sendCode = document.getElementById('sendCode')
  const twofa = document.getElementById('twofa')
  const confirm = document.getElementById('confirmLogin')

  if(loginBtn){loginBtn.addEventListener('click', ()=>{modal.setAttribute('aria-hidden','false')})}
  if(close){close.addEventListener('click', ()=>{modal.setAttribute('aria-hidden','true'); twofa.style.display='none'})}
  if(sendCode){sendCode.addEventListener('click', ()=>{ twofa.style.display='block'; alert('Código 2FA enviado (simulado)') })}
  if(confirm){confirm.addEventListener('click', ()=>{ modal.setAttribute('aria-hidden','true'); twofa.style.display='none'; alert('Login confirmado (simulado)') })}
})
