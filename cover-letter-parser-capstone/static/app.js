const form=document.getElementById("coverLetterForm");
const input=document.getElementById("coverLetterInput");
const dropZone=document.getElementById("dropZone");
const selectedFile=document.getElementById("selectedFile");
const jobDescription=document.getElementById("jobDescription");
const analyzeButton=document.getElementById("analyzeButton");
const statusBox=document.getElementById("status");
const results=document.getElementById("results");
const categoryMax={"Contact Information":10,"Professional Structure":15,"Job Relevance":20,"Skills and Qualifications":20,"Writing Clarity":15,"Personalization":10,"Completeness":10};

input.addEventListener("change",()=>selectedFile.textContent=input.files[0]?.name||"No file selected");
["dragenter","dragover"].forEach(n=>dropZone.addEventListener(n,e=>{e.preventDefault();dropZone.classList.add("dragging")}));
["dragleave","drop"].forEach(n=>dropZone.addEventListener(n,e=>{e.preventDefault();dropZone.classList.remove("dragging")}));
dropZone.addEventListener("drop",e=>{if(e.dataTransfer.files.length){input.files=e.dataTransfer.files;selectedFile.textContent=e.dataTransfer.files[0].name}});

form.addEventListener("submit",async e=>{
e.preventDefault();
if(!input.files.length){showStatus("Choose a cover letter first.");return}
analyzeButton.disabled=true;analyzeButton.textContent="Analyzing...";
showStatus("Reading and evaluating your cover letter...");results.classList.add("hidden");
const data=new FormData();data.append("cover_letter",input.files[0]);data.append("job_description",jobDescription.value);
try{
const response=await fetch("/api/parse",{method:"POST",body:data});
const result=await response.json();
if(!response.ok)throw new Error(result.error||"Something went wrong.");
sessionStorage.setItem("extractedCoverLetterText",result.extracted_text||"");
sessionStorage.setItem("coverLetterFilename",result.filename||input.files[0].name);
renderResults(result);statusBox.classList.add("hidden");
}catch(error){showStatus(error.message)}
finally{analyzeButton.disabled=false;analyzeButton.textContent="Analyze Cover Letter"}
});

function showStatus(message){statusBox.textContent=message;statusBox.classList.remove("hidden")}
function safe(value){return value||"—"}
function renderChips(id,items,empty){const c=document.getElementById(id);c.innerHTML="";
if(!items||!items.length){const s=document.createElement("span");s.className="selected-file";s.textContent=empty;c.appendChild(s);return}
items.forEach(x=>{const s=document.createElement("span");s.className="chip";s.textContent=x;c.appendChild(s)})}
function renderList(id,items){const list=document.getElementById(id);list.innerHTML="";
(items?.length?items:["No information available."]).forEach(x=>{const li=document.createElement("li");li.textContent=x;list.appendChild(li)})}
function renderCategories(scores){const c=document.getElementById("categories");c.innerHTML="";
Object.entries(scores||{}).forEach(([name,score])=>{const max=categoryMax[name]||100;const p=Math.min(100,Math.round(score/max*100));
const row=document.createElement("div");row.className="category";
row.innerHTML=`<div class="category-top"><strong>${name}</strong><span>${score}/${max}</span></div><div class="bar"><span style="width:${p}%"></span></div>`;
c.appendChild(row)})}
function renderJobMatch(m){const p=document.getElementById("jobMatchPanel");
if(!m||m.match_percentage===null){p.classList.add("hidden");return}
document.getElementById("matchPercentage").textContent=`${m.match_percentage}%`;
renderChips("matchedKeywords",m.matched_keywords,"No matching keywords were detected.");p.classList.remove("hidden")}
function renderResults(d){
["score","ringScore"].forEach(id=>document.getElementById(id).textContent=d.score??0);
document.getElementById("rating").textContent=safe(d.rating);
document.getElementById("name").textContent=safe(d.name);
document.getElementById("email").textContent=safe(d.email);
document.getElementById("phone").textContent=safe(d.phone);
document.getElementById("linkedin").textContent=safe(d.linkedin);
document.getElementById("wordCount").textContent=d.word_count??"—";
document.getElementById("summary").textContent=safe(d.summary);
renderChips("skills",d.skills,"No skills matched the current skill dictionary.");
renderList("strengths",d.strengths);renderList("improvements",d.improvements);
renderCategories(d.category_scores);renderJobMatch(d.job_match);
results.classList.remove("hidden");results.scrollIntoView({behavior:"smooth",block:"start"})}
