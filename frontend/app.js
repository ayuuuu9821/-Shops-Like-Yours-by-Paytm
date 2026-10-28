const API = "http://127.0.0.1:8000";
let chart;
const money = n => new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",maximumFractionDigits:0}).format(Number(n||0));
const el = id => document.getElementById(id);
function params(){return new URLSearchParams({category:el("category").value,area:el("area").value})}
function toast(msg){el("toast").textContent=msg;el("toast").style.display="block";setTimeout(()=>el("toast").style.display="none",3200)}
async function getJSON(url,opts){const r=await fetch(url,opts);if(!r.ok)throw new Error((await r.json()).detail||"API request failed");return r.json()}
async function load(){
 try{
  const q=params(), sales=Number(el("salesInput").value||0);
  const [overview,benchmark]=await Promise.all([
   getJSON(`${API}/api/overview?${q}`),
   getJSON(`${API}/api/benchmark?${q}&merchant_daily_sales=${encodeURIComponent(sales)}`)
  ]);
  el("totalSales").textContent=money(overview.total_sales);
  el("avgSales").textContent=money(overview.average_daily_sales);
  el("transactions").textContent=Number(overview.transactions).toLocaleString("en-IN");
  el("positionMetric").textContent=benchmark.position;
  el("yourSales").textContent=money(sales);
  el("peerAvg").textContent=money(benchmark.peer_average_daily_sales);
  const max=Math.max(sales,benchmark.peer_average_daily_sales,1);
  el("salesBar").style.width=Math.min(100,sales/max*100)+"%";
  el("benchmarkText").textContent=`You are ${money(Math.abs(benchmark.gap_vs_peer_average))} ${benchmark.gap_vs_peer_average>=0?"above":"below"} the demo peer average per day. Comparison group: ${benchmark.peer_count} synthetic shops.`;
  el("opportunityTitle").textContent=benchmark.position;
  el("opportunityText").textContent=benchmark.gap_vs_peer_average<0?"Test a small offer during a slow period and measure whether it increases transactions without hurting margins.":"Avoid changing everything at once. Test one small offer and check whether it adds profitable sales.";
  const labels=overview.daily_sales.map(x=>x.date.slice(5));
  const values=overview.daily_sales.map(x=>x.sales);
  if(chart)chart.destroy();
  chart=new Chart(el("salesChart"),{type:"line",data:{labels,datasets:[{label:"Sales (₹)",data:values,borderColor:"#1769ff",backgroundColor:"rgba(23,105,255,.09)",fill:true,tension:.32,pointRadius:1.5,borderWidth:2}]},options:{responsive:true,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>money(c.raw)}}},scales:{x:{grid:{display:false},ticks:{maxTicksLimit:8,color:"#8a99ac",font:{size:10}}},y:{grid:{color:"#edf1f6"},ticks:{color:"#8a99ac",font:{size:10},callback:v=>"₹"+Number(v).toLocaleString("en-IN")}}}}});
 }catch(e){toast("Cannot reach backend. Start FastAPI first (see README).");console.error(e)}
}
async function makeAdvice(){
 try{
  const data={shop_name:el("shopName").value||"My Shop",category:el("category").value,area:el("area").value,daily_sales:Number(el("salesInput").value||0),average_bill:180,language:el("language").value,period:"weekly"};
  const r=await getJSON(`${API}/api/advice`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});
  el("actionTitle").textContent="Your next 7-day experiment";
  el("actionText").textContent=r.personalized_action;
  el("campaignText").textContent=r.advertising_idea;
  el("measureText").textContent=r.measurement;
  el("opportunityTitle").textContent=r.position;
  el("opportunityText").textContent=r.personalized_action;
 }catch(e){toast("Cannot reach backend. Start FastAPI first.");console.error(e)}
}
el("refreshBtn").addEventListener("click",load);
el("adviceBtn").addEventListener("click",makeAdvice);
el("category").addEventListener("change",load);
el("area").addEventListener("change",load);
el("salesInput").addEventListener("change",load);
load();
