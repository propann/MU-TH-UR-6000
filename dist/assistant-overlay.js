(() => {
  if (window.top !== window.self || document.getElementById('muthur-assistant-host')) return;
  const host = document.createElement('div');
  host.id = 'muthur-assistant-host';
  document.body.appendChild(host);
  const root = host.attachShadow({ mode: 'open' });
  root.innerHTML = `<style>
    :host{all:initial}button,textarea,select{font:inherit}.orb{position:fixed;right:18px;bottom:18px;z-index:2147483600;width:58px;height:58px;border:1px solid #ff3b2f;border-radius:50%;background:radial-gradient(circle,#fff6a0 0 5%,#ff5a2a 11%,#d0140b 30%,#280201 67%);box-shadow:0 0 22px #ff3b2f88;color:transparent;cursor:pointer}.panel{position:fixed;right:18px;bottom:88px;z-index:2147483600;width:min(420px,calc(100vw - 24px));height:min(610px,calc(100vh - 110px));display:none;grid-template-rows:auto auto 1fr auto;background:#030604;color:#c9f5d6;border:1px solid #1d4a2e;box-shadow:0 18px 80px #000;font:13px/1.45 'IBM Plex Mono',Consolas,monospace}.panel.open{display:grid}.head{display:flex;align-items:center;justify-content:space-between;padding:13px 15px;border-bottom:1px solid #143521;color:#3dff7f}.head strong{font-size:17px;letter-spacing:.06em}.head button{background:none;border:0;color:#5c7d67;cursor:pointer}.mode{display:flex;gap:6px;padding:9px 12px;border-bottom:1px solid #143521}.mode button{padding:6px 9px;border:1px solid #143521;background:#07100a;color:#5c7d67;cursor:pointer}.mode .on{border-color:#3dff7f;color:#3dff7f}.log{overflow:auto;padding:13px;display:flex;flex-direction:column;gap:10px}.msg{padding:10px;border:1px solid #143521;background:#07100a;white-space:pre-wrap;overflow-wrap:anywhere}.me{margin-left:28px;border-color:#1d4a2e}.ai{margin-right:28px;border-left:3px solid #3dff7f}.notice{color:#ffb53d}.form{display:block;padding:11px;border-top:1px solid #143521}.form textarea{display:block;width:100%;box-sizing:border-box;min-height:42px;max-height:180px;resize:none;overflow-y:auto;padding:10px 12px;border:1px solid #1d4a2e;border-radius:3px;background:#050b07;color:#c9f5d6;line-height:1.5;white-space:pre-wrap;overflow-wrap:anywhere}.form textarea:focus{outline:1px solid #3dff7f;outline-offset:1px}.small{padding:0 12px 9px;color:#5c7d67;font-size:10px}
    @media(max-width:540px){.orb{right:12px;bottom:12px}.panel{inset:8px;width:auto;height:auto}.panel.open~.orb{display:none}}
  </style><section class="panel" aria-label="Assistant Mistral"><header class="head"><strong>MU-TH-UR // VIBE</strong><button title="Fermer">✕</button></header><div class="mode"><button class="on" data-mode="chat">CHAT</button><button data-mode="edit">ÉDITEUR</button></div><div class="log"><div class="msg ai">Assistant disponible depuis toutes les fenêtres. Le contexte inclut la fenêtre courante et, si Obsidian est activé, des extraits pertinents de tes notes.</div></div><div><label style="display:block;padding:8px 12px;color:#ffb53d"><input type="checkbox" id="vault-context" checked> Utiliser Obsidian · extraits envoyés à Mistral</label><form class="form"><textarea required rows="1" placeholder="Demande à Mistral…"></textarea></form><div class="small">Entrée pour envoyer · Maj + Entrée pour une nouvelle ligne</div></div></section><button class="orb" aria-label="Ouvrir l'assistant Mistral">IA</button>`;
  const panel = root.querySelector('.panel'), orb = root.querySelector('.orb');
  const close = root.querySelector('.head button'), log = root.querySelector('.log');
  const form = root.querySelector('form'), input = root.querySelector('textarea');
  let mode = 'chat';
  const history = JSON.parse(sessionStorage.getItem('muthur-assistant-history') || '[]').slice(-12);
  const add = (kind, text) => { const node=document.createElement('div'); node.className='msg '+kind; node.textContent=text; log.appendChild(node); log.scrollTop=log.scrollHeight; };
  const resizeInput = () => { input.style.height='auto'; input.style.height=`${Math.min(input.scrollHeight,180)}px`; };
  history.forEach(item => add(item.role === 'user' ? 'me' : 'ai', item.content));
  orb.onclick=()=>{panel.classList.add('open');input.focus()}; close.onclick=()=>panel.classList.remove('open');
  root.querySelectorAll('[data-mode]').forEach(button => button.onclick=()=>{
    root.querySelectorAll('[data-mode]').forEach(x=>x.classList.remove('on')); button.classList.add('on'); mode=button.dataset.mode;
    if(mode==='edit') add('notice','Mode éditeur Vibe : les modifications doivent être préparées dans un worktree et confirmées depuis Super IA. Aucun shell arbitraire n’est exposé ici.');
  });
  input.addEventListener('keydown', event => {
    if (event.key !== 'Enter' || event.shiftKey || event.isComposing || event.repeat) return;
    event.preventDefault();
    form.requestSubmit();
  });
  input.addEventListener('input', resizeInput);
  form.onsubmit=async event=>{
    event.preventDefault(); const text=input.value.trim(); if(!text)return; input.value=''; resizeInput(); add('me',text);
    history.push({role:'user',content:text}); input.disabled=true;
    try{
      const context=`Fenêtre: ${document.title}\nChemin: ${location.pathname}\nMode demandé: ${mode}`;
      const messages=[{role:'system',content:'Tu es MU-TH-UR, assistant du cockpit Azoth. Réponds en français. Ne prétends jamais avoir modifié un fichier. En mode éditeur, prépare un plan précis et indique les fichiers à modifier; l’application réelle exige un worktree et une confirmation.'},{role:'system',content:context},...history.slice(-10)];
      const response=await fetch('/ia/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({provider:'mistral',model:'mistral-small-latest',temperature:.3,maxTokens:2048,vaultContext:root.querySelector('#vault-context').checked,messages})});
      const data=await response.json().catch(()=>({})); if(!response.ok)throw new Error(data.error||`HTTP ${response.status}`);
      const answer=String(data.message||'Réponse vide'); add('ai',answer); if(data.sources?.length)add('notice','Sources Obsidian : '+data.sources.join(', ')); history.push({role:'assistant',content:answer});
      sessionStorage.setItem('muthur-assistant-history',JSON.stringify(history.slice(-12)));
    }catch(error){add('notice',`Assistant indisponible : ${error.message}`)}finally{input.disabled=false;input.focus()}
  };
  resizeInput();
})();
