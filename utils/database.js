/**
 * Database wrapper for SQLite (better-sqlite3)
 * Provides methods similar to Mongoose models
 */

const Database = require('better-sqlite3');
const path = require('path');
const bcrypt = require('bcryptjs');

const DB_PATH = process.env.DATABASE_PATH || path.join(__dirname, '../data/vitis_ai.db');

class DatabaseWrapper {
  constructor() {
    this.db = new Database(DB_PATH);
    this.db.pragma('foreign_keys = ON');
    
    // Prepare statements for better performance
    this.prepareStatements();
  }

  prepareStatements() {
    // User statements
    this.stmts = {
      // Users
      getUserById: this.db.prepare('SELECT * FROM users WHERE id = ?'),
      getUserByEmail: this.db.prepare('SELECT * FROM users WHERE email = ?'),
      getUserByUsername: this.db.prepare('SELECT * FROM users WHERE username = ?'),
      createUser: this.db.prepare(`
        INSERT INTO users (username, email, password, full_name, organization, role)
        VALUES (?, ?, ?, ?, ?, ?)
      `),
      updateUser: this.db.prepare(`
        UPDATE users SET full_name = ?, organization = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
      `),
      updateUserLastLogin: this.db.prepare(`
        UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
      `),
      incrementEvaluationCount: this.db.prepare(`
        UPDATE users SET evaluation_count = evaluation_count + 1 WHERE id = ?
      `),
      decrementEvaluationCount: this.db.prepare(`
        UPDATE users SET evaluation_count = MAX(0, evaluation_count - 1) WHERE id = ?
      `),
      
      // Evaluations
      createEvaluation: this.db.prepare(`
        INSERT INTO evaluations (
          user_id, location_type, location_coords, region,
          climate_avg_temp_year, climate_avg_temp_growing_season, climate_min_temp_winter,
          climate_max_temp_summer, climate_growing_degree_days, climate_rainfall_year,
          climate_rainfall_summer, climate_humidity_avg, climate_sunshine_hours,
          climate_frost_days, climate_huglin_index, climate_cool_night_index,
          relief_elevation, relief_slope, relief_aspect, relief_tpi, relief_insolation,
          relief_distance_to_sea,
          soil_soil_type, soil_soil_ph, soil_organic_matter, soil_soil_drainage, soil_soil_texture,
          satellite_ndvi, satellite_ndwi, satellite_cloud_coverage,
          geo_latitude, geo_longitude, geo_distance_to_river,
          suitability_score, category, confidence, model_version,
          shap_values, top_factors, risks, recommendations,
          processing_time_ms, cached, cache_expiry
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `),
      getEvaluationById: this.db.prepare('SELECT * FROM evaluations WHERE id = ?'),
      getEvaluationByUserAndId: this.db.prepare('SELECT * FROM evaluations WHERE id = ? AND user_id = ?'),
      getEvaluationsByUser: this.db.prepare(`
        SELECT * FROM evaluations WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?
      `),
      countEvaluationsByUser: this.db.prepare('SELECT COUNT(*) as count FROM evaluations WHERE user_id = ?'),
      deleteEvaluation: this.db.prepare('DELETE FROM evaluations WHERE id = ? AND user_id = ?'),
      findCachedEvaluation: this.db.prepare(`
        SELECT * FROM evaluations 
        WHERE geo_latitude = ? AND geo_longitude = ? AND cached = 1 AND cache_expiry > datetime('now')
        LIMIT 1
      `),
      getEvaluationsAsGeoJSON: this.db.prepare(`
        SELECT id, location_type, location_coords, suitability_score, category, region, created_at
        FROM evaluations WHERE user_id = ? LIMIT ?
      `)
    };
  }

  // ============================================
  // User Methods
  // ============================================

  async createUser(userData) {
    try {
      const { username, email, password, fullName, organization, role = 'user' } = userData;
      
      // Check if user exists
      const existingEmail = this.stmts.getUserByEmail.get(email);
      if (existingEmail) {
        throw new Error('Email already registered');
      }
      
      const existingUsername = this.stmts.getUserByUsername.get(username);
      if (existingUsername) {
        throw new Error('Username already taken');
      }
      
      // Hash password
      const salt = await bcrypt.genSalt(10);
      const hashedPassword = await bcrypt.hash(password, salt);
      
      const result = this.stmts.createUser.run(username, email, hashedPassword, fullName || null, organization || null, role);
      
      return {
        id: result.lastInsertRowid,
        username,
        email,
        full_name: fullName,
        organization,
        role,
        is_active: true,
        created_at: new Date().toISOString()
      };
    } catch (error) {
      throw error;
    }
  }

