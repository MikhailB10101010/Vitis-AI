/**
 * Evaluation Routes
 * Оценка пригодности участков для виноделия
 * 
 * FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010
 * FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-018
 * FR-019, FR-020, FR-021, FR-022, FR-023, FR-025, FR-026, FR-034
 */

const express = require('express');
const router = express.Router();
const { body, validationResult } = require('express-validator');
const Evaluation = require('../models/Evaluation');

// ============================================
// Validation Rules
// ============================================

const evaluateValidation = [
  body('latitude')
    .isFloat({ min: -90, max: 90 })
    .withMessage('Latitude must be between -90 and 90'),
  
  body('longitude')
    .isFloat({ min: -180, max: 180 })
    .withMessage('Longitude must be between -180 and 180'),
  
  body('region').optional().trim(),
  
  // Optional polygon coordinates
  body('polygon').optional().isArray()
];

// ============================================
// Helper Functions (Mock implementations)
// ============================================

/**
 * Mock function to get climate data from external API
 * В реальности здесь будет интеграция с ERA5, Open-Meteo и т.д.
 */
async function getClimateData(latitude, longitude) {
  // TODO: Implement real API integration
  return {
    avg_temp_year: 12.5,
    avg_temp_growing_season: 18.3,
    min_temp_winter: -5.2,
    max_temp_summer: 32.1,
    growing_degree_days: 2850, // GDD - Winkler index
    rainfall_year: 650,
    rainfall_summer: 180,
    humidity_avg: 65,
    sunshine_hours: 2200,
    frost_days: 45,
    huglin_index: 2400,
    cool_night_index: 14
  };
}

/**
 * Mock function to get relief data from SRTM DEM
 */
async function getReliefData(latitude, longitude) {
  // TODO: Implement real API integration with Google Earth Engine / NASA Earthdata
  return {
    elevation: 150, // meters
    slope: 5.2, // degrees
    aspect: 180, // degrees (south-facing)
    tpi: 0.3, // Topographic Position Index
    insolation: 4.5, // solar radiation kWh/m²/day
    distance_to_sea: 50 // km
  };
}

/**
 * Mock function to get soil data from SoilGrids
 */
async function getSoilData(latitude, longitude) {
  // TODO: Implement real API integration
  return {
    soil_type: 'Chernozem',
    soil_ph: 7.2,
    organic_matter: 3.5, // %
    soil_drainage: 'well-drained',
    soil_texture: 'loam'
  };
}

/**
 * Mock function to get satellite data
 */
async function getSatelliteData(latitude, longitude) {
  // TODO: Implement Sentinel-2 integration
  return {
    ndvi: 0.65,
    ndwi: 0.25,
    cloud_coverage: 5
  };
}

/**
 * Mock ML model prediction
 * В реальности здесь будет загрузка CatBoost модели и предсказание
 */
function predictSuitability(features) {
  // TODO: Load real CatBoost model from .pkl file
  // Simple mock calculation based on key features
  let score = 50;
  
  // Growing degree days (optimal: 2500-3500)
  const gdd = features.climate.growing_degree_days || 2500;
  if (gdd >= 2500 && gdd <= 3500) score += 15;
  else if (gdd >= 2000 && gdd <= 4000) score += 5;
  
  // Elevation (optimal: 100-500m for most varieties)
  const elev = features.relief.elevation || 200;
  if (elev >= 100 && elev <= 500) score += 10;
  
  // Slope (optimal: 2-15 degrees for drainage)
  const slope = features.relief.slope || 5;
  if (slope >= 2 && slope <= 15) score += 10;
  
  // Soil pH (optimal: 6.0-7.5 for grapes)
  const ph = features.soil.soil_ph || 7.0;
  if (ph >= 6.0 && ph <= 7.5) score += 10;
  
  // Add some randomness for demo
  score += Math.random() * 10 - 5;
  
  // Clamp to 0-100
  return Math.max(0, Math.min(100, Math.round(score)));
}

/**
 * Generate SHAP values (mock)
 */
function generateSHAPValues(features) {
  // TODO: Implement real SHAP calculation
  return [
    { feature_name: 'growing_degree_days', value: 12.5, impact: 'positive' },
    { feature_name: 'elevation', value: 8.3, impact: 'positive' },
    { feature_name: 'slope', value: 6.2, impact: 'positive' },
    { feature_name: 'soil_ph', value: 4.1, impact: 'positive' },
    { feature_name: 'rainfall_summer', value: -2.3, impact: 'negative' },
    { feature_name: 'frost_days', value: -3.5, impact: 'negative' },
    { feature_name: 'humidity_avg', value: 1.8, impact: 'positive' }
  ];
}

/**
 * Generate recommendations based on prediction
 */
function generateRecommendations(score, features) {
  const varieties = {
    high: ['Саперави', 'Красностоп', 'Ркацители', 'Мускат'],
    medium: ['Каберне Совиньон', 'Мерло', 'Шардоне'],
    low: ['Изабелла', 'Лидия']
  };
  
  let category = 'low';
  if (score >= 70) category = 'high';
  else if (score >= 40) category = 'medium';
  
  return {
    suitable_varieties: varieties[category],
    planting_advice: category === 'high' 
      ? 'Отличные условия для коммерческого виноградарства' 
      : category === 'medium'
      ? 'Требуется дополнительный анализ и уход'
      : 'Высокий риск неудачи, рекомендуется выбрать другой участок',
    irrigation_needs: features.climate.rainfall_summer < 200 
      ? 'Требуется регулярный полив' 
      : 'Естественных осадков достаточно'
  };
}

