/**
 * User Routes
 * История оценок, профиль пользователя (SQLite)
 */

const express = require('express');
const router = express.Router();
const Evaluation = require('../models/Evaluation');
const User = require('../models/User');
const { getDb } = require('../models/User');

/**
 * GET /api/user/history
 * Получить историю оценок пользователя
 */
router.get('/history', async (req, res, next) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;
    const offset = (page - 1) * limit;

    const evaluations = Evaluation.findByUserId(req.user.id, limit, offset);
    const total = Evaluation.countByUserId(req.user.id);

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
    const user = User.findById(req.user.id);
    
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
    const db = getDb();
    
    const stmt = db.prepare(`
      UPDATE users 
      SET full_name = COALESCE(?, full_name), 
          organization = COALESCE(?, organization),
          updated_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `);
    
    stmt.run(fullName || null, organization || null, req.user.id);
    
    const updatedUser = User.findById(req.user.id);
    
    res.json({
      success: true,
      message: 'Profile updated successfully',
      data: updatedUser
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
    const db = getDb();
    
    // Check if evaluation exists and belongs to user
    const evaluation = db.prepare(
      'SELECT id FROM evaluations WHERE id = ? AND user_id = ?'
    ).get(parseInt(req.params.id), req.user.id);

    if (!evaluation) {
      return res.status(404).json({
        success: false,
        message: 'Evaluation not found'
      });
    }

    // Delete evaluation
    db.prepare('DELETE FROM evaluations WHERE id = ?').run(evaluation.id);

    // Decrement evaluation count
    db.prepare(
      'UPDATE users SET evaluation_count = MAX(0, evaluation_count - 1) WHERE id = ?'
    ).run(req.user.id);

    res.json({
      success: true,
      message: 'Evaluation deleted successfully'
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
