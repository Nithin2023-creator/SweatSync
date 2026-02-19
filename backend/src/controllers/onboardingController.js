const geminiService = require('../services/geminiService');

const getNextStep = async (req, res) => {
    const { chat_history } = req.body;

    if (!Array.isArray(chat_history)) {
        return res.status(400).json({ error: "chat_history is required and must be an array" });
    }

    try {
        const nextStep = await geminiService.getNextOnboardingStep(chat_history);
        res.json(nextStep);
    } catch (error) {
        res.status(500).json({ error: "Failed to generate next step", details: error.message });
    }
};

module.exports = { getNextStep };