// ============================================
// Routes
// ============================================

/**
 * POST /api/evaluate
 * Оценить пригодность участка для виноделия
 * 
 * Request:
 * {
 *   "latitude": 45.0456,
 *   "longitude": 38.9765,
 *   "region": "Краснодарский край" (optional)
 * }
 */
router.post('/', evaluateValidation, async (req, res, next) => {
  const startTime = Date.now();
  
  try {
    // Check validation errors
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        message: 'Validation failed',
        errors: errors.array()
      });
    }

    const { latitude, longitude, region, polygon } = req.body;
    const userId = req.user._id;

    // Check cache first (TTL 24 hours per FR-023)
    const cached = Evaluation.findCached(latitude, longitude);
    if (cached) {
      return res.json({
        success: true,
        message: 'Result from cache',
        cached: true,
        data: cached
      });
    }

    // Validate region (Southern Russia check per FR-025)
    // TODO: Implement proper geofencing for Southern Russia
    const isSouthernRussia = latitude > 43 && latitude < 48 && longitude > 35 && longitude < 45;
    if (!isSouthernRussia && process.env.NODE_ENV === 'production') {
      return res.status(400).json({
        success: false,
        message: 'Координаты должны находиться в регионе Юга России'
      });
    }

    // Gather features from various sources (parallel execution)
    const [climate, relief, soil, satellite] = await Promise.all([
      getClimateData(latitude, longitude),
      getReliefData(latitude, longitude),
      getSoilData(latitude, longitude),
      getSatelliteData(latitude, longitude)
    ]);

    // Compile all features
    const features = {
      climate,
      relief,
      soil,
      satellite,
      geographic: {
        latitude,
        longitude,
        distance_to_river: 0 // TODO: Calculate
      }
    };

    // Make prediction
    const suitabilityScore = predictSuitability(features);
    
    // Generate SHAP values
    const shapValues = generateSHAPValues(features);
    
    // Get top factors
    const topFactors = shapValues
      .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
      .slice(0, 5)
      .map(item => ({
        factor: item.feature_name,
        influence: Math.abs(item.value),
        direction: item.impact === 'positive' ? '+' : '-'
      }));

    // Generate recommendations
    const recommendations = generateRecommendations(suitabilityScore, features);

    // Determine risk levels
    const risks = {
      frost_risk: {
        level: climate.frost_days > 60 ? 'high' : climate.frost_days > 30 ? 'medium' : 'low',
        description: `Вероятность заморозков: ${climate.frost_days} дней/год`
      },
      drought_risk: {
        level: climate.rainfall_year < 400 ? 'high' : climate.rainfall_year < 600 ? 'medium' : 'low',
        description: `Годовое количество осадков: ${climate.rainfall_year} мм`
      },
      heatwave_risk: {
        level: climate.max_temp_summer > 35 ? 'high' : climate.max_temp_summer > 30 ? 'medium' : 'low',
        description: `Максимальная температура лета: ${climate.max_temp_summer}°C`
      }
    };

    // Create evaluation record
    const evaluationData = {
      userId,
      location: {
        type: polygon ? 'Polygon' : 'Point',
        coordinates: polygon || [longitude, latitude]
      },
      region: region || 'Юг России',
      features,
      prediction: {
        suitability_score: suitabilityScore,
        category: suitabilityScore >= 70 ? 'high' : suitabilityScore >= 40 ? 'medium' : 'low',
        confidence: 'medium',
        model_version: '1.0.0'
      },
      shapValues,
      topFactors,
      risks,
      recommendations,
      processingTimeMs: Date.now() - startTime,
      cached: false,
      cacheExpiry: new Date(Date.now() + 24 * 60 * 60 * 1000) // 24 hours TTL
    };

    const evaluation = await Evaluation.create(evaluationData);

    // Update user's evaluation count (optional, not critical)
    try {
      const User = require('../models/User');
      const db = require('../models/User').getDb();
      db.prepare('UPDATE users SET evaluation_count = evaluation_count + 1 WHERE id = ?').run(userId);
    } catch (e) {
      // Ignore errors in updating count
    }

    const processingTime = Date.now() - startTime;

    res.json({
      success: true,
      message: 'Evaluation completed',
      cached: false,
      processing_time_ms: processingTime,
      data: evaluation
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/evaluate/:id
 * Получить результаты оценки по ID
 */
router.get('/:id', async (req, res, next) => {
  try {
    const evaluation = Evaluation.findById(parseInt(req.params.id));

    if (!evaluation || evaluation.user !== req.user.id) {
      return res.status(404).json({
        success: false,
        message: 'Evaluation not found'
      });
    }

    res.json({
      success: true,
      data: evaluation
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/evaluate/geojson
 * Экспорт оценок в формате GeoJSON
 */
router.get('/geojson', async (req, res, next) => {
  try {
    const evaluations = Evaluation.findByUserId(req.user.id, 100);

    const geojson = {
      type: 'FeatureCollection',
      features: evaluations.map(e => ({
        type: 'Feature',
        geometry: e.location,
        properties: {
          id: e.id,
          suitability_score: e.prediction.suitability_score,
          category: e.prediction.category,
          region: e.region,
          created_at: e.createdAt
        }
      }))
    };

    res.json({
      success: true,
      data: geojson
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
