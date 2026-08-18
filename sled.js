(function(){
  try{
    var COOKIE='ta_ref';
    var DAYS=90;
    var CLICK="https://usesled.com/kerr-and-company/api/click";
    var qs=new URLSearchParams(window.location.search);
    var ref=qs.get('ref');
    function get(n){var m=document.cookie.match('(^|;)\\s*'+n+'\\s*=\\s*([^;]+)');return m?decodeURIComponent(m[2]):null;}
    function set(n,v,d){var e=new Date(Date.now()+d*864e5).toUTCString();document.cookie=n+'='+encodeURIComponent(v)+';expires='+e+';path=/;SameSite=Lax';}
    var existing=get(COOKIE);
    if(ref){
      if(ref!==existing) set(COOKIE,ref,DAYS);
      existing=ref;
      var img=new Image();
      img.src=CLICK+'?ref='+encodeURIComponent(ref)+'&t='+Date.now();
    }
    window.sled={ref:existing,tenant:"kerr-and-company"};
  }catch(e){}
})();