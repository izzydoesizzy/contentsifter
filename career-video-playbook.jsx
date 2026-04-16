import { useState } from "react";

const HOOKS = [
  { cat: "Pattern Interrupt", text: "DELETE your resume. Right now. I'm serious. …Okay not really — but delete THIS section, because it's costing you interviews." },
  { cat: "Pattern Interrupt", text: "—and THAT is why hiring managers reject 80% of candidates in the first 10 seconds." },
  { cat: "Pattern Interrupt", text: "See this rejection email? Here's how to make these stop showing up in your inbox." },
  { cat: "Pattern Interrupt", text: "This has nothing to do with resumes, but it'll change how you land your next role forever." },
  { cat: "Pattern Interrupt", text: "STOP. If you've applied to more than 50 jobs this month and heard nothing back — this video is the reason why." },
  { cat: "Pattern Interrupt", text: "I just reviewed a resume that was PERFECT. Perfect formatting. Perfect bullet points. And it would get rejected by every company in Toronto. Here's why." },
  { cat: "Curiosity", text: "I reviewed 500 resumes last month. Here's the one mistake 90% made." },
  { cat: "Curiosity", text: "I probably shouldn't share what happened in this interview, but…" },
  { cat: "Curiosity", text: "Here's what happened when my client stopped applying online for 30 days." },
  { cat: "Curiosity", text: "Nobody is talking about this, and it's costing you interviews." },
  { cat: "Curiosity", text: "The one thing about salary negotiation that nobody tells you…" },
  { cat: "Curiosity", text: "I just found out why you keep getting ghosted after interviews…" },
  { cat: "Curiosity", text: "There's a section on LinkedIn that 90% of job seekers leave blank — and it's the one recruiters actually search for." },
  { cat: "Curiosity", text: "I coached a client who got 3 offers in 2 weeks. The strategy? Nothing to do with her resume." },
  { cat: "Curiosity", text: "The highest-paid professionals in Canada all do one thing before every salary negotiation. It takes 5 minutes." },
  { cat: "Curiosity", text: "I tracked what happened when I sent the same resume to 100 jobs in two formats. The results made me rethink everything I teach." },
  { cat: "Curiosity", text: "Recruiters spend 6 seconds on your resume. But there's one line they always read first — and most people waste it." },
  { cat: "Contrarian", text: "Everyone says tailor your resume to every job. I 100% disagree." },
  { cat: "Contrarian", text: "Unpopular opinion: networking events are a waste of time. Here's what works instead." },
  { cat: "Contrarian", text: "The biggest lie in career advice that nobody challenges." },
  { cat: "Contrarian", text: "LinkedIn Easy Apply is why you're not getting interviews." },
  { cat: "Contrarian", text: "Cover letters are dead. Here's what replaced them." },
  { cat: "Contrarian", text: "This 'best practice' is actually holding you back from getting hired." },
  { cat: "Contrarian", text: "The worst career advice on TikTok right now? 'Job hop every 12 months.' Here's why it's destroying careers." },
  { cat: "Contrarian", text: "Your cover letter doesn't matter. After helping 200+ clients land jobs in Canada, here's what actually does." },
  { cat: "Contrarian", text: "Stop 'tailoring your resume to every job.' It's the most overrated advice in career coaching." },
  { cat: "Contrarian", text: "If you're applying to jobs online in 2026, you're using a strategy that worked in 2015." },
  { cat: "Story", text: "My client got 3 job offers in one week after being ghosted for 6 months. Here's exactly what we changed." },
  { cat: "Story", text: "I sat across from a hiring manager who told me the REAL reason they reject candidates in 10 seconds." },
  { cat: "Story", text: "She was about to accept a $60K offer. I told her to do this instead. She got $95K." },
  { cat: "Story", text: "It was day 47 of my job search. Zero callbacks. Then I changed ONE thing." },
  { cat: "Story", text: "Last Tuesday, a client called me in tears. Here's what happened next." },
  { cat: "Story", text: "Last week a client called crying. Laid off after 12 years. No idea where to start. Here's what I told her." },
  { cat: "Story", text: "A hiring manager told me the real reason they rejected a perfectly qualified candidate. It had nothing to do with experience." },
  { cat: "Story", text: "I used to think salary negotiation was about being aggressive. Then I lost a $30K raise because of one sentence." },
  { cat: "Story", text: "My client went from 200 applications with zero callbacks to 3 interviews in one week. We changed the first 3 lines of her resume." },
  { cat: "Story", text: "I was coaching a VP of Marketing who got fired and was too embarrassed to tell anyone. Six weeks later — $40K raise." },
  { cat: "Stat-Based", text: "75% of resumes never get seen by a human. Here's how to be in the other 25%." },
  { cat: "Stat-Based", text: "Hiring managers spend 7.4 seconds on your resume. Here's what they look at first." },
  { cat: "Stat-Based", text: "92% of people bomb behavioral interviews. Here's the 3-step formula that works." },
  { cat: "Stat-Based", text: "Canada just lost 84,000 jobs in one month. But only 0.4% of Canadians changed jobs. The market isn't broken — your strategy is." },
  { cat: "Stat-Based", text: "85% of jobs are filled through networking, not online applications. So why are you spending 5 hours a day on Indeed?" },
  { cat: "Stat-Based", text: "Canadian youth unemployment just hit 13.3%. If you're under 25, you need a completely different strategy." },
  { cat: "Stat-Based", text: "I analyzed 200 job postings in Toronto last week. 73% asked for ONE skill most candidates don't even mention." },
  { cat: "Doing It Wrong", text: "You're answering 'Tell me about yourself' wrong. Here's the 60-second formula." },
  { cat: "Doing It Wrong", text: "You're writing your resume summary wrong. Here's what actually gets interviews." },
  { cat: "Doing It Wrong", text: "If you're still sending the same resume to every job, no wonder you're not hearing back." },
  { cat: "Doing It Wrong", text: "You're doing LinkedIn wrong. 3 changes that get recruiters to message YOU." },
  { cat: "Doing It Wrong", text: "Your resume isn't getting rejected by humans. It's getting rejected by software before a human ever sees it." },
  { cat: "Doing It Wrong", text: "If you're putting 'References available upon request' on your resume in 2026, you're signaling you're behind the times." },
  { cat: "Doing It Wrong", text: "Your LinkedIn headline says your job title. But recruiters aren't searching for job titles — they're searching for THIS." },
  { cat: "Doing It Wrong", text: "The way you're following up after interviews is actually making hiring managers LESS likely to hire you." },
  { cat: "Stop Doing X", text: "Stop applying to jobs online. Do this instead." },
  { cat: "Stop Doing X", text: "Stop saying 'I'm a hard worker' in interviews. Say this instead." },
  { cat: "Stop Doing X", text: "Stop putting these 5 things on your resume. Recruiters hate them." },
  { cat: "Stop Doing X", text: "Stop accepting the first offer. Here's the exact script to negotiate." },
  { cat: "Stop Doing X", text: "Stop applying to jobs on Monday morning. I'll show you the exact day and time that gets callbacks." },
  { cat: "Stop Doing X", text: "Stop sending your resume as a Word doc. It could be why you're getting ghosted." },
  { cat: "Stop Doing X", text: "Stop listing your duties on your resume. Nobody cares what you were SUPPOSED to do." },
  { cat: "Stop Doing X", text: "If you're a Canadian professional making under $80K — stop accepting the first offer." },
  { cat: "Authority", text: "After coaching 200+ career changers, here's the pattern I see." },
  { cat: "Authority", text: "I've reviewed 10,000 resumes. Here's what the top 1% do differently." },
  { cat: "Authority", text: "I spent 15 years in HR. Here's the truth about how hiring actually works." },
  { cat: "Authority", text: "As a career coach, I review 20+ resumes a week. The mistake I see most often will surprise you." },
  { cat: "Authority", text: "I've sat on both sides of the hiring table. Here's the insider truth about what gets you hired." },
  { cat: "Authority", text: "After coaching hundreds of career pivots, the #1 reason people fail isn't what you think." },
  { cat: "Hypothetical", text: "What if I told you the job you want doesn't have a posting? 70% of roles are never publicly advertised." },
  { cat: "Hypothetical", text: "Imagine walking into a salary negotiation knowing the EXACT number the company budgeted. You can." },
  { cat: "Hypothetical", text: "What would you do if you got laid off tomorrow? Most people have no plan. Here are the first 5 steps." },
  { cat: "🇨🇦 Canada", text: "Canada just posted a 6.7% unemployment rate. If you're job hunting in this market, here are the 3 strategies actually working." },
  { cat: "🇨🇦 Canada", text: "26,000+ federal workers just got layoff notices. If you're one of them, here's your exact first-week playbook." },
  { cat: "🇨🇦 Canada", text: "Ontario just banned ghost job postings and made companies disclose salary ranges. Here's what this means for your search." },
  { cat: "🇨🇦 Canada", text: "Return-to-office mandates are back across Canada. The smartest professionals are using this to negotiate something most don't think to ask for." },
  { cat: "🇨🇦 Canada", text: "AI just replaced half of Klue Labs' workforce in Vancouver. But here's the skill that makes you irreplaceable." },
  { cat: "🇨🇦 Canada", text: "Everyone's talking about AI replacing jobs. Nobody's telling you about the massive advantage it created for job seekers." },
  { cat: "🇨🇦 Canada", text: "With tariff wars hitting Canadian manufacturing, I'm seeing something I haven't seen in 10 years of coaching." },
  { cat: "🇨🇦 Canada", text: "LinkedIn just changed their algorithm AGAIN. This update either helps you or crushes you depending on one thing." },
  { cat: "🇨🇦 Canada", text: "Ontario employers must now tell you if AI screened your application. Here's how to use that to your advantage." },
  { cat: "🇨🇦 Canada", text: "Men over 65 now earn more than 25-34 year olds in Canada for the first time ever. Here's what that means for your career." },
];
const HOOK_CATS = [...new Set(HOOKS.map(h => h.cat))];
const FW = [
  { name:"Problem → Agitate → Solution",abbr:"PAS",color:"#E74C3C",steps:["Hook with problem (0–3s)","Amplify pain (3–15s)","Solution with proof (15–45s)","CTA (5s)"],ex:"You've sent 200 applications and heard nothing. Every day you're losing confidence. Here's the 3-part outreach strategy to bypass ATS and land interviews in 2 weeks."},
  { name:"Myth vs. Reality",abbr:"MvR",color:"#9B59B6",steps:["State the myth","Say 'Reality:' + truth","Proof or experience"],ex:"'You need 100% of qualifications.' Reality: hiring managers expect 60–70%."},
  { name:"Do This, Not That",abbr:"DTNT",color:"#2980B9",steps:["Common wrong approach","Right approach","Why it works"],ex:"Don't say 'I'm a team player.' Say 'I led a cross-functional team of 6 that shipped 2 weeks early.'"},
  { name:"Listicle",abbr:"LIST",color:"#27AE60",steps:["Easiest tip first","Most impactful in middle","Most unexpected last"],ex:"3 things to say in every interview: 1) 'I researched your Q3 goals…' 2) 'Here's my 90-day approach…' 3) 'What would success look like?'"},
  { name:"Hot Take",abbr:"HOT",color:"#E67E22",steps:["Bold opinion","Reasoning","Evidence","'Agree or disagree?'"],ex:"Job boards make you feel busy, not get hired. 80% of roles filled through referrals. Agree or disagree?"},
  { name:"Story → Lesson",abbr:"S→L",color:"#1ABC9C",steps:["Moment of tension","Brief story","Extract lesson","Apply to viewer"],ex:"Client about to give up after 8 months. Tried personalized video messages to hiring managers. 3 offers in 2 weeks."},
  { name:"What I'd Do If…",abbr:"WIDI",color:"#F39C12",steps:["Hypothetical scenario","Step-by-step plan","Key principle"],ex:"If I had to find a job in 30 days: Week 1 optimize LinkedIn + 20 outreach. Week 2 informational interviews. Week 3 warm applications. Week 4 follow up."},
  { name:"Before → After → Bridge",abbr:"BAB",color:"#8E44AD",steps:["Paint painful 'Before'","Show ideal 'After'","Reveal the 'Bridge'"],ex:"Before: 50 apps/week, hearing nothing. After: 3-5 interviews/week. Bridge: Stop boards, start personalized DM outreach."},
  { name:"Hook → Story → Offer",abbr:"HSO",color:"#2ECC71",steps:["Bold hook","Compelling story","Offer/CTA as next step"],ex:"Hook: 'Rejected from 47 jobs before I changed ONE thing.' Story: Buried results under duties. Flipped bullets. Offer: Free resume guide in bio."},
  { name:"SCQA",abbr:"SCQA",color:"#3498DB",steps:["Situation (accepted truth)","Complication","Question viewer thinks","Answer"],ex:"Situation: 'Network to find jobs.' Complication: DMs ignored. Question: How to build real connections? Answer: Comment on posts 2 weeks before DM."},
  { name:"Epiphany Bridge",abbr:"EPPH",color:"#E74C3C",steps:["Your backstory","The wall you hit","Aha moment","Transformation"],ex:"Used to coach memorized answers. Clients bombed. Then one nailed it by just telling stories. Interviews aren't tests — they're conversations."},
  { name:"POV Scenario",abbr:"POV",color:"#9B59B6",steps:["'POV: You're [scenario]…'","Act/narrate from viewer's view","Twist/resolution","Takeaway"],ex:"POV: Interview. 'Biggest weakness?' You say 'I struggled with delegation — here's what I did.' Interviewer leans in. That's the answer."},
  { name:"SOAR",abbr:"SOAR",color:"#16A085",steps:["Person + context","Challenge","Specific steps","Measurable result"],ex:"Sarah: 12yr teacher → corporate L&D. Reframed teaching as 'curriculum design for 150+ stakeholders.' 6 weeks → L&D Manager, $30K raise."},
  { name:"Unexpected Confession",abbr:"CONF",color:"#D35400",steps:["'I shouldn't share this, but…'","Vulnerable insight","Lesson","Actionable takeaway"],ex:"As a recruiter, I spent <7 seconds on most resumes. The ones I skipped weren't bad — they were forgettable. No numbers. Your resume is a highlight reel."},
  { name:"One-Minute Fix",abbr:"1MIN",color:"#2980B9",steps:["Name pain point","Promise 60s fix","ONE change","Before/after"],ex:"Your LinkedIn headline: 'Marketing Manager at XYZ.' → 'Marketing Manager | 3 brands $1M→$10M | Open to opportunities.' One change."},
  { name:"This Cost Me $___",abbr:"COST",color:"#C0392B",steps:["Specific dollar cost","Quick story","The mistake","The fix"],ex:"Not negotiating cost me $45K over 3 years. Fix: 'Can I have 48 hours to review the full package?' Worth tens of thousands."},
  { name:"Counterintuitive Reveal",abbr:"CREV",color:"#7D3C98",steps:["Common best practice","Why it's counterproductive","Better alternative","Why it works"],ex:"Stop customizing every resume. Create 3 master versions by role type. Spend saved time on outreach. Clients got 3x more interviews."},
  { name:"Challenge / Experiment",abbr:"EXP",color:"#1ABC9C",steps:["'I tried X for Y days'","Show process","Results with data","Takeaway"],ex:"50 generic LinkedIn requests vs 50 voice messages. Generic: 23% accept, 0 convos. Voice: 68% accept, 14 convos, 3 coffee chats."},
  { name:"Behind the Curtain",abbr:"BTC",color:"#34495E",steps:["'What recruiters won't tell you…'","Insider info","Implications","Adjustment"],ex:"Recruiters have a gut feeling in 90 seconds. Energy, opener, clarity — that's it. Here's my 90-second formula."},
  { name:"Eavesdrop (Client Coaching)",abbr:"EAVE",color:"#E67E22",steps:["'Here's what I told my client…'","Recreate coaching moment","Key insight","Invite viewer to apply"],ex:"'I've been searching 4 months, about to give up.' I said: 'You're in the messy middle. Let's audit what's NOT working.' Cut apps 50%, warm outreach → 2 interviews in a week."},
  { name:"Rapid Stack",abbr:"RAPID",color:"#27AE60",steps:["'X things in Y seconds. Go.'","Rapid-fire with text overlay","'Save this.'"],ex:"5 things NEVER say in interview: 1) 'No questions.' 2) 'Work too hard.' 3) 'I'll do anything.' 4) 'Bad boss.' 5) 'What does your company do?' Save this."},
  { name:"Zoom Out (Reframe)",abbr:"ZOOM",color:"#2C3E50",steps:["Viewer's narrow frustration","Zoom out to bigger picture","Reframe entirely","New perspective + action"],ex:"Stressed about the gap? Zoom out. Managers have seen millions. They care what you DID during it. Reframe the gap as a chapter, not a hole."},
  { name:"Steal My Script",abbr:"SCRPT",color:"#E74C3C",steps:["Name the situation","'Here's the exact script'","Word-for-word template","Why each part works"],ex:"Salary expectations? 'Based on my research, I'm targeting $X-$Y. I'm flexible — I'd love to understand the full package.' Anchor high. Show homework. Keep the door open."},
  { name:"Red Flag / Green Flag",abbr:"🚩🟢",color:"#C0392B",steps:["Introduce context","3-5 red flags","3-5 green flags","'Know your worth.'"],ex:"🚩 'Fast-paced' = understaffed. 🟢 'We invest in development' = growth. 🚩 'Wear many hats' = 3 jobs. 🟢 Salary range posted = respect."},
  { name:"If/Then Decision Tree",abbr:"IF/TH",color:"#8E44AD",steps:["'Not sure whether to X?'","2-3 branches","Context per path","'Save for when you need it'"],ex:"Accept offer? IF below min + no negotiation → Walk. IF below but great growth → 'Revisit at 6 months?' IF at/above → Negotiate anyway."},
  { name:"Time Machine",abbr:"TIME",color:"#F39C12",steps:["'If I could tell younger me…'","What you did wrong","What you know now","The shortcut"],ex:"25-year-old me: stop chasing titles. Chase skills. I spent 3 years gunning for 'Senior' while ignoring stakeholder management. Title came when I stopped chasing."},
  { name:"Wrong Q → Right Q",abbr:"WQ→RQ",color:"#16A085",steps:["Question everyone asks","Why it's wrong","Right question","Answer it"],ex:"Everyone: 'How do I get more interviews?' Wrong. Right: 'How do I get interviews at companies I WANT?' Pick 20 dream companies. Engage their hiring managers. Then apply."},
  { name:"4P (Promise-Picture-Proof-Push)",abbr:"4P",color:"#2980B9",steps:["Bold promise","Vivid mental image","Evidence","Clear CTA"],ex:"Promise: Land interviews with no posting. Picture: VP messages 'We created this role for you.' Proof: 3 clients did this. Push: Comment 'SCRIPT.'"},
  { name:"Day in the Life (Process)",abbr:"DITL",color:"#7F8C8D",steps:["'Here's what happens when you hire me'","Walk through process","Show methodology","'This is what we'd do'"],ex:"Day 1: Audit resume, LinkedIn, strategy. Week 1: Rebuild with results. Week 2-4: Build outreach system. No fluff."},
  { name:"3C (Context-Contrast-Conclusion)",abbr:"3C",color:"#D35400",steps:["Context (trend)","Contrast (common vs effective)","Conclusion (principle + action)"],ex:"Context: AI writes everyone's letters. Contrast: Most sound generic. Winners inject stories. Conclusion: Future is AI + your unique stories."},
  { name:"AIDA",abbr:"AIDA",color:"#1ABC9C",steps:["Attention (bold, 0-3s)","Interest (surprising fact)","Desire (transformation)","Action (CTA)"],ex:"93% of recruiters check LinkedIn first. Most profiles = boring resumes. Top 1% tell a story. Comment 'PROFILE' for my audit checklist."},
];
const PILLARS = [
  { name:"Resume Optimization",icon:"📄",topics:["The 6-second resume test","Resume before/after in 60 seconds","XYZ bullet formula","How to explain employment gaps","One-page vs. two-page: the real answer","ATS formatting dos and don'ts","Stop putting these 5 things on your resume","Quantify your achievements","AI resume screening: how to beat it","Resume keywords ATS systems scan for","Resume with zero experience","Why Word docs get corrupted","The resume summary that gets callbacks","Skills section: what to include in 2026"]},
  { name:"Interview Prep",icon:"🎤",topics:["'Tell me about yourself' formula","STAR method in 30 seconds","5 questions to ask at the END","Body language that screams 'hire me'","Behavioral questions decoded","Video interview mistakes","How to recover when you bomb a question","What they discuss after you leave","'Where do you see yourself in 5 years?'","'Greatest weakness' — the answer that works","Panel interview survival guide","Red flags in your interviewer","How to follow up without being annoying","Phone screen vs final round strategies"]},
  { name:"LinkedIn Strategy",icon:"💼",topics:["Your headline is costing you jobs","LinkedIn summary formula","#OpenToWork badge: help or hurt?","Get recruiters to find YOU","LinkedIn keywords for recruiter searches","How to ask for recommendations","Activity that impresses hiring managers","Profile photo dos and don'ts","LinkedIn's new algorithm: what changed","Voice messages — the secret weapon","LinkedIn's AI job tools","Creator mode for job seekers"]},
  { name:"Salary Negotiation",icon:"💰",topics:["Exact script to negotiate $10K more","Counter a lowball offer","Never say this number first","Negotiating beyond salary","When to walk away","Negotiate a raise at your current job","Should you disclose current salary?","Salary research tools","Ontario's pay transparency law","Negotiate remote work into your offer"]},
  { name:"Job Search Strategy",icon:"🔍",topics:["Stop applying online — do this instead","The hidden job market","Cold email template 80% response rate","Informational interview scripts","Networking for introverts","Coffee chat template","LinkedIn messaging without spam","Job search timeline expectations","Why you're getting ghosted","Job boards are broken","Stand out from AI applications"]},
  { name:"Career Pivots",icon:"🔀",topics:["5 signs it's time to leave","Career change at 30/40/50","Transferable skills you didn't know","Pivot without a pay cut","Explain a career change in interview","Career pivot roadmap","Industries hiring you haven't considered","Corporate to freelance — the real math","Trades as safe bet in 2026"]},
  { name:"Mindset & Confidence",icon:"🧠",topics:["Imposter syndrome — how to stop","Speaking up in meetings","Setting boundaries at work","Stop apologizing in emails","Dealing with a toxic boss","Quiet quitting vs healthy boundaries","Overlooked for promotion","The messy middle of job searching","Stay motivated after months"]},
  { name:"🇨🇦 Canada Hot Topics",icon:"🇨🇦",topics:["84,000 jobs lost — what to do now","26,000 federal layoffs — rights & next steps","Ontario pay transparency law explained","Ontario banned 'Canadian experience'","AI disclosure required in Ontario hiring","Ghost job postings now illegal in Ontario","45-day interview follow-up rule","Federal 4-day RTO mandate July 2026","All 5 banks require 4 days in-office","Ontario 5-day RTO for provincial staff","Scotiabank cutting 2,500 in Toronto","Bell, GM, Algoma, Shopify layoffs","Student enrollment cap hitting colleges","AI replaced half of Klue Labs","64% say AI apps harder to screen","Trades boom: 101K apprenticeships","Youth unemployment 13.3%","Toronto vs Calgary for career moves","Gig economy: 17% of Canadians","DEI rollback — what's happening in Canada","CRA gig income reporting traps","US tariffs hitting Canadian manufacturing","Only 0.4% changed jobs last month","Men 65+ earn more than 25-34 year olds"]},
];
const CTAS = [
  { stage:"Viewer → Follower",emoji:"🎯",color:"#e74c3c",items:["Follow for Part 2","Follow to see the full template tomorrow","Follow for daily job search strategies","Create numbered series ('Day 3 of resume tips')"]},
  { stage:"Follower → Subscriber",emoji:"📧",color:"#f39c12",items:["DM me 'RESUME' for my free template","Comment 'GUIDE' and I'll DM my checklist","Grab the free guide — link in bio","Take my free Career Readiness Quiz","DM 'SCRIPT' for negotiation template"]},
  { stage:"Subscriber → Client",emoji:"🤝",color:"#27ae60",items:["Book a free discovery call — link in bio","DM me 'READY' for personalized help","Opening 3 coaching spots — DM 'COACHING'","I break this down with clients — link in profile"]},
  { stage:"Algorithm Boosters",emoji:"📈",color:"#8b5cf6",items:["Send this to a friend who needs it (→ DM shares)","Save this for your next interview (→ saves)","Comment [keyword] for full guide (→ comments + DMs)","Tag someone who needs this (→ shares)"]},
];
const NEWS = [
  { title:"84,000 Jobs Lost in February",stat:"6.7% unemployment",detail:"Full-time dropped 108K. Youth 13.3%. Only 0.4% changed jobs — lowest mobility in years.",angle:"PAS: paint the stat, agitate the fear, solve with outreach strategy."},
  { title:"26,000+ Federal Layoff Notices",stat:"40K cuts by 2028-29",detail:"Shared Services 1K+, Health Canada 1K+, StatsCan 850, NRCan ~700, CRA 479 in March, Bank of Canada ~10%.",angle:"Target public servants who've never written a private-sector resume. Eavesdrop or SOAR."},
  { title:"Ontario's New Job Posting Laws",stat:"Effective Jan 1 2026",detail:"Pay transparency, AI disclosure, 'Canadian experience' ban, ghost job ban, 45-day follow-up rule, 3-day job-seeking leave. Fines up to $500K.",angle:"Explainer series — each law is its own Reel. Myth vs Reality or One-Minute Fix."},
  { title:"Return-to-Office Mandates",stat:"Federal: 4 days July 6",detail:"Federal 4-day, Ontario provincial 5-day. All Big 5 banks 4 days. PSAC: 'slap in the face.' Could save $6B going remote.",angle:"Hot Take: 'RTO mandates are actually an opportunity to negotiate.' BAB framework."},
  { title:"Private Sector Layoffs",stat:"Thousands affected",detail:"Scotiabank 2,500, Bell 700, GM 2,000+, Algoma 1,000, Shopify partnerships, Imperial Oil 20%, GFL HQ to Miami. Colleges: Conestoga 400, Humber, Georgian closures.",angle:"Story → Lesson with anonymized stories. Steal My Script with severance templates."},
  { title:"AI Reshaping Canadian Jobs",stat:"60% workforce exposed",detail:"Klue Labs cut ~half citing AI. Foundever 1,000+ (Rogers). AI postings doubled since 2018. 64% say AI apps harder to screen.",angle:"3C: Context (disruption), Contrast (fear vs opportunity), Conclusion (upskill)."},
  { title:"Trades Boom",stat:"101,541 apprenticeships",detail:"Record registrations 2024, up 6% YoY. Average age 27 — many tried university first. 'AI-proof' careers.",angle:"Counterintuitive Reveal: 'Smartest career move in 2026 might be quitting your desk job.'"},
  { title:"Cost of Living & Relocations",stat:"Toronto: $75-85K to live",detail:"Average salary $62K — a $13-23K gap. 1BR $2,300-2,900. Calgary saves ~$33,600/yr. Men 65+ earn more than 25-34.",angle:"What I'd Do If: 'Toronto professional making under $80K — my 3-step plan.'"},
  { title:"DEI Under Pressure",stat:"350+ tech workers signed letter",detail:"U.S. rollbacks. Canada's Charter protects equity but budgets quietly shrinking. Ontario banned 'Canadian experience.'",angle:"Hot Take: 'DEI isn't dead in Canada — it's being rebranded.'"},
  { title:"Gig Economy Surging",stat:"17% of Canadians",detail:"26% of 18-34. 30%+ freelance. CRA platforms must report income. 29% risk penalties.",angle:"Red Flag / Green Flag: precarious gig vs genuine opportunity."},
];

