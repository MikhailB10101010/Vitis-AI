/**
 * Evaluation Model
 * Модель оценки участка для виноделия
 * 
 * Хранит:
 * - GeoJSON координаты участка (точка или полигон)
 * - Признаки (features) из различных источников
 * - Результаты ML-модели (вероятность пригодности)
 * - SHAP values для интерпретации
 * - Историю оценок пользователя
 */

const mongoose = require('mongoose');

const evaluationSchema = new mongoose.Schema({
  // Reference to user
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  
  // Location data (GeoJSON)
  location: {
    type: {
      type: String,
      enum: ['Point', 'Polygon'],
      required: true
    },
    coordinates: {
      type: [Number], // For Point: [longitude, latitude], for Polygon: [[[lon, lat], ...]]
      required: true
    }
  },
  
  // Address/region information
  region: {
    type: String,
    trim: true
  },
  
  // Features from various sources
  features: {
    // Climate features (ERA5, Open-Meteo)
    climate: {
      avg_temp_year: Number,
      avg_temp_growing_season: Number,
      min_temp_winter: Number,
      max_temp_summer: Number,
      growing_degree_days: Number, // GDD - Winkler index
      rainfall_year: Number,
      rainfall_summer: Number,
      humidity_avg: Number,
      sunshine_hours: Number,
      frost_days: Number,
      huglin_index: Number,
      cool_night_index: Number
    },
    
    // Relief features (SRTM DEM)
    relief: {
      elevation: Number, // meters
      slope: Number, // degrees
      aspect: Number, // degrees (0-360)
      tpi: Number, // Topographic Position Index
      insolation: Number, // solar radiation
      distance_to_sea: Number // km
    },
    
    // Soil features (SoilGrids)
    soil: {
      soil_type: String,
      soil_ph: Number,
      organic_matter: Number, // %
      soil_drainage: String,
      soil_texture: String
    },
    
    // Satellite data (Sentinel-2)
    satellite: {
      ndvi: Number, // Normalized Difference Vegetation Index
      ndwi: Number, // Normalized Difference Water Index
      cloud_coverage: Number // %
    },
    
    // Geographic features
    geographic: {
      latitude: Number,
      longitude: Number,
      distance_to_river: Number // km
    }
  },
  
  // ML Model results
  prediction: {
    // Probability of suitability (0-100%)
    suitability_score: {
      type: Number,
      required: true,
      min: 0,
      max: 100
    },
    
    // Suitability category
    category: {
      type: String,
      enum: ['low', 'medium', 'high'],
      required: true
    },
    
    // Model confidence
    confidence: {
      type: String,
      enum: ['low', 'medium', 'high'],
      default: 'medium'
    },
    
    // Model version
    model_version: {
      type: String,
      default: '1.0.0'
    }
  },
  
  // SHAP values for interpretability
  shap_values: [{
    feature_name: String,
    value: Number,
    impact: String // 'positive' or 'negative'
  }],
  
  // Top influencing factors
  top_factors: [{
    factor: String,
    influence: Number,
    direction: String // '+' or '-'
  }],
  
  // Risk assessment
  risks: {
    frost_risk: {
      level: { type: String, enum: ['low', 'medium', 'high'] },
      description: String
    },
    drought_risk: {
      level: { type: String, enum: ['low', 'medium', 'high'] },
      description: String
    },
    heatwave_risk: {
      level: { type: String, enum: ['low', 'medium', 'high'] },
      description: String
    }
  },
  
  // Recommendations
  recommendations: {
    suitable_varieties: [String], // e.g., ['Саперави', 'Красностоп']
    planting_advice: String,
    irrigation_needs: String
  },
  
  // Metadata
  status: {
    type: String,
    enum: ['pending', 'completed', 'failed'],
    default: 'completed'
  },
  
  processing_time_ms: Number,
  
  // Cache control
  cached: {
    type: Boolean,
    default: false
  },
  
  cache_expiry: Date
}, {
  timestamps: true
});

// ============================================
// Indexes
// ============================================

// 2dsphere index for geospatial queries
evaluationSchema.index({ location: '2dsphere' });

// Indexes for common queries
evaluationSchema.index({ user: 1, createdAt: -1 });
evaluationSchema.index({ 'prediction.suitability_score': -1 });
evaluationSchema.index({ 'prediction.category': 1 });
evaluationSchema.index({ cached: 1, cache_expiry: 1 });
evaluationSchema.index({ status: 1 });

// Compound index for user's evaluations in a region
evaluationSchema.index({ user: 1, region: 1, createdAt: -1 });

// ============================================
// Methods
// ============================================

// Determine suitability category based on score
evaluationSchema.methods.categorizeScore = function() {
  const score = this.prediction.suitability_score;
  if (score < 40) {
    this.prediction.category = 'low';
  } else if (score < 70) {
    this.prediction.category = 'medium';
  } else {
    this.prediction.category = 'high';
  }
};

// Check if cache is expired
evaluationSchema.methods.isCacheExpired = function() {
  if (!this.cached || !this.cache_expiry) {
    return true;
  }
  return new Date() > this.cache_expiry;
};

// Convert to GeoJSON format
evaluationSchema.methods.toGeoJSON = function() {
  return {
    type: 'Feature',
    geometry: this.location,
    properties: {
      id: this._id,
      suitability_score: this.prediction.suitability_score,
      category: this.prediction.category,
      region: this.region,
      created_at: this.createdAt
    }
  };
};

// ============================================
// Static Methods
// ============================================

// Find evaluations near a point
evaluationSchema.statics.findNear = function(longitude, latitude, maxDistance = 50000, limit = 10) {
  return this.find({
    location: {
      $near: {
        $geometry: {
          type: 'Point',
          coordinates: [longitude, latitude]
        },
        $maxDistance: maxDistance
      }
    }
  }).limit(limit);
};

// Get cached evaluation
evaluationSchema.statics.findCached = function(longitude, latitude) {
  return this.findOne({
    'features.geographic.latitude': latitude,
    'features.geographic.longitude': longitude,
    cached: true,
    cache_expiry: { $gt: new Date() }
  });
};

const Evaluation = mongoose.model('Evaluation', evaluationSchema);

module.exports = Evaluation;
