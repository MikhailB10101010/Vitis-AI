/**
 * Evaluation Model
 * Модель оценки участка для виноделия (SQLite)
 * 
 * Хранит:
 * - Координаты участка (точка или полигон)
 * - Признаки (features) из различных источников
 * - Результаты ML-модели (вероятность пригодности)
 * - SHAP values для интерпретации
 * - Историю оценок пользователя
 */

const Database = require('better-sqlite3');
const path = require('path');
const { getDb } = require('./User');

class Evaluation {
  constructor(db) {
    this.db = db;
    this.initTable();
  }

  initTable() {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        location_type TEXT CHECK(location_type IN ('Point', 'Polygon')),
        location_coords TEXT NOT NULL,
        region TEXT,
        features_climate_avg_temp_year REAL,
        features_climate_avg_temp_growing_season REAL,
        features_climate_min_temp_winter REAL,
        features_climate_max_temp_summer REAL,
        features_climate_growing_degree_days REAL,
        features_climate_rainfall_year REAL,
        features_climate_rainfall_summer REAL,
        features_climate_humidity_avg REAL,
        features_climate_sunshine_hours REAL,
        features_climate_frost_days REAL,
        features_climate_huglin_index REAL,
        features_climate_cool_night_index REAL,
        features_relief_elevation REAL,
        features_relief_slope REAL,
        features_relief_aspect REAL,
        features_relief_tpi REAL,
        features_relief_insolation REAL,
        features_relief_distance_to_sea REAL,
        features_soil_soil_type TEXT,
        features_soil_soil_ph REAL,
        features_soil_organic_matter REAL,
        features_soil_soil_drainage TEXT,
        features_soil_soil_texture TEXT,
        features_satellite_ndvi REAL,
        features_satellite_ndwi REAL,
        features_satellite_cloud_coverage REAL,
        features_geographic_latitude REAL,
        features_geographic_longitude REAL,
        features_geographic_distance_to_river REAL,
        prediction_suitability_score REAL NOT NULL,
        prediction_category TEXT CHECK(prediction_category IN ('low', 'medium', 'high')) NOT NULL,
        prediction_confidence TEXT DEFAULT 'medium',
        prediction_model_version TEXT DEFAULT '1.0.0',
        shap_values TEXT,
        top_factors TEXT,
        risks_frost_level TEXT,
        risks_frost_description TEXT,
        risks_drought_level TEXT,
        risks_drought_description TEXT,
        risks_heatwave_level TEXT,
        risks_heatwave_description TEXT,
        recommendations_suitable_varieties TEXT,
        recommendations_planting_advice TEXT,
        recommendations_irrigation_needs TEXT,
        status TEXT DEFAULT 'completed' CHECK(status IN ('pending', 'completed', 'failed')),
        processing_time_ms INTEGER,
        cached INTEGER DEFAULT 0,
        cache_expiry DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
      )
    `);
    
    // Create indexes
    this.db.exec('CREATE INDEX IF NOT EXISTS idx_evaluations_user_id ON evaluations(user_id)');
    this.db.exec('CREATE INDEX IF NOT EXISTS idx_evaluations_created_at ON evaluations(created_at DESC)');
    this.db.exec('CREATE INDEX IF NOT EXISTS idx_evaluations_suitability_score ON evaluations(prediction_suitability_score DESC)');
    this.db.exec('CREATE INDEX IF NOT EXISTS idx_evaluations_category ON evaluations(prediction_category)');
    this.db.exec('CREATE INDEX IF NOT EXISTS idx_evaluations_cached ON evaluations(cached, cache_expiry)');
    this.db.exec('CREATE INDEX IF NOT EXISTS idx_evaluations_status ON evaluations(status)');
    this.db.exec('CREATE INDEX IF NOT EXISTS idx_evaluations_location ON evaluations(features_geographic_latitude, features_geographic_longitude)');
  }

  async create(evaluationData) {
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
      status = 'completed',
      processingTimeMs,
      cached = false,
      cacheExpiry
    } = evaluationData;

    const stmt = this.db.prepare(`
      INSERT INTO evaluations (
        user_id, location_type, location_coords, region,
        features_climate_avg_temp_year, features_climate_avg_temp_growing_season,
        features_climate_min_temp_winter, features_climate_max_temp_summer,
        features_climate_growing_degree_days, features_climate_rainfall_year,
        features_climate_rainfall_summer, features_climate_humidity_avg,
        features_climate_sunshine_hours, features_climate_frost_days,
        features_climate_huglin_index, features_climate_cool_night_index,
        features_relief_elevation, features_relief_slope, features_relief_aspect,
        features_relief_tpi, features_relief_insolation, features_relief_distance_to_sea,
        features_soil_soil_type, features_soil_soil_ph, features_soil_organic_matter,
        features_soil_soil_drainage, features_soil_soil_texture,
        features_satellite_ndvi, features_satellite_ndwi, features_satellite_cloud_coverage,
        features_geographic_latitude, features_geographic_longitude, features_geographic_distance_to_river,
        prediction_suitability_score, prediction_category, prediction_confidence, prediction_model_version,
        shap_values, top_factors,
        risks_frost_level, risks_frost_description,
        risks_drought_level, risks_drought_description,
        risks_heatwave_level, risks_heatwave_description,
        recommendations_suitable_varieties, recommendations_planting_advice, recommendations_irrigation_needs,
        status, processing_time_ms, cached, cache_expiry
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    const result = stmt.run(
      userId,
      location.type,
      JSON.stringify(location.coordinates),
      region || null,
      features?.climate?.avg_temp_year || null,
      features?.climate?.avg_temp_growing_season || null,
      features?.climate?.min_temp_winter || null,
      features?.climate?.max_temp_summer || null,
      features?.climate?.growing_degree_days || null,
      features?.climate?.rainfall_year || null,
      features?.climate?.rainfall_summer || null,
      features?.climate?.humidity_avg || null,
      features?.climate?.sunshine_hours || null,
      features?.climate?.frost_days || null,
      features?.climate?.huglin_index || null,
      features?.climate?.cool_night_index || null,
      features?.relief?.elevation || null,
      features?.relief?.slope || null,
      features?.relief?.aspect || null,
      features?.relief?.tpi || null,
      features?.relief?.insolation || null,
      features?.relief?.distance_to_sea || null,
      features?.soil?.soil_type || null,
      features?.soil?.soil_ph || null,
      features?.soil?.organic_matter || null,
      features?.soil?.soil_drainage || null,
      features?.soil?.soil_texture || null,
      features?.satellite?.ndvi || null,
      features?.satellite?.ndwi || null,
      features?.satellite?.cloud_coverage || null,
      features?.geographic?.latitude || null,
      features?.geographic?.longitude || null,
      features?.geographic?.distance_to_river || null,
      prediction.suitability_score,
      prediction.category,
      prediction.confidence || 'medium',
      prediction.model_version || '1.0.0',
      shapValues ? JSON.stringify(shapValues) : null,
      topFactors ? JSON.stringify(topFactors) : null,
      risks?.frost_risk?.level || null,
      risks?.frost_risk?.description || null,
      risks?.drought_risk?.level || null,
      risks?.drought_risk?.description || null,
      risks?.heatwave_risk?.level || null,
      risks?.heatwave_risk?.description || null,
      recommendations?.suitable_varieties ? JSON.stringify(recommendations.suitable_varieties) : null,
      recommendations?.planting_advice || null,
      recommendations?.irrigation_needs || null,
      status,
      processingTimeMs || null,
      cached ? 1 : 0,
      cacheExpiry || null
    );

    return this.findById(result.lastInsertRowid);
  }

