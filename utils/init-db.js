/**
 * Database initialization script for SQLite (sql.js)
 * Creates tables and indexes for Vitis-AI application
 */

const initSqlJs = require('sql.js');
const path = require('path');
const fs = require('fs');

const DB_PATH = path.join(__dirname, '../data/vitis_ai.db');

async function initDatabase() {
  // Initialize sql.js
  const SQL = await initSqlJs();
  
  // Ensure data directory exists
  const dataDir = path.dirname(DB_PATH);
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }
  
  console.log(`📁 Database path: ${DB_PATH}`);
  
  // Load existing database or create new one
  let db;
  if (fs.existsSync(DB_PATH)) {
    const fileBuffer = fs.readFileSync(DB_PATH);
    db = new SQL.Database(fileBuffer);
    console.log('📂 Loading existing database...');
  } else {
    db = new SQL.Database();
    console.log('🆕 Creating new database...');
  }
  
  console.log('🔧 Initializing database...');
  
  try {
    // Enable foreign keys
    db.run('PRAGMA foreign_keys = ON');
    
    // Create users table
    db.run(`
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user' CHECK(role IN ('user', 'admin')),
        full_name TEXT,
        organization TEXT,
        is_active BOOLEAN DEFAULT 1,
        is_verified BOOLEAN DEFAULT 0,
        last_login DATETIME,
        evaluation_count INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Create evaluations table
    db.run(`
      CREATE TABLE IF NOT EXISTS evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        location_type TEXT CHECK(location_type IN ('Point', 'Polygon')) NOT NULL,
        location_coords TEXT NOT NULL,
        region TEXT,
        
        -- Climate features
        climate_avg_temp_year REAL,
        climate_avg_temp_growing_season REAL,
        climate_min_temp_winter REAL,
        climate_max_temp_summer REAL,
        climate_growing_degree_days REAL,
        climate_rainfall_year REAL,
        climate_rainfall_summer REAL,
        climate_humidity_avg REAL,
        climate_sunshine_hours REAL,
        climate_frost_days REAL,
        climate_huglin_index REAL,
        climate_cool_night_index REAL,
        
        -- Relief features
        relief_elevation REAL,
        relief_slope REAL,
        relief_aspect REAL,
        relief_tpi REAL,
        relief_insolation REAL,
        relief_distance_to_sea REAL,
        
        -- Soil features
        soil_soil_type TEXT,
        soil_soil_ph REAL,
        soil_organic_matter REAL,
        soil_soil_drainage TEXT,
        soil_soil_texture TEXT,
        
        -- Satellite features
        satellite_ndvi REAL,
        satellite_ndwi REAL,
        satellite_cloud_coverage REAL,
        
        -- Geographic features
        geo_latitude REAL,
        geo_longitude REAL,
        geo_distance_to_river REAL,
        
        -- Prediction results
        suitability_score REAL NOT NULL,
        category TEXT CHECK(category IN ('low', 'medium', 'high')) NOT NULL,
        confidence TEXT DEFAULT 'medium' CHECK(confidence IN ('low', 'medium', 'high')),
        model_version TEXT DEFAULT '1.0.0',
        
        -- SHAP values (JSON array)
        shap_values TEXT,
        
        -- Top factors (JSON array)
        top_factors TEXT,
        
        -- Risk assessment (JSON object)
        risks TEXT,
        
        -- Recommendations (JSON object)
        recommendations TEXT,
        
        -- Metadata
        status TEXT DEFAULT 'completed' CHECK(status IN ('pending', 'completed', 'failed')),
        processing_time_ms INTEGER,
        cached BOOLEAN DEFAULT 0,
        cache_expiry DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
      )
    `);

    // Create indexes
    console.log('📇 Creating indexes...');
    
    db.run(`CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)`);
    db.run(`CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)`);
    db.run(`CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)`);
    
    db.run(`CREATE INDEX IF NOT EXISTS idx_evaluations_user_id ON evaluations(user_id)`);
    db.run(`CREATE INDEX IF NOT EXISTS idx_evaluations_created_at ON evaluations(created_at DESC)`);
    db.run(`CREATE INDEX IF NOT EXISTS idx_evaluations_suitability_score ON evaluations(suitability_score DESC)`);
    db.run(`CREATE INDEX IF NOT EXISTS idx_evaluations_category ON evaluations(category)`);
    db.run(`CREATE INDEX IF NOT EXISTS idx_evaluations_cached ON evaluations(cached, cache_expiry)`);
    db.run(`CREATE INDEX IF NOT EXISTS idx_evaluations_status ON evaluations(status)`);
    db.run(`CREATE INDEX IF NOT EXISTS idx_evaluations_region ON evaluations(region)`);
    
    // Composite index for user's evaluations
    db.run(`CREATE INDEX IF NOT EXISTS idx_evaluations_user_created ON evaluations(user_id, created_at DESC)`);
    
    // Index for geospatial queries (using latitude/longitude)
    db.run(`CREATE INDEX IF NOT EXISTS idx_evaluations_coords ON evaluations(geo_latitude, geo_longitude)`);

    // Create triggers for updated_at
    db.run(`
      CREATE TRIGGER IF NOT EXISTS update_users_updated_at 
      AFTER UPDATE ON users
      BEGIN
        UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
      END
    `);

    db.run(`
      CREATE TRIGGER IF NOT EXISTS update_evaluations_updated_at 
      AFTER UPDATE ON evaluations
      BEGIN
        UPDATE evaluations SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
      END
    `);

    // Save database to file
    const data = db.export();
    const buffer = Buffer.from(data);
    fs.writeFileSync(DB_PATH, buffer);
    
    console.log('✅ Database initialized successfully!');
    console.log(`📊 Database file: ${DB_PATH}`);

  } catch (error) {
    console.error('❌ Database initialization error:', error.message);
    process.exit(1);
  } finally {
    db.close();
  }
}

initDatabase();
