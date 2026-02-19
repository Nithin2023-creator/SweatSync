const { GoogleGenerativeAI } = require("@google/generative-ai");

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

const model = genAI.getGenerativeModel({
    model: "gemini-1.5-flash",
    generationConfig: {
        responseMimeType: "application/json",
    },
});

const SYSTEM_PROMPT = `
You are an elite fitness coach conducting an intake interview for SweatSync.
Your goal is to gather a complete fitness psychographic profile (Biometrics, Goal, Constraints, Friction Points).

Required fields to eventually populate:
- age
- sex
- weight_kg
- height_cm
- goals
- experience_level
- allowed_days
- available_equipment
- medical_flags
- injuries_description

RULES:
1. Ask one topic per turn (you may combine closely related fields like weight+height).
2. Always return 3-4 contextually relevant options + "Other" for choice questions.
3. "Other" must ALWAYS be the last item in the predicted_options array.
4. When all fields are gathered, return onboarding_complete=true and populate the 'sho' object.
5. ALWAYS respond in valid JSON matching this exact schema:
{
  "agent_message": "string (conversational text)",
  "input_type": "string (e.g., 'single_choice', 'multi_choice', 'number', 'number_pair', 'complete')",
  "predicted_options": ["string array (3-4 options + 'Other')"],
  "onboarding_complete": "boolean",
  "sho": "object or null"
}
`;

async function getNextOnboardingStep(chatHistory) {
    try {
        const chat = model.startChat({
            history: [
                {
                    role: "user",
                    parts: [{ text: SYSTEM_PROMPT }],
                },
                ...chatHistory.map((msg) => ({
                    role: msg.role === "assistant" ? "model" : "user",
                    parts: [{ text: msg.content }],
                })),
            ],
        });

        const result = await chat.sendMessage("Determine the next onboarding step.");
        const response = await result.response;
        const text = response.text();
        return JSON.parse(text);
    } catch (error) {
        console.error("Gemini Service Error:", error);
        throw error;
    }
}

module.exports = { getNextOnboardingStep };