  findById(id) {
    const row = this.db.prepare('SELECT * FROM evaluations WHERE id = ?').get(id);
    if (!row) return null;
    
    return this._mapRowToEvaluation(row);
  }

  findByUserId(userId, limit = 50, offset = 0) {
    const rows = this.db.prepare(
      'SELECT * FROM evaluations WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?'
    ).all(userId, limit, offset);
    
    return rows.map(row => this._mapRowToEvaluation(row));
  }

  findCached(latitude, longitude) {
    const row = this.db.prepare(`
      SELECT * FROM evaluations 
      WHERE features_geographic_latitude = ? 
        AND features_geographic_longitude = ? 
        AND cached = 1 
        AND (cache_expiry IS NULL OR cache_expiry > datetime('now'))
      LIMIT 1
    `).get(latitude, longitude);
    
    return row ? this._mapRowToEvaluation(row) : null;
  }

  findNear(latitude, longitude, maxDistanceKm = 50, limit = 10) {
    // Simple distance calculation using Haversine formula approximation
    const rows = this.db.prepare(`
      SELECT *, 
        (6371 * acos(
          cos(radians(?)) * cos(radians(features_geographic_latitude)) * 
          cos(radians(features_geographic_longitude) - radians(?)) + 
          sin(radians(?)) * sin(radians(features_geographic_latitude))
        )) AS distance
      FROM evaluations
      WHERE features_geographic_latitude IS NOT NULL
        AND features_geographic_longitude IS NOT NULL
      HAVING distance <= ?
      ORDER BY distance ASC
      LIMIT ?
    `).all(latitude, longitude, latitude, maxDistanceKm, limit);
    
    return rows.map(row => this._mapRowToEvaluation(row));
  }

