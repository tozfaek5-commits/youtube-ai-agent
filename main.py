async function generate(){
  const topic=document.getElementById('topic').value;
  const btn=document.querySelector('button');
  const res=document.getElementById('result');
  btn.innerText='⏳ جاري توليد 6 مشاهد... (دقيقتين)'; btn.disabled=true;
  res.style.display='block'; res.innerHTML='⏳ يتم توليد الصوت والصور... لا تغلق الصفحة';
  try{
    const r=await fetch('/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topic})});
    const text = await r.text(); // نقرأ كنص أولاً
    try {
      const data=JSON.parse(text);
      if(data.success){res.innerHTML=`✅ تم!<br><br>🎬 <a href="${data.url}" target="_blank">${data.url}</a>`; btn.innerText='✅ تم بنجاح';}
      else{res.innerHTML='❌ خطأ من السيرفر:<br>'+data.error; btn.innerText='حاول مرة أخرى';}
    } catch {
      // لو السيرفر لم يرد JSON، نعرض ما رده فعلاً
      res.innerHTML='❌ السيرفر لا يعمل (Deploy Failed):<br><pre style="white-space:pre-wrap">'+text.substring(0,500)+'</pre>'; 
      btn.innerText='حاول مرة أخرى';
    }
  }catch(e){res.innerHTML='❌ فشل الاتصال: '+e; btn.innerText='حاول مرة أخرى';}
  btn.disabled=false;
}
