(()=>{"use strict";
const $=id=>document.getElementById(id);
const state={revealed:false,initialObservation:"",verdict:null,recorded:false};
const panel=$("visual-attestation");if(!panel)return;
const digestText=value=>{let h=2166136261;for(let i=0;i<value.length;i++){h^=value.charCodeAt(i);h=Math.imul(h,16777619);}return "demo-"+(h>>>0).toString(16).padStart(8,"0");};
const reveal=$("visual-reveal"), submit=$("visual-submit");
reveal.addEventListener("click",()=>{
 const observation=$("visual-observation").value.trim();
 if(observation.length<12){$("visual-observation").focus();$("visual-observation").setCustomValidity("Please record an observation of at least 12 characters before revealing the model assessment.");$("visual-observation").reportValidity();return;}
 $("visual-observation").setCustomValidity("");
 state.initialObservation=observation;state.revealed=true;
 $("visual-assessment").classList.remove("hidden");$("visual-model-lock").textContent="REVEALED";
 $("visual-model-panel").querySelector(".visual-locked").classList.add("hidden");
 $("visual-verdict").classList.remove("hidden");$("visual-state").textContent="HUMAN REVIEW IN PROGRESS";
 reveal.disabled=true;reveal.textContent="AI assessment revealed";
 $("visual-verdict").scrollIntoView({behavior:"smooth",block:"nearest"});
});
submit.addEventListener("click",()=>{
 if(!state.revealed)return;
 const choice=panel.querySelector('input[name="visual-verdict"]:checked');
 const rationale=$("visual-rationale").value.trim();
 if(!choice){alert("Select a verdict before recording.");return;}
 if(rationale.length<8){$("visual-rationale").focus();$("visual-rationale").setCustomValidity("Please provide a short rationale (at least 8 characters).");$("visual-rationale").reportValidity();return;}
 $("visual-rationale").setCustomValidity("");
 const record={evidence_id:"SYNTH-VIS-001",assessment_id:"SYNTH-ASSESS-001",reviewer:"UNAUTHENTICATED_DEMO_REVIEWER",verdict:choice.value,initial_observation:state.initialObservation,rationale,model_output_revealed_after_initial_observation:true,recorded_at:new Date().toISOString(),persistence:"BROWSER_MEMORY_ONLY",authority:"NO_PHYSICAL_ACTION_AUTHORISED"};
 record.demo_reference=digestText(JSON.stringify(record));state.recorded=true;state.verdict=record;
 $("visual-state").textContent="DEMO VERDICT RECORDED";$("visual-record").classList.remove("hidden");
 $("visual-record").innerHTML="<b>Demonstration attestation recorded</b><br>Verdict: "+record.verdict+"<br>Evidence: "+record.evidence_id+"<br>Assessment: "+record.assessment_id+"<br>Reviewer: "+record.reviewer+"<br>Recorded: "+record.recorded_at+"<br>Demo reference: <code>"+record.demo_reference+"</code><br><br>This reference is a lightweight browser demonstration identifier, not a cryptographic signature or tamper-proof audit proof.";
 submit.disabled=true;submit.textContent="Demonstration verdict recorded";
});
})();