  async getUserByEmail(email) {
    const user = this.stmts.getUserByEmail.get(email);
    if (!user) return null;
    
    return {
      ...user,
      _id: user.id,
      toJSON: () => {
        const { password, ...userWithoutPassword } = user;
        return userWithoutPassword;
      }
    };
  }

  async getUserById(id) {
    const user = this.stmts.getUserById.get(id);
    if (!user) return null;
    
    return {
      ...user,
      _id: user.id,
      toJSON: () => {
        const { password, ...userWithoutPassword } = user;
        return userWithoutPassword;
      },
      updateLastLogin: async () => {
        this.stmts.updateUserLastLogin.run(id);
      },
      save: async () => {
        this.stmts.updateUser.run(user.full_name, user.organization, id);
      }
    };
  }

  async comparePassword(user, candidatePassword) {
    const userData = this.stmts.getUserById.get(user.id);
    if (!userData) return false;
    
    return await bcrypt.compare(candidatePassword, userData.password);
  }

  async updateUserProfile(userId, updates) {
    const { fullName, organization } = updates;
    this.stmts.updateUser.run(fullName, organization, userId);
    return this.getUserById(userId);
  }

  async incrementEvaluationCount(userId) {
    this.stmts.incrementEvaluationCount.run(userId);
  }

  async decrementEvaluationCount(userId) {
    this.stmts.decrementEvaluationCount.run(userId);
  }

  // ============================================
  // Evaluation Methods
  // ============================================

  async createEvaluation(evaluationData) {
    const {
      userId,
      location,
      region,
      features,
      prediction,
      shapValues,
      topFactors,
      risks,
      recommendations,
      processingTimeMs,
      cached,
      cacheExpiry
    } = evaluationData;

    const coords = JSON.stringify(location.coordinates);
    
    const result = this.stmts.createEvaluation.run(
      userId,
      location.type,
      coords,
      region,
      
      // Climate
      features.climate?.avg_temp_year,
      features.climate?.avg_temp_growing_season,
      features.climate?.min_temp_winter,
      features.climate?.max_temp_summer,
      features.climate?.growing_degree_days,
      features.climate?.rainfall_year,
      features.climate?.rainfall_summer,
      features.climate?.humidity_avg,
      features.climate?.sunshine_hours,
      features.climate?.frost_days,
      features.climate?.huglin_index,
      features.climate?.cool_night_index,
      
      // Relief
      features.relief?.elevation,
      features.relief?.slope,
      features.relief?.aspect,
      features.relief?.tpi,
      features.relief?.insolation,
      features.relief?.distance_to_sea,
      
      // Soil
      features.soil?.soil_type,
      features.soil?.soil_ph,
      features.soil?.organic_matter,
      features.soil?.soil_drainage,
      features.soil?.soil_texture,
      
      // Satellite
      features.satellite?.ndvi,
      features.satellite?.ndwi,
      features.satellite?.cloud_coverage,
      
      // Geographic
      features.geographic?.latitude,
      features.geographic?.longitude,
      features.geographic?.distance_to_river,
      
      // Prediction
      prediction.suitability_score,
      prediction.category,
      prediction.confidence || 'medium',
      prediction.model_version || '1.0.0',
      
      // JSON fields
      JSON.stringify(shapValues || []),
      JSON.stringify(topFactors || []),
      JSON.stringify(risks || {}),
      JSON.stringify(recommendations || {}),
      
      processingTimeMs,
      cached ? 1 : 0,
      cacheExpiry ? new Date(cacheExpiry).toISOString() : null
    );

    return this.getEvaluationById(result.lastInsertRowid);
  }

  getEvaluationById(id) {
    const evaluation = this.stmts.getEvaluationById.get(id);
    if (!evaluation) return null;
    
    return this._transformEvaluation(evaluation);
  }

  getEvaluationByUserAndId(userId, id) {
    const evaluation = this.stmts.getEvaluationByUserAndId.get(id, userId);
    if (!evaluation) return null;
    
    return this._transformEvaluation(evaluation);
  }

  getEvaluationsByUser(userId, page = 1, limit = 20) {
    const offset = (page - 1) * limit;
    const evaluations = this.stmts.getEvaluationsByUser.all(userId, limit, offset);
    
    return evaluations.map(e => this._transformEvaluation(e, true));
  }

