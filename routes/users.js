/**
 * User Routes
 * История оценок, профиль пользователя
 */

const express = require('express');
const router = express.Router();
const Evaluation = require('../models/Evaluation');
const User = require('../models/User');

/**
 * GET /api/user/history
 * Получить историю оценок пользователя
 */
router.get('/history', async (req, res, next) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;

    const evaluations = await Evaluation.findByUser(req.user.id, page, limit);

    const total = await Evaluation.countByUser(req.user.id);

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
    const user = await User.findById(req.user.id);
    
    res.json({
      success: true,
      data: user.toJSON()
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
    
    const user = await User.findById(req.user.id);
    if (fullName) user.fullName = fullName;
    if (organization) user.organization = organization;
    
    await user.save();
    
    res.json({
      success: true,
      message: 'Profile updated successfully',
      data: user.toJSON()
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
    const deleted = await Evaluation.deleteByUserAndId(req.user.id, req.params.id);

    if (!deleted) {
      return res.status(404).json({
        success: false,
        message: 'Evaluation not found'
      });
    }

    // Decrement evaluation count
    const db = require('../utils/database').getDb();
    db.decrementEvaluationCount(req.user.id);

    res.json({
      success: true,
      message: 'Evaluation deleted successfully'
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