  _mapRowToEvaluation(row) {
    return {
      _id: row.id,
      id: row.id,
      user: row.user_id,
      location: {
        type: row.location_type,
        coordinates: JSON.parse(row.location_coords)
      },
      region: row.region,
      features: {
        climate: {
          avg_temp_year: row.features_climate_avg_temp_year,
          avg_temp_growing_season: row.features_climate_avg_temp_growing_season,
          min_temp_winter: row.features_climate_min_temp_winter,
          max_temp_summer: row.features_climate_max_temp_summer,
          growing_degree_days: row.features_climate_growing_degree_days,
          rainfall_year: row.features_climate_rainfall_year,
          rainfall_summer: row.features_climate_rainfall_summer,
          humidity_avg: row.features_climate_humidity_avg,
          sunshine_hours: row.features_climate_sunshine_hours,
          frost_days: row.features_climate_frost_days,
          huglin_index: row.features_climate_huglin_index,
          cool_night_index: row.features_climate_cool_night_index
        },
        relief: {
          elevation: row.features_relief_elevation,
          slope: row.features_relief_slope,
          aspect: row.features_relief_aspect,
          tpi: row.features_relief_tpi,
          insolation: row.features_relief_insolation,
          distance_to_sea: row.features_relief_distance_to_sea
        },
        soil: {
          soil_type: row.features_soil_soil_type,
          soil_ph: row.features_soil_soil_ph,
          organic_matter: row.features_soil_organic_matter,
          soil_drainage: row.features_soil_soil_drainage,
          soil_texture: row.features_soil_soil_texture
        },
        satellite: {
          ndvi: row.features_satellite_ndvi,
          ndwi: row.features_satellite_ndwi,
          cloud_coverage: row.features_satellite_cloud_coverage
        },
        geographic: {
          latitude: row.features_geographic_latitude,
          longitude: row.features_geographic_longitude,
          distance_to_river: row.features_geographic_distance_to_river
        }
      },
      prediction: {
        suitability_score: row.prediction_suitability_score,
        category: row.prediction_category,
        confidence: row.prediction_confidence,
        model_version: row.prediction_model_version
      },
      shap_values: row.shap_values ? JSON.parse(row.shap_values) : [],
      top_factors: row.top_factors ? JSON.parse(row.top_factors) : [],
      risks: {
        frost_risk: {
          level: row.risks_frost_level,
          description: row.risks_frost_description
        },
        drought_risk: {
          level: row.risks_drought_level,
          description: row.risks_drought_description
        },
        heatwave_risk: {
          level: row.risks_heatwave_level,
          description: row.risks_heatwave_description
        }
      },
      recommendations: {
        suitable_varieties: row.recommendations_suitable_varieties ? JSON.parse(row.recommendations_suitable_varieties) : [],
        planting_advice: row.recommendations_planting_advice,
        irrigation_needs: row.recommendations_irrigation_needs
      },
      status: row.status,
      processing_time_ms: row.processing_time_ms,
      cached: row.cached === 1,
      cache_expiry: row.cache_expiry,
      createdAt: row.created_at,
      updatedAt: row.updated_at
    };
  }

  countByUserId(userId) {
    const result = this.db.prepare('SELECT COUNT(*) as count FROM evaluations WHERE user_id = ?').get(userId);
    return result.count;
  }
}

let evaluationModelInstance = null;

function getEvaluationModel() {
  if (!evaluationModelInstance) {
    evaluationModelInstance = new Evaluation(getDb());
  }
  return evaluationModelInstance;
}

module.exports = getEvaluationModel();
module.exports.getEvaluationModel = getEvaluationModel;