  countEvaluationsByUser(userId) {
    const result = this.stmts.countEvaluationsByUser.get(userId);
    return result.count;
  }

  deleteEvaluation(userId, id) {
    const result = this.stmts.deleteEvaluation.run(id, userId);
    return result.changes > 0;
  }

  async findCachedEvaluation(longitude, latitude) {
    const cachedEval = this.stmts.findCachedEvaluation.get(latitude, longitude);
    if (!cachedEval) return null;
    
    return this._transformEvaluation(cachedEval);
  }

  getEvaluationsAsGeoJSON(userId, limit = 100) {
    const evaluations = this.stmts.getEvaluationsAsGeoJSON.all(userId, limit);
    
    return {
      type: 'FeatureCollection',
      features: evaluations.map(e => ({
        type: 'Feature',
        geometry: {
          type: e.location_type,
          coordinates: JSON.parse(e.location_coords)
        },
        properties: {
          id: e.id,
          suitability_score: e.suitability_score,
          category: e.category,
          region: e.region,
          created_at: e.created_at
        }
      }))
    };
  }

  _transformEvaluation(evaluation, excludeShap = false) {
    const transformed = {
      id: evaluation.id,
      _id: evaluation.id,
      user: evaluation.user_id,
      location: {
        type: evaluation.location_type,
        coordinates: JSON.parse(evaluation.location_coords)
      },
      region: evaluation.region,
      features: {
        climate: {
          avg_temp_year: evaluation.climate_avg_temp_year,
          avg_temp_growing_season: evaluation.climate_avg_temp_growing_season,
          min_temp_winter: evaluation.climate_min_temp_winter,
          max_temp_summer: evaluation.climate_max_temp_summer,
          growing_degree_days: evaluation.climate_growing_degree_days,
          rainfall_year: evaluation.climate_rainfall_year,
          rainfall_summer: evaluation.climate_rainfall_summer,
          humidity_avg: evaluation.climate_humidity_avg,
          sunshine_hours: evaluation.climate_sunshine_hours,
          frost_days: evaluation.climate_frost_days,
          huglin_index: evaluation.climate_huglin_index,
          cool_night_index: evaluation.climate_cool_night_index
        },
        relief: {
          elevation: evaluation.relief_elevation,
          slope: evaluation.relief_slope,
          aspect: evaluation.relief_aspect,
          tpi: evaluation.relief_tpi,
          insolation: evaluation.relief_insolation,
          distance_to_sea: evaluation.relief_distance_to_sea
        },
        soil: {
          soil_type: evaluation.soil_soil_type,
          soil_ph: evaluation.soil_soil_ph,
          organic_matter: evaluation.soil_organic_matter,
          soil_drainage: evaluation.soil_soil_drainage,
          soil_texture: evaluation.soil_soil_texture
        },
        satellite: {
          ndvi: evaluation.satellite_ndvi,
          ndwi: evaluation.satellite_ndwi,
          cloud_coverage: evaluation.satellite_cloud_coverage
        },
        geographic: {
          latitude: evaluation.geo_latitude,
          longitude: evaluation.geo_longitude,
          distance_to_river: evaluation.geo_distance_to_river
        }
      },
      prediction: {
        suitability_score: evaluation.suitability_score,
        category: evaluation.category,
        confidence: evaluation.confidence,
        model_version: evaluation.model_version
      },
      shap_values: excludeShap ? undefined : JSON.parse(evaluation.shap_values || '[]'),
      top_factors: JSON.parse(evaluation.top_factors || '[]'),
      risks: JSON.parse(evaluation.risks || '{}'),
      recommendations: JSON.parse(evaluation.recommendations || '{}'),
      status: evaluation.status,
      processing_time_ms: evaluation.processing_time_ms,
      cached: Boolean(evaluation.cached),
      cache_expiry: evaluation.cache_expiry,
      createdAt: evaluation.created_at,
      updatedAt: evaluation.updated_at,
      
      // Helper methods
      isCacheExpired: function() {
        if (!this.cached || !this.cache_expiry) return true;
        return new Date() > new Date(this.cache_expiry);
      },
      toGeoJSON: function() {
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
    };
    
    return transformed;
  }

  close() {
    this.db.close();
  }
}

// Singleton instance
let dbInstance = null;

function getDb() {
  if (!dbInstance) {
    dbInstance = new DatabaseWrapper();
  }
  return dbInstance;
}

module.exports = {
  DatabaseWrapper,
  getDb
};
