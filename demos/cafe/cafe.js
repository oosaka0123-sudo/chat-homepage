(()=>{
document.documentElement.classList.add('js-ready');
const header=document.querySelector('[data-header]');
const toggle=document.querySelector('.menu-toggle');
const closeBtn=document.querySelector('[data-overlay-close]');
const menu=document.querySelector('.overlay-menu');
const video=document.querySelector('[data-overlay-video]');
const sectionNo=document.querySelector('[data-section-no]');
const sectionName=document.querySelector('[data-section-name]');
const progress=document.querySelector('[data-scroll-progress]');
const main=document.querySelector('main');
const footer=document.querySelector('footer');
const demoBar=document.querySelector('.demo-bar');
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
let videoUrl='';
let loadingVideo=null;

const setHeader=()=>header?.classList.toggle('is-scrolled',scrollY>48);
const setProgress=()=>{const max=Math.max(1,document.documentElement.scrollHeight-innerHeight);const pct=Math.min(100,Math.max(0,scrollY/max*100));if(progress)progress.style.height=pct+'%'};
const setInert=v=>[header,main,footer,demoBar].forEach(el=>{if(el)el.inert=v});

async function ensureVideo(){
  if(!video||reduced.matches)return;
  if(video.dataset.ready==='true'){
    try{await video.play();menu?.classList.add('is-video-ready')}catch{}
    return;
  }
  if(loadingVideo)return loadingVideo;
  loadingVideo=(async()=>{
    try{
      const urls=Array.from({length:6},(_,i)=>'cafe-overlay.part'+i+'.b64');
      const parts=await Promise.all(urls.map(async url=>{const res=await fetch(url,{cache:'force-cache'});if(!res.ok)throw new Error('overlay asset '+res.status);return res.text()}));
      const raw=atob(parts.join('').replace(/\s+/g,''));
      const bytes=new Uint8Array(raw.length);
      for(let i=0;i<raw.length;i++)bytes[i]=raw.charCodeAt(i);
      videoUrl=URL.createObjectURL(new Blob([bytes],{type:'video/mp4'}));
      video.src=videoUrl;
      video.dataset.ready='true';
      await video.play();
      menu?.classList.add('is-video-ready');
    }catch(err){
      console.warn('Cafe overlay video unavailable',err);
    }finally{loadingVideo=null}
  })();
  return loadingVideo;
}
function openMenu(){
  if(!menu||!toggle)return;
  menu.classList.add('is-open');
  menu.setAttribute('aria-hidden','false');
  toggle.setAttribute('aria-expanded','true');
  document.documentElement.classList.add('menu-open');
  document.body.classList.add('menu-open');
  setInert(true);
  (closeBtn||menu.querySelector('a'))?.focus();
  if(!reduced.matches)ensureVideo();
}
function closeMenu(restore=true){
  if(!menu||!toggle)return;
  menu.classList.remove('is-open','is-video-ready');
  menu.setAttribute('aria-hidden','true');
  toggle.setAttribute('aria-expanded','false');
  document.documentElement.classList.remove('menu-open');
  document.body.classList.remove('menu-open');
  video?.pause();
  setInert(false);
  if(restore)toggle.focus();
}
toggle?.addEventListener('click',openMenu);
closeBtn?.addEventListener('click',()=>closeMenu(true));
menu?.querySelectorAll('.overlay-links a,.overlay-meta a').forEach(a=>a.addEventListener('click',()=>closeMenu(false)));
document.addEventListener('keydown',e=>{
  if(toggle?.getAttribute('aria-expanded')!=='true')return;
  if(e.key==='Escape'){e.preventDefault();closeMenu(true);return}
  if(e.key!=='Tab')return;
  const items=[closeBtn,...menu.querySelectorAll('a[href],button:not([disabled])')].filter(Boolean).filter(el=>!el.inert&&getComputedStyle(el).visibility!=='hidden');
  if(!items.length)return;
  const first=items[0],last=items[items.length-1];
  if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}
  else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}
});
reduced.addEventListener?.('change',e=>{if(e.matches){video?.pause();menu?.classList.remove('is-video-ready')}else if(menu?.classList.contains('is-open'))ensureVideo()});
addEventListener('scroll',()=>{setHeader();setProgress()},{passive:true});
setHeader();setProgress();

const sections=[...document.querySelectorAll('[data-section]')];
if('IntersectionObserver'in window){
  const sectionObserver=new IntersectionObserver(entries=>{for(const e of entries){if(e.isIntersecting){if(sectionNo)sectionNo.textContent=e.target.dataset.section||'01';if(sectionName)sectionName.textContent=e.target.dataset.sectionName||''}}},{rootMargin:'-34% 0px -56% 0px',threshold:0});
  sections.forEach(el=>sectionObserver.observe(el));
  if(!reduced.matches){
    const revealObserver=new IntersectionObserver(entries=>{for(const e of entries){if(e.isIntersecting){e.target.classList.add('is-visible');revealObserver.unobserve(e.target)}}},{rootMargin:'0px 0px -8% 0px',threshold:.08});
    document.querySelectorAll('.reveal,.reveal-title').forEach(el=>revealObserver.observe(el));
  }else document.querySelectorAll('.reveal,.reveal-title').forEach(el=>el.classList.add('is-visible'));
}else document.querySelectorAll('.reveal,.reveal-title').forEach(el=>el.classList.add('is-visible'));

addEventListener('pagehide',()=>{if(videoUrl)URL.revokeObjectURL(videoUrl)},{once:true});
})();