const PILLAR_META={
  "Resume Optimization":{keyword:"RESUME",resource:"resume checklist",li:["#resume","#resumetips","#careercoach","#jobsearch","#ATS"],ig:["#resume","#resumetips","#careercoach","#jobsearch","#ATS","#resumewriting","#careeradvice","#jobhunt","#hiringtips","#resumehelp"]},
  "Interview Prep":{keyword:"INTERVIEW",resource:"interview prep guide",li:["#interview","#interviewtips","#jobinterview","#careeradvice","#hiring"],ig:["#interview","#interviewtips","#jobinterview","#interviewprep","#careercoach","#behavioralinterview","#STARmethod","#jobsearch","#careeradvice","#hiringtips"]},
  "LinkedIn Strategy":{keyword:"PROFILE",resource:"LinkedIn audit checklist",li:["#linkedin","#linkedintips","#personalbranding","#networking","#jobsearch"],ig:["#linkedin","#linkedintips","#personalbranding","#networking","#careercoach","#linkedinprofile","#jobsearch","#recruitertips","#careeradvice","#professionalbrand"]},
  "Salary Negotiation":{keyword:"SALARY",resource:"salary negotiation scripts",li:["#salarynegotiation","#salary","#compensation","#knowyourworth","#careeradvice"],ig:["#salarynegotiation","#salary","#compensation","#knowyourworth","#careercoach","#negotiation","#payraise","#careeradvice","#joboffers","#moneytips"]},
  "Job Search Strategy":{keyword:"JOBSEARCH",resource:"hidden job market guide",li:["#jobsearch","#jobhunt","#careerchange","#networking","#hiringnow"],ig:["#jobsearch","#jobhunt","#careerchange","#networking","#hiringnow","#jobmarket","#careercoach","#coldoutreach","#careeradvice","#jobsearchtips"]},
  "Career Pivots":{keyword:"PIVOT",resource:"career pivot roadmap",li:["#careerpivot","#careerchange","#newcareer","#transferableskills","#careeradvice"],ig:["#careerpivot","#careerchange","#newcareer","#transferableskills","#careercoach","#careerswitch","#jobsearch","#careeradvice","#professionaldevelopment","#midcareer"]},
  "Mindset & Confidence":{keyword:"MINDSET",resource:"confidence playbook",li:["#careerconfidence","#impostersyndrome","#professionaldevelopment","#mindset","#leadership"],ig:["#careerconfidence","#impostersyndrome","#professionaldevelopment","#mindset","#careercoach","#boundaries","#worklife","#motivation","#careeradvice","#selfbelief"]},
  "🇨🇦 Canada Hot Topics":{keyword:"CANADA",resource:"Canadian job market report",li:["#canadajobs","#canadacareers","#ontariojobs","#torontojobs","#canadianeconomy"],ig:["#canadajobs","#canadacareers","#torontojobs","#ontariojobs","#canadianeconomy","#careercoach","#jobmarket","#careeradvice","#canadianworkers","#jobsearchcanada"]}
};

