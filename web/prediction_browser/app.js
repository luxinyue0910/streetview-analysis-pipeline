let sample, predictions, index=0;
const $=id=>document.getElementById(id);
function zoom(p,im){$('zoomImage').src=im.url;$('zoomTitle').textContent=`${p.point_id} · ${im.angle}°`;$('zoom').showModal();}
function render(){
  const p=sample.points[index],selected=predictions[p.id].predicted;
  $('progress').textContent=`浏览第 ${index+1} / ${sample.points.length} 个点位`;
  $('position').textContent=`点位 ${String(index+1).padStart(2,'0')} / ${sample.points.length}`;
  $('pointTitle').textContent=p.point_id.replace('_','，');$('pointMeta').textContent=`${p.road_level}级道路 · 模型自动选择 · 未标记待复核`;
  $('jump').value=index;$('prev').disabled=index===0;$('next').disabled=index===sample.points.length-1;
  $('pairText').textContent=`模型保留：${selected.join('° / ')}°`;$('cards').replaceChildren();
  for(const im of p.images){
    const slot=selected.indexOf(im.angle),card=document.createElement('article');card.className='card'+(slot>=0?' selected':'');
    card.innerHTML=`<div class="card-top"><span>${im.angle}°</span><span class="badge">${slot>=0?'模型保留 · side_'+(slot===0?'a':'b'):'模型未选'}</span></div><button class="image-button" aria-label="放大 ${im.angle} 度图片"><img src="${im.url}" alt="${im.angle} 度街景"></button><div class="card-bottom"><button class="quiet">放大原图</button></div>`;
    card.querySelector('.image-button').onclick=card.querySelector('.quiet').onclick=()=>zoom(p,im);
    $('cards').append(card);
  }
}
function go(i){index=Math.max(0,Math.min(sample.points.length-1,i));render();}
$('prev').onclick=()=>go(index-1);$('next').onclick=()=>go(index+1);$('jump').onchange=e=>go(Number(e.target.value));$('closeZoom').onclick=()=>$('zoom').close();
document.addEventListener('keydown',e=>{if(!sample||$('zoom').open||document.activeElement.tagName==='SELECT')return;if(e.key==='ArrowLeft')go(index-1);if(e.key==='ArrowRight')go(index+1);});
(async()=>{try{
  const [stateRes,predRes]=await Promise.all([fetch('/api/state'),fetch('/api/predictions')]);
  if(!stateRes.ok||!predRes.ok)throw new Error('读取失败');
  const state=await stateRes.json(),data=await predRes.json();sample=state.sample;
  if(data.sample_id!==sample.sample_id)throw new Error('预测与样本不匹配');
  predictions=Object.fromEntries(data.predictions.map(p=>[p.id,p]));
  sample.points.forEach((p,i)=>{const option=document.createElement('option');option.value=i;option.textContent=`${i+1} · ${p.road_level}级 · ${predictions[p.id].predicted.join('/')}`;$('jump').append(option);});render();
}catch(e){$('error').hidden=false;$('error').textContent='无法加载模型结果：'+e.message;}})();
