/**
 * Evaluation Model (SQLite version)
 * Модель оценки участка для виноделия
 * 
 * Хранит:
 * - GeoJSON координаты участка (точка или полигон)
 * - Признаки (features) из различных источников
 * - Результаты ML-модели (вероятность пригодности)
 * - SHAP values для интерпретации
 * - Историю оценок пользователя
 */

const { getDb } = require('../utils/database');

class Evaluation {
  constructor(evaluationData) {
    if (evaluationData) {
      this.id = evaluationData.id || evaluationData._id;
      this.user = evaluationData.user || evaluationData.user_id;
      this.location = evaluationData.location;
      this.region = evaluationData.region;
      this.features = evaluationData.features;
      this.prediction = evaluationData.prediction;
      this.shap_values = evaluationData.shap_values;
      this.top_factors = evaluationData.top_factors;
      this.risks = evaluationData.risks;
      this.recommendations = evaluationData.recommendations;
      this.status = evaluationData.status || 'completed';
      this.processing_time_ms = evaluationData.processing_time_ms;
      this.cached = evaluationData.cached || false;
      this.cache_expiry = evaluationData.cache_expiry;
      this.createdAt = evaluationData.createdAt || evaluationData.created_at;
      this.updatedAt = evaluationData.updatedAt || evaluationData.updated_at;
    }
  }

  static async create(evaluationData) {
    const db = getDb();
    return await db.createEvaluation(evaluationData);
  }

  static async findById(id) {
    const db = getDb();
    return db.getEvaluationById(id);
  }

  static async findByUserAndId(userId, id) {
    const db = getDb();
    return db.getEvaluationByUserAndId(userId, id);
  }

  static async findByUser(userId, page = 1, limit = 20) {
    const db = getDb();
    return db.getEvaluationsByUser(userId, page, limit);
  }

  static async countByUser(userId) {
    const db = getDb();
    return db.countEvaluationsByUser(userId);
  }

  static async deleteByUserAndId(userId, id) {
    const db = getDb();
    return db.deleteEvaluation(userId, id);
  }

  static async findCached(longitude, latitude) {
    const db = getDb();
    return await db.findCachedEvaluation(longitude, latitude);
  }

  static async getAsGeoJSON(userId, limit = 100) {
    const db = getDb();
    return db.getEvaluationsAsGeoJSON(userId, limit);
  }

  categorizeScore() {
    const score = this.prediction.suitability_score;
    if (score < 40) {
      this.prediction.category = 'low';
    } else if (score < 70) {
      this.prediction.category = 'medium';
    } else {
      this.prediction.category = 'high';
    }
  }

  isCacheExpired() {
    if (!this.cached || !this.cache_expiry) {
      return true;
    }
    return new Date() > new Date(this.cache_expiry);
  }

  toGeoJSON() {
    return {
      type: 'Feature',
      geometry: this.location,
      properties: {
        id: this.id,
        suitability_score: this.prediction.suitability_score,
        category: this.prediction.category,
        region: this.region,
        created_at: this.createdAt
      }
    };
  }

  async save() {
    // For SQLite, we don't have a direct update method yet
    // This would need to be implemented in the database wrapper
    throw new Error('Update not implemented for Evaluation model');
  }
}

module.exports = Evaluation;
