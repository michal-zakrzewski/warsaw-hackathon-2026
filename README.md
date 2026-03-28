# warsaw-hackathon-2026

Short idea description
GreenCredit Copilot is a multimodal AI assistant for farmers that helps them discover the best green investment to make, estimate ROI and carbon/energy impact, and identify which green loan or grant they are most likely to qualify for. Instead of making farmers search through financing programs and technical requirements manually, the system collects business information through voice and uploaded media, analyzes the opportunity, and returns a clear recommendation with application-ready guidance.
This fits the hackathon theme well because it is built as a multimodal agent system using voice, text, images/documents, and tool-based reasoning on the Google stack, with Vapi as the conversational layer.  
⸻
Demo workflow
1. Voice intake
The farmer starts by talking to the assistant through Vapi.
The assistant asks simple questions like:
• where is your farm located,
• what is your current energy usage,
• what equipment or buildings do you have,
• what is your goal: lower bills, energy independence, grant, or loan.
This creates a natural onboarding flow instead of a long form.
2. Multimodal input
The user then uploads:
• farm address,
• a photo or short video,
• optionally an electricity bill or short PDF.
3. Agent analysis
The system processes all inputs and evaluates a few possible initiatives, for example:
• solar panels,
• battery storage,
• insulation / efficiency upgrade.
It then estimates:
• expected savings,
• ROI / payback period,
• carbon reduction,
• likely matching financing programs.
4. Decision output
The platform shows:
• the best project,
• the best financing option,
• projected ROI,
• required documents / missing info,
• explanation of why this is the recommended path.
5. Wow moment
The assistant can also show a “before vs after” recommendation:
“Right now you do not meet the threshold for Program B.
If you install a 20 kW solar system, your projected savings and emissions reduction improve enough to make this a better-fit application.”
⸻
How multimodal agents work behind the scenes
1. Intake Agent
Handles the voice conversation through Vapi.
Its job is to collect structured business and farm information from natural speech.
2. Document & Media Agent
Takes uploaded images, videos, and bills/PDFs and extracts useful signals:
• farm/building type,
• possible roof or equipment context,
• utility data,
• missing fields.
3. Simulation Agent
Runs deterministic calculations for:
• solar generation,
• energy savings,
• ROI,
• carbon reduction.
This should be code-based, not LLM-based.
4. Financing Agent
Matches the farm/project profile against a small set of green financing programs and checks basic eligibility logic.
5. Strategy Agent
Combines everything and answers the key question:
“What should this farmer do next to maximize value and improve qualification chances?”
This is the main “agentic” layer because it reasons across multiple inputs, tools, and outputs rather than just answering one prompt.
⸻
Why multimodal agents are useful here
A normal chatbot would just give generic advice.
A multimodal agent can:
• talk to the user naturally,
• read uploaded files,
• understand photos/documents,
• run calculations,
• compare options,
• produce a concrete recommendation.
So the value is not just conversation — it is decision-making from mixed real-world inputs.
⸻
Very short pitch version
GreenCredit Copilot is a multimodal AI agent for farmers that interviews users by voice, analyzes farm data from media and documents, estimates ROI for green upgrades, and recommends the financing option they are most likely to qualify for.
