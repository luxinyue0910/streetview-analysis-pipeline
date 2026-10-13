let sample, labels = {}, index = 0, queue = Promise.resolve(), failed = false;
const $ = id => document.getElementById(id);
const labelFor = p => labels[p.id] || {selected: [], status: 'draft', note: ''};
const statusName = s => ({confirmed:'已确认', needs_review:'待复核', draft:'草稿'}[s] || '未标注');
function error(message) { $('error').textContent = message; $('error').hidden = !message; }
function updateProgress() {
  const confirmed = sample.points.filter(p => labels[p.id]?.status === 'confirmed').length;
  const review = sample.points.filter(p => labels[p.id]?.status === 'needs_review').length;
  $('progress').textContent = `明确 ${confirmed} / ${sample.points.length} · 勉强选择 ${review} · 未完成 ${sample.points.length-confirmed-review}`;
  $('progressBar').style.width = `${(confirmed+review)/sample.points.length*100}%`;
  for (const [i,p] of sample.points.entries()) $('jump').options[i].textContent = `${String(i+1).padStart(2,'0')} · ${p.road_level}级 · ${statusName(labels[p.id]?.status)}`;
}
function render() {
  const p = sample.points[index], l = labelFor(p);
  $('position').textContent = `点位 ${String(index+1).padStart(2,'0')} / ${sample.points.length}`;
  $('pointTitle').textContent = p.point_id.replace('_', '，');
  $('pointMeta').textContent = `${p.road_level}级道路 · 中心点位 · ${statusName(labels[p.id]?.status)}`;
  $('jump').value = index; $('note').value = l.note;
  $('prev').disabled = index === 0; $('next').disabled = index === sample.points.length-1;
  $('confirm').disabled = l.selected.length !== 2 || failed;
  $('swap').disabled = l.selected.length !== 2; $('review').disabled = l.selected.length !== 2 || failed;
  $('selectionStatus').textContent = `已选 ${l.selected.length} / 2`;
  $('cards').replaceChildren();
  p.images.forEach((im,i) => {
    const slot = l.selected.indexOf(im.angle), card = document.createElement('article');
    card.className = `card${slot >= 0 ? ' selected' : ''}`;
    card.innerHTML = `<div class="card-top"><span>${im.angle}°</span><span class="badge">${slot>=0 ? 'side_'+(slot===0?'a':'b') : '未选择'}</span></div><button class="image-button" aria-label="选择 ${im.angle} 度图片" aria-pressed="${slot>=0}"><img src="${im.url}" alt="${im.angle} 度街景"></button><div class="card-bottom"><button class="pick">${slot>=0?'取消选择':'选择照片'} · ${i+1}</button><button class="quiet zoom-btn">放大</button></div>`;
    card.querySelector('.image-button').onclick = card.querySelector('.pick').onclick = () => toggle(im.angle);
    card.querySelector('img').onerror = () => error('图片读取失败，请刷新页面；不要确认缺图点位。');
    card.querySelector('.zoom-btn').onclick = () => { $('zoomImage').src=im.url; $('zoomTitle').textContent=`${p.point_id} · ${im.angle}°`; $('zoom').showModal(); };
    $('cards').append(card);
  });
  updateProgress();
}
function persist(p) {
  const body = JSON.stringify({id:p.id,...labelFor(p)});
  $('saveState').textContent='正在保存…';
  queue = queue.catch(() => {}).then(async () => {
    try {
      const res=await fetch('/api/label',{method:'POST',headers:{'Content-Type':'application/json'},body});
      if(!res.ok) throw new Error(await res.text());
      failed=false; $('saveState').textContent='已保存到本地'; error('');
      $('confirm').disabled=labelFor(sample.points[index]).selected.length!==2; $('review').disabled=$('confirm').disabled;
    } catch(e) {
      failed=true; $('saveState').textContent='保存失败'; $('confirm').disabled=true; $('review').disabled=true;
      error('保存失败，请保持页面打开并重试操作。'+e.message);
      throw e;
    }
  });
  queue.catch(() => {});
  return queue;
}
function toggle(angle) {
  const p=sample.points[index], l=labelFor(p), selected=[...l.selected];
  const pos=selected.indexOf(angle);
  if(pos>=0) selected.splice(pos,1);
  else if(selected.length<2) selected.push(angle);
  else { error('已经选了两张，请先取消其中一张再替换。'); return; }
  labels[p.id]={...l,selected,status:'draft'}; render(); persist(p);
}
async function go(target) {
  try { await queue; index=Math.max(0,Math.min(sample.points.length-1,target)); render(); } catch(e) {}
}
async function finish(status) {
  const p=sample.points[index], l=labelFor(p);
  if(l.selected.length!==2) return;
  labels[p.id]={...l,status}; render();
  try { await persist(p); if(index<sample.points.length-1) {index++;render();} else {render();$('selectionStatus').textContent='已到最后一个点位，可检查进度并导出 CSV。';} } catch(e) {}
}
$('prev').onclick=()=>go(index-1); $('next').onclick=()=>go(index+1);
$('jump').onchange=e=>go(Number(e.target.value));
$('confirm').onclick=()=>finish('confirmed'); $('review').onclick=()=>finish('needs_review');
$('clear').onclick=()=>{const p=sample.points[index];labels[p.id]={...labelFor(p),selected:[],status:'draft'};render();persist(p);};
$('swap').onclick=()=>{const p=sample.points[index],l=labelFor(p);labels[p.id]={...l,selected:[...l.selected].reverse(),status:'draft'};render();persist(p);};
$('note').oninput=e=>{const p=sample.points[index];labels[p.id]={...labelFor(p),note:e.target.value};persist(p);};
$('closeZoom').onclick=()=>$('zoom').close();
document.addEventListener('keydown',e=>{
  if(!sample || $('zoom').open || ['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName))return;
  if(['1','2','3','4'].includes(e.key)){e.preventDefault();toggle(sample.points[index].images[Number(e.key)-1].angle);}
  if(e.key==='ArrowLeft')go(index-1);if(e.key==='ArrowRight')go(index+1);
  if(e.key==='Enter' && !$('confirm').disabled){e.preventDefault();finish('confirmed');}
});
(async()=>{try{
  const res=await fetch('/api/state');if(!res.ok)throw new Error('读取失败');
  const data=await res.json();sample=data.sample;labels=data.labels;
  sample.points.forEach((p,i)=>{const o=document.createElement('option');o.value=i;$('jump').append(o);});
  const first=sample.points.findIndex(p=>labels[p.id]?.status!=='confirmed' && labels[p.id]?.status!=='needs_review');index=first<0?0:first;
  render();$('saveState').textContent='进度已读取 · 本地保存';
}catch(e){error('无法加载标注数据：'+e.message);}})();
