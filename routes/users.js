/**
 * User Routes
 * История оценок, профиль пользователя
 */

const express = require('express');
const router = express.Router();
const Evaluation = require('../models/Evaluation');

/**
 * GET /api/user/history
 * Получить историю оценок пользователя
 */
router.get('/history', async (req, res, next) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;
    const skip = (page - 1) * limit;

    const evaluations = await Evaluation.find({
      user: req.user._id
    })
    .sort({ createdAt: -1 })
    .skip(skip)
    .limit(limit)
    .select('-shap_values'); // Exclude detailed SHAP values for list view

    const total = await Evaluation.countDocuments({
      user: req.user._id
    });

    res.json({
      success: true,
      data: {
        evaluations,
        pagination: {
          current_page: page,
          total_pages: Math.ceil(total / limit),
          total_items: total,
          items_per_page: limit
        }
      }
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/user/profile
 * Получить профиль пользователя
 */
router.get('/profile', async (req, res, next) => {
  try {
    const user = await req.user.constructor.findById(req.user._id);
    
    res.json({
      success: true,
      data: user
    });
  } catch (error) {
    next(error);
  }
});

/**
 * PUT /api/user/profile
 * Обновить профиль пользователя
 */
router.put('/profile', async (req, res, next) => {
  try {
    const { fullName, organization } = req.body;
    
    if (fullName) req.user.fullName = fullName;
    if (organization) req.user.organization = organization;
    
    await req.user.save();
    
    res.json({
      success: true,
      message: 'Profile updated successfully',
      data: req.user
    });
  } catch (error) {
    next(error);
  }
});

/**
 * DELETE /api/user/evaluation/:id
 * Удалить оценку из истории
 */
router.delete('/evaluation/:id', async (req, res, next) => {
  try {
    const evaluation = await Evaluation.findOneAndDelete({
      _id: req.params.id,
      user: req.user._id
    });

    if (!evaluation) {
      return res.status(404).json({
        success: false,
        message: 'Evaluation not found'
      });
    }

    // Decrement evaluation count
    await req.user.updateOne({
      $inc: { evaluationCount: -1 }
    });

    res.json({
      success: true,
      message: 'Evaluation deleted successfully'
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
