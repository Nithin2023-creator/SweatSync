const express = require('express');
const router = express.Router();
const onboardingController = require('../controllers/onboardingController');

router.post('/next-step', onboardingController.getNextStep);

module.exports = router;