function copyText(t){navigator.clipboard.writeText(t)}
function CopyBtn({text,label}){const[c,setC]=useState(false);return<button onClick={()=>{copyText(text);setC(true);setTimeout(()=>setC(false),1400)}} style={{background:c?"#1a1a2e":"rgba(255,255,255,0.06)",border:"1px solid rgba(255,255,255,0.12)",color:c?"#4ade80":"#c0c0cc",padding:"4px 10px",borderRadius:6,fontSize:11,cursor:"pointer",fontFamily:"'DM Sans',sans-serif",whiteSpace:"nowrap"}}>{c?"✓":(label||"Copy")}</button>}

const TABS=["Hooks","Frameworks","Topics","🇨🇦 News","CTAs","Platform","Workflow","Generator","Scripts"];

export default function App(){
  const[tab,setTab]=useState(0);
  const[hf,setHf]=useState("All");
  const[hs,setHs]=useState("");
  const[ef,setEf]=useState(null);
  const[en,setEn]=useState(null);
  const[gen,setGen]=useState(null);
  const[fav,setFav]=useState([]);
  const[sf,setSf]=useState(false);
  const[scripts,setScripts]=useState(null);
  const[sv,setSv]=useState(null);

  const togFav=i=>setFav(p=>p.includes(i)?p.filter(x=>x!==i):[...p,i]);
  const filt=HOOKS.filter(h=>(hf==="All"||h.cat===hf)&&(!hs||h.text.toLowerCase().includes(hs.toLowerCase())));
  const disp=sf?HOOKS.filter((_,i)=>fav.includes(i)):filt;

  const generate=()=>{
    const hook=HOOKS[Math.floor(Math.random()*HOOKS.length)];
    const fw=FW[Math.floor(Math.random()*FW.length)];
    const pillar=PILLARS[Math.floor(Math.random()*PILLARS.length)];
    const topic=pillar.topics[Math.floor(Math.random()*pillar.topics.length)];
    const cta=CTAS[Math.floor(Math.random()*CTAS.length)];
    const ci=cta.items[Math.floor(Math.random()*cta.items.length)];
    const pl=Math.random()>.5?"Instagram Reels":"LinkedIn Video";
    setGen({hook,fw,pillar,topic,ci,cs:cta.stage,pl});
  };

  const generateScripts=(fp,ft)=>{
    const pillar=fp||PILLARS[Math.floor(Math.random()*PILLARS.length)];
    const topic=ft||pillar.topics[Math.floor(Math.random()*pillar.topics.length)];
    const meta=PILLAR_META[pillar.name]||PILLAR_META["Job Search Strategy"];
    const fws=[...FW].sort(()=>Math.random()-0.5).slice(0,5);
    const hks=[...HOOKS].sort(()=>Math.random()-0.5);
    const fmt=s=>`${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;
    const vars=fws.map((fw,i)=>{
      const hook=hks[i];
      const cg=CTAS[i%CTAS.length];
      const ci=cg.items[Math.floor(Math.random()*cg.items.length)];
      const sc=fw.steps.length;
      const ss=Math.floor(42/sc);
      const beats=fw.steps.map((step,si)=>({step,time:`${fmt(3+si*ss)}–${fmt(si===sc-1?45:3+(si+1)*ss)}`}));
      const scriptText=`🎤 SCRIPT — ${fw.abbr}: ${fw.name}\n📍 Topic: ${topic}\n\n[HOOK — 0:00]\n"${hook.text}"\n\n${beats.map((b,bi)=>`[STEP ${bi+1} — ${b.time}] ${b.step}`).join('\n\n')}\n\n[CTA — ${fmt(45)}]\n"${ci}"\n\n---\n💡 Example: "${fw.ex}"`;
      const liCaption=`${hook.text}\n\n${topic} — most professionals get this wrong.\n\nHere's what actually works ↓\n\n${fw.steps.map((s,si)=>`${si+1}. ${s}`).join('\n')}\n\n${ci}\n\n—\n♻️ Repost to help someone in your network\n🔔 Follow for daily career strategies\n\n${meta.li.join(' ')}`;
      const igCaption=`${hook.text} 👇\n\n${topic} — here's what you need to know.\n\n${fw.steps.map((s,si)=>`${si+1}. ${s}`).join('\n')}\n\n${ci}\n\n💬 DM me "${meta.keyword}" for my free ${meta.resource}\n\n.\n.\n.\n${meta.ig.join(' ')}`;
      return {fw,hook,ci,cs:cg.stage,beats,scriptText,liCaption,igCaption,kw:meta.keyword,res:meta.resource};
    });
    setSv(null);
    setScripts({pillar,topic,meta,variations:vars});
  };

  const S={card:{background:"rgba(255,255,255,0.03)",border:"1px solid rgba(255,255,255,0.06)",borderRadius:10,padding:"14px 16px",marginBottom:8},lbl:{display:"inline-block",fontSize:9,fontWeight:700,textTransform:"uppercase",letterSpacing:1.5,color:"#8b5cf6",marginBottom:6,background:"rgba(139,92,246,0.1)",padding:"2px 8px",borderRadius:4},pill:(a,c)=>({padding:"5px 12px",borderRadius:20,fontSize:11,fontWeight:600,border:a?`1px solid ${c||"#8b5cf6"}`:"1px solid rgba(255,255,255,0.08)",background:a?`${c||"#8b5cf6"}22`:"rgba(255,255,255,0.03)",color:a?(c||"#a78bfa"):"#7a7a8e",cursor:"pointer",fontFamily:"'DM Sans',sans-serif"})};

  return(<div style={{minHeight:"100vh",background:"#0a0a14",color:"#e8e8f0",fontFamily:"'DM Sans',sans-serif"}}>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@700;800&display=swap" rel="stylesheet"/>
    <div style={{background:"linear-gradient(135deg,#0a0a14,#161630 50%,#1a0a2e)",borderBottom:"1px solid rgba(255,255,255,0.06)",padding:"28px 20px 16px"}}>
      <div style={{maxWidth:800,margin:"0 auto"}}>
        <div style={{fontSize:11,textTransform:"uppercase",letterSpacing:3,color:"#8b5cf6",marginBottom:6,fontWeight:600}}>ClearCareer Playbook</div>
        <h1 style={{fontFamily:"'Playfair Display',serif",fontSize:26,fontWeight:800,margin:0,lineHeight:1.15,background:"linear-gradient(135deg,#e8e8f0,#8b5cf6)",WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent"}}>Short-Form Video Playbook</h1>
        <p style={{color:"#7a7a8e",fontSize:13,marginTop:6}}>{HOOKS.length} hooks · {FW.length} frameworks · {PILLARS.reduce((a,p)=>a+p.topics.length,0)} topics · {NEWS.length} 🇨🇦 stories</p>
      </div>
    </div>
    <div style={{position:"sticky",top:0,zIndex:100,background:"rgba(10,10,20,0.92)",backdropFilter:"blur(12px)",borderBottom:"1px solid rgba(255,255,255,0.06)",overflowX:"auto"}}>
      <div style={{display:"flex",maxWidth:800,margin:"0 auto",padding:"0 8px"}}>
        {TABS.map((t,i)=><button key={t} onClick={()=>setTab(i)} style={{background:"none",border:"none",padding:"12px 11px",fontSize:12,fontWeight:tab===i?700:500,color:tab===i?"#8b5cf6":"#7a7a8e",borderBottom:tab===i?"2px solid #8b5cf6":"2px solid transparent",cursor:"pointer",whiteSpace:"nowrap",fontFamily:"'DM Sans',sans-serif"}}>{t}</button>)}
      </div>
    </div>
    <div style={{maxWidth:800,margin:"0 auto",padding:"20px 16px 80px"}}>

      {tab===0&&<div>
        <div style={{display:"flex",gap:8,marginBottom:12,flexWrap:"wrap"}}>
          <input placeholder="Search hooks…" value={hs} onChange={e=>setHs(e.target.value)} style={{flex:1,minWidth:140,padding:"8px 12px",borderRadius:8,border:"1px solid rgba(255,255,255,0.1)",background:"rgba(255,255,255,0.04)",color:"#e8e8f0",fontSize:13,fontFamily:"'DM Sans',sans-serif",outline:"none"}}/>
          <button onClick={()=>setSf(!sf)} style={{...S.pill(sf),padding:"8px 12px"}}>★ {fav.length}</button>
        </div>
        {!sf&&<div style={{display:"flex",gap:6,flexWrap:"wrap",marginBottom:14}}>{["All",...HOOK_CATS].map(c=><button key={c} onClick={()=>setHf(c)} style={S.pill(hf===c)}>{c}</button>)}</div>}
        <div style={{fontSize:11,color:"#5a5a6e",marginBottom:10}}>{disp.length} hooks</div>
        {disp.map(h=>{const ri=HOOKS.indexOf(h);return<div key={ri} style={S.card}><div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",gap:8}}><div style={{flex:1}}><span style={S.lbl}>{h.cat}</span><p style={{margin:0,fontSize:14,lineHeight:1.5,color:"#d4d4de"}}>"{h.text}"</p></div><div style={{display:"flex",gap:4,flexShrink:0,marginTop:4}}><button onClick={()=>togFav(ri)} style={{background:"none",border:"1px solid rgba(255,255,255,0.1)",borderRadius:6,padding:"4px 8px",cursor:"pointer",fontSize:13,color:fav.includes(ri)?"#fbbf24":"#5a5a6e"}}>{fav.includes(ri)?"★":"☆"}</button><CopyBtn text={h.text}/></div></div></div>})}
      </div>}

      {tab===1&&<div>{FW.map((fw,i)=><div key={i} onClick={()=>setEf(ef===i?null:i)} style={{...S.card,borderColor:ef===i?fw.color+"44":"rgba(255,255,255,0.06)",cursor:"pointer",borderRadius:12,padding:"16px 18px",marginBottom:10}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}><div style={{display:"flex",alignItems:"center",gap:10}}><span style={{display:"inline-block",width:40,height:40,borderRadius:10,background:fw.color+"22",color:fw.color,fontSize:12,fontWeight:700,lineHeight:"40px",textAlign:"center"}}>{fw.abbr}</span><span style={{fontSize:14,fontWeight:600}}>{fw.name}</span></div><span style={{color:"#5a5a6e",fontSize:18}}>{ef===i?"−":"+"}</span></div>
        {ef===i&&<div style={{marginTop:14,paddingTop:12,borderTop:"1px solid rgba(255,255,255,0.06)"}}>
          <div style={{fontSize:10,fontWeight:700,textTransform:"uppercase",letterSpacing:1.5,color:"#7a7a8e",marginBottom:8}}>Steps</div>
          {fw.steps.map((s,si)=><div key={si} style={{display:"flex",gap:10,marginBottom:5}}><span style={{width:18,height:18,borderRadius:"50%",flexShrink:0,background:fw.color+"22",color:fw.color,fontSize:10,fontWeight:700,lineHeight:"18px",textAlign:"center"}}>{si+1}</span><span style={{fontSize:13,color:"#c0c0cc",lineHeight:1.4}}>{s}</span></div>)}
          <div style={{background:"rgba(0,0,0,0.3)",borderRadius:8,padding:"12px 14px",borderLeft:`3px solid ${fw.color}`,marginTop:10}}>
            <div style={{fontSize:10,fontWeight:700,textTransform:"uppercase",letterSpacing:1.5,color:"#7a7a8e",marginBottom:6}}>Example</div>
            <p style={{margin:0,fontSize:13,color:"#b0b0be",lineHeight:1.5,fontStyle:"italic"}}>{fw.ex}</p>
            <div style={{marginTop:8}}><CopyBtn text={fw.ex} label="Copy example"/></div>
          </div>
        </div>}
      </div>)}</div>}

      {tab===2&&<div>{PILLARS.map((p,pi)=><div key={pi} style={{marginBottom:18}}><div style={{display:"flex",alignItems:"center",gap:8,marginBottom:10}}><span style={{fontSize:20}}>{p.icon}</span><span style={{fontSize:15,fontWeight:700}}>{p.name}</span><span style={{fontSize:11,color:"#5a5a6e",marginLeft:"auto"}}>{p.topics.length}</span></div><div style={{display:"flex",flexWrap:"wrap",gap:6}}>{p.topics.map((t,ti)=><button key={ti} onClick={()=>copyText(t)} style={{padding:"6px 12px",borderRadius:8,fontSize:12,border:"1px solid rgba(255,255,255,0.08)",background:"rgba(255,255,255,0.03)",color:"#b0b0be",cursor:"pointer",fontFamily:"'DM Sans',sans-serif"}}>{t}</button>)}</div></div>)}<p style={{fontSize:11,color:"#5a5a6e",marginTop:8}}>Tap any topic to copy</p></div>}

      {tab===3&&<div><p style={{fontSize:13,color:"#7a7a8e",marginBottom:16,lineHeight:1.5}}>Current Canadian career stories with video angles. Tap to expand.</p>
        {NEWS.map((n,i)=><div key={i} onClick={()=>setEn(en===i?null:i)} style={{...S.card,cursor:"pointer",borderRadius:12,borderColor:en===i?"#dc262644":"rgba(255,255,255,0.06)"}}>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}><div><div style={{fontSize:14,fontWeight:600,marginBottom:4}}>🇨🇦 {n.title}</div><span style={{fontSize:11,fontWeight:600,color:"#dc2626",background:"rgba(220,38,38,0.1)",padding:"2px 8px",borderRadius:4}}>{n.stat}</span></div><span style={{color:"#5a5a6e",fontSize:18}}>{en===i?"−":"+"}</span></div>
          {en===i&&<div style={{marginTop:12,paddingTop:10,borderTop:"1px solid rgba(255,255,255,0.06)"}}>
            <p style={{fontSize:13,color:"#b0b0be",lineHeight:1.6,margin:"0 0 10px"}}>{n.detail}</p>
            <div style={{background:"rgba(139,92,246,0.06)",border:"1px solid rgba(139,92,246,0.15)",borderRadius:8,padding:"10px 12px"}}><div style={{fontSize:10,fontWeight:700,textTransform:"uppercase",letterSpacing:1.5,color:"#8b5cf6",marginBottom:4}}>Video Angle</div><p style={{margin:0,fontSize:12,color:"#a78bfa",lineHeight:1.5}}>{n.angle}</p></div>
          </div>}
        </div>)}
      </div>}

      {tab===4&&<div>{CTAS.map((c,ci)=><div key={ci} style={{marginBottom:20}}><div style={{fontSize:13,fontWeight:700,marginBottom:10,color:c.color}}>{c.emoji} {c.stage}</div>{c.items.map((item,ii)=><div key={ii} style={{...S.card,display:"flex",justifyContent:"space-between",alignItems:"center",gap:10}}><span style={{fontSize:13,color:"#c0c0cc",lineHeight:1.4}}>{item}</span><CopyBtn text={item}/></div>)}</div>)}</div>}

      {tab===5&&<div>
        {[{name:"Instagram Reels",emoji:"📱",color:"#E1306C",stats:[{l:"Sweet spot",v:"15–30s tips, 30–60s stories"},{l:"Max",v:"Up to 20 min (algo favors <90s)"},{l:"Frequency",v:"3–5/week + daily Stories"},{l:"Best times",v:"Tue–Thu 7–9 AM or 11 AM–1 PM"},{l:"Hashtags",v:"3–5 (SEO keywords > hashtags)"},{l:"#1 signal",v:"DM shares → unconnected reach"},{l:"#2 signal",v:"Saves → feed algorithm"},{l:"Non-follower reach",v:"55% default"},{l:"Sound off",v:"85% watch muted"},{l:"Trial Reels",v:"Test with non-followers risk-free"},{l:"Carousels",v:"Now up to 20 slides"},{l:"SEO",v:"Public Reels indexed by Google"}],tip:"DM shares are #1 distribution signal. SEO keywords in captions now outperform hashtags. Every video should make viewers think 'I need to send this to someone.'"},
          {name:"LinkedIn Video",emoji:"💼",color:"#0A66C2",stats:[{l:"Sweet spot",v:"30–90 seconds"},{l:"Max",v:"10 min native"},{l:"Frequency",v:"2–3/week"},{l:"Best times",v:"Tue–Thu 8–10 AM or 12–2 PM"},{l:"Hashtags",v:"3–5, end of post"},{l:"Video boost",v:"+69% vs other formats, 2x text"},{l:"Golden window",v:"First 60 min engagement"},{l:"Sound off",v:"92% watch muted"},{l:"Creator gap",v:"Only 3% post content"},{l:"Views growth",v:"+36% YoY"},{l:"AI content",v:"Downranked since Jan 2026"}],tip:"Front-load hook in first 75 chars. Algorithm rewards professional knowledge value. Saves & Sends are tracked KPIs."},
          {name:"TikTok",emoji:"🎵",color:"#00F2EA",stats:[{l:"Sweet spot",v:"15–30s discovery, 30–60s edu"},{l:"Frequency",v:"3–5/week"},{l:"Key signals",v:"70%+ completion, 5%+ engagement"},{l:"Trend cycle",v:"7–14 day peak per audio"},{l:"2026 priorities",v:"Reali-Tea, Curiosity Detours, Emotional ROI"},{l:"Biz audio",v:"Check 'Approved for Business' filter"}],tip:"Micro-series ('Day 3 of Resume Tips') drives binge behavior. Comment reply videos are a simple growth lever."},
        ].map((pl,pi)=><div key={pi} style={{...S.card,borderColor:pl.color+"22",borderRadius:14,padding:"20px 18px",marginBottom:16}}>
          <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:14}}><span style={{fontSize:24}}>{pl.emoji}</span><span style={{fontSize:18,fontWeight:700,color:pl.color}}>{pl.name}</span></div>
          {pl.stats.map((s,si)=><div key={si} style={{display:"flex",justifyContent:"space-between",padding:"7px 0",borderBottom:si<pl.stats.length-1?"1px solid rgba(255,255,255,0.04)":"none"}}><span style={{fontSize:12,color:"#7a7a8e"}}>{s.l}</span><span style={{fontSize:13,fontWeight:600,color:"#d4d4de",textAlign:"right",maxWidth:"55%"}}>{s.v}</span></div>)}
          <div style={{marginTop:14,padding:"12px 14px",borderRadius:8,background:pl.color+"0D",borderLeft:`3px solid ${pl.color}`}}><p style={{margin:0,fontSize:12,color:"#b0b0be",lineHeight:1.5}}>💡 {pl.tip}</p></div>
        </div>)}
        <div style={{...S.card,borderRadius:14,padding:"20px 18px",borderColor:"rgba(139,92,246,0.15)"}}>
          <div style={{fontSize:14,fontWeight:700,color:"#a78bfa",marginBottom:12}}>🔥 Trending Formats (April 2026)</div>
          {[{f:"Hormozi-style captions",d:"Word-by-word bold, keyword highlighted yellow/red. 15-32% engagement lift."},{f:"Educational micro-series",d:"'5 Days to a Better Resume' — numbered episodes drive follows."},{f:"Comment reply videos",d:"Turn questions into 30-second answers. Signals relevance."},{f:"Green screen commentary",d:"Resume/LinkedIn screenshots as background with expert narration."},{f:"'World Stop!' transformation",d:"One-take before/after. Perfect for coaching transformations."},{f:"Skits and role-play",d:"Play interviewer + candidate. Highest engagement for career content."},{f:"Split-screen before/after",d:"Bad resume vs good. Most saved format."},{f:"Steal My Script / Template",d:"Copy-paste content = highest save rates."}].map((t,ti)=><div key={ti} style={{marginBottom:10}}><span style={{fontSize:13,fontWeight:600,color:"#d4d4de"}}>{t.f}</span><p style={{margin:"2px 0 0",fontSize:12,color:"#8a8a9e",lineHeight:1.4}}>{t.d}</p></div>)}
        </div>
      </div>}

      {tab===6&&<div>
        {[{phase:"Week Before",time:"2–3 hrs",emoji:"📋",steps:["Choose 4 weekly themes from pillars","Plan: 2 educational + 1 story + 1 promo per week","Script 12-16 videos: hook → bullets → CTA","Select framework for each","Check 🇨🇦 News tab for timely hooks","Decide platform-specific vs cross-post"]},
          {phase:"Day 1: Film",time:"3–4 hrs",emoji:"🎬",steps:["Set up: phone, tripod, ring light, lav mic","Film all 12-16 back-to-back","Change outfits every 3-4 videos","Keep each 30-60 seconds","Film 2-3 extra evergreen as buffer","Shoot 9:16 vertical (1080×1920)"]},
          {phase:"Day 2: Edit & Schedule",time:"4–6 hrs",emoji:"✂️",steps:["Edit in CapCut/Descript — Hormozi captions","Text hook in first frame, jump cuts every 3-5s","Captions: IG (hook + keywords + 3-5 tags), LI (hook in 75 chars)","Download clean — no watermarks cross-platform","Schedule: IG Tue-Fri 7-9AM · LI Tue-Thu 8-10AM","Repurpose best scripts → text posts + newsletter"]},
          {phase:"Daily",time:"15–20 min",emoji:"💬",steps:["Engage 15 min before/after each post","Reply ALL comments within 30-60 min","DMs: keyword triggers → lead magnets","Comment on hiring managers' posts (LinkedIn)","Save top hooks to favorites (★ in Hooks tab)"]},
        ].map((p,pi)=><div key={pi} style={{...S.card,borderRadius:12,padding:"16px 18px",marginBottom:12}}>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:10}}><div style={{display:"flex",alignItems:"center",gap:8}}><span style={{fontSize:20}}>{p.emoji}</span><span style={{fontSize:15,fontWeight:700}}>{p.phase}</span></div><span style={{fontSize:11,fontWeight:600,color:"#8b5cf6",background:"rgba(139,92,246,0.1)",padding:"3px 10px",borderRadius:12}}>{p.time}</span></div>
          {p.steps.map((s,si)=><div key={si} style={{display:"flex",gap:10,marginBottom:5}}><span style={{color:"#5a5a6e",fontSize:12,marginTop:1,flexShrink:0}}>▸</span><span style={{fontSize:13,color:"#b0b0be",lineHeight:1.5}}>{s}</span></div>)}
        </div>)}
        <div style={{background:"rgba(139,92,246,0.06)",border:"1px solid rgba(139,92,246,0.15)",borderRadius:12,padding:"16px 18px"}}>
          <div style={{fontSize:13,fontWeight:700,color:"#a78bfa",marginBottom:8}}>🛠 Tools</div>
          <div style={{fontSize:12,color:"#9a9aae",lineHeight:1.8}}><strong style={{color:"#c0c0cc"}}>Plan:</strong> Notion/Sheets · <strong style={{color:"#c0c0cc"}}>Voice:</strong> AudioPen · <strong style={{color:"#c0c0cc"}}>Film:</strong> Phone+tripod+ring light+lav · <strong style={{color:"#c0c0cc"}}>Edit:</strong> CapCut/Descript/Submagic · <strong style={{color:"#c0c0cc"}}>Schedule:</strong> Meta Business Suite/Buffer · <strong style={{color:"#c0c0cc"}}>Leads:</strong> ManyChat+ConvertKit · <strong style={{color:"#c0c0cc"}}>Analytics:</strong> Native+Metricool</div>
        </div>
      </div>}

      {tab===7&&<div>
        <p style={{fontSize:13,color:"#7a7a8e",marginBottom:16,lineHeight:1.5}}>Stuck? Generate a random video concept — hook + framework + topic + CTA + platform.</p>
        <button onClick={generate} style={{width:"100%",padding:"14px",borderRadius:12,background:"linear-gradient(135deg,#8b5cf6,#6d28d9)",border:"none",color:"#fff",fontSize:15,fontWeight:700,cursor:"pointer",fontFamily:"'DM Sans',sans-serif",boxShadow:"0 4px 24px rgba(139,92,246,0.3)"}}>🎲 Generate Video Concept</button>
        {gen&&<div style={{marginTop:20,...S.card,borderColor:"rgba(139,92,246,0.2)",borderRadius:14,padding:"20px 18px"}}>
          {[{label:"Platform",value:gen.pl,emoji:gen.pl.includes("Insta")?"📱":"💼"},{label:"Pillar",value:`${gen.pillar.icon} ${gen.pillar.name}`},{label:"Topic",value:gen.topic},{label:"Framework",value:`${gen.fw.abbr} — ${gen.fw.name}`},{label:"Hook",value:`"${gen.hook.text}"`,copy:gen.hook.text},{label:"CTA",value:gen.ci,sub:gen.cs}].map((r,ri)=><div key={ri} style={{padding:"9px 0",borderBottom:ri<5?"1px solid rgba(255,255,255,0.04)":"none"}}>
            <div style={{fontSize:10,fontWeight:700,textTransform:"uppercase",letterSpacing:1.5,color:"#7a7a8e",marginBottom:3}}>{r.label}</div>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",gap:8}}><span style={{fontSize:14,color:"#d4d4de",lineHeight:1.4}}>{r.emoji&&<span style={{marginRight:6}}>{r.emoji}</span>}{r.value}{r.sub&&<span style={{fontSize:11,color:"#5a5a6e",marginLeft:6}}>({r.sub})</span>}</span>{r.copy&&<CopyBtn text={r.copy}/>}</div>
          </div>)}
          <button onClick={generate} style={{marginTop:14,width:"100%",padding:"10px",background:"rgba(139,92,246,0.1)",border:"1px solid rgba(139,92,246,0.2)",borderRadius:8,color:"#a78bfa",fontSize:13,fontWeight:600,cursor:"pointer",fontFamily:"'DM Sans',sans-serif"}}>🔄 Regenerate</button>
        </div>}
      </div>}

      {tab===8&&<div>
        <p style={{fontSize:13,color:"#7a7a8e",marginBottom:16,lineHeight:1.5}}>Generate 5 complete video scripts on one topic, each with a different framework angle. Includes full script, LinkedIn caption, and Instagram caption with ManyChat trigger.</p>
        <button onClick={()=>generateScripts()} style={{width:"100%",padding:"14px",borderRadius:12,background:"linear-gradient(135deg,#e74c3c,#c0392b)",border:"none",color:"#fff",fontSize:15,fontWeight:700,cursor:"pointer",fontFamily:"'DM Sans',sans-serif",boxShadow:"0 4px 24px rgba(231,76,60,0.3)"}}>🎬 Generate 5 Scripts</button>

        {scripts&&<div style={{marginTop:20}}>
          <div style={{...S.card,borderColor:"rgba(139,92,246,0.2)",borderRadius:12,padding:"16px 18px",display:"flex",alignItems:"center",gap:10,marginBottom:12}}>
            <span style={{fontSize:22}}>{scripts.pillar.icon}</span>
            <div>
              <div style={{fontSize:10,fontWeight:700,textTransform:"uppercase",letterSpacing:1.5,color:"#8b5cf6",marginBottom:2}}>Topic</div>
              <div style={{fontSize:15,fontWeight:600,color:"#e8e8f0"}}>{scripts.topic}</div>
              <div style={{fontSize:11,color:"#7a7a8e"}}>{scripts.pillar.name}</div>
            </div>
          </div>

          <div style={{display:"flex",gap:8,marginBottom:16}}>
            <button onClick={()=>generateScripts()} style={{flex:1,padding:"10px",borderRadius:8,background:"rgba(231,76,60,0.1)",border:"1px solid rgba(231,76,60,0.2)",color:"#e74c3c",fontSize:13,fontWeight:600,cursor:"pointer",fontFamily:"'DM Sans',sans-serif"}}>🔄 New Topic</button>
            <button onClick={()=>generateScripts(scripts.pillar,scripts.topic)} style={{flex:1,padding:"10px",borderRadius:8,background:"rgba(139,92,246,0.1)",border:"1px solid rgba(139,92,246,0.2)",color:"#a78bfa",fontSize:13,fontWeight:600,cursor:"pointer",fontFamily:"'DM Sans',sans-serif"}}>🎲 New Angles</button>
          </div>

          {scripts.variations.map((v,vi)=><div key={vi} style={{...S.card,cursor:"pointer",borderColor:sv===vi?v.fw.color+"44":"rgba(255,255,255,0.06)",borderRadius:12,padding:"16px 18px",marginBottom:10}} onClick={()=>setSv(sv===vi?null:vi)}>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
              <div style={{display:"flex",alignItems:"center",gap:10}}>
                <span style={{display:"inline-block",width:34,height:34,borderRadius:8,background:v.fw.color+"22",color:v.fw.color,fontSize:11,fontWeight:700,lineHeight:"34px",textAlign:"center"}}>V{vi+1}</span>
                <div><span style={{fontSize:14,fontWeight:600}}>{v.fw.name}</span><span style={{fontSize:11,color:"#7a7a8e",marginLeft:8}}>({v.fw.abbr})</span></div>
              </div>
              <span style={{color:"#5a5a6e",fontSize:18}}>{sv===vi?"−":"+"}</span>
            </div>

            {sv===vi&&<div style={{marginTop:14,paddingTop:12,borderTop:"1px solid rgba(255,255,255,0.06)"}} onClick={e=>e.stopPropagation()}>

              <div style={{marginBottom:20}}>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:10}}>
                  <div style={{fontSize:12,fontWeight:700,textTransform:"uppercase",letterSpacing:1.5,color:"#e74c3c"}}>🎤 Script (~45–60s)</div>
                  <CopyBtn text={v.scriptText} label="Copy script"/>
                </div>

                <div style={{background:"rgba(231,76,60,0.08)",borderLeft:"3px solid #e74c3c",borderRadius:"0 8px 8px 0",padding:"10px 14px",marginBottom:8}}>
                  <div style={{fontSize:10,fontWeight:700,color:"#e74c3c",marginBottom:4}}>HOOK — 0:00</div>
                  <p style={{margin:0,fontSize:14,color:"#e8e8f0",fontStyle:"italic",lineHeight:1.5}}>"{v.hook.text}"</p>
                  <div style={{fontSize:10,color:"#7a7a8e",marginTop:4}}>{v.hook.cat}</div>
                </div>

                {v.beats.map((b,bi)=><div key={bi} style={{background:"rgba(255,255,255,0.02)",borderLeft:`3px solid ${v.fw.color}44`,borderRadius:"0 8px 8px 0",padding:"10px 14px",marginBottom:6}}>
                  <div style={{fontSize:10,fontWeight:700,color:v.fw.color,marginBottom:4}}>STEP {bi+1} — {b.time}</div>
                  <p style={{margin:0,fontSize:13,color:"#c0c0cc",lineHeight:1.5}}>{b.step}</p>
                </div>)}

                <div style={{background:"rgba(39,174,96,0.08)",borderLeft:"3px solid #27ae60",borderRadius:"0 8px 8px 0",padding:"10px 14px",marginBottom:8}}>
                  <div style={{fontSize:10,fontWeight:700,color:"#27ae60",marginBottom:4}}>CTA — 0:45</div>
                  <p style={{margin:0,fontSize:14,color:"#e8e8f0",fontStyle:"italic",lineHeight:1.5}}>"{v.ci}"</p>
                  <div style={{fontSize:10,color:"#7a7a8e",marginTop:4}}>{v.cs}</div>
                </div>

                <div style={{background:"rgba(0,0,0,0.3)",borderRadius:8,padding:"10px 14px",marginTop:8}}>
                  <div style={{fontSize:10,fontWeight:700,color:"#7a7a8e",marginBottom:4}}>💡 EXAMPLE FOR INSPIRATION</div>
                  <p style={{margin:0,fontSize:12,color:"#9a9aae",lineHeight:1.5,fontStyle:"italic"}}>"{v.fw.ex}"</p>
                </div>
              </div>

              <div style={{marginBottom:20}}>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:8}}>
                  <div style={{fontSize:12,fontWeight:700,textTransform:"uppercase",letterSpacing:1.5,color:"#0A66C2"}}>💼 LinkedIn</div>
                  <CopyBtn text={v.liCaption} label="Copy caption"/>
                </div>
                <div style={{background:"rgba(10,102,194,0.06)",border:"1px solid rgba(10,102,194,0.15)",borderRadius:8,padding:"12px 14px"}}>
                  <pre style={{margin:0,fontSize:12,color:"#b0b0be",lineHeight:1.6,whiteSpace:"pre-wrap",fontFamily:"'DM Sans',sans-serif"}}>{v.liCaption}</pre>
                </div>
                <div style={{fontSize:11,color:"#5a5a6e",marginTop:6,lineHeight:1.5}}>📌 Post Tue–Thu 8–10 AM · Engage in comments first 60 min · Pin a value-add comment</div>
              </div>

              <div>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:8}}>
                  <div style={{fontSize:12,fontWeight:700,textTransform:"uppercase",letterSpacing:1.5,color:"#E1306C"}}>📱 Instagram + ManyChat</div>
                  <CopyBtn text={v.igCaption} label="Copy caption"/>
                </div>
                <div style={{background:"rgba(225,48,108,0.06)",border:"1px solid rgba(225,48,108,0.15)",borderRadius:8,padding:"12px 14px"}}>
                  <pre style={{margin:0,fontSize:12,color:"#b0b0be",lineHeight:1.6,whiteSpace:"pre-wrap",fontFamily:"'DM Sans',sans-serif"}}>{v.igCaption}</pre>
                </div>
                <div style={{background:"rgba(139,92,246,0.06)",border:"1px solid rgba(139,92,246,0.15)",borderRadius:8,padding:"10px 12px",marginTop:8}}>
                  <div style={{fontSize:10,fontWeight:700,color:"#8b5cf6",marginBottom:4}}>MANYCHAT AUTOMATION</div>
                  <p style={{margin:0,fontSize:12,color:"#a78bfa"}}>Trigger keyword: <strong>"{v.kw}"</strong> → Send {v.res} link</p>
                </div>
                <div style={{fontSize:11,color:"#5a5a6e",marginTop:6,lineHeight:1.5}}>📌 Post as Reel · Share to Story with "DM me {v.kw} 👇" sticker · Reply to comments within 30 min</div>
              </div>

            </div>}
          </div>)}
        </div>}
      </div>}
    </div>
  </div>);
}